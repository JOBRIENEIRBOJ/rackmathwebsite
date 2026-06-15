#!/usr/bin/env python3
"""Build Rack Math blog pages from Markdown posts."""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content" / "blog"
BLOG_DIR = ROOT / "blog"
SITE_URL = "https://www.rackmath.com"
SITE_NAME = "Rack Math"
BASE_PAGES = [
    ("/", "1.0"),
    ("/tools/", "0.9"),
    ("/features.html", "0.8"),
    ("/about.html", "0.7"),
    ("/faq.html", "0.8"),
    ("/blog.html", "0.8"),
    ("/blog/archive.html", "0.7"),
]


@dataclass(frozen=True)
class Post:
    title: str
    description: str
    date: date
    slug: str
    source_path: Path
    body: str

    @property
    def url_path(self) -> str:
        return f"/blog/{self.slug}.html"

    @property
    def output_path(self) -> Path:
        return BLOG_DIR / f"{self.slug}.html"


def parse_front_matter(markdown: str, path: Path) -> tuple[dict[str, str], str]:
    if not markdown.startswith("---\n"):
        raise ValueError(f"{path} is missing front matter")

    _, raw_meta, body = markdown.split("---", 2)
    meta: dict[str, str] = {}
    for line in raw_meta.strip().splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, body.strip()


def load_posts(*, include_future: bool = False, today: date | None = None) -> list[Post]:
    posts: list[Post] = []
    publish_date = today or datetime.now(timezone.utc).date()
    for path in sorted(CONTENT_DIR.glob("*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"), path)
        missing = [key for key in ("title", "description", "date", "slug") if not meta.get(key)]
        if missing:
            raise ValueError(f"{path} is missing front matter fields: {', '.join(missing)}")

        post_date = datetime.strptime(meta["date"], "%Y-%m-%d").date()
        if post_date > publish_date and not include_future:
            continue

        posts.append(
            Post(
                title=meta["title"],
                description=meta["description"],
                date=post_date,
                slug=meta["slug"],
                source_path=path,
                body=body,
            )
        )

    return sorted(
        posts,
        key=lambda post: (post.date, post.source_path.name),
        reverse=True,
    )


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def validate_unique_posts(posts: list[Post]) -> None:
    seen_titles: dict[str, Post] = {}
    seen_slugs: dict[str, Post] = {}

    for post in posts:
        title_key = normalize_key(post.title)
        slug_key = normalize_key(post.slug)

        if title_key in seen_titles:
            first = seen_titles[title_key]
            raise ValueError(
                "Duplicate blog title found: "
                f"{post.title!r} in {post.source_path.relative_to(ROOT)} "
                f"matches {first.source_path.relative_to(ROOT)}"
            )

        if slug_key in seen_slugs:
            first = seen_slugs[slug_key]
            raise ValueError(
                "Duplicate blog slug found: "
                f"{post.slug!r} in {post.source_path.relative_to(ROOT)} "
                f"matches {first.source_path.relative_to(ROOT)}"
            )

        seen_titles[title_key] = post
        seen_slugs[slug_key] = post


def render_inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\[(.+?)\]\((https?://[^\s)]+)\)", r'<a href="\2">\1</a>', escaped)
    return escaped


def render_markdown(markdown: str) -> str:
    lines = markdown.splitlines()
    html_lines: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            html_lines.append(f"<p>{render_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def flush_list() -> None:
        if list_items:
            html_lines.append("<ul>")
            html_lines.extend(f"  <li>{render_inline(item)}</li>" for item in list_items)
            html_lines.append("</ul>")
            list_items.clear()

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            flush_list()
            continue

        if line.startswith("## "):
            flush_paragraph()
            flush_list()
            html_lines.append(f"<h2>{render_inline(line[3:])}</h2>")
        elif line.startswith("# "):
            flush_paragraph()
            flush_list()
            html_lines.append(f"<h1>{render_inline(line[2:])}</h1>")
        elif line.startswith("- "):
            flush_paragraph()
            list_items.append(line[2:])
        else:
            flush_list()
            paragraph.append(line)

    flush_paragraph()
    flush_list()
    return "\n".join(html_lines)


def without_leading_h1(markdown: str) -> str:
    lines = markdown.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:]).strip()
    return markdown


def nav(current: str, prefix: str = "") -> str:
    tool_links = [
        ("All tools", f"{prefix}tools/"),
        ("Barbell Plate Calculator", f"{prefix}tools/barbell-plate-calculator.html"),
        ("Warmup Set Calculator", f"{prefix}tools/warmup-set-calculator.html"),
        ("One Rep Max Calculator", f"{prefix}tools/one-rep-max-calculator.html"),
        ("Common Barbell Weights", f"{prefix}tools/common-barbell-weights.html"),
        ("lb/kg Plate Converter", f"{prefix}tools/lb-kg-plate-converter.html"),
        ("RPE Calculator", f"{prefix}tools/rpe-calculator.html"),
        ("Training Volume Calculator", f"{prefix}tools/training-volume-calculator.html"),
        ("Powerlifting Attempt Calculator", f"{prefix}tools/powerlifting-attempt-calculator.html"),
        ("AI Workout Builder", f"{prefix}tools/ai-workout-builder.html"),
        ("Workout Plan Importer", f"{prefix}tools/workout-plan-importer.html"),
    ]
    tools_current = ' aria-current="page"' if current == "tools" else ""
    tools_dropdown = "\n".join(f'          <a href="{href}">{label}</a>' for label, href in tool_links)
    links = [
        ("Features", f"{prefix}features.html", "features"),
        ("About", f"{prefix}about.html", "about"),
        ("FAQ", f"{prefix}faq.html", "faq"),
        ("Blog", f"{prefix}blog.html", "blog"),
        ("Premium", f"{prefix}index.html#premium", "premium"),
    ]
    rendered = [
        f"""        <div class="nav-dropdown"{tools_current}>
          <button class="nav-dropdown-trigger" type="button">Tools</button>
          <div class="nav-dropdown-menu">
{tools_dropdown}
          </div>
        </div>"""
    ]
    for label, href, key in links:
        current_attr = ' aria-current="page"' if current == key else ""
        rendered.append(f'        <a href="{href}"{current_attr}>{label}</a>')
    return "\n".join(rendered)


def header(current: str, prefix: str = "") -> str:
    return f"""    <header class="site-header">
      <a class="brand" href="{prefix}index.html" aria-label="RackMath home">
        <img class="brand-mark" src="{prefix}assets/rackmathblue-header.png" alt="" aria-hidden="true">
        <span>RackMath</span>
      </a>
      <button class="nav-toggle" type="button" aria-label="Open navigation" aria-expanded="false">
        <span></span>
        <span></span>
      </button>
      <nav class="site-nav" aria-label="Primary navigation">
{nav(current, prefix)}
      </nav>
      <a class="header-cta" href="https://www.rackmath.app/">Try free</a>
    </header>"""


def footer(prefix: str = "") -> str:
    return f"""    <footer class="site-footer">
      <div>
        <a class="brand" href="{prefix}index.html" aria-label="RackMath home">
          <img class="brand-mark" src="{prefix}assets/rackmathblue-header.png" alt="" aria-hidden="true">
          <span>RackMath</span>
        </a>
        <p>Barbell plate math, workout sessions, and progress tracking for lifters.</p>
      </div>
      <nav aria-label="Footer navigation">
        <a href="{prefix}tools/">Tools</a>
        <a href="{prefix}features.html">Features</a>
        <a href="{prefix}about.html">About</a>
        <a href="{prefix}faq.html">FAQ</a>
        <a href="{prefix}blog.html">Blog</a>
        <a href="{prefix}blog/archive.html">Archive</a>
        <a href="https://www.rackmath.app/">Open app</a>
      </nav>
    </footer>"""


def footer_from_blog() -> str:
    return """    <footer class="site-footer">
      <div>
        <a class="brand" href="../index.html" aria-label="RackMath home">
          <img class="brand-mark" src="../assets/rackmathblue-header.png" alt="" aria-hidden="true">
          <span>RackMath</span>
        </a>
        <p>Barbell plate math, workout sessions, and progress tracking for lifters.</p>
      </div>
      <nav aria-label="Footer navigation">
        <a href="../tools/">Tools</a>
        <a href="../features.html">Features</a>
        <a href="../about.html">About</a>
        <a href="../faq.html">FAQ</a>
        <a href="../blog.html">Blog</a>
        <a href="archive.html">Archive</a>
        <a href="https://www.rackmath.app/">Open app</a>
      </nav>
    </footer>"""


def page_shell(
    title: str,
    description: str,
    canonical_path: str,
    body: str,
    current: str,
    prefix: str = "",
    footer_html: str | None = None,
) -> str:
    title_text = html.escape(title)
    description_text = html.escape(description)
    canonical = f"{SITE_URL}{canonical_path}"
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title_text}</title>
    <meta name="description" content="{description_text}">
    <link rel="canonical" href="{canonical}">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="{SITE_NAME}">
    <meta property="og:title" content="{title_text}">
    <meta property="og:description" content="{description_text}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{SITE_URL}/assets/rackmathblue-gradient.png">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title_text}">
    <meta name="twitter:description" content="{description_text}">
    <meta name="twitter:image" content="{SITE_URL}/assets/rackmathblue-gradient.png">
    <meta name="theme-color" content="#0a6dff">
    <link rel="icon" href="{prefix}assets/rackmathblue.png" type="image/png">
    <link rel="apple-touch-icon" href="{prefix}assets/rackmathblue.png">
    <link rel="stylesheet" href="{prefix}styles.css?v=20260604">
  </head>
  <body>
{header(current, prefix)}
{body}
{footer_html or footer(prefix)}
    <script src="{prefix}script.js"></script>
  </body>
</html>
"""


def render_blog_index(posts: list[Post]) -> str:
    latest_posts = posts[:6]
    cards = "\n".join(
        f"""          <article class="blog-card">
            <p class="blog-date"><time datetime="{post.date.isoformat()}">{post.date.strftime("%B %-d, %Y")}</time></p>
            <h2><a href="blog/{post.slug}.html">{html.escape(post.title)}</a></h2>
            <p>{html.escape(post.description)}</p>
            <a class="text-link" href="blog/{post.slug}.html">Read post</a>
          </article>"""
        for post in latest_posts
    )
    if not cards:
        cards = """          <article class="blog-card">
            <p class="blog-date">Coming soon</p>
            <h2>New posts are on the way.</h2>
            <p>Future-dated posts have been added and will publish automatically on their scheduled dates.</p>
          </article>"""
    body = f"""    <main>
      <section class="page-hero">
        <p class="eyebrow">Rack Math Blog</p>
        <h1>Daily weight lifting calculator notes.</h1>
        <p>Short posts about barbell plate loading, workout tracking, training flow, and the small decisions that keep lifting sessions moving.</p>
      </section>

      <section class="section blog-list" aria-label="Blog posts">
{cards}
      </section>

      <section class="section blog-post-nav" aria-label="Blog archive">
        <a class="text-link" href="blog/archive.html">View all posts in the archive</a>
      </section>
    </main>"""
    return page_shell(
        "Rack Math Blog | Weight Lifting Calculator Tips",
        "Daily Rack Math posts about weight lifting calculator tips, barbell plate loading, workout tracking, and training progress.",
        "/blog.html",
        body,
        "blog",
    )


def render_archive(posts: list[Post]) -> str:
    by_year: dict[int, list[Post]] = {}
    for post in posts:
        by_year.setdefault(post.date.year, []).append(post)

    groups = []
    for year in sorted(by_year, reverse=True):
        items = "\n".join(
            f"""            <li>
              <time datetime="{post.date.isoformat()}">{post.date.strftime("%B %-d, %Y")}</time>
              <a href="{post.slug}.html">{html.escape(post.title)}</a>
            </li>"""
            for post in by_year[year]
        )
        groups.append(
            f"""        <section class="archive-year" aria-labelledby="archive-{year}">
          <h2 id="archive-{year}">{year}</h2>
          <ul>
{items}
          </ul>
        </section>"""
        )

    if not groups:
        groups.append(
            """        <section class="archive-year" aria-label="No published posts">
          <h2>Coming soon</h2>
          <p>Future-dated posts will appear here automatically on their scheduled dates.</p>
        </section>"""
        )

    body = f"""    <main>
      <section class="page-hero">
        <p class="eyebrow">Archive</p>
        <h1>All Rack Math blog posts.</h1>
        <p>Every published note about weight lifting calculators, barbell plate loading, workout tracking, and training flow.</p>
      </section>

      <section class="section archive-list" aria-label="All blog posts">
{"\n".join(groups)}
      </section>
    </main>"""
    return page_shell(
        "Rack Math Blog Archive",
        "Browse every Rack Math blog post about weight lifting calculators, barbell plate loading, workout tracking, and training progress.",
        "/blog/archive.html",
        body,
        "blog",
        "../",
        footer_from_blog(),
    )


def render_post(post: Post) -> str:
    article = render_markdown(without_leading_h1(post.body))
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post.title,
        "description": post.description,
        "datePublished": post.date.isoformat(),
        "dateModified": post.date.isoformat(),
        "mainEntityOfPage": f"{SITE_URL}{post.url_path}",
        "author": {"@type": "Organization", "name": SITE_NAME},
        "publisher": {"@type": "Organization", "name": SITE_NAME},
    }
    body = f"""    <main>
      <section class="page-hero blog-post-hero">
        <p class="eyebrow">Rack Math Blog</p>
        <p class="blog-date"><time datetime="{post.date.isoformat()}">{post.date.strftime("%B %-d, %Y")}</time></p>
        <h1>{html.escape(post.title)}</h1>
        <p>{html.escape(post.description)}</p>
      </section>

      <section class="section blog-post-layout">
        <article class="blog-post-content">
{article}
        </article>
      </section>

      <section class="section blog-post-nav" aria-label="Blog navigation">
        <a class="text-link" href="../blog.html">Back to blog</a>
        <a class="text-link" href="archive.html">Archive</a>
        <a class="text-link" href="https://www.rackmath.app/">Open Rack Math</a>
      </section>
      <script type="application/ld+json">
        {json.dumps(schema, indent=8)}
      </script>
    </main>"""
    return page_shell(
        f"{post.title} | Rack Math Blog",
        post.description,
        post.url_path,
        body,
        "blog",
        "../",
        footer_from_blog(),
    )


def write_sitemap(posts: list[Post]) -> None:
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for path, priority in BASE_PAGES:
        url = ET.SubElement(urlset, "url")
        ET.SubElement(url, "loc").text = f"{SITE_URL}{path}"
        ET.SubElement(url, "priority").text = priority

    for post in posts:
        url = ET.SubElement(urlset, "url")
        ET.SubElement(url, "loc").text = f"{SITE_URL}{post.url_path}"
        ET.SubElement(url, "lastmod").text = post.date.isoformat()
        ET.SubElement(url, "priority").text = "0.6"

    ET.indent(urlset, space="  ")
    tree = ET.ElementTree(urlset)
    tree.write(ROOT / "sitemap.xml", encoding="utf-8", xml_declaration=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Rack Math blog pages from Markdown posts.")
    parser.add_argument(
        "--include-future",
        action="store_true",
        help="Include future-dated posts in the generated site for local preview.",
    )
    parser.add_argument(
        "--today",
        help="Override today's date in YYYY-MM-DD format, useful for testing scheduled publishing.",
    )
    args = parser.parse_args()

    today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else None
    posts = load_posts(include_future=args.include_future, today=today)
    validate_unique_posts(posts)

    BLOG_DIR.mkdir(exist_ok=True)
    for generated_page in BLOG_DIR.glob("*.html"):
        generated_page.unlink()

    (ROOT / "blog.html").write_text(render_blog_index(posts), encoding="utf-8")
    (BLOG_DIR / "archive.html").write_text(render_archive(posts), encoding="utf-8")
    for post in posts:
        post.output_path.write_text(render_post(post), encoding="utf-8")
    write_sitemap(posts)
    print(f"Built {len(posts)} published blog post(s)")


if __name__ == "__main__":
    main()
