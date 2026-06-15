# RackMath SEO Implementation Tracker

This tracker follows the RackMath SEO + value build plan. Update it whenever an SEO foundation task, generated page, or conversion hook ships.

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
