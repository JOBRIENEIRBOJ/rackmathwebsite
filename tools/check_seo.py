#!/usr/bin/env python3
"""Validate RackMath SEO metadata, canonical URLs, links, and redirects."""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, urljoin, urlsplit
from xml.etree import ElementTree as ET

import build_blog
from site_shared import SITE_NAME


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "content" / "seo-pages.json"
SITEMAP_PATH = ROOT / "sitemap.xml"
REDIRECTS_PATH = ROOT / "_redirects"
SITE_URL = "https://rackmath.com"
LEGACY_SITE_NAME = "Rack" + " Math"

BASE_OUTPUTS = {
    ROOT / "index.html": "/",
    ROOT / "features.html": "/features",
    ROOT / "about.html": "/about",
    ROOT / "faq.html": "/faq",
    ROOT / "blog.html": "/blog",
    ROOT / "privacy.html": "/privacy",
    ROOT / "terms.html": "/terms",
    ROOT / "blog" / "archive.html": "/blog/archive",
}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.anchors: list[str] = []
        self.app_links: list[str] = []
        self.canonicals: list[str] = []
        self.og_urls: list[str] = []
        self.og_site_names: list[str] = []
        self.titles: list[str] = []
        self.descriptions: list[str] = []
        self.h1s: list[str] = []
        self.schema_text: list[str] = []
        self._in_title = False
        self._title_parts: list[str] = []
        self._in_h1 = False
        self._h1_parts: list[str] = []
        self._in_schema = False
        self._schema_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "title":
            self._in_title = True
            self._title_parts = []
        elif tag == "h1":
            self._in_h1 = True
            self._h1_parts = []
        elif tag == "a" and values.get("href"):
            self.anchors.append(str(values["href"]))
            if "data-rm-app-link" in values:
                self.app_links.append(str(values["href"]))
        elif tag == "link" and "canonical" in str(values.get("rel", "")).lower().split():
            if values.get("href"):
                self.canonicals.append(str(values["href"]))
        elif tag == "meta" and values.get("property") == "og:url" and values.get("content"):
            self.og_urls.append(str(values["content"]))
        elif tag == "meta" and values.get("property") == "og:site_name" and values.get("content"):
            self.og_site_names.append(str(values["content"]))
        elif tag == "meta" and values.get("name", "").lower() == "description" and values.get("content"):
            self.descriptions.append(" ".join(str(values["content"]).split()))
        elif tag == "script" and values.get("type") == "application/ld+json":
            self._in_schema = True
            self._schema_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._in_title:
            self.titles.append(" ".join("".join(self._title_parts).split()))
            self._in_title = False
            self._title_parts = []
        elif tag == "h1" and self._in_h1:
            self.h1s.append(" ".join("".join(self._h1_parts).split()))
            self._in_h1 = False
            self._h1_parts = []
        elif tag == "script" and self._in_schema:
            self.schema_text.append("".join(self._schema_parts))
            self._in_schema = False
            self._schema_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)
        if self._in_h1:
            self._h1_parts.append(data)
        if self._in_schema:
            self._schema_parts.append(data)


def page_path(slug: str) -> Path:
    if slug.endswith("/"):
        return ROOT / slug.strip("/") / "index.html"
    return ROOT / slug.lstrip("/")


def public_path(page: dict) -> str:
    return build_blog.clean_url_path(page.get("publicPath", page["slug"]))


def count(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def expected_pages(registry: dict, posts: list[build_blog.Post]) -> dict[Path, str]:
    pages = dict(BASE_OUTPUTS)
    for page in registry["pages"]:
        if page.get("status") == "published":
            pages[page_path(page["slug"])] = public_path(page)
    for post in posts:
        pages[post.output_path] = post.url_path
    return pages


def sitemap_locations(errors: list[str]) -> list[str]:
    if not SITEMAP_PATH.exists():
        errors.append("missing sitemap.xml")
        return []
    try:
        root = ET.parse(SITEMAP_PATH).getroot()
    except ET.ParseError as exc:
        errors.append(f"sitemap.xml is not valid XML: {exc}")
        return []
    return [element.text or "" for element in root.findall("{*}url/{*}loc")]


def sitemap_lastmods(errors: list[str]) -> dict[str, str]:
    try:
        root = ET.parse(SITEMAP_PATH).getroot()
    except (ET.ParseError, OSError) as exc:
        errors.append(f"cannot inspect sitemap lastmod values: {exc}")
        return {}

    values: dict[str, str] = {}
    for entry in root.findall("{*}url"):
        location = entry.findtext("{*}loc", default="").strip()
        lastmod = entry.findtext("{*}lastmod", default="").strip()
        if location and lastmod:
            values[location] = lastmod
    return values


def internal_path(href: str, canonical_url: str) -> str | None:
    if href.startswith(("mailto:", "tel:", "javascript:")):
        return None
    resolved = urlsplit(urljoin(canonical_url, href))
    if resolved.netloc and resolved.netloc not in {"rackmath.com", "www.rackmath.com"}:
        return None
    return resolved.path or urlsplit(canonical_url).path


def schema_urls(value: object) -> list[str]:
    if isinstance(value, dict):
        return [url for child in value.values() for url in schema_urls(child)]
    if isinstance(value, list):
        return [url for child in value for url in schema_urls(child)]
    if isinstance(value, str) and value.startswith((f"{SITE_URL}/", "https://www.rackmath.com/")):
        return [value]
    return []


def schema_nodes(value: object) -> list[dict]:
    if isinstance(value, dict):
        return [value, *(node for child in value.values() for node in schema_nodes(child))]
    if isinstance(value, list):
        return [node for child in value for node in schema_nodes(child)]
    return []


def redirect_destination_path(destination: str) -> str:
    parsed = urlsplit(destination)
    return parsed.path if parsed.netloc else destination.split("?", 1)[0].split("#", 1)[0]


def parse_redirects(errors: list[str]) -> dict[str, tuple[str, str]]:
    if not REDIRECTS_PATH.exists():
        errors.append("missing _redirects")
        return {}
    redirects: dict[str, tuple[str, str]] = {}
    for line_number, raw_line in enumerate(REDIRECTS_PATH.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        source, destination, status = parts[:3]
        if source.startswith("/") and "*" not in source:
            destination_path = redirect_destination_path(destination)
            if source != "/" and source.rstrip("/") == destination_path.rstrip("/"):
                errors.append(
                    f"_redirects:{line_number}: trailing-slash-equivalent self-redirect "
                    f"{source} -> {destination_path}"
                )
            if source in redirects and redirects[source] != (destination, status):
                errors.append(f"_redirects:{line_number}: conflicting rule for {source}")
            redirects[source] = (destination, status)
    return redirects


def main() -> int:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    posts = build_blog.load_posts()
    pages = expected_pages(registry, posts)
    canonical_paths = set(pages.values())
    canonical_urls = {f"{SITE_URL}{path}" for path in canonical_paths}
    errors: list[str] = []
    warnings: list[str] = []
    unique_values: dict[str, dict[str, list[str]]] = {
        "title": {},
        "description": {},
        "h1": {},
    }

    if len(canonical_paths) != len(pages):
        owners: dict[str, list[str]] = {}
        for path, canonical in pages.items():
            owners.setdefault(canonical, []).append(str(path.relative_to(ROOT)))
        for canonical, paths in owners.items():
            if len(paths) > 1:
                errors.append(f"{canonical}: duplicate canonical owners: {', '.join(paths)}")

    sitemap_urls = sitemap_locations(errors)
    sitemap_dates = sitemap_lastmods(errors)
    sitemap_set = set(sitemap_urls)
    if len(sitemap_urls) != len(sitemap_set):
        errors.append("sitemap.xml contains duplicate <loc> entries")
    for url in sitemap_urls:
        path = urlsplit(url).path
        if not url.startswith(f"{SITE_URL}/") and url != f"{SITE_URL}/":
            errors.append(f"sitemap.xml contains a non-canonical host: {url}")
        if ".html" in path:
            errors.append(f"sitemap.xml contains an .html URL: {url}")
        if url not in canonical_urls:
            errors.append(f"sitemap.xml contains an unknown canonical URL: {url}")
    for url in sorted(canonical_urls - sitemap_set):
        errors.append(f"sitemap.xml is missing canonical URL: {url}")

    for page in registry["pages"]:
        if page.get("status") != "published" or not page.get("updated"):
            continue
        url = f"{SITE_URL}{public_path(page)}"
        if sitemap_dates.get(url) != page["updated"]:
            errors.append(
                f"sitemap.xml lastmod for {url} is {sitemap_dates.get(url) or 'missing'}, "
                f"expected {page['updated']}"
            )
    for post in posts:
        url = f"{SITE_URL}{post.url_path}"
        expected_date = (post.updated or post.date).isoformat()
        if sitemap_dates.get(url) != expected_date:
            errors.append(
                f"sitemap.xml lastmod for {url} is {sitemap_dates.get(url) or 'missing'}, "
                f"expected {expected_date}"
            )

    for output_path, canonical_path in pages.items():
        label = str(output_path.relative_to(ROOT))
        canonical_url = f"{SITE_URL}{canonical_path}"
        if not output_path.exists():
            errors.append(f"{label}: missing generated file")
            continue

        text = output_path.read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(text)
        checks = [
            (count(r"<title\b", text) == 1, "must have exactly one title tag"),
            (count(r'<meta\s+name="description"', text) == 1, "must have exactly one meta description"),
            (count(r"<h1\b", text) == 1, "must have exactly one h1"),
            (len(parser.canonicals) == 1, "must have exactly one canonical"),
            (parser.og_site_names == [SITE_NAME], f"og:site_name must be {SITE_NAME}"),
            (len(parser.anchors) >= 3, "must contain at least three crawlable links"),
        ]
        for ok, message in checks:
            if not ok:
                errors.append(f"{label}: {message}")

        metadata = {
            "title": parser.titles,
            "description": parser.descriptions,
            "h1": parser.h1s,
        }
        for field, values in metadata.items():
            if len(values) == 1:
                normalized = values[0].casefold()
                unique_values[field].setdefault(normalized, []).append(label)

        if parser.titles and not 30 <= len(parser.titles[0]) <= 65:
            warnings.append(f"{label}: title length is {len(parser.titles[0])} characters")
        if parser.descriptions and not 70 <= len(parser.descriptions[0]) <= 170:
            warnings.append(
                f"{label}: meta description length is {len(parser.descriptions[0])} characters"
            )

        if parser.canonicals and parser.canonicals[0] != canonical_url:
            errors.append(
                f"{label}: canonical is {parser.canonicals[0]}, expected {canonical_url}"
            )
        if ".html" in canonical_path:
            errors.append(f"{label}: canonical path must be extensionless")
        if canonical_path != "/" and canonical_path.endswith("/") != (output_path.name == "index.html"):
            errors.append(f"{label}: hub trailing-slash convention does not match its output path")
        if parser.og_urls and parser.og_urls != [canonical_url]:
            errors.append(f"{label}: og:url must match the canonical URL")
        if LEGACY_SITE_NAME in text:
            errors.append(f"{label}: legacy spaced brand spelling must be {SITE_NAME}")

        homepage_schema_names: dict[str, list[str]] = {
            "WebSite": [],
            "Organization": [],
            "SoftwareApplication": [],
        }
        for raw_schema in parser.schema_text:
            try:
                schema = json.loads(raw_schema)
            except json.JSONDecodeError as exc:
                errors.append(f"{label}: invalid JSON-LD: {exc}")
                continue
            for url in schema_urls(schema):
                if ".html" in urlsplit(url).path:
                    errors.append(f"{label}: schema contains an .html URL: {url}")
            if canonical_path == "/":
                for node in schema_nodes(schema):
                    schema_type = node.get("@type")
                    if schema_type in homepage_schema_names and isinstance(node.get("name"), str):
                        homepage_schema_names[schema_type].append(node["name"])

        if canonical_path == "/":
            for schema_type, names in homepage_schema_names.items():
                if names != [SITE_NAME]:
                    errors.append(
                        f"{label}: homepage {schema_type} name must be exactly {SITE_NAME}; "
                        f"found {names or 'none'}"
                    )

        for href in parser.anchors:
            target_path = internal_path(href, canonical_url)
            if target_path is None:
                continue
            if ".html" in target_path:
                errors.append(f"{label}: internal link uses .html: {href}")
                continue
            if target_path not in canonical_paths:
                alternate = next(
                    (
                        path
                        for path in canonical_paths
                        if path.rstrip("/") == target_path.rstrip("/")
                    ),
                    None,
                )
                if alternate:
                    errors.append(
                        f"{label}: internal link uses {target_path}; canonical spelling is {alternate}"
                    )
                else:
                    errors.append(f"{label}: internal link target is not a published page: {href}")

    for field, values in unique_values.items():
        for labels in values.values():
            if len(labels) > 1:
                errors.append(f"duplicate {field} across pages: {', '.join(labels)}")

    keyword_owners: dict[str, list[str]] = {}
    canonical_owners: dict[str, list[str]] = {}
    allowed_intents = {"informational", "transactional", "commercial"}
    for page in registry["pages"]:
        if page.get("status") != "published":
            continue
        keyword = str(page.get("primaryKeyword", "")).strip().casefold()
        if keyword:
            keyword_owners.setdefault(keyword, []).append(page["slug"])
        else:
            errors.append(f"{page['slug']}: missing primaryKeyword ownership")

        search_intent = str(page.get("searchIntent", "")).strip().casefold()
        if search_intent not in allowed_intents:
            errors.append(
                f"{page['slug']}: searchIntent must be one of {', '.join(sorted(allowed_intents))}"
            )

        if not str(page.get("cluster", "")).strip():
            errors.append(f"{page['slug']}: missing cluster ownership")

        canonical_owner = str(page.get("canonicalOwner", "")).strip()
        expected_owner = public_path(page)
        if canonical_owner != expected_owner:
            errors.append(
                f"{page['slug']}: canonicalOwner is {canonical_owner or 'missing'}, expected {expected_owner}"
            )
        if canonical_owner:
            canonical_owners.setdefault(canonical_owner, []).append(page["slug"])
    for keyword, owners in keyword_owners.items():
        if len(owners) > 1:
            errors.append(f'primary keyword "{keyword}" has multiple owners: {", ".join(owners)}')
    for owner, pages_with_owner in canonical_owners.items():
        if len(pages_with_owner) > 1:
            errors.append(
                f'canonical owner "{owner}" has multiple registry pages: {", ".join(pages_with_owner)}'
            )

    for page in registry["pages"]:
        if page.get("status") != "published" or page.get("type") != "tool":
            continue
        html_text = page_path(page["slug"]).read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(html_text)
        if not parser.app_links:
            errors.append(f"{page['slug']}: tool page must include a tracked app handoff")
            continue
        for href in parser.app_links:
            query = dict(parse_qsl(urlsplit(href).query, keep_blank_values=True))
            if query.get("source") != "seo":
                errors.append(f"{page['slug']}: app handoff must include source=seo: {href}")
            if not query.get("intent"):
                errors.append(f"{page['slug']}: app handoff must include intent: {href}")

    redirects = parse_redirects(errors)
    redirects_text = REDIRECTS_PATH.read_text(encoding="utf-8")
    if "https://www.rackmath.com/* https://rackmath.com/:splat 301!" not in redirects_text:
        errors.append("_redirects: missing forced www to apex canonical-host redirect")
    for source, destination in build_blog.clean_redirect_rules(posts):
        rule = redirects.get(source)
        if not rule:
            errors.append(f"_redirects: missing duplicate-URL redirect {source} -> {destination}")
            continue
        actual_destination, status = rule
        if redirect_destination_path(actual_destination) != destination:
            errors.append(
                f"_redirects: {source} redirects to {actual_destination}, expected {destination}"
            )
        if status != "301!":
            errors.append(f"_redirects: {source} must use a forced permanent 301!")

    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    if re.search(r"Disallow:\s*/tools/?\s*$", robots, flags=re.IGNORECASE | re.MULTILINE):
        errors.append("robots.txt blocks /tools/")

    if errors:
        for error in errors:
            print(f"SEO check failed: {error}")
        print(f"SEO checks failed with {len(errors)} error(s)")
        return 1

    for warning in warnings[:20]:
        print(f"SEO warning: {warning}")
    if len(warnings) > 20:
        print(f"SEO warning: {len(warnings) - 20} additional warnings suppressed")

    print(
        f"SEO checks passed for {len(pages)} pages, "
        f"{len(sitemap_urls)} sitemap URLs, and {len(build_blog.clean_redirect_rules(posts))} redirects"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
