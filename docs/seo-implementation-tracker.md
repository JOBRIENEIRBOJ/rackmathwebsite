# RackMath SEO Implementation Tracker

This tracker follows the RackMath SEO + value build plan. Update it whenever an SEO foundation task, generated page, or conversion hook ships.

## Practical progression and PR articles — 2026-11-18

- Status: Published and verified on 2026-11-18
- Requested outcome: two genuinely useful articles explaining when to increase weight and how personal records work, including expectations and sensible increments. Speak to an intelligent beginner with very simple examples and a reassuring tone.
- Scope: two new original Markdown posts, their generated HTML, blog listings/archive, sitemap/redirects, and this tracker. Keep site styling and app behavior unchanged.
- Editorial requirements: performance-based decisions rather than promised weekly gains; distinguish PRs from one-rep max testing, small increments from universal safety guarantees, and example training logs from prescribed schedules. Verify any RackMath-specific PR claims against current code.
- Implementation: two original articles at `/blog/when-to-increase-weight-lifting` and `/blog/how-personal-records-work`, with original workout/comparison tables, cross-links, calculator links, and reader-friendly source notes. Training examples are explicitly illustrative; the PR article includes verified History / Insights guidance and distinguishes general rep progress from RackMath's stored categories.
- Sources: ACSM 2026 position stand (PubMed 41843416), Chaves et al. 2024 progression trial (PubMed 38286426), and Mitter et al. 2022 reproducibility study (PLOS ONE 10.1371/journal.pone.0268074). Source claims are limited to the findings; no promised weekly gains or universal safe increment.
- Verification: independent factual/product/arithmetic review passed; all 40 existing automated tests passed. Build validates 135 pages / 135 sitemap URLs / 139 redirects. Desktop 1440px, mobile 390px, and narrow 320px checks passed for tables, dates/canonicals, citations and return links, article cross-links, blog listing, no horizontal overflow or script errors. Screenshots reviewed in `/tmp/rackmath-articles-20261118/`. Source URLs use descriptive labels to fit narrow screens.
- Release: code commit `59e00f34c46847df41939b78c56eeff40ee7d732` passed a clean committed build, all 40 tests, staged-artifact validation, and generated-file parity. Both GitHub workflows passed; Netlify production deploy `6afdb665d3fc9f8a3d6491d2` is ready.
- Live verification: both articles return HTTP 200 and match the checked content, with correct canonicals and publication dates. Physical HTML URLs redirect to their canonical routes. Both articles appear in the blog listing/archive and the 135-URL sitemap with 2026-11-18 dates.
- IndexNow: the matching production plugin run received 4 URLs (the two articles, `/blog`, and `/blog/archive`), 0 removed, HTTP 200. Receipt does not prove indexing or ranking improvement.
- Existing unrelated local changes remain excluded.

## Barbell plate guide and reference chart — 2026-11-18

- Status: Deployed and verified on 2026-11-18
- Requested outcome: improve the existing barbell plate guide into a useful resource that coaches and equipment guides can reference.
- Scope: preserve the existing canonical article URL; add original, accessible loading diagrams, a printable lb/kg reference chart, clearer examples and calculator links, and accurate modification metadata. Keep the existing site design and app behavior.
- Implementation: expanded the existing article with two original accessible loading diagrams, 24 lb/kg table rows, a one-page printable PDF, and examples for different bars and limited plate sets. Updated the description, visible update date, BlogPosting modification date, blog listing, and sitemap while preserving the canonical URL.
- Build support: added safe standalone asset images and semantic tables to the Markdown renderer, scoped figure/table styles, an individually approved public PDF, and download-aware SEO validation. A standalone deterministic authoring script can regenerate the assets; production adds no dependencies.
- Content review: all 24 rows and additional examples independently checked. Explicitly exclude collars from table totals, explain that available sizes do not represent physical inventory counts, and note that an alternative plate combination may reach a target missed by largest-first selection. Removed an unsupported app inventory/collar claim from the draft.
- Verification: all 40 automated tests pass (29 Python, 11 Node). Renderer comparison confirms unchanged output for all 61 original article bodies. Build validates 133 pages / 133 sitemap URLs / 137 redirects. Desktop 1440px, mobile 390px, and narrow 320px browser checks pass: diagrams, semantic tables, all row arithmetic, metadata, PDF retrieval, calculator navigation, no horizontal overflow or script errors. Screenshots reviewed in `/tmp/rackmath-guide-20261118/`.
- PDF verification: one US Letter page; 24 correct rows; clickable calculator link; rendered image visually checked; repeat asset generation is byte-identical. QA renders are in `/tmp/rackmath-guide-assets-qa/`.
- Release: code commit `3bc16f30532e8eb93395f50d0ede816cdf976775` passed a clean committed build, all 40 tests, staged-artifact validation, and generated-file parity. GitHub SEO build quality and scheduled blog workflows passed. Netlify production deploy `6afdb1c9ad274ac17ad2610b` is ready.
- Live verification: article returns HTTP 200 with the expected canonical and 2026-11-18 modification date, two figures and two semantic tables. Both SVGs and the PDF return HTTP 200 and exactly match committed assets. The sitemap retains 133 URLs and the correct guide date; the private asset-authoring script returns HTTP 404.
- IndexNow: manifest comparison identifies only `/blog` and this guide. The matching production plugin run succeeded with 2 URLs submitted, 0 removed, and HTTP 200 received. Receipt does not establish indexing or ranking improvement.
- Existing unrelated local changes remain excluded: deleted screenshot, six untracked images, Search Console ZIP, and `supabase/`.

## Automated URL submission — 2026-11-17

- Status: Deployed and initial submission verified on 2026-11-17
- Requested outcome: connect automatic URL notifications for the public RackMath website after successful deployments.
- Provider: IndexNow, Bing's recommended API for this task. Plugin discovery did not return a direct Bing Webmaster connector. Use a separate site-verification key; no Bing account-wide API credential is needed.
- Changed files: `plugins/indexnow/`, `tools/build_dist.py`, focused Node/Python tests, `netlify.toml`, `package.json`, `.github/workflows/seo-quality.yml`, `.gitignore`, `README.md`, and this tracker.
- Scope: production `main` deploys of `rackmath.com` only; notify meaningful new/changed/deleted canonical pages, retain accepted submission state, and skip unchanged/deploy-preview/app URLs. Initial notification is limited to the three pages updated in this session: `/`, `/tools/`, and `/tools/barbell-calculator`.
- Local verification: all 19 Python and 11 Node tests pass. The real Netlify production-context offline build loads the plugin, validates 133 pages / 133 sitemap URLs / 137 redirects, and skips submission because it is local. Independent review found no artifact/configuration blockers. `git diff --check` passes.
- Clean committed release: build, all 30 tests, dist validation, and generated-file diff passed. GitHub SEO build quality passed for code commit `2555b489cb95ec6bbfce6568f839e2babc4e96d8`.
- Production setup: a separate IndexNow ownership token is configured only for production Builds; its value is not committed or logged. The live key file returns HTTP 200 and exactly matches the configured token. The private manifest, submission state, and plugin source return HTTP 404.
- Production evidence: Netlify deploy `6afd0d0bf3bf7ffd6fc030c6` is ready for code commit `2555b489cb95ec6bbfce6568f839e2babc4e96d8`. Its successful `onSuccess` plugin report records 3 URLs submitted, 0 removed, HTTP 202 (ownership validation pending), and the initial baseline saved. Submission receipt is not proof of indexing or ranking improvement.
- Follow-up check: this documentation-only deployment should report `No page content changes; no URLs submitted.` Verify the report for its exact deploy ID using `netlify api getLatestPluginRuns` with the site ID and package `./plugins/indexnow` to confirm cached state persists.
- Existing unrelated local changes remain excluded, as recorded below.

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
