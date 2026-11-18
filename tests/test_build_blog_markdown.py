from __future__ import annotations

import json
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

    def test_renders_standalone_asset_images_with_optional_captions(self) -> None:
        rendered = build_blog.render_markdown(
            '![Balanced bar](/assets/guides/balanced-bar.svg "Load both sides equally.")\n\n'
            '![Plate example](/assets/guides/plate-example.webp)'
        )

        self.assertEqual(2, rendered.count('<figure class="blog-figure">'))
        self.assertIn(
            '<img src="/assets/guides/balanced-bar.svg" alt="Balanced bar" '
            'loading="lazy" decoding="async">', rendered,
        )
        self.assertIn('<figcaption>Load both sides equally.</figcaption>', rendered)
        self.assertEqual(1, rendered.count("<figcaption>"))
        self.assertNotIn("<p><figure", rendered)

    def test_image_labels_and_captions_are_escaped_text(self) -> None:
        rendered = build_blog.render_markdown(
            r'![Bar "left" <left> & \[right\]](/assets/guides/bar.svg '
            r'"Keep \"left\" & <script> together")'
        )

        self.assertIn('alt="Bar &quot;left&quot; &lt;left&gt; &amp; [right]"', rendered)
        self.assertIn(
            '<figcaption>Keep &quot;left&quot; &amp; &lt;script&gt; together</figcaption>',
            rendered,
        )
        self.assertNotIn("<script>", rendered)

    def test_images_reject_remote_schemes_traversal_and_nonimage_assets(self) -> None:
        for source in [
            "https://example.com/bar.svg", "//example.com/bar.svg", "javascript:alert",
            "data:image/svg+xml;base64,PHN2Zz4=", "assets/guides/bar.svg",
            "/private/bar.svg", "/assets/../private.svg", "/assets/guides/../../private.svg",
            "/assets/%2e%2e/private.svg", "/assets/guides%2fbar.svg",
            "/assets/guides/bar.svg?redirect=elsewhere", "/assets/guides/bar.svg#fragment",
            r"/assets/guides\bar.svg", "/assets//guides/bar.svg",
            "/assets/guides/script.js", "/assets/guides/page.html",
            '/assets/guides/bar.svg"onerror="alert',
        ]:
            with self.subTest(source=source):
                rendered = build_blog.render_markdown(f'![Example]({source})')
                self.assertNotIn("<img", rendered)
                self.assertNotIn("<figure", rendered)
                self.assertNotIn("<script", rendered)
                self.assertNotIn("<a ", rendered)

    def test_renders_accessible_pipe_tables_and_inline_cell_content(self) -> None:
        rendered = build_blog.render_markdown(
            "Total | Bar | Each side\n"
            ":--- | :---: | ---:\n"
            "**135 lb** | 45 lb | [45 lb](/tools/barbell-calculator)\n"
            "185 lb | 45 lb | 70 lb"
        )

        self.assertIn(
            '<div class="blog-table-wrap" role="region" tabindex="0" '
            'aria-label="Table scroll region">', rendered,
        )
        self.assertIn(
            '<thead>\n<tr><th scope="col">Total</th><th scope="col">Bar</th>'
            '<th scope="col">Each side</th></tr>\n</thead>', rendered,
        )
        self.assertIn('<td><strong>135 lb</strong></td>', rendered)
        self.assertIn('<td><a href="/tools/barbell-calculator">45 lb</a></td>', rendered)
        self.assertEqual(3, rendered.count('<tr>'))
        self.assertTrue(rendered.endswith('</tbody>\n</table>\n</div>'))

    def test_table_cells_escape_html_and_allow_escaped_pipes(self) -> None:
        rendered = build_blog.render_markdown(
            '| <script> | Notes |\n| --- | --- |\n'
            r'| Left \| right | <img src=x onerror="alert"> & "quote" |' '\n'
            '| Safe | [bad](javascript:alert) |'
        )

        self.assertIn('<th scope="col">&lt;script&gt;</th>', rendered)
        self.assertIn('<td>Left | right</td>', rendered)
        self.assertIn('&lt;img src=x onerror=&quot;alert&quot;&gt; &amp; &quot;quote&quot;', rendered)
        self.assertIn('<td>bad</td>', rendered)
        self.assertNotIn('<script>', rendered)
        self.assertNotIn('<img ', rendered)
        self.assertNotIn('javascript:', rendered)

    def test_table_pads_short_rows_and_ignores_excess_cells(self) -> None:
        rendered = build_blog.render_markdown(
            '| A | B | C |\n| --- | --- | --- |\n'
            '| 1 | 2 |\n| 3 | 4 | 5 | Extra |'
        )
        self.assertIn('<tr><td>1</td><td>2</td><td></td></tr>', rendered)
        self.assertIn('<tr><td>3</td><td>4</td><td>5</td></tr>', rendered)
        self.assertNotIn('Extra', rendered)

    def test_table_requires_a_valid_matching_separator_row(self) -> None:
        for markdown in [
            '| A | B |\n| text | text |',
            '| A | B |\n| --- |',
            '| A | B |\n| -- | --- |',
            'Ordinary prose with a | pipe.',
        ]:
            with self.subTest(markdown=markdown):
                rendered = build_blog.render_markdown(markdown)
                self.assertNotIn('<table>', rendered)
                self.assertTrue(rendered.startswith('<p>'))

    def test_images_and_tables_preserve_adjacent_block_boundaries(self) -> None:
        rendered = build_blog.render_markdown(
            'Before.\n![Bar](/assets/guides/bar.svg)\n'
            '> Quoted | text.\n'
            '| A | B |\n| --- | --- |\n| 1 | 2 |\n'
            '## Heading | text\n'
            '- List | item\n'
            '| C | D |\n| --- | --- |\n| 3 | 4 |\n'
            '![Plates | both sides](/assets/guides/plates.svg)\n'
            '1. Finish | safely\nAfter.'
        )

        self.assertTrue(rendered.startswith('<p>Before.</p>\n<figure'))
        self.assertIn('</figure>\n<blockquote><p>Quoted | text.</p></blockquote>\n<div', rendered)
        self.assertIn('</table>\n</div>\n<h2>Heading | text</h2>\n<ul>', rendered)
        self.assertIn('</ul>\n<div', rendered)
        self.assertIn('</table>\n</div>\n<figure', rendered)
        self.assertIn('</figure>\n<ol>\n  <li>Finish | safely</li>\n</ol>\n<p>After.</p>', rendered)
        self.assertEqual(2, rendered.count('<table>'))

    def test_table_footnotes_keep_reference_links_and_backlinks(self) -> None:
        rendered = build_blog.render_markdown(
            '| Weight | Note |\n| --- | --- |\n| 135 lb | Check the bar.[^bar] |\n\n'
            '[^bar]: Bars vary in weight.'
        )
        self.assertIn('<td>Check the bar.<sup id="fnref-bar">', rendered)
        self.assertIn('class="footnote-backref" href="#fnref-bar"', rendered)

    def test_existing_block_output_is_unchanged_without_images_or_tables(self) -> None:
        self.assertEqual(
            '<p>Intro <strong>bold</strong>.</p>\n'
            '<h2>Steps</h2>\n<ol>\n  <li>One</li>\n  <li>Two</li>\n</ol>\n'
            '<blockquote><p>Be careful.</p></blockquote>\n'
            '<p>Next paragraph continued.</p>',
            build_blog.render_markdown(
                'Intro **bold**.\n\n## Steps\n1. One\n2. Two\n'
                '> Be careful.\nNext paragraph\ncontinued.'
            ),
        )

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
        self.assertIn("Practical RackMath guides about barbell loading", index)
        self.assertNotIn("Daily weight lifting calculator notes", index)
        self.assertIn("All RackMath guides.", archive)
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

    def test_sitemap_preserves_hub_dates_without_duplicate_urls(self) -> None:
        registry = {"pages": [
            {"status": "published", "type": "hub", "slug": "/tools/", "updated": "2026-11-17"},
            {"status": "published", "type": "hub", "slug": "/workouts/"},
        ]}
        for builder in (build_blog, build_site):
            with self.subTest(builder=builder.__name__), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "content").mkdir()
                (root / "content" / "seo-pages.json").write_text(json.dumps(registry), encoding="utf-8")
                with mock.patch.object(builder, "ROOT", root):
                    if builder is build_blog:
                        builder.write_sitemap([])
                    else:
                        builder.write_sitemap([], registry)
                entries = ET.parse(root / "sitemap.xml").getroot().findall("{*}url")
                locations = [entry.findtext("{*}loc") for entry in entries]
                self.assertEqual(len(locations), len(set(locations)))
                tools = next(entry for entry in entries if entry.findtext("{*}loc") == "https://rackmath.com/tools/")
                self.assertEqual("2026-11-17", tools.findtext("{*}lastmod"))
                self.assertEqual("0.9", tools.findtext("{*}priority"))
                self.assertEqual(["loc", "lastmod", "priority"], [child.tag.rsplit("}", 1)[-1] for child in tools])
                workouts = next(entry for entry in entries if entry.findtext("{*}loc") == "https://rackmath.com/workouts/")
                self.assertIsNone(workouts.find("{*}lastmod"))

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
