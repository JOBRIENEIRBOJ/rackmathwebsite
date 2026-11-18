# RackMath SEO Implementation Tracker

This tracker follows the RackMath SEO + value build plan. Update it whenever an SEO foundation task, generated page, or conversion hook ships.

## Calculator SEO improvement — 2026-11-17

- Status: Deployed and verified on 2026-11-17
- Scope: improve search targeting for the existing barbell calculator and weight lifting tools hub; preserve canonical URLs, the calculator interaction, and the app's intentional noindex policy.
- Planned files: `content/seo-pages.json`, `tools/build_site.py`, `index.html`, their generated tool pages and sitemap, and this tracker.
- Baseline: connected Search Console data for 2026-10-18 through 2026-11-14 (all countries/devices) reports 626 impressions, 3 clicks, 0.48% CTR, and average position 6.54 for `barbell calculator`; `weight lifting calculator` reports 1 impression, 0 clicks, and average position 36. These are period averages, not current rank measurements.
- Evidence: https://search.google.com/search-console/performance/search-analytics?resource_id=sc-domain%3Arackmath.com (exact query filters); Ahrefs project 10526045. Public pages are crawlable and self-canonical; no indexing blocker was found on the two target URLs.
- Implementation: use `/tools/barbell-calculator` for plate-loading intent and `/tools/` for broader weight lifting calculations. Improve titles, summaries, static worked examples, and contextual links without adding duplicate landing pages.
- Verification planned: production build, existing SEO/artifact validation, desktop/mobile browser checks, calculation smoke checks, and scoped diff inspection. Publication authorized by the user on 2026-11-17.
- Build follow-up: the existing sitemap deduplication drops registry update dates for base hub URLs. Include `tools/build_blog.py` alongside `tools/build_site.py` so full-site and blog-only builds retain the tools hub's actual modification date.
- Existing unrelated local changes: deleted `Screenshot 2026-05-20 145206.png`, untracked images, Search Console ZIP, and `supabase/`; leave untouched.

### Completed changes and verification

- Updated `/tools/barbell-calculator` title, description, social metadata, introduction, explicit lb/kg worked formula, equipment FAQ/schema, and links to the broader calculator collection.
- Retargeted `/tools/` to weight lifting calculators, with direct calculator entry links and guidance distinguishing plate loading, estimated maxes, warmups, and volume. Added a descriptive link from the homepage FAQ.
- Preserved canonical URLs, calculator JavaScript/styles, redirect rules, and all app source files. Sitemap dates changed only for the two substantially updated tool pages.
- Fixed hub modification-date preservation in both sitemap generators, keeping XML elements in schema order. Added a regression test covering full-site and blog-only builds, duplicate prevention, priority preservation, and omission of dates when unknown.
- Changed source files: `content/seo-pages.json`, `tools/build_site.py`, `tools/build_blog.py`, `index.html`, `tests/test_build_blog_markdown.py`, and this tracker. Regenerated `tools/index.html`, `tools/barbell-calculator.html`, and `sitemap.xml`.
- `python3 -m unittest discover -s tests -v`: 12/12 passed.
- `npm run build`: passed; SEO validation covered 133 pages, 133 sitemap URLs, and 137 redirects; 182 public files staged and validated. Existing metadata-length warnings elsewhere remain.
- `npm run lint` in the original `platecalculator` workspace: passed, 264 source files. The separate website has no lint script; its production SEO and artifact validators passed.
- Desktop (1440×1000) and mobile (390×844) browser checks: passed titles/headings/canonicals, calculator navigation, 225 lb → 90 lb per side, 100 kg → 40 kg per side, expandable FAQ, no horizontal overflow, and no first-party script errors. Screenshots reviewed; external requests were blocked during local QA. Local harness and screenshots: `/tmp/rackmath-seo-20261117/`.
- `git diff --check`: passed. Unrelated pre-existing changes remain untouched.
- Release: publish only the nine intended SEO files through `JOBRIENEIRBOJ/rackmathwebsite` on `main` and Netlify project `rackmathlp` (`rackmath.com`). Verify the build from committed files, wait for Netlify to report ready, and check live titles, canonicals, content, and sitemap dates.
- Release result: code commit `55c27a0250c886f4f578d5000d8947828f76cc56` pushed to `main`; Netlify production deploy `6afd059e96aa39fa83f762a8` reached `ready`. A clean detached worktree passed all 12 tests, the full build (176 tracked public files), and generated-file parity. GitHub `SEO build quality` and `Publish scheduled blog posts` both passed.
- Live verification: `/`, `/tools/`, and `/tools/barbell-calculator` returned 200 with expected titles, descriptions, H1s, self-canonicals, and parseable JSON-LD. Both tools show the new content and 2026-11-17 sitemap modification dates; sitemap retains 133 URLs. Legacy tool HTML URLs redirect correctly, source files return 404, and `.app` retains its noindex meta/header. Unrelated local changes were excluded from the commit and deploy.
- Measurement handoff: after publication, inspect both URLs in Search Console and compare the next complete 28-day period with the recorded baseline, using the same query/country/device filters. Improved rankings or clicks are not established by local validation.

| Status | Phase | Workstream | Current / Next Step |
| --- | --- | --- | --- |
| Completed | Existing site | Static homepage, features, FAQ, blog, legal pages | Keep and improve |
| Completed | Existing SEO basics | Titles, meta descriptions, H1s, canonicals on main pages | Validate with automated checks |
| Completed | Existing blog | Markdown blog generator and sitemap output | Extended by the full site generator |
| Completed | Asset kit | Free barbell visualizer found in `website-landing-kit.zip/` | Used for first tool page |
| Completed | Phase 0 | SEO tracker | `docs/seo-implementation-tracker.md` added |
| Completed | Phase 0 | Content registry | `content/seo-pages.json` added with planned SEO pages |
| Completed | Phase 0 | Static generation | `tools/build_site.py` generates SEO pages and sitemap |
| Completed | Phase 0 | Crawl/index rules | `/tools/` is no longer blocked in `robots.txt` |
| Completed | Phase 0 | Sitemap system | Published registry pages are included in `sitemap.xml` |
| Completed | Phase 0 | Shared SEO helpers | Generator emits title/meta, canonical, breadcrumbs, schema, and internal links |
| Completed | Phase 0 | Top nav | `Tools` added to shared navigation |
| Completed | Phase 1 | Free tool launch | `/tools/` and `/tools/barbell-plate-calculator.html` published |
| Completed | Phase 1 | Calculator integration | Free barbell visualizer integrated from the landing kit |
| Completed | Phase 1 | App handoff | Calculator CTA deep-links to RackMath with `source=seo` |
| Completed | Phase 2 | Tool library | Warmup, 1RM, common weights, lb/kg, RPE, volume, attempts, AI builder, importer pages published |
| Completed | Phase 3 | Workout templates | First 12 workout template pages published |
| Completed | Phase 4 | Exercise library | First 20 exercise pages published |
| Completed | Phase 5 | Feature pages | First 8 feature landing pages published |
| Completed | Phase 7 | Persona pages | First 7 persona pages published |
| Completed | Phase 8 | Public programs | Curated public program pages and app start links published |
| Completed | Phase 9 | Analytics | Website events connected; app-side conversion events documented in `docs/analytics-events.md` |

## Page Status Rules

- `published`: generated into public HTML, linked, crawlable, and in the sitemap.
- `current`: actively being implemented.
- `queued`: planned in the registry but not public yet.
- `external`: requires account or app-side access outside this repository.

## Required Checks Before Marking Published

- One unique `<title>`.
- One unique meta description.
- One `<h1>`.
- Self-referencing canonical.
- Crawlable internal links.
- Sitemap inclusion.
- Page-specific RackMath app CTA.
- Structured data only when it describes visible content.
