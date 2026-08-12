#!/usr/bin/env python3
"""Shared URL, asset, and document chrome for RackMath static generators."""

from __future__ import annotations

import html
import re
from datetime import date
from urllib.parse import parse_qsl, urlencode, urlsplit


SITE_URL = "https://rackmath.com"
APP_URL = "https://www.rackmath.app"
SITE_NAME = "Rack Math"
BRAND_NAME = "RackMath"

ASSET_VERSION = "20260615"
ASSETS = {
    "brand_mark": "assets/rackmathblue-header.png",
    "icon": "assets/rackmathblue.png",
    "social_image": "assets/rackmathblue-gradient.png",
    "stylesheet": "styles.css",
    "script": "script.js",
}

BASE_PAGES = [
    ("/", "1.0"),
    ("/tools/", "0.9"),
    ("/workouts/", "0.9"),
    ("/exercises/", "0.9"),
    ("/programs/", "0.8"),
    ("/for/", "0.8"),
    ("/features", "0.8"),
    ("/about", "0.7"),
    ("/faq", "0.8"),
    ("/blog", "0.8"),
    ("/blog/archive", "0.7"),
    ("/privacy", "0.3"),
    ("/terms", "0.3"),
]

NAV_GROUPS = [
    (
        "Tools",
        "tools",
        [
            ("All tools", "/tools/"),
            ("Barbell Calculator", "/tools/barbell-calculator"),
            ("Warmup Set Calculator", "/tools/warmup-set-calculator"),
            ("Common Barbell Weights", "/tools/common-barbell-weights"),
            ("lb/kg Plate Converter", "/tools/lb-kg-plate-converter"),
        ],
    ),
    (
        "Workouts",
        "workouts",
        [
            ("All workouts", "/workouts/"),
            ("Beginner Barbell Workout", "/workouts/beginner-barbell-workout"),
            ("5x5 Workout Tracker", "/workouts/5x5-workout-tracker"),
            ("Push Pull Legs", "/workouts/push-pull-legs"),
        ],
    ),
    (
        "Exercises",
        "exercises",
        [
            ("All exercises", "/exercises/"),
            ("Bench Press", "/exercises/bench-press"),
            ("Barbell Squat", "/exercises/barbell-squat"),
            ("Deadlift", "/exercises/deadlift"),
            ("Overhead Press", "/exercises/overhead-press"),
        ],
    ),
    (
        "For",
        "for",
        [
            ("All lifter types", "/for/"),
            ("Beginners", "/for/beginners"),
            ("Home Gym Lifters", "/for/home-gym-lifters"),
            ("Powerlifters", "/for/powerlifters"),
        ],
    ),
    (
        "Programs",
        "programs",
        [
            ("All programs", "/programs/"),
            ("3-Day Beginner Barbell", "/programs/3-day-beginner-barbell-program"),
            ("5x5 Beginner Strength", "/programs/5x5-beginner-strength-program"),
            ("Upper Lower Strength Hypertrophy", "/programs/upper-lower-strength-hypertrophy"),
        ],
    ),
]

NAV_LINKS = [
    ("Features", "/features", "features"),
    ("About", "/about", "about"),
    ("FAQ", "/faq", "faq"),
    ("Blog", "/blog", "blog"),
    ("Premium", "/#premium", "premium"),
]

FOOTER_LINKS = [
    ("Tools", "/tools/"),
    ("Workouts", "/workouts/"),
    ("Exercises", "/exercises/"),
    ("For", "/for/"),
    ("Programs", "/programs/"),
    ("Features", "/features"),
    ("About", "/about"),
    ("FAQ", "/faq"),
    ("Blog", "/blog"),
    ("Archive", "/blog/archive"),
    ("Privacy", "/privacy"),
    ("Terms", "/terms"),
]


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def clean_url_path(path: str) -> str:
    """Return the single public URL spelling for an HTML output path."""
    if path == "/index.html":
        return "/"
    if path.endswith("/index.html"):
        return path[: -len("index.html")]
    if path.endswith(".html"):
        return path[:-5]
    return path


def prefix_for(path: str) -> str:
    """Return the relative prefix from a generated HTML output to the site root."""
    parts = [part for part in path.strip("/").split("/") if part]
    depth = len(parts) if path.endswith("/") else max(len(parts) - 1, 0)
    return "../" * depth


def relative_href(path: str, prefix: str = "") -> str:
    clean_path = clean_url_path(path)
    if clean_path == "/":
        return prefix or "/"
    if clean_path.startswith("/#"):
        return f"{prefix}{clean_path[1:]}" if prefix else clean_path
    return f"{prefix}{clean_path.lstrip('/')}"


def public_path(page: dict) -> str:
    return clean_url_path(page.get("publicPath", page["slug"]))


def public_url(path_or_page: str | dict) -> str:
    path = public_path(path_or_page) if isinstance(path_or_page, dict) else clean_url_path(path_or_page)
    return f"{SITE_URL}{path}"


def registry_lastmod(page: dict) -> str | None:
    """Return a validated ISO date for sitemap lastmod, or None when unknown."""
    updated = page.get("updated")
    if updated is None:
        return None
    if not isinstance(updated, str):
        raise ValueError(f"{page['slug']}: updated must be an ISO date string")
    try:
        return date.fromisoformat(updated).isoformat()
    except ValueError as exc:
        raise ValueError(f"{page['slug']}: invalid updated date {updated!r}") from exc


def href_for_page(page: dict, prefix: str = "") -> str:
    return relative_href(public_path(page), prefix)


def app_href(route: str) -> str:
    """Normalize an app route to the public landing page with preserved attribution."""
    parsed = urlsplit(route)
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    intent_path = parsed.path.strip("/")

    if intent_path:
        params.setdefault("intent", intent_path)
    else:
        params.setdefault("intent", params.get("section") or "onboarding")
    params.setdefault("source", "seo")

    return escape(f"{APP_URL}/?{urlencode(params)}")


def nav(current: str, prefix: str = "") -> str:
    rendered: list[str] = []
    for label, key, links in NAV_GROUPS:
        current_attr = ' aria-current="page"' if current == key else ""
        dropdown = "\n".join(
            f'          <a href="{relative_href(path, prefix)}">{escape(link_label)}</a>'
            for link_label, path in links
        )
        rendered.append(
            f"""        <div class="nav-dropdown"{current_attr}>
          <button class="nav-dropdown-trigger" type="button">{escape(label)}</button>
          <div class="nav-dropdown-menu">
{dropdown}
          </div>
        </div>"""
        )

    for label, path, key in NAV_LINKS:
        current_attr = ' aria-current="page"' if current == key else ""
        rendered.append(
            f'        <a href="{relative_href(path, prefix)}"{current_attr}>{escape(label)}</a>'
        )
    return "\n".join(rendered)


def header(current: str, prefix: str = "", app_source: str = "seo") -> str:
    app_link = app_href(f"/?source={app_source}&intent=onboarding")
    return f"""    <header class="site-header">
      <a class="brand" href="{prefix or '/'}" aria-label="{BRAND_NAME} home">
        <img class="brand-mark" src="{prefix}{ASSETS['brand_mark']}" width="779" height="308" alt="" aria-hidden="true">
        <span>{BRAND_NAME}</span>
      </a>
      <button class="nav-toggle" type="button" aria-label="Open navigation" aria-expanded="false">
        <span></span>
        <span></span>
      </button>
      <nav class="site-nav" aria-label="Primary navigation">
{nav(current, prefix)}
      </nav>
      <a class="header-cta" href="{app_link}" data-rm-app-link data-rm-event="app_deeplink_clicked">Try free</a>
    </header>"""


def footer(prefix: str = "", app_source: str = "seo") -> str:
    app_link = app_href(f"/?source={app_source}&intent=onboarding")
    links = "\n".join(
        f'        <a href="{relative_href(path, prefix)}">{escape(label)}</a>'
        for label, path in FOOTER_LINKS
    )
    return f"""    <footer class="site-footer">
      <div>
        <a class="brand" href="{prefix or '/'}" aria-label="{BRAND_NAME} home">
          <img class="brand-mark" src="{prefix}{ASSETS['brand_mark']}" width="779" height="308" alt="" aria-hidden="true">
          <span>{BRAND_NAME}</span>
        </a>
        <p>Barbell plate math, workout sessions, and progress tracking for lifters.</p>
      </div>
      <nav aria-label="Footer navigation">
{links}
        <a href="{app_link}" data-rm-app-link data-rm-event="app_deeplink_clicked">Open app</a>
      </nav>
    </footer>"""


def replace_document_chrome(
    html_text: str,
    *,
    current: str,
    prefix: str = "",
    app_source: str = "seo",
) -> str:
    """Replace one marked header and footer while preserving a hand-authored body."""
    replacements = {
        "header": header(current, prefix, app_source),
        "footer": footer(prefix, app_source),
    }
    updated = html_text
    for tag, replacement in replacements.items():
        pattern = re.compile(
            rf'^    <{tag} class="site-{tag}">.*?^    </{tag}>$',
            flags=re.DOTALL | re.MULTILINE,
        )
        updated, count = pattern.subn(replacement, updated)
        if count != 1:
            raise ValueError(f"Expected exactly one RackMath {tag} block; found {count}")
    return updated


def document_shell(
    *,
    title: str,
    description: str,
    canonical_path: str,
    body: str,
    current: str,
    prefix: str = "",
    og_type: str = "website",
    schema_html: str = "",
    extra_script: str = "",
    social_image: str | None = None,
    social_image_alt: str | None = None,
    app_source: str = "seo",
) -> str:
    """Render the shared metadata, header, footer, and assets for a generated page."""
    title_text = escape(title)
    description_text = escape(description)
    canonical = public_url(canonical_path)
    social_image_value = social_image or ASSETS["social_image"]
    if social_image_value.startswith(("https://", "http://")):
        social_image_url = social_image_value
    else:
        social_image_url = f"{SITE_URL}/{social_image_value.lstrip('/')}"
    social_alt = social_image_alt or f"{SITE_NAME} blue gradient logo"
    schema_block = f"{schema_html}\n" if schema_html else ""
    extra_script_block = f"{extra_script}\n" if extra_script else ""
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title_text}</title>
    <meta name="description" content="{description_text}">
    <link rel="canonical" href="{canonical}">
    <meta property="og:type" content="{escape(og_type)}">
    <meta property="og:site_name" content="{SITE_NAME}">
    <meta property="og:title" content="{title_text}">
    <meta property="og:description" content="{description_text}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{escape(social_image_url)}">
    <meta property="og:image:alt" content="{escape(social_alt)}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title_text}">
    <meta name="twitter:description" content="{description_text}">
    <meta name="twitter:image" content="{escape(social_image_url)}">
    <meta name="twitter:image:alt" content="{escape(social_alt)}">
    <meta name="theme-color" content="#0a6dff">
    <link rel="icon" href="{prefix}{ASSETS['icon']}" type="image/png">
    <link rel="apple-touch-icon" href="{prefix}{ASSETS['icon']}">
    <link rel="stylesheet" href="{prefix}{ASSETS['stylesheet']}?v={ASSET_VERSION}">
{schema_block}  </head>
  <body>
{header(current, prefix, app_source)}
{body}
{footer(prefix, app_source)}
    <script src="{prefix}{ASSETS['script']}"></script>
{extra_script_block}  </body>
</html>
"""
