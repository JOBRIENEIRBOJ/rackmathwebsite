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
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

from site_shared import (
    BASE_PAGES,
    SITE_NAME,
    SITE_URL,
    clean_url_path,
    document_shell,
    registry_lastmod,
)


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content" / "blog"
BLOG_DIR = ROOT / "blog"
REDIRECTS_PATH = ROOT / "_redirects"
REDIRECTS_START = "# BEGIN GENERATED CLEAN URL REDIRECTS"
REDIRECTS_END = "# END GENERATED CLEAN URL REDIRECTS"
CONSOLIDATION_REDIRECTS = {
    "/blog/barbell-plate-math-the-simple-version": "/blog/how-to-calculate-plates-on-a-barbell",
    "/blog/what-is-a-weight-lifting-calculator": "/tools/barbell-calculator",
}


def output_paths(posts: list[Post] | None = None) -> list[str]:
    """List public HTML output paths without assuming they share one generator."""
    paths = [
        "/index.html",
        "/features.html",
        "/about.html",
        "/faq.html",
        "/blog.html",
        "/privacy.html",
        "/terms.html",
        "/blog/archive.html",
    ]

    registry_path = ROOT / "content" / "seo-pages.json"
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        paths.extend(
            f"{page['slug']}index.html" if page["slug"].endswith("/") else page["slug"]
            for page in registry["pages"]
            if page.get("status") == "published"
        )

    if posts is not None:
        paths.extend(f"/blog/{post.slug}.html" for post in posts)

    return sorted(set(paths))


def clean_redirect_rules(posts: list[Post]) -> list[tuple[str, str]]:
    """Redirect legacy and physical HTML URLs to their canonical owners.

    Netlify normalizes trailing slashes while matching ``_redirects`` rules, so
    explicit ``/page/ -> /page`` rules also match ``/page`` and self-redirect.
    Its serving layer already handles the slash form for clean URLs.
    """
    rules: set[tuple[str, str]] = set(CONSOLIDATION_REDIRECTS.items())
    rules.update(
        (f"{source}.html", destination)
        for source, destination in CONSOLIDATION_REDIRECTS.items()
    )
    for output_path in output_paths(posts):
        canonical_path = clean_url_path(output_path)
        destination = CONSOLIDATION_REDIRECTS.get(canonical_path, canonical_path)
        if output_path != destination:
            rules.add((output_path, destination))

    return sorted(rules)


def write_clean_url_redirects(posts: list[Post]) -> None:
    """Refresh the generated redirect block without changing legacy rules."""
    existing = REDIRECTS_PATH.read_text(encoding="utf-8") if REDIRECTS_PATH.exists() else ""
    generated_block = re.compile(
        rf"\n?{re.escape(REDIRECTS_START)}.*?{re.escape(REDIRECTS_END)}\n?",
        flags=re.DOTALL,
    )
    manual = generated_block.sub("\n", existing).strip()
    manual_sources = {
        line.split()[0]
        for line in manual.splitlines()
        if line.strip() and not line.lstrip().startswith("#") and len(line.split()) >= 2
    }
    generated = [
        f"{source} {destination} 301!"
        for source, destination in clean_redirect_rules(posts)
        if source not in manual_sources
    ]
    parts = [part for part in (manual, REDIRECTS_START, "\n".join(generated), REDIRECTS_END) if part]
    REDIRECTS_PATH.write_text("\n".join(parts) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class Post:
    title: str
    description: str
    date: date
    slug: str
    source_path: Path
    body: str
    updated: date | None = None

    @property
    def url_path(self) -> str:
        return f"/blog/{self.slug}"

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
        updated_date = (
            datetime.strptime(meta["updated"], "%Y-%m-%d").date()
            if meta.get("updated")
            else None
        )
        if updated_date is not None and updated_date < post_date:
            raise ValueError(
                f"{path} has updated date {updated_date.isoformat()} before "
                f"publication date {post_date.isoformat()}"
            )
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
                updated=updated_date,
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


INLINE_TOKEN = re.compile(
    r"\[([^\]\n]+)\]\(([^)\n]+)\)"
    r"|\[\^([A-Za-z0-9_-]+)\]"
    r"|https?://[^\s<]+"
)
FOOTNOTE_DEFINITION = re.compile(r"^ {0,3}\[\^([A-Za-z0-9_-]+)\]:\s*(.*)$")
ORDERED_LIST_ITEM = re.compile(r"^\d+[.)]\s+(.+)$")


def render_emphasis(text: str) -> str:
    """Render the small emphasis subset used by RackMath blog Markdown."""
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(?=\S)(.+?\S)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"__(?=\S)(.+?\S)__", r"<strong>\1</strong>", escaped)
    escaped = re.sub(
        r"(?<!\*)\*(?![\s*])(.+?\S)\*(?!\*)",
        r"<em>\1</em>",
        escaped,
    )
    escaped = re.sub(
        r"(?<![\w_])_(?![\s_])(.+?\S)_(?![\w_])",
        r"<em>\1</em>",
        escaped,
    )
    return escaped


def safe_markdown_href(href: str) -> str | None:
    """Allow web URLs and same-site relative URLs, but reject active schemes."""
    href = href.strip()
    if not href or any(ord(character) < 32 for character in href):
        return None
    if "\\" in href or href.startswith("//"):
        return None

    parsed = urlsplit(href)
    if parsed.scheme:
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            return None
    elif parsed.netloc:
        return None
    return href


def render_inline(
    text: str,
    *,
    footnote_references: dict[str, list[str]] | None = None,
    known_footnotes: set[str] | None = None,
) -> str:
    """Render escaped inline Markdown, links, citations, and emphasis."""
    rendered: list[str] = []
    cursor = 0

    for match in INLINE_TOKEN.finditer(text):
        rendered.append(render_emphasis(text[cursor : match.start()]))
        token = match.group(0)
        link_label, link_href, footnote_label = match.groups()

        if link_label is not None and link_href is not None:
            safe_href = safe_markdown_href(link_href)
            if safe_href is None:
                rendered.append(render_emphasis(link_label))
            else:
                rendered.append(
                    f'<a href="{html.escape(safe_href, quote=True)}">'
                    f"{render_emphasis(link_label)}</a>"
                )
        elif footnote_label is not None:
            if (
                footnote_references is None
                or known_footnotes is None
                or footnote_label not in known_footnotes
            ):
                rendered.append(html.escape(token))
            else:
                reference_ids = footnote_references.setdefault(footnote_label, [])
                suffix = f"-{len(reference_ids) + 1}" if reference_ids else ""
                reference_id = f"fnref-{footnote_label}{suffix}"
                reference_ids.append(reference_id)
                rendered.append(
                    f'<sup id="{reference_id}"><a class="footnote-ref" '
                    f'href="#fn-{footnote_label}" aria-label="Footnote '
                    f'{html.escape(footnote_label, quote=True)}">'
                    f"{html.escape(footnote_label)}</a></sup>"
                )
        else:
            bare_href = token.rstrip(".,;:!?")
            trailing_punctuation = token[len(bare_href) :]
            rendered.append(
                f'<a href="{html.escape(bare_href, quote=True)}">'
                f"{html.escape(bare_href)}</a>"
            )
            rendered.append(html.escape(trailing_punctuation))

        cursor = match.end()

    rendered.append(render_emphasis(text[cursor:]))
    return "".join(rendered)


def extract_footnotes(markdown: str) -> tuple[list[str], dict[str, str]]:
    """Remove footnote definitions from the document and preserve their order."""
    lines = markdown.splitlines()
    body_lines: list[str] = []
    definitions: dict[str, str] = {}
    index = 0

    while index < len(lines):
        match = FOOTNOTE_DEFINITION.match(lines[index])
        if not match:
            body_lines.append(lines[index])
            index += 1
            continue

        label, definition = match.groups()
        continuation: list[str] = [definition.strip()]
        index += 1
        while index < len(lines) and re.match(r"^ {2,}\S", lines[index]):
            continuation.append(lines[index].strip())
            index += 1
        definitions[label] = " ".join(part for part in continuation if part)

    return body_lines, definitions


def render_markdown(markdown: str) -> str:
    lines, footnotes = extract_footnotes(markdown)
    terminal_sources_heading = False
    if footnotes:
        last_content_index = len(lines) - 1
        while last_content_index >= 0 and not lines[last_content_index].strip():
            last_content_index -= 1
        if (
            last_content_index >= 0
            and lines[last_content_index].strip().casefold() == "## sources"
        ):
            terminal_sources_heading = True
            del lines[last_content_index:]

    html_lines: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_tag: str | None = None
    quote_lines: list[str] = []
    footnote_references: dict[str, list[str]] = {}
    known_footnotes = set(footnotes)

    def inline(text: str) -> str:
        return render_inline(
            text,
            footnote_references=footnote_references,
            known_footnotes=known_footnotes,
        )

    def flush_paragraph() -> None:
        if paragraph:
            html_lines.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def flush_list() -> None:
        nonlocal list_tag
        if list_items and list_tag:
            html_lines.append(f"<{list_tag}>")
            html_lines.extend(f"  <li>{inline(item)}</li>" for item in list_items)
            html_lines.append(f"</{list_tag}>")
            list_items.clear()
        list_tag = None

    def flush_quote() -> None:
        if quote_lines:
            html_lines.append(f"<blockquote><p>{inline(' '.join(quote_lines))}</p></blockquote>")
            quote_lines.clear()

    def flush_blocks() -> None:
        flush_paragraph()
        flush_list()
        flush_quote()

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            flush_blocks()
            continue

        ordered_item = ORDERED_LIST_ITEM.match(line)
        if line.startswith("### "):
            flush_blocks()
            html_lines.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            flush_blocks()
            html_lines.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("# "):
            flush_blocks()
            html_lines.append(f"<h1>{inline(line[2:])}</h1>")
        elif line.startswith(">"):
            flush_paragraph()
            flush_list()
            quote_lines.append(line[1:].lstrip())
        elif line.startswith("- "):
            flush_paragraph()
            flush_quote()
            if list_tag not in (None, "ul"):
                flush_list()
            list_tag = "ul"
            list_items.append(line[2:])
        elif ordered_item:
            flush_paragraph()
            flush_quote()
            if list_tag not in (None, "ol"):
                flush_list()
            list_tag = "ol"
            list_items.append(ordered_item.group(1))
        else:
            flush_list()
            flush_quote()
            paragraph.append(line)

    flush_blocks()

    if footnotes:
        labels = list(footnote_references)
        labels.extend(label for label in footnotes if label not in footnote_references)
        footnotes_heading = "Sources" if terminal_sources_heading else "Sources and notes"
        html_lines.append('<section class="footnotes" aria-labelledby="footnotes-heading">')
        html_lines.append(f'<h2 id="footnotes-heading">{footnotes_heading}</h2>')
        html_lines.append("<ol>")
        for label in labels:
            backlinks = " ".join(
                f'<a class="footnote-backref" href="#{reference_id}" '
                f'aria-label="Back to footnote {html.escape(label, quote=True)} reference">↩</a>'
                for reference_id in footnote_references.get(label, [])
            )
            suffix = f" {backlinks}" if backlinks else ""
            html_lines.append(
                f'  <li id="fn-{html.escape(label, quote=True)}">'
                f"{render_inline(footnotes[label])}{suffix}</li>"
            )
        html_lines.append("</ol>")
        html_lines.append("</section>")

    return "\n".join(html_lines)


def without_leading_h1(markdown: str) -> str:
    lines = markdown.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:]).strip()
    return markdown


def render_blog_index(posts: list[Post]) -> str:
    latest_posts = posts[:6]
    cards = "\n".join(
        f"""          <article class="blog-card">
            <p class="blog-date"><time datetime="{post.date.isoformat()}">{post.date.strftime("%B %-d, %Y")}</time></p>
            <h2><a href="blog/{post.slug}">{html.escape(post.title)}</a></h2>
            <p>{html.escape(post.description)}</p>
            <a class="text-link" href="blog/{post.slug}">Read post</a>
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
        <h1>Practical guides for loading and lifting.</h1>
        <p>Clear, beginner-friendly guides about barbell loading, lifting calculations, training, and the small decisions that keep workouts moving.</p>
      </section>

      <section class="section blog-list" aria-label="Blog posts">
{cards}
      </section>

      <section class="section blog-post-nav" aria-label="Blog archive">
        <a class="text-link" href="blog/archive">View all posts in the archive</a>
      </section>
    </main>"""
    return document_shell(
        title="Rack Math Blog | Weight Lifting Calculator Tips",
        description="Practical Rack Math guides about barbell loading, lifting calculations, beginner training, and workout progress.",
        canonical_path="/blog",
        body=body,
        current="blog",
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
              <a href="{post.slug}">{html.escape(post.title)}</a>
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

    groups_html = "\n".join(groups)
    body = f"""    <main>
      <section class="page-hero">
        <p class="eyebrow">Archive</p>
        <h1>All Rack Math guides.</h1>
        <p>Browse every practical guide about lifting calculations, barbell loading, workout tracking, and training.</p>
      </section>

      <section class="section archive-list" aria-label="All blog posts">
{groups_html}
      </section>
    </main>"""
    return document_shell(
        title="Rack Math Blog Archive",
        description="Browse every Rack Math guide about lifting calculations, barbell loading, workout tracking, and training progress.",
        canonical_path="/blog/archive",
        body=body,
        current="blog",
        prefix="../",
    )


def render_post(post: Post) -> str:
    article = render_markdown(without_leading_h1(post.body))
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post.title,
        "description": post.description,
        "datePublished": post.date.isoformat(),
        "dateModified": (post.updated or post.date).isoformat(),
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
        <a class="text-link" href="../blog">Back to blog</a>
        <a class="text-link" href="archive">Archive</a>
        <a class="text-link" href="https://www.rackmath.app/?source=seo&amp;tool=barbell-plate-calculator&amp;intent=tools%2Fplate-calculator">Open RackMath calculator</a>
      </section>
      <script type="application/ld+json">
        {json.dumps(schema, indent=8)}
      </script>
    </main>"""
    return document_shell(
        title=f"{post.title} | Rack Math Blog",
        description=post.description,
        canonical_path=post.url_path,
        body=body,
        current="blog",
        prefix="../",
        og_type="article",
    )


def write_sitemap(posts: list[Post]) -> None:
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    seen: set[str] = set()

    def add(path: str, priority: str, lastmod: str | None = None) -> None:
        if path in seen:
            return
        seen.add(path)
        url = ET.SubElement(urlset, "url")
        ET.SubElement(url, "loc").text = f"{SITE_URL}{path}"
        if lastmod:
            ET.SubElement(url, "lastmod").text = lastmod
        ET.SubElement(url, "priority").text = priority

    for path, priority in BASE_PAGES:
        add(path, priority)

    registry_path = ROOT / "content" / "seo-pages.json"
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        priority_by_type = {
            "hub": "0.8",
            "tool": "0.8",
            "workout": "0.7",
            "exercise": "0.7",
            "feature": "0.7",
        }
        for page in registry["pages"]:
            if page.get("status") != "published":
                continue
            path = clean_url_path(page.get("publicPath", page["slug"]))
            add(path, priority_by_type.get(page["type"], "0.6"), registry_lastmod(page))

    for post in posts:
        add(post.url_path, "0.6", (post.updated or post.date).isoformat())

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
    write_clean_url_redirects(posts)
    print(f"Built {len(posts)} published blog post(s)")


if __name__ == "__main__":
    main()
