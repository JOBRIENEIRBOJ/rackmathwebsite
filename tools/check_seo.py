#!/usr/bin/env python3
"""Validate basic SEO requirements for published RackMath pages."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "content" / "seo-pages.json"
SITEMAP_PATH = ROOT / "sitemap.xml"


def page_path(slug: str) -> Path:
    if slug.endswith("/"):
        return ROOT / slug.strip("/") / "index.html"
    return ROOT / slug.lstrip("/")


def count(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def main() -> int:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    sitemap = SITEMAP_PATH.read_text(encoding="utf-8") if SITEMAP_PATH.exists() else ""
    errors: list[str] = []

    for page in registry["pages"]:
        if page.get("status") != "published":
            continue

        slug = page["slug"]
        path = page_path(slug)
        if not path.exists():
            errors.append(f"{slug}: missing generated file {path.relative_to(ROOT)}")
            continue

        html = path.read_text(encoding="utf-8")
        checks = [
            (count(r"<title\b", html) == 1, "must have exactly one title tag"),
            (count(r'<meta\s+name="description"', html) == 1, "must have exactly one meta description"),
            (count(r"<h1\b", html) == 1, "must have exactly one h1"),
            (count(r'rel="canonical"', html) == 1, "must have exactly one canonical"),
            (f"https://www.rackmath.com{slug}" in html, "must contain self-referencing canonical URL"),
            (f"https://www.rackmath.com{slug}" in sitemap, "must be included in sitemap.xml"),
            (count(r"<a\s+[^>]*href=", html) >= 3, "must contain crawlable links"),
        ]
        for ok, message in checks:
            if not ok:
                errors.append(f"{slug}: {message}")

        if page.get("type") == "tool" and "source=seo" not in html:
            errors.append(f"{slug}: tool page must include a source=seo app handoff")

    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    if re.search(r"Disallow:\s*/tools/?\s*$", robots, flags=re.IGNORECASE | re.MULTILINE):
        errors.append("robots.txt blocks /tools/")

    if errors:
        for error in errors:
            print(f"SEO check failed: {error}")
        return 1

    print("SEO checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
