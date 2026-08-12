from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_blog  # noqa: E402
import build_site  # noqa: E402


class MarkdownRendererTests(unittest.TestCase):
    def test_renders_headings_lists_and_blockquotes(self) -> None:
        rendered = build_blog.render_markdown(
            """### Setup

1. Load the bar
2. Check both sides

- Use collars
- Start light

> Move with **control**.
> Leave *one rep* in reserve.
"""
        )

        self.assertIn("<h3>Setup</h3>", rendered)
        self.assertIn("<ol>\n  <li>Load the bar</li>\n  <li>Check both sides</li>\n</ol>", rendered)
        self.assertIn("<ul>\n  <li>Use collars</li>\n  <li>Start light</li>\n</ul>", rendered)
        self.assertIn(
            "<blockquote><p>Move with <strong>control</strong>. "
            "Leave <em>one rep</em> in reserve.</p></blockquote>",
            rendered,
        )

    def test_renders_safe_internal_and_external_links(self) -> None:
        rendered = build_blog.render_inline(
            "Use the [calculator](/tools/barbell-calculator), read the "
            "[next post](another-post), visit [RackMath](https://rackmath.com), "
            "and ignore [unsafe](javascript:alert)."
        )

        self.assertIn('<a href="/tools/barbell-calculator">calculator</a>', rendered)
        self.assertIn('<a href="another-post">next post</a>', rendered)
        self.assertIn('<a href="https://rackmath.com">RackMath</a>', rendered)
        self.assertNotIn("javascript:", rendered)
        self.assertNotIn('<a href="javascript:', rendered)
        self.assertIn("and ignore unsafe.", rendered)

    def test_escapes_html_and_supports_emphasis(self) -> None:
        rendered = build_blog.render_inline(
            '<script>alert("x")</script> **strong** *emphasis* __also strong__'
        )

        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn("<strong>strong</strong>", rendered)
        self.assertIn("<em>emphasis</em>", rendered)
        self.assertIn("<strong>also strong</strong>", rendered)

    def test_renders_footnote_references_definitions_links_and_backrefs(self) -> None:
        rendered = build_blog.render_markdown(
            """A supported claim.[^1]

## Sources

[^1]: CDC. https://www.cdc.gov/example
"""
        )

        self.assertIn(
            '<sup id="fnref-1"><a class="footnote-ref" href="#fn-1" '
            'aria-label="Footnote 1">1</a></sup>',
            rendered,
        )
        self.assertIn(
            '<section class="footnotes" aria-labelledby="footnotes-heading">', rendered
        )
        self.assertEqual(1, rendered.count("<h2>Sources</h2>") + rendered.count(">Sources</h2>"))
        self.assertIn('<h2 id="footnotes-heading">Sources</h2>', rendered)
        self.assertIn('<li id="fn-1">CDC. <a href="https://www.cdc.gov/example">', rendered)
        self.assertIn('class="footnote-backref" href="#fnref-1"', rendered)
        self.assertNotIn("[^1]", rendered)

    def test_render_post_uses_supported_calculator_handoff(self) -> None:
        post = build_blog.Post(
            title="Example",
            description="Example description.",
            date=date(2026, 8, 12),
            slug="example",
            source_path=ROOT / "content" / "blog" / "example.md",
            body="# Example\n\nBody.",
        )

        rendered = build_blog.render_post(post)
        blog_nav = rendered.split(
            '<section class="section blog-post-nav" aria-label="Blog navigation">', 1
        )[1].split("</section>", 1)[0]

        self.assertIn(
            "https://www.rackmath.app/?source=seo&amp;tool=barbell-plate-calculator"
            "&amp;intent=tools%2Fplate-calculator",
            blog_nav,
        )
        self.assertIn(">Open RackMath calculator</a>", blog_nav)
        self.assertNotIn("intent=onboarding", blog_nav)

    def test_footnotes_after_a_substantive_sources_section_get_their_own_heading(self) -> None:
        rendered = build_blog.render_markdown(
            """## Sources

- CDC guidance

A note.[^1]

[^1]: Supporting detail.
"""
        )

        self.assertIn("<h2>Sources</h2>", rendered)
        self.assertIn('<h2 id="footnotes-heading">Sources and notes</h2>', rendered)

    def test_blog_index_and_archive_use_evergreen_copy(self) -> None:
        index = build_blog.render_blog_index([])
        archive = build_blog.render_archive([])

        self.assertIn("Practical guides for loading and lifting.", index)
        self.assertIn("Practical Rack Math guides about barbell loading", index)
        self.assertNotIn("Daily weight lifting calculator notes", index)
        self.assertIn("All Rack Math guides.", archive)
        self.assertNotIn("Every published note", archive)

    def test_consolidation_redirects_include_clean_and_html_legacy_urls(self) -> None:
        rules = dict(build_blog.clean_redirect_rules([]))

        self.assertEqual(
            "/blog/how-to-calculate-plates-on-a-barbell",
            rules["/blog/barbell-plate-math-the-simple-version"],
        )
        self.assertEqual(
            "/blog/how-to-calculate-plates-on-a-barbell",
            rules["/blog/barbell-plate-math-the-simple-version.html"],
        )
        self.assertEqual(
            "/tools/barbell-calculator",
            rules["/blog/what-is-a-weight-lifting-calculator"],
        )
        self.assertEqual(
            "/tools/barbell-calculator",
            rules["/blog/what-is-a-weight-lifting-calculator.html"],
        )

    def test_updated_front_matter_sets_date_modified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            content_dir = Path(temporary_directory)
            (content_dir / "post.md").write_text(
                """---
title: "Updated post"
description: "Example description."
date: "2026-08-01"
updated: "2026-08-12"
slug: "updated-post"
---

# Updated post

Body.
""",
                encoding="utf-8",
            )
            with mock.patch.object(build_blog, "CONTENT_DIR", content_dir):
                post = build_blog.load_posts(include_future=True)[0]

        self.assertEqual(date(2026, 8, 1), post.date)
        self.assertEqual(date(2026, 8, 12), post.updated)
        rendered = build_blog.render_post(post)
        self.assertIn('"datePublished": "2026-08-01"', rendered)
        self.assertIn('"dateModified": "2026-08-12"', rendered)

    def test_updated_front_matter_cannot_predate_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            content_dir = Path(temporary_directory)
            post_path = content_dir / "post.md"
            post_path.write_text(
                """---
title: "Invalid update"
description: "Example description."
date: "2026-08-12"
updated: "2026-08-01"
slug: "invalid-update"
---

# Invalid update
""",
                encoding="utf-8",
            )
            with mock.patch.object(build_blog, "CONTENT_DIR", content_dir):
                with self.assertRaisesRegex(ValueError, "updated date .* before publication date"):
                    build_blog.load_posts(include_future=True)

    def test_sitemap_uses_updated_date_for_modified_posts(self) -> None:
        post = build_blog.Post(
            title="Updated post",
            description="Example description.",
            date=date(2026, 8, 1),
            updated=date(2026, 8, 12),
            slug="updated-post",
            source_path=ROOT / "content" / "blog" / "updated-post.md",
            body="# Updated post\n\nBody.",
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            sitemap_path = Path(temporary_directory) / "sitemap.xml"
            with mock.patch.object(build_blog, "ROOT", Path(temporary_directory)):
                build_blog.write_sitemap([post])
            root = ET.parse(sitemap_path).getroot()

        entries = {
            entry.findtext("{*}loc"): entry.findtext("{*}lastmod")
            for entry in root.findall("{*}url")
        }
        self.assertEqual(
            "2026-08-12",
            entries["https://rackmath.com/blog/updated-post"],
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            sitemap_path = Path(temporary_directory) / "sitemap.xml"
            with mock.patch.object(build_site, "ROOT", Path(temporary_directory)):
                build_site.write_sitemap([post], {"pages": []})
            root = ET.parse(sitemap_path).getroot()

        entries = {
            entry.findtext("{*}loc"): entry.findtext("{*}lastmod")
            for entry in root.findall("{*}url")
        }
        self.assertEqual(
            "2026-08-12",
            entries["https://rackmath.com/blog/updated-post"],
        )


if __name__ == "__main__":
    unittest.main()
