# RackMath Website

Static marketing site for RackMath.app.

## Local preview

```bash
npm run build
python3 -m http.server 4173 --directory dist
```

Then open `http://localhost:4173`.

The production build regenerates the static site, runs the SEO checks, and
stages an allowlisted deploy artifact in `dist/`. Netlify publishes only this
directory, so source content, documentation, scripts, build tools, package
metadata, and repository files are never part of the public deployment.
The staging step also gives the first-party CSS and JavaScript files
content-based filenames and rewrites references only in `dist/`, allowing
those immutable assets to use a one-year browser cache while HTML continues
to revalidate on every request.

To recheck an existing deploy artifact without rebuilding it, run:

```bash
npm run check:dist
```

The staging step adds the asynchronous Ahrefs Web Analytics script to the
`<head>` of every public HTML page. The script and site key are configured in
`tools/build_dist.py` and included automatically in each production build.

The separate first-party remote analytics integration is optional. When both
`RACKMATH_ANALYTICS_URL` (the full HTTPS tracking endpoint) and
`RACKMATH_ANALYTICS_ANON_KEY` are available at build time, the staging step
creates `assets/analytics-config.js` inside
`dist/` and loads it before the fingerprinted main script on every page. If
neither variable is set, no runtime config file or tag is emitted. Supplying
only one variable fails the build so a partial analytics configuration cannot
be deployed.
Both values are intentionally visible in the browser: use only the Supabase
public anon/publishable key, never a service-role key or another secret. In
Netlify, do not mark this public key as a secret value because secret scanning
correctly rejects secret values found in deploy output.

## Automatic URL submission

Production deploys use a local Netlify IndexNow plugin to notify Bing and other
participating search engines about new, changed, and removed public pages.
This does not submit URLs to Google; keep the existing Google sitemap submission.

The plugin runs only after a successful remote production deploy of `main` on
the `rackmathlp` project. It checks the live ownership file, submits canonical
`https://rackmath.com/` URLs, and remembers accepted page hashes in Netlify's
build cache. Unchanged pages, previews, asset-only changes, and `.app` URLs are
excluded. The first run submits only the homepage, tools hub, and barbell
calculator changed during the November 17 SEO update, then seeds its baseline.

`INDEXNOW_KEY` is a separate 32-character lowercase hexadecimal ownership token
configured in Netlify's **production / Builds** environment. The build generates
`dist/<key>.txt`, whose contents must equal the key. This file is intentionally
public for ownership verification; it is not a Bing account API credential.
Do not put a Bing Webmaster account API key in this variable or commit the value
to source. Configure it as a non-secret build value because the protocol requires
the generated ownership file to be public. Local and CI builds without the
variable do not publish an ownership file or submit requests.

Page hashes and submission state stay in ignored `.netlify/` files, outside the
public deploy allowlist. HTTP 200 means received; HTTP 202 means received with
ownership validation pending. Neither establishes indexing or ranking changes.
Submission failures appear in the Netlify deploy summary/log without taking the
website offline, and leave the previous state available for retry on a later
successful deploy. Clearing Netlify's build cache resets the baseline; it does
not trigger a full-site submission.

Run `npm test` for generator, artifact, and mocked API checks. After setup, confirm
the IndexNow result in the Netlify deploy log and Bing Webmaster Tools' IndexNow
report. Removing `[[context.production.plugins]]` for `./plugins/indexnow` stops
automatic notifications. Keep the sitemap available independently.

References: [Bing URL submission](https://www.bing.com/webmasters/help/?topicid=62f2860b),
[IndexNow protocol](https://www.indexnow.org/documentation),
[Netlify plugin lifecycle](https://docs.netlify.com/extend/develop-and-share/develop-build-plugins/).

## Blog workflow

Blog posts live in `content/blog` as Markdown files with front matter. Create a draft with:

```bash
python3 tools/new_blog_post.py "How to Load 225 lb on a Barbell"
```

Then edit the new Markdown file and rebuild the static blog pages:

```bash
python3 tools/build_site.py
```

The full site generator updates `blog.html`, individual files in `blog/`, SEO pages such as `tools/`, and `sitemap.xml`.
It also updates `blog/archive.html`, which lists every post by year.

To validate published SEO pages after a build, run:

```bash
python3 tools/check_seo.py
```

The older blog-only command still exists for focused blog work:

```bash
python3 tools/build_blog.py
```

Future-dated posts stay hidden until their front matter `date` arrives. To preview future posts locally, run:

```bash
python3 tools/build_blog.py --include-future
```

GitHub Actions uses two blog workflows:

- `.github/workflows/generate-blog-draft.yml` creates the next AI-generated Markdown draft and opens a pull request for review.
- `.github/workflows/publish-blog.yml` runs every day at 10:15 UTC and publishes only approved drafts that have already been merged into `main`.

Review generated drafts in the pull request, edit the Markdown in `content/blog/` if needed, then merge the PR. The post will publish when its front matter `date` is today or earlier.

## CTA links

The landing page currently sends purchase, trial, and open-app calls to:

```text
https://www.rackmath.app/
```

Update those URLs in the HTML files if the production calculator, checkout, free trial, or app sign-in URL changes.

## SEO page workflow

SEO pages are tracked in `content/seo-pages.json`.

- Mark a page `queued` while it is planned.
- Mark a page `published` only when the generator outputs public HTML, the URL is crawlable, the page is linked, and `python3 tools/check_seo.py` passes.
- Keep roadmap status in `docs/seo-implementation-tracker.md`.

The first generated SEO pages are:

- `tools/index.html`
- `tools/barbell-plate-calculator.html`
