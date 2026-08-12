#!/usr/bin/env python3
"""Stage and validate the public RackMath site in ``dist/``.

The repository contains generated pages alongside their source content and build
tools. Netlify must publish only the explicit public allowlist below so those
source files can never become web-accessible by accident.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

ROOT_PUBLIC_FILES = frozenset(
    {
        "_redirects",
        "about.html",
        "blog.html",
        "faq.html",
        "features.html",
        "index.html",
        "privacy.html",
        "robots.txt",
        "script.js",
        "sitemap.xml",
        "styles.css",
        "terms.html",
    }
)

# These directories are public URL namespaces. Only their generated HTML is
# staged; source files such as tools/*.py are intentionally excluded.
PUBLIC_HTML_DIRECTORIES = frozenset(
    {"blog", "exercises", "features", "for", "programs", "tools", "workouts"}
)

# Assets remain deliberately extension-allowlisted. Add a new public asset type
# here explicitly instead of making arbitrary repository files deployable.
PUBLIC_ASSET_SUFFIXES = frozenset(
    {
        ".avif",
        ".css",
        ".gif",
        ".ico",
        ".jpeg",
        ".jpg",
        ".js",
        ".png",
        ".svg",
        ".ttf",
        ".webp",
        ".woff",
        ".woff2",
    }
)

REQUIRED_PUBLIC_FILES = frozenset(
    {
        "_redirects",
        "assets/rackmathblue-header.png",
        "blog.html",
        "blog/archive.html",
        "index.html",
        "robots.txt",
        "sitemap.xml",
        "tools/barbell-calculator.html",
        "tools/index.html",
    }
)

FINGERPRINT_LENGTH = 12
FINGERPRINT_SOURCES = (
    Path("styles.css"),
    Path("script.js"),
    Path("assets/free-barbell-visualizer.js"),
    Path("assets/lifting-tools.js"),
)
FINGERPRINTED_ROOT_ASSET_PATTERN = re.compile(
    rf"^(?:styles|script)\.[0-9a-f]{{{FINGERPRINT_LENGTH}}}\.(?:css|js)$"
)
ANALYTICS_CONFIG_PATH = Path("assets/analytics-config.js")
ANALYTICS_ENDPOINT_ENV = "RACKMATH_ANALYTICS_URL"
ANALYTICS_ANON_KEY_ENV = "RACKMATH_ANALYTICS_ANON_KEY"
MAIN_SCRIPT_PATTERN = re.compile(
    rf'<script\s+src="(?P<prefix>(?:\.\./)*)script(?:\.[0-9a-f]{{{FINGERPRINT_LENGTH}}})?\.js(?:\?[^" ]*)?"></script>'
)
HTML_ASSET_REFERENCE_PATTERN = re.compile(
    r"(?P<attribute>\b(?:href|src)\s*=\s*)(?P<quote>['\"])(?P<url>[^'\"]+)(?P=quote)",
    re.IGNORECASE,
)


class DistBuildError(RuntimeError):
    """Raised when the deploy artifact is incomplete or unsafe."""


def relative_file_is_allowed(path: Path) -> bool:
    """Return whether a relative path is in the deploy allowlist."""

    if path.is_absolute() or ".." in path.parts or not path.parts:
        return False

    if len(path.parts) == 1:
        return path.name in ROOT_PUBLIC_FILES or bool(
            FINGERPRINTED_ROOT_ASSET_PATTERN.fullmatch(path.name)
        )

    top_level = path.parts[0]
    if top_level == "assets":
        return path.suffix.lower() in PUBLIC_ASSET_SUFFIXES
    if top_level in PUBLIC_HTML_DIRECTORIES:
        return path.suffix.lower() == ".html"
    return False


def copy_public_file(source: Path, destination: Path) -> None:
    """Copy one regular public file without following symbolic links."""

    if source.is_symlink() or not source.is_file():
        raise DistBuildError(f"Public source must be a regular file: {source.relative_to(ROOT)}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def add_analytics_runtime_config(staging: Path) -> bool:
    """Generate and load the optional public analytics runtime configuration."""

    endpoint = os.environ.get(ANALYTICS_ENDPOINT_ENV, "").strip()
    anon_key = os.environ.get(ANALYTICS_ANON_KEY_ENV, "").strip()
    if bool(endpoint) != bool(anon_key):
        raise DistBuildError(
            f"Set both {ANALYTICS_ENDPOINT_ENV} and {ANALYTICS_ANON_KEY_ENV}, or neither"
        )
    if not endpoint:
        return False

    parsed_endpoint = urlsplit(endpoint)
    if parsed_endpoint.scheme != "https" or not parsed_endpoint.netloc:
        raise DistBuildError(f"{ANALYTICS_ENDPOINT_ENV} must be a full HTTPS endpoint URL")

    payload = json.dumps(
        {"endpoint": endpoint, "anonKey": anon_key},
        ensure_ascii=True,
        separators=(",", ":"),
    )
    config_path = staging / ANALYTICS_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        f"window.RACKMATH_ANALYTICS_CONFIG = Object.freeze({payload});\n",
        encoding="utf-8",
    )

    for html_path in sorted(staging.rglob("*.html")):
        html = html_path.read_text(encoding="utf-8")
        match = MAIN_SCRIPT_PATTERN.search(html)
        if not match:
            raise DistBuildError(
                "Analytics config cannot load before the main script in "
                f"{html_path.relative_to(staging)}"
            )
        config_tag = f'<script src="{match.group("prefix")}assets/analytics-config.js"></script>'
        html = f"{html[:match.start()]}{config_tag}\n    {html[match.start():]}"
        html_path.write_text(html, encoding="utf-8")
    return True


def fingerprinted_path(relative: Path, digest: str) -> Path:
    """Return the content-addressed public path for one source asset."""

    return relative.with_name(f"{relative.stem}.{digest}{relative.suffix}")


def local_asset_path(base: Path, html_path: Path, url: str) -> Path | None:
    """Resolve a local HTML asset URL without allowing it to escape ``base``."""

    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None

    decoded_path = unquote(parsed.path)
    candidate = (
        base / decoded_path.lstrip("/")
        if decoded_path.startswith("/")
        else html_path.parent / decoded_path
    )
    resolved_base = base.resolve()
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_base)
    except ValueError as error:
        raise DistBuildError(
            f"Asset reference escapes the deploy directory in {html_path.relative_to(base)}: {url}"
        ) from error
    return resolved_candidate


def fingerprint_public_assets(staging: Path) -> dict[Path, Path]:
    """Fingerprint selected CSS/JS assets and rewrite only staged HTML references."""

    replacements: dict[Path, Path] = {}
    for relative in FINGERPRINT_SOURCES:
        source = staging / relative
        if not source.is_file() or source.is_symlink():
            raise DistBuildError(f"Fingerprint source is missing or unsafe: {relative}")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()[:FINGERPRINT_LENGTH]
        destination_relative = fingerprinted_path(relative, digest)
        destination = staging / destination_relative
        if destination.exists():
            raise DistBuildError(f"Fingerprint destination already exists: {destination_relative}")
        source.replace(destination)
        replacements[source.resolve()] = destination_relative

    reference_counts = {relative: 0 for relative in replacements.values()}
    for html_path in sorted(staging.rglob("*.html")):
        html = html_path.read_text(encoding="utf-8")

        def replace_reference(match: re.Match[str]) -> str:
            url = match.group("url")
            resolved = local_asset_path(staging, html_path, url)
            destination_relative = replacements.get(resolved) if resolved else None
            if destination_relative is None:
                return match.group(0)

            reference_counts[destination_relative] += 1
            if urlsplit(url).path.startswith("/"):
                rewritten = f"/{destination_relative.as_posix()}"
            else:
                rewritten = Path(
                    os.path.relpath(staging / destination_relative, html_path.parent)
                ).as_posix()
            return (
                f"{match.group('attribute')}{match.group('quote')}"
                f"{rewritten}{match.group('quote')}"
            )

        rewritten_html = HTML_ASSET_REFERENCE_PATTERN.sub(replace_reference, html)
        if rewritten_html != html:
            html_path.write_text(rewritten_html, encoding="utf-8")

    unreferenced = [path for path, count in reference_counts.items() if count == 0]
    if unreferenced:
        rendered = ", ".join(path.as_posix() for path in sorted(unreferenced))
        raise DistBuildError(f"Fingerprint assets were not referenced by staged HTML: {rendered}")
    return {source.relative_to(staging): destination for source, destination in replacements.items()}


def route_candidates(base: Path, url_path: str) -> list[Path]:
    """Return safe physical-file candidates for a canonical public URL path."""

    relative = Path(url_path.lstrip("/"))
    if not url_path.startswith("/") or ".." in relative.parts:
        return []

    if url_path.endswith("/"):
        return [base / relative / "index.html"]
    if relative.suffix:
        return [base / relative]
    return [base / relative, base / f"{relative}.html", base / relative / "index.html"]


def route_exists(dist: Path, route: str) -> bool:
    """Return whether an internal sitemap route resolves to a staged HTML file."""

    parsed = urlsplit(route)
    if parsed.scheme and parsed.netloc not in {"rackmath.com", "www.rackmath.com"}:
        return False
    candidates = route_candidates(dist, unquote(parsed.path))
    return any(candidate.is_file() for candidate in candidates)


def sitemap_html_sources() -> set[Path]:
    """Resolve the canonical sitemap inventory to generated source HTML files."""

    sitemap_path = ROOT / "sitemap.xml"
    try:
        sitemap_root = ET.parse(sitemap_path).getroot()
    except (ET.ParseError, OSError) as error:
        raise DistBuildError(f"Cannot stage invalid sitemap.xml: {error}") from error

    sources: set[Path] = set()
    locations = sitemap_root.findall(
        "{http://www.sitemaps.org/schemas/sitemap/0.9}url/"
        "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
    )
    if not locations:
        raise DistBuildError("Cannot stage a sitemap with no URLs")

    for element in locations:
        location = (element.text or "").strip()
        parsed = urlsplit(location)
        if parsed.scheme != "https" or parsed.netloc != "rackmath.com":
            raise DistBuildError(f"Sitemap URL is not canonical: {location}")

        url_path = unquote(parsed.path)
        relative = Path(url_path.lstrip("/"))
        if not url_path.startswith("/") or ".." in relative.parts:
            raise DistBuildError(f"Sitemap URL has an unsafe path: {location}")

        candidates = route_candidates(ROOT, url_path)
        source = next((candidate for candidate in candidates if candidate.is_file()), None)
        if source is None:
            raise DistBuildError(f"Sitemap URL has no generated source file: {location}")

        source_relative = source.relative_to(ROOT)
        if not relative_file_is_allowed(source_relative):
            raise DistBuildError(
                f"Sitemap URL resolves outside the deploy allowlist: {source_relative}"
            )
        if len(source_relative.parts) > 1:
            sources.add(source)
    return sources


def validate_redirects(path: Path) -> list[str]:
    errors: list[str] = []
    rules = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        rules.append(line)
        parts = line.split()
        if len(parts) < 3:
            errors.append(f"_redirects:{line_number} is not a complete redirect rule")
            continue
        source, destination = parts[:2]
        if source.startswith("/") and "*" not in source:
            parsed_destination = urlsplit(destination)
            destination_path = (
                parsed_destination.path
                if parsed_destination.netloc
                else destination.split("?", 1)[0].split("#", 1)[0]
            )
            if source != "/" and source.rstrip("/") == destination_path.rstrip("/"):
                errors.append(
                    f"_redirects:{line_number} creates a trailing-slash-equivalent "
                    f"self-redirect: {source} -> {destination_path}"
                )
    if not rules:
        errors.append("_redirects must contain at least one redirect rule")
    return errors


def validate_sitemap(dist: Path) -> list[str]:
    errors: list[str] = []
    sitemap_path = dist / "sitemap.xml"
    try:
        root = ET.parse(sitemap_path).getroot()
    except (ET.ParseError, OSError) as error:
        return [f"sitemap.xml is not valid XML: {error}"]

    locations = [
        (element.text or "").strip()
        for element in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
    ]
    if not locations:
        errors.append("sitemap.xml must contain at least one URL")
        return errors

    for location in locations:
        parsed = urlsplit(location)
        if parsed.scheme != "https" or parsed.netloc != "rackmath.com":
            errors.append(f"sitemap.xml contains a non-canonical URL: {location}")
        elif not route_exists(dist, location):
            errors.append(f"sitemap.xml URL has no staged file: {location}")
    return errors


def sitemap_html_inventory(dist: Path) -> set[Path]:
    """Return the physical HTML inventory represented by the staged sitemap."""

    try:
        root = ET.parse(dist / "sitemap.xml").getroot()
    except (ET.ParseError, OSError) as error:
        raise DistBuildError(f"Cannot inventory invalid staged sitemap.xml: {error}") from error

    inventory: set[Path] = set()
    for element in root.findall(
        "{http://www.sitemaps.org/schemas/sitemap/0.9}url/"
        "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
    ):
        location = (element.text or "").strip()
        parsed = urlsplit(location)
        if parsed.scheme != "https" or parsed.netloc != "rackmath.com":
            continue
        candidates = route_candidates(dist, unquote(parsed.path))
        staged_file = next((candidate for candidate in candidates if candidate.is_file()), None)
        if staged_file and staged_file.suffix.lower() == ".html":
            inventory.add(staged_file.relative_to(dist))
    return inventory


def validate_fingerprinted_assets(dist: Path) -> tuple[set[Path], list[str]]:
    """Validate one correctly named, content-matching asset per logical source."""

    errors: list[str] = []
    fingerprinted: set[Path] = set()
    for source_relative in FINGERPRINT_SOURCES:
        source = dist / source_relative
        if source.exists():
            errors.append(f"unfingerprinted deploy asset is present: {source_relative}")

        filename_pattern = re.compile(
            rf"^{re.escape(source_relative.stem)}\."
            rf"(?P<digest>[0-9a-f]{{{FINGERPRINT_LENGTH}}})"
            rf"{re.escape(source_relative.suffix)}$"
        )
        matches = [
            candidate
            for candidate in source.parent.glob(
                f"{source_relative.stem}.*{source_relative.suffix}"
            )
            if filename_pattern.fullmatch(candidate.name)
        ]
        if len(matches) != 1:
            errors.append(
                f"expected one fingerprinted asset for {source_relative}, found {len(matches)}"
            )
            continue

        candidate = matches[0]
        if candidate.is_symlink() or not candidate.is_file():
            errors.append(f"fingerprinted deploy asset is unsafe: {candidate.relative_to(dist)}")
            continue

        expected_digest = hashlib.sha256(candidate.read_bytes()).hexdigest()[:FINGERPRINT_LENGTH]
        actual_digest = filename_pattern.fullmatch(candidate.name).group("digest")
        if actual_digest != expected_digest:
            errors.append(
                "fingerprinted asset name does not match its content: "
                f"{candidate.relative_to(dist)}"
            )
        fingerprinted.add(candidate.relative_to(dist))
    return fingerprinted, errors


def validate_html_asset_references(dist: Path, fingerprinted: set[Path]) -> list[str]:
    """Reject missing or unhashed first-party CSS/JS references in staged HTML."""

    errors: list[str] = []
    referenced_fingerprints: set[Path] = set()
    for html_path in sorted(dist.rglob("*.html")):
        html = html_path.read_text(encoding="utf-8")
        for match in HTML_ASSET_REFERENCE_PATTERN.finditer(html):
            url = match.group("url")
            parsed = urlsplit(url)
            if Path(parsed.path).suffix.lower() not in {".css", ".js"}:
                continue

            try:
                resolved = local_asset_path(dist, html_path, url)
            except DistBuildError as error:
                errors.append(str(error))
                continue
            if resolved is None:
                continue

            relative = resolved.relative_to(dist.resolve())
            if not resolved.is_file():
                errors.append(
                    f"missing first-party asset in {html_path.relative_to(dist)}: {url}"
                )
                continue

            if relative in fingerprinted:
                referenced_fingerprints.add(relative)
                continue
            if relative == ANALYTICS_CONFIG_PATH or relative.parts[:2] == ("assets", "vendor"):
                continue
            errors.append(
                "unfingerprinted first-party CSS/JS reference in "
                f"{html_path.relative_to(dist)}: {url}"
            )

    for relative in sorted(fingerprinted - referenced_fingerprints):
        errors.append(f"fingerprinted asset is not referenced by staged HTML: {relative}")
    return errors


def validate_dist(dist: Path = DIST) -> int:
    """Validate that ``dist`` contains all and only public deploy files."""

    if dist.is_symlink() or not dist.is_dir():
        raise DistBuildError(f"Deploy directory is missing or unsafe: {dist}")

    errors: list[str] = []
    relative_files: set[Path] = set()
    for path in dist.rglob("*"):
        relative = path.relative_to(dist)
        if path.is_symlink():
            errors.append(f"symbolic links are forbidden in dist: {relative}")
        elif path.is_file():
            relative_files.add(relative)
            if not relative_file_is_allowed(relative):
                errors.append(f"forbidden deploy artifact: {relative}")

    for required in sorted(REQUIRED_PUBLIC_FILES):
        path = dist / required
        if not path.is_file():
            errors.append(f"required public file is missing: {required}")
        elif path.stat().st_size == 0:
            errors.append(f"required public file is empty: {required}")

    robots = dist / "robots.txt"
    if robots.is_file() and "Sitemap: https://rackmath.com/sitemap.xml" not in robots.read_text(encoding="utf-8"):
        errors.append("robots.txt must advertise the canonical sitemap URL")

    redirects = dist / "_redirects"
    if redirects.is_file():
        errors.extend(validate_redirects(redirects))

    if (dist / "sitemap.xml").is_file():
        errors.extend(validate_sitemap(dist))

        try:
            expected_html = sitemap_html_inventory(dist)
        except DistBuildError as error:
            errors.append(str(error))
            expected_html = set()
        expected_html.update(
            Path(filename) for filename in ROOT_PUBLIC_FILES if filename.endswith(".html")
        )
        for relative in sorted(relative_files):
            if relative.suffix.lower() == ".html" and relative not in expected_html:
                errors.append(f"HTML is not allowlisted by the canonical sitemap: {relative}")

    fingerprinted, fingerprint_errors = validate_fingerprinted_assets(dist)
    errors.extend(fingerprint_errors)
    errors.extend(validate_html_asset_references(dist, fingerprinted))

    analytics_config = dist / ANALYTICS_CONFIG_PATH
    for html_path in sorted(dist.rglob("*.html")):
        html = html_path.read_text(encoding="utf-8")
        main_script = MAIN_SCRIPT_PATTERN.search(html)
        config_position = html.find("analytics-config.js")
        if analytics_config.is_file():
            if not main_script or config_position < 0 or config_position > main_script.start():
                errors.append(
                    "analytics-config.js must load before script.js in "
                    f"{html_path.relative_to(dist)}"
                )
        elif config_position >= 0:
            errors.append(
                f"{html_path.relative_to(dist)} references a missing analytics-config.js"
            )

    if errors:
        rendered = "\n".join(f"- {error}" for error in errors)
        raise DistBuildError(f"Deploy validation failed:\n{rendered}")
    return len(relative_files)


def stage_dist() -> int:
    """Build a validated deploy directory from the explicit public allowlist."""

    staging = Path(tempfile.mkdtemp(prefix=".dist-staging-", dir=ROOT))
    try:
        for filename in sorted(ROOT_PUBLIC_FILES):
            source = ROOT / filename
            if not source.is_file():
                raise DistBuildError(f"Required public source is missing: {filename}")
            copy_public_file(source, staging / filename)

        assets = ROOT / "assets"
        if not assets.is_dir() or assets.is_symlink():
            raise DistBuildError("Public assets directory is missing or unsafe")
        for source in sorted(assets.rglob("*")):
            if not source.is_file():
                continue
            relative = source.relative_to(ROOT)
            if relative == ANALYTICS_CONFIG_PATH:
                raise DistBuildError(
                    f"{ANALYTICS_CONFIG_PATH} is generated at build time and must not exist in source"
                )
            if source.suffix.lower() not in PUBLIC_ASSET_SUFFIXES:
                raise DistBuildError(f"Asset type is not allowlisted: {relative}")
            copy_public_file(source, staging / relative)

        for source in sorted(sitemap_html_sources()):
            copy_public_file(source, staging / source.relative_to(ROOT))

        add_analytics_runtime_config(staging)
        fingerprint_public_assets(staging)

        file_count = validate_dist(staging)

        if DIST.is_symlink():
            raise DistBuildError("Refusing to replace a symbolic-link dist directory")
        if DIST.exists():
            if not DIST.is_dir():
                raise DistBuildError("Refusing to replace a non-directory dist path")
            shutil.rmtree(DIST)
        staging.replace(DIST)
        return file_count
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate the existing dist directory without rebuilding it.",
    )
    args = parser.parse_args()

    try:
        count = validate_dist() if args.validate_only else stage_dist()
    except (DistBuildError, OSError) as error:
        print(error, file=sys.stderr)
        return 1

    action = "Validated" if args.validate_only else "Staged and validated"
    print(f"{action} {count} public file(s) in {DIST.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
