# RackMath SEO launch checklist

Use this order so the public site never sends an event type that the analytics
database rejects and so the URL migration can be measured cleanly.

## Before deployment

1. Export 16 months of Google Search Console data by query, page, country, and
   device. Save the current indexed-page and canonical reports before changing
   URLs.
2. Update the published Termly privacy disclosure for first-party website
   analytics. The marketing site uses a random session-scoped identifier; the
   Edge Function also receives the normal request IP and user-agent for abuse
   controls and diagnostics. No entered weight, calculated load, workout text,
   or other lifting input is included in the marketing analytics payload.
3. In the app Supabase project, apply migration
   `040_extend_marketing_analytics_taxonomy.sql`.
4. Deploy the updated `track-analytics` and `owner-analytics` Edge Functions and
   their shared CORS helper.
5. Deploy the `.app` build with its global `X-Robots-Tag: noindex, follow`
   response header.
6. Configure the marketing Netlify site with:
   - `RACKMATH_ANALYTICS_URL`: the full HTTPS `track-analytics` function URL;
   - `RACKMATH_ANALYTICS_ANON_KEY`: the public Supabase anon/publishable key,
     never the service-role key.
7. Deploy the marketing site from `npm run build`; Netlify must publish only
   `dist/`.

## Immediate production verification

- Confirm `/`, `/tools/barbell-calculator`, and a blog URL return 200.
- Confirm an old `.html` URL and the wrong trailing-slash variant each return a
  single permanent redirect to the clean canonical URL.
- Confirm canonical, `og:url`, JSON-LD URLs, and the sitemap agree.
- Confirm `/package.json`, `/package-lock.json`, `/README.md`,
  `/tools/build_site.py`, `/content/seo-pages.json`, and
  `/docs/analytics-events.md` return 404.
- Confirm fingerprinted CSS/JS responses are immutable and HTML revalidates.
- Confirm the `.app` responses for `/`, `/delete-account/`, `/robots.txt`,
  `/sitemap.xml`, `/manifest.json`, and one client-side route include
  `X-Robots-Tag: noindex, follow`.
- Confirm `.app/robots.txt` permits crawling and its sitemap contains no URLs.

## Analytics acceptance journey

In a fresh browser session:

1. Land on `/tools/barbell-calculator`.
2. Submit one calculation.
3. Click the attributed RackMath app link.
4. Complete a test signup and first workout when practical.
5. Confirm the owner dashboard receives distinct-visitor stages for
   `seo_page_viewed`, `seo_tool_completed`, `seo_app_link_clicked`,
   `seo_app_landing`, `signup_completed`, and `first_workout_completed`.
6. Inspect the website analytics request and confirm its properties do not
   contain target weight, loaded weight, plate inventory, or workout text.

## Search rollout

1. Submit `https://rackmath.com/sitemap.xml` in Search Console.
2. Request inspection for the homepage, calculator, common-weights page, and
   the three core loading guides.
3. Inspect representative retired `.html` URLs and verify Google observes the
   permanent redirect and new canonical.
4. Keep all migration redirects indefinitely.
5. Review weekly for the first month: duplicate canonical selection, indexed
   `.app` URLs, redirect errors, priority-query page splitting, and calculator
   impressions/clicks.
6. Set numeric growth targets only after 28 clean days of baseline data.

## Deliberately deferred

Blog article rewrites, citations/footnotes, expert review, and topic-queue
retargeting remain the final editorial phase. Do not auto-publish additional
broad beginner-confidence articles until the calculator cluster and Search
Console baseline have been reviewed.
