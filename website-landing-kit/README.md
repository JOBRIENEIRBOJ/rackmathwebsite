# Rack Math Landing Page Optimization Kit

Use this folder as a portable source kit for the separate Rack Math website project.
It includes copy, SEO metadata, markup sections, CSS tokens, and brand assets you
can upload into another Codespace.

## Files

- `landing-page-brief.md`: strategy, page structure, and implementation notes.
- `landing-copy.json`: reusable page copy, CTA labels, feature cards, and FAQ text.
- `seo-meta.html`: metadata tags to adapt in the website `<head>`.
- `landing-sections.html`: semantic HTML sections for a website landing page.
- `landing-styles.css`: CSS tokens and component styling for the supplied sections.
- `asset-manifest.json`: asset descriptions, recommended usage, and alt text.
- `assets/`: Rack Math logos, app icon, and calculator screenshot.

## Recommended Upload Path

Copy the whole `website-landing-kit/` folder into the website repo first. Then move:

- images from `assets/` into the website's public/static assets directory
- `seo-meta.html` content into the root layout/head component
- copy from `landing-copy.json` into the website's content layer
- sections from `landing-sections.html` into the homepage component
- styles from `landing-styles.css` into the homepage stylesheet or design system

## Implementation Notes

The recommended landing approach is app-first: show the calculator product
quickly, then explain programs, tracking, sync, and premium value. Avoid hiding
the product behind a generic marketing hero.

Primary CTA:
`Open Rack Math`

Secondary CTA:
`See how it works`

Best first viewport:
brand, concise value proposition, two CTAs, app screenshot, and three short
proof/value points.

