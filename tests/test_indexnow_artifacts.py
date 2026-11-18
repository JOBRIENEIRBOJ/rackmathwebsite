from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build_dist


PAGE = '''<!doctype html><html><head><title>Calculator</title>
<meta name="description" content="Calculate plates">
<link rel="stylesheet" href="styles.123.css">
<script type="application/ld+json">{"name":"Calculator","@type":"SoftwareApplication"}</script>
</head><body><header>Navigation</header><main><h1>Calculator</h1><p>135 lb</p></main>
<footer>Footer</footer><script src="script.123.js"></script></body></html>'''


class IndexNowArtifactTests(unittest.TestCase):
    def test_ownership_file_is_explicitly_allowlisted_and_matches_key(self):
        key = "a1" * 16
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict("os.environ", {"INDEXNOW_KEY": key}):
            root = Path(directory)
            build_dist.add_indexnow_key(root)
            self.assertEqual(key, (root / f"{key}.txt").read_text())
            self.assertTrue(build_dist.relative_file_is_allowed(Path(f"{key}.txt")))
            self.assertFalse(build_dist.relative_file_is_allowed(Path(f"{'b2' * 16}.txt")))
            self.assertFalse(build_dist.relative_file_is_allowed(Path("secret.txt")))
            self.assertFalse(build_dist.relative_file_is_allowed(Path(".netlify/indexnow-manifest.json")))
            (root / f"{key}.txt").write_text("wrong")
            with self.assertRaisesRegex(build_dist.DistBuildError, "ownership file is missing or does not match"):
                build_dist.validate_dist(root)

    def test_unconfigured_build_publishes_no_ownership_file(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict("os.environ", {"INDEXNOW_KEY": ""}):
            root = Path(directory)
            build_dist.add_indexnow_key(root)
            self.assertEqual([], list(root.iterdir()))
            self.assertFalse(build_dist.relative_file_is_allowed(Path(f"{'a1' * 16}.txt")))

    def test_invalid_keys_fail_without_echoing_the_value(self):
        for key in ["private-credential-value", "../outside", "a" * 31, "A" * 32]:
            with self.subTest(key=key), mock.patch.dict("os.environ", {"INDEXNOW_KEY": key}):
                with self.assertRaises(build_dist.DistBuildError) as error:
                    build_dist.indexnow_key()
                self.assertNotIn(key, str(error.exception))

    def test_digest_ignores_chrome_assets_and_normalizes_schema_key_order(self):
        changed = PAGE.replace("Navigation", "Updated navigation").replace("Footer", "New footer")
        changed = changed.replace("styles.123.css", "styles.456.css").replace("script.123.js", "script.456.js")
        changed = changed.replace('{"name":"Calculator","@type":"SoftwareApplication"}', '{"@type":"SoftwareApplication","name":"Calculator"}')
        self.assertEqual(build_dist.indexnow_page_digest(PAGE), build_dist.indexnow_page_digest(changed))

    def test_digest_detects_visible_content_and_seo_updates(self):
        for original, replacement in [("135 lb", "225 lb"), ("<title>Calculator", "<title>Barbell Calculator"), ("Calculate plates", "Load plates"), ('"name":"Calculator"', '"name":"Barbell"')]:
            with self.subTest(original=original):
                self.assertNotEqual(build_dist.indexnow_page_digest(PAGE), build_dist.indexnow_page_digest(PAGE.replace(original, replacement)))

    def test_manifest_is_private_and_only_contains_canonical_page_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            staging = root / "dist"
            (staging / "tools").mkdir(parents=True)
            (staging / "index.html").write_text(PAGE)
            (staging / "tools" / "barbell-calculator.html").write_text(PAGE)
            (staging / "sitemap.xml").write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://rackmath.com/</loc></url><url><loc>https://rackmath.com/tools/barbell-calculator</loc></url></urlset>')
            with mock.patch.object(build_dist, "ROOT", root):
                build_dist.write_indexnow_manifest(staging)
            manifest = json.loads((root / ".netlify/indexnow-manifest.json").read_text())
            self.assertEqual(1, manifest["version"])
            self.assertEqual("rackmath.com", manifest["host"])
            self.assertEqual({"https://rackmath.com/", "https://rackmath.com/tools/barbell-calculator"}, set(manifest["pages"]))
            self.assertTrue(all(len(value) == 64 for value in manifest["pages"].values()))
            self.assertFalse((staging / ".netlify").exists())

    def test_manifest_rejects_app_foreign_query_and_unsafe_paths(self):
        for url in ["https://www.rackmath.app/", "https://example.com/", "https://rackmath.com/?preview=1", "https://rackmath.com/%2e%2e/outside"]:
            with self.subTest(url=url), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "sitemap.xml").write_text(f'<urlset><url><loc>{url}</loc></url></urlset>')
                with mock.patch.object(build_dist, "ROOT", root), self.assertRaises(build_dist.DistBuildError):
                    build_dist.write_indexnow_manifest(root)


if __name__ == "__main__":
    unittest.main()
