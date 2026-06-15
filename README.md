# RackMath Website

Static marketing site for RackMath.app.

## Local preview

```bash
python3 -m http.server 4173
```

Then open `http://localhost:4173`.

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
