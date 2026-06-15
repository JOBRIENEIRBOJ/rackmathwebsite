#!/usr/bin/env python3
"""Build Rack Math static pages from registry-backed content."""

from __future__ import annotations

import html
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

import build_blog


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "content" / "seo-pages.json"
SITE_URL = "https://www.rackmath.com"
APP_URL = "https://www.rackmath.app"
BASE_PAGES = [
    ("/", "1.0"),
    ("/tools/", "0.9"),
    ("/features.html", "0.8"),
    ("/about.html", "0.7"),
    ("/faq.html", "0.8"),
    ("/blog.html", "0.8"),
    ("/blog/archive.html", "0.7"),
]


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def published_pages(registry: dict) -> list[dict]:
    return [page for page in registry["pages"] if page.get("status") == "published"]


def escape(value: str) -> str:
    return html.escape(str(value), quote=True)


def app_href(route: str) -> str:
    return urljoin(f"{APP_URL}/", route.lstrip("/"))


def prefix_for(slug: str) -> str:
    parts = [part for part in slug.strip("/").split("/") if part]
    depth = len(parts) if slug.endswith("/") else max(len(parts) - 1, 0)
    return "../" * depth


def nav(current: str, prefix: str = "") -> str:
    tool_links = [
        ("All tools", f"{prefix}tools/"),
        ("Barbell Plate Calculator", f"{prefix}tools/barbell-plate-calculator.html"),
        ("Warmup Set Calculator", f"{prefix}tools/warmup-set-calculator.html"),
        ("One Rep Max Calculator", f"{prefix}tools/one-rep-max-calculator.html"),
        ("Common Barbell Weights", f"{prefix}tools/common-barbell-weights.html"),
        ("lb/kg Plate Converter", f"{prefix}tools/lb-kg-plate-converter.html"),
        ("RPE Calculator", f"{prefix}tools/rpe-calculator.html"),
        ("Training Volume Calculator", f"{prefix}tools/training-volume-calculator.html"),
        ("Powerlifting Attempt Calculator", f"{prefix}tools/powerlifting-attempt-calculator.html"),
        ("AI Workout Builder", f"{prefix}tools/ai-workout-builder.html"),
        ("Workout Plan Importer", f"{prefix}tools/workout-plan-importer.html"),
    ]
    tools_current = ' aria-current="page"' if current == "tools" else ""
    tools_dropdown = "\n".join(f'          <a href="{href}">{label}</a>' for label, href in tool_links)
    links = [
        ("Features", f"{prefix}features.html", "features"),
        ("About", f"{prefix}about.html", "about"),
        ("FAQ", f"{prefix}faq.html", "faq"),
        ("Blog", f"{prefix}blog.html", "blog"),
        ("Premium", f"{prefix}index.html#premium", "premium"),
    ]
    rendered = [
        f"""        <div class="nav-dropdown"{tools_current}>
          <button class="nav-dropdown-trigger" type="button">Tools</button>
          <div class="nav-dropdown-menu">
{tools_dropdown}
          </div>
        </div>"""
    ]
    rendered.extend(
        f'        <a href="{href}"{" aria-current=\"page\"" if current == key else ""}>{label}</a>'
        for label, href, key in links
    )
    return "\n".join(rendered)


def header(current: str, prefix: str = "") -> str:
    return f"""    <header class="site-header">
      <a class="brand" href="{prefix}index.html" aria-label="RackMath home">
        <img class="brand-mark" src="{prefix}assets/rackmathblue-header.png" alt="" aria-hidden="true">
        <span>RackMath</span>
      </a>
      <button class="nav-toggle" type="button" aria-label="Open navigation" aria-expanded="false">
        <span></span>
        <span></span>
      </button>
      <nav class="site-nav" aria-label="Primary navigation">
{nav(current, prefix)}
      </nav>
      <a class="header-cta" href="{APP_URL}/">Try free</a>
    </header>"""


def footer(prefix: str = "") -> str:
    return f"""    <footer class="site-footer">
      <div>
        <a class="brand" href="{prefix}index.html" aria-label="RackMath home">
          <img class="brand-mark" src="{prefix}assets/rackmathblue-header.png" alt="" aria-hidden="true">
          <span>RackMath</span>
        </a>
        <p>Barbell plate math, workout sessions, and progress tracking for lifters.</p>
      </div>
      <nav aria-label="Footer navigation">
        <a href="{prefix}tools/">Tools</a>
        <a href="{prefix}features.html">Features</a>
        <a href="{prefix}about.html">About</a>
        <a href="{prefix}faq.html">FAQ</a>
        <a href="{prefix}blog.html">Blog</a>
        <a href="{APP_URL}/">Open app</a>
      </nav>
    </footer>"""


def breadcrumb_schema(page: dict) -> dict:
    section = page.get("section", "")
    items = [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}/"},
    ]
    if section:
        items.append(
            {
                "@type": "ListItem",
                "position": 2,
                "name": section.replace("-", " ").title(),
                "item": f"{SITE_URL}/{section}/",
            }
        )
    if page["type"] != "hub":
        items.append(
            {
                "@type": "ListItem",
                "position": len(items) + 1,
                "name": page["h1"],
                "item": f"{SITE_URL}{page['slug']}",
            }
        )
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


def software_schema(page: dict) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "Rack Math",
        "applicationCategory": "HealthApplication",
        "operatingSystem": "Web",
        "url": f"{SITE_URL}{page['slug']}",
        "description": page["description"],
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    }


def calculator_faq_schema() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": "How do I calculate plates for a barbell?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Subtract the bar weight from your target weight, divide the remaining weight by two, then load that amount on each side using your available plates.",
                },
            },
            {
                "@type": "Question",
                "name": "Does this plate calculator work for kilograms?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Yes. Switch the unit control to kg to use common 20 kg and 15 kg bars with kilogram plates.",
                },
            },
            {
                "@type": "Question",
                "name": "What if my target weight cannot be loaded exactly?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "The calculator shows the closest loadable weight based on the plates you selected.",
                },
            },
        ],
    }


def schema_scripts(page: dict) -> str:
    schemas: list[dict] = []
    if "BreadcrumbList" in page.get("schema", []):
        schemas.append(breadcrumb_schema(page))
    if "SoftwareApplication" in page.get("schema", []):
        schemas.append(software_schema(page))
    if page["slug"] == "/tools/barbell-plate-calculator.html":
        schemas.append(calculator_faq_schema())
    return "\n".join(
        f'    <script type="application/ld+json">\n      {json.dumps(schema, indent=6)}\n    </script>'
        for schema in schemas
    )


def page_shell(page: dict, body: str, current: str = "tools", extra_script: str = "") -> str:
    prefix = prefix_for(page["slug"])
    canonical = f"{SITE_URL}{page['slug']}"
    schema = schema_scripts(page)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(page["title"])}</title>
    <meta name="description" content="{escape(page["description"])}">
    <link rel="canonical" href="{canonical}">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Rack Math">
    <meta property="og:title" content="{escape(page["title"])}">
    <meta property="og:description" content="{escape(page["description"])}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{SITE_URL}/assets/rackmathblue-gradient.png">
    <meta property="og:image:alt" content="Rack Math blue gradient logo">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{escape(page["title"])}">
    <meta name="twitter:description" content="{escape(page["description"])}">
    <meta name="twitter:image" content="{SITE_URL}/assets/rackmathblue-gradient.png">
    <meta name="twitter:image:alt" content="Rack Math blue gradient logo">
    <meta name="theme-color" content="#0a6dff">
    <link rel="icon" href="{prefix}assets/rackmathblue.png" type="image/png">
    <link rel="apple-touch-icon" href="{prefix}assets/rackmathblue.png">
    <link rel="stylesheet" href="{prefix}styles.css?v=20260615">
{schema}
  </head>
  <body>
{header(current, prefix)}
{body}
{footer(prefix)}
    <script src="{prefix}script.js"></script>
{extra_script}
  </body>
</html>
"""


def render_related_links(page: dict, registry: dict, prefix: str) -> str:
    pages_by_slug = {item["slug"]: item for item in registry["pages"]}
    links = []
    for slug in page.get("related", []):
        related = pages_by_slug.get(slug)
        if related:
            href = f"{prefix}{slug.lstrip('/')}"
            label = related["h1"]
        else:
            href = f"{prefix}{slug.lstrip('/')}"
            label = slug.strip("/").replace("-", " ").replace(".html", "").title()
        links.append(f'          <a class="related-card" href="{href}">{escape(label)}</a>')
    return "\n".join(links)


def render_tools_hub(page: dict, registry: dict) -> str:
    prefix = prefix_for(page["slug"])
    published_tools = [
        item for item in registry["pages"] if item.get("section") == "tools" and item.get("type") == "tool"
    ]
    cards = "\n".join(
        f"""          <a class="tool-card" href="{prefix + item["slug"].lstrip("/") if item.get("status") == "published" else '#'}"{" aria-disabled=\"true\"" if item.get("status") != "published" else ""}>
            <span class="tool-card-kicker">{escape(item.get("eyebrow", "RackMath tool"))}</span>
            <h2>{escape(item["h1"])}</h2>
            <p>{escape(item["description"])}</p>
            <span class="tool-card-action">{'Open tool' if item.get("status") == "published" else 'Planned'}</span>
          </a>"""
        for item in published_tools
    )
    body = f"""    <main>
      <section class="page-hero seo-hero">
        <p class="eyebrow">{escape(page["eyebrow"])}</p>
        <h1>{escape(page["h1"])}</h1>
        <p>{escape(page["summary"])}</p>
        <div class="hero-actions">
          <a class="button primary" href="{app_href(page["appRoute"])}" data-rm-app-link data-rm-event="app_deeplink_clicked">Try RackMath free</a>
          <a class="button secondary" href="{prefix}tools/barbell-plate-calculator.html">Try the plate calculator</a>
        </div>
      </section>

      <section class="section tool-grid" aria-label="RackMath lifting tools">
{cards}
      </section>
    </main>"""
    return page_shell(page, body)


def render_calculator_section(page: dict) -> str:
    cta_href = app_href(page["appRoute"])
    return f"""      <section class="rm-free-calculator" id="barbell-plate-calculator" data-rm-calculator aria-labelledby="rm-free-calculator-title">
        <div class="rm-section-heading rm-free-calculator-heading">
          <p class="rm-eyebrow">Free barbell plate calculator</p>
          <h2 id="rm-free-calculator-title">Visualize the plates for any barbell lift.</h2>
          <p class="rm-section-copy">Use this free RackMath barbell visualizer to calculate plates per side for pounds or kilograms. Enter a target weight, choose your bar, and see the loaded bar before your next set.</p>
        </div>

        <div class="rm-free-calculator-grid">
          <form class="rm-calculator-panel" data-rm-calculator-form aria-label="Free barbell plate calculator">
            <div class="rm-field">
              <label for="rm-target-weight">Target weight</label>
              <div class="rm-input-shell">
                <input id="rm-target-weight" data-rm-target-weight type="number" inputmode="decimal" min="0" step="2.5" value="225">
                <span data-rm-unit-label>lb</span>
              </div>
            </div>

            <div class="rm-field">
              <span class="rm-control-label">Units</span>
              <div class="rm-segmented" role="radiogroup" aria-label="Weight unit">
                <label><input data-rm-unit type="radio" name="rm-free-unit" value="lbs" checked><span>lb</span></label>
                <label><input data-rm-unit type="radio" name="rm-free-unit" value="kg"><span>kg</span></label>
              </div>
            </div>

            <div class="rm-field">
              <label for="rm-bar-weight">Bar</label>
              <select id="rm-bar-weight" data-rm-bar-select>
                <option value="45">Olympic barbell, 45 lb</option>
                <option value="33">Women's Olympic barbell, 33 lb</option>
                <option value="20">Training bar, 20 lb</option>
              </select>
            </div>

            <fieldset class="rm-field rm-plate-field">
              <legend>Available plates</legend>
              <div class="rm-plate-toggle-grid" data-rm-plate-controls>
                <label><input type="checkbox" value="55" data-rm-plate-option><span>55</span></label>
                <label><input type="checkbox" value="45" data-rm-plate-option checked><span>45</span></label>
                <label><input type="checkbox" value="35" data-rm-plate-option checked><span>35</span></label>
                <label><input type="checkbox" value="25" data-rm-plate-option checked><span>25</span></label>
                <label><input type="checkbox" value="10" data-rm-plate-option checked><span>10</span></label>
                <label><input type="checkbox" value="5" data-rm-plate-option checked><span>5</span></label>
                <label><input type="checkbox" value="2.5" data-rm-plate-option checked><span>2.5</span></label>
              </div>
            </fieldset>

            <button class="button primary rm-calculator-submit" type="submit">Calculate plates</button>
          </form>

          <div class="rm-visualizer-panel">
            <p class="rm-result-message" data-rm-result-message aria-live="polite">225 lb uses 90 lb per side.</p>
            <div class="rm-barbell-frame" data-rm-visualizer aria-label="Barbell visualizer">
              <div class="rm-plate-stack rm-plate-stack-left" data-rm-left-stack>
                <span class="rm-plate" style="--rm-plate-color: #f8fafc; --rm-plate-text: #111827; --rm-plate-height: 126px; --rm-plate-width: 30px;">45</span>
                <span class="rm-plate" style="--rm-plate-color: #f8fafc; --rm-plate-text: #111827; --rm-plate-height: 126px; --rm-plate-width: 30px;">45</span>
              </div>
              <div class="rm-bar-core"><span data-rm-bar-label>45 lb bar</span></div>
              <div class="rm-plate-stack rm-plate-stack-right" data-rm-right-stack>
                <span class="rm-plate" style="--rm-plate-color: #f8fafc; --rm-plate-text: #111827; --rm-plate-height: 126px; --rm-plate-width: 30px;">45</span>
                <span class="rm-plate" style="--rm-plate-color: #f8fafc; --rm-plate-text: #111827; --rm-plate-height: 126px; --rm-plate-width: 30px;">45</span>
              </div>
            </div>

            <div class="rm-result-grid">
              <div><span>Each side</span><strong data-rm-per-side>90 lb</strong></div>
              <div><span>Total loaded</span><strong data-rm-total>225 lb</strong></div>
              <div><span>Plates per side</span><strong data-rm-plate-list>45 + 45</strong></div>
            </div>

            <a class="button secondary rm-full-app-link" href="{cta_href}" data-rm-app-link data-rm-event="app_deeplink_clicked">Save this lift in RackMath</a>
          </div>
        </div>
      </section>"""


def render_calculator_page(page: dict, registry: dict) -> str:
    prefix = prefix_for(page["slug"])
    related = render_related_links(page, registry, prefix)
    examples = [
        ("95 lb", "25 lb per side"),
        ("135 lb", "45 lb per side"),
        ("185 lb", "45 + 25 per side"),
        ("225 lb", "45 + 45 per side"),
        ("315 lb", "45 + 45 + 45 per side"),
        ("405 lb", "45 + 45 + 45 + 45 per side"),
    ]
    rows = "\n".join(f"              <tr><td>{target}</td><td>{plates}</td></tr>" for target, plates in examples)
    body = f"""    <main>
      <section class="page-hero seo-hero">
        <p class="eyebrow">{escape(page["eyebrow"])}</p>
        <h1>{escape(page["h1"])}</h1>
        <p>{escape(page["summary"])}</p>
      </section>

{render_calculator_section(page)}

      <section class="section seo-content-grid">
        <article>
          <p class="eyebrow">How it works</p>
          <h2>Calculate plates without doing gym-floor arithmetic.</h2>
          <p>RackMath subtracts the bar weight from your target weight, divides the remaining load across both sleeves, and builds the closest plate setup from the plates you selected.</p>
          <p>If your exact target cannot be loaded with the available plates, the calculator shows the closest loadable weight so you can adjust the set without guessing.</p>
        </article>
        <article>
          <p class="eyebrow">Mistakes to avoid</p>
          <h2>Check the bar before counting plates.</h2>
          <p>A 45 lb bar, 20 kg bar, women's bar, training bar, specialty bar, or collars can change the math. Pick the actual bar and plates you have before you load the set.</p>
        </article>
      </section>

      <section class="section table-section" aria-labelledby="common-loads-heading">
        <div class="section-heading">
          <p class="eyebrow">Common examples</p>
          <h2 id="common-loads-heading">Common barbell plate setups.</h2>
        </div>
        <div class="responsive-table">
          <table>
            <thead><tr><th>Target weight</th><th>45 lb bar plate setup</th></tr></thead>
            <tbody>
{rows}
            </tbody>
          </table>
        </div>
      </section>

      <section class="section faq-list" aria-label="Barbell plate calculator FAQ">
        <details>
          <summary>How do I calculate plates for a barbell?</summary>
          <p>Subtract the bar weight from your target weight, divide the remaining weight by two, then load that amount on each side using your available plates.</p>
        </details>
        <details>
          <summary>Does this plate calculator work for kilograms?</summary>
          <p>Yes. Switch the unit control to kg to use common 20 kg and 15 kg bars with kilogram plates.</p>
        </details>
        <details>
          <summary>What if my target weight cannot be loaded exactly?</summary>
          <p>The calculator shows the closest loadable weight based on the plates you selected, so you can adjust the set without doing extra math.</p>
        </details>
      </section>

      <section class="section related-pages" aria-labelledby="related-heading">
        <div class="section-heading">
          <p class="eyebrow">Related</p>
          <h2 id="related-heading">Keep the workout moving.</h2>
        </div>
        <div class="related-grid">
{related}
        </div>
      </section>

      <section class="final-cta">
        <p class="eyebrow">Want this inside your workout?</p>
        <h2>Save the lift in RackMath and get exact plates, warmups, timers, and history.</h2>
        <div class="hero-actions">
          <a class="button primary" href="{app_href(page["appRoute"])}" data-rm-app-link data-rm-event="app_deeplink_clicked">{escape(page["primaryCta"])}</a>
        </div>
      </section>
    </main>"""
    return page_shell(
        page,
        body,
        extra_script=f'    <script src="{prefix}assets/free-barbell-visualizer.js"></script>',
    )


def tool_key(page: dict) -> str:
    slug = page["slug"]
    return {
        "/tools/warmup-set-calculator.html": "warmup",
        "/tools/one-rep-max-calculator.html": "oneRepMax",
        "/tools/common-barbell-weights.html": "commonWeights",
        "/tools/lb-kg-plate-converter.html": "converter",
        "/tools/rpe-calculator.html": "rpe",
        "/tools/training-volume-calculator.html": "volume",
        "/tools/powerlifting-attempt-calculator.html": "attempts",
        "/tools/ai-workout-builder.html": "aiBuilder",
        "/tools/workout-plan-importer.html": "importer",
    }[slug]


def render_tool_controls(page: dict) -> str:
    key = tool_key(page)
    if key == "warmup":
        return """            <div class="tool-form-grid">
              <label>Working weight <input name="workingWeight" type="number" min="0" step="5" value="225"></label>
              <label>Units <select name="unit"><option value="lb">lb</option><option value="kg">kg</option></select></label>
            </div>"""
    if key == "oneRepMax":
        return """            <div class="tool-form-grid">
              <label>Weight lifted <input name="weight" type="number" min="0" step="5" value="185"></label>
              <label>Reps <input name="reps" type="number" min="1" max="30" step="1" value="5"></label>
              <label>Units <select name="unit"><option value="lb">lb</option><option value="kg">kg</option></select></label>
            </div>"""
    if key == "commonWeights":
        return """            <p class="tool-static-copy">These common setups assume a 45 lb bar and standard pound plates. Use the full RackMath calculator when your bar, collars, or available plates are different.</p>"""
    if key == "converter":
        return """            <div class="tool-form-grid">
              <label>Pounds <input name="pounds" type="number" min="0" step="5" value="225"></label>
            </div>"""
    if key == "rpe":
        return """            <div class="tool-form-grid">
              <label>Estimated 1RM <input name="oneRm" type="number" min="0" step="5" value="250"></label>
              <label>Target reps <input name="reps" type="number" min="1" max="20" step="1" value="5"></label>
              <label>Target RPE <input name="rpe" type="number" min="6" max="10" step="0.5" value="8"></label>
            </div>"""
    if key == "volume":
        return """            <div class="tool-form-grid">
              <label>Sets <input name="sets" type="number" min="1" step="1" value="5"></label>
              <label>Reps <input name="reps" type="number" min="1" step="1" value="5"></label>
              <label>Weight <input name="weight" type="number" min="0" step="5" value="225"></label>
            </div>"""
    if key == "attempts":
        return """            <div class="tool-form-grid">
              <label>Recent max or estimated max <input name="max" type="number" min="0" step="5" value="315"></label>
            </div>"""
    if key == "aiBuilder":
        return """            <div class="tool-form-grid">
              <label>Goal <select name="goal"><option value="strength">Strength</option><option value="hypertrophy">Hypertrophy</option><option value="beginner">Beginner</option><option value="powerlifting">Powerlifting</option></select></label>
              <label>Training days <select name="days"><option>2</option><option selected>3</option><option>4</option><option>5</option></select></label>
            </div>"""
    if key == "importer":
        return """            <label class="tool-full-field">Paste a plan preview <textarea name="planText" rows="6">Squat 3x5
Bench Press 3x5
Barbell Row 3x8</textarea></label>"""
    raise ValueError(f"No controls for {page['slug']}")


def render_tool_explainer(page: dict) -> tuple[str, str]:
    copy = {
        "/tools/warmup-set-calculator.html": (
            "Plan jumps before the bar is loaded.",
            "Warmups should prepare you for the working set without turning the session into a second workout. Use the generated jumps as a starting point, then adjust for fatigue, equipment, and how the day feels.",
        ),
        "/tools/one-rep-max-calculator.html": (
            "Estimate strength without testing a true max.",
            "A one rep max estimate is useful for programming, progress checks, and attempt planning. It is still an estimate, so RackMath treats it as training context rather than a promise.",
        ),
        "/tools/common-barbell-weights.html": (
            "Memorize the common numbers, calculate the rest.",
            "Most gyms revolve around familiar plate combinations. RackMath makes those obvious and helps when the load is less familiar, your bar is different, or your plates are limited.",
        ),
        "/tools/lb-kg-plate-converter.html": (
            "Convert the number, then load a practical bar.",
            "Exact conversions are useful, but gyms run on available plates. Round to the nearest practical jump, then use RackMath when you need exact plate loading.",
        ),
        "/tools/rpe-calculator.html": (
            "Turn effort into a load target.",
            "RPE works best when it supports training decisions instead of replacing judgment. Use the result as a starting target, then adjust based on bar speed and how consistent your reps feel.",
        ),
        "/tools/training-volume-calculator.html": (
            "Know the workload behind the session.",
            "Volume is not the whole story, but it is a useful signal. RackMath makes it easier to connect sets, reps, weight, and weekly training history.",
        ),
        "/tools/powerlifting-attempt-calculator.html": (
            "Plan attempts around makes, not hopes.",
            "A good attempt plan starts with a confident opener, builds the total on the second, and leaves room for a third attempt if the day is there.",
        ),
        "/tools/ai-workout-builder.html": (
            "Start from intent, then personalize in the app.",
            "The website can sketch the shape of a workout. RackMath is where the plan becomes saved, editable, trackable, and ready for plate loading.",
        ),
        "/tools/workout-plan-importer.html": (
            "Turn written programming into something you can run.",
            "Pasted plans are useful only when they become actionable. RackMath turns them into workouts with exercises, sets, reps, weights, and tracking.",
        ),
    }
    return copy[page["slug"]]


def render_standard_tool_page(page: dict, registry: dict) -> str:
    prefix = prefix_for(page["slug"])
    key = tool_key(page)
    heading, copy = render_tool_explainer(page)
    related = render_related_links(page, registry, prefix)
    submit_label = "Preview result" if key in {"aiBuilder", "importer"} else "Calculate"
    body = f"""    <main>
      <section class="page-hero seo-hero">
        <p class="eyebrow">{escape(page.get("eyebrow", "Free lifting tool"))}</p>
        <h1>{escape(page["h1"])}</h1>
        <p>{escape(page.get("summary", page["description"]))}</p>
      </section>

      <section class="section tool-workspace" aria-labelledby="tool-panel-heading">
        <form class="tool-panel" data-rm-tool="{key}" aria-label="{escape(page["h1"])}">
          <div>
            <p class="eyebrow">Free tool</p>
            <h2 id="tool-panel-heading">{escape(page["h1"])}</h2>
          </div>
{render_tool_controls(page)}
          <button class="button primary" type="submit">{submit_label}</button>
          <div class="tool-output" data-tool-output aria-live="polite"></div>
        </form>

        <article class="tool-context">
          <p class="eyebrow">RackMath angle</p>
          <h2>{escape(heading)}</h2>
          <p>{escape(copy)}</p>
          <a class="button secondary" href="{app_href(page["appRoute"])}" data-rm-app-link data-rm-event="app_deeplink_clicked">{escape(page["primaryCta"])}</a>
        </article>
      </section>

      <section class="section seo-content-grid">
        <article>
          <p class="eyebrow">Free value</p>
          <h2>Use the page for the generic answer.</h2>
          <p>This tool gives you the quick answer without requiring an account. It is designed for the search moment, when you need a number or a plan before the next set.</p>
        </article>
        <article>
          <p class="eyebrow">App handoff</p>
          <h2>Use RackMath when the result needs to be saved.</h2>
          <p>Open RackMath when you want the result connected to your workout, plate setup, history, PRs, warmups, or program progression.</p>
        </article>
      </section>

      <section class="section related-pages" aria-labelledby="related-heading">
        <div class="section-heading">
          <p class="eyebrow">Related</p>
          <h2 id="related-heading">Keep going with RackMath tools.</h2>
        </div>
        <div class="related-grid">
{related}
        </div>
      </section>

      <section class="final-cta">
        <p class="eyebrow">Want this in your training flow?</p>
        <h2>Open RackMath to save, personalize, and track the result.</h2>
        <div class="hero-actions">
          <a class="button primary" href="{app_href(page["appRoute"])}" data-rm-app-link data-rm-event="app_deeplink_clicked">{escape(page["primaryCta"])}</a>
        </div>
      </section>
    </main>"""
    return page_shell(
        page,
        body,
        extra_script=f'    <script src="{prefix}assets/lifting-tools.js"></script>',
    )


def write_page(page: dict, html_text: str) -> None:
    slug = page["slug"]
    if slug.endswith("/"):
        output = ROOT / slug.strip("/") / "index.html"
    else:
        output = ROOT / slug.lstrip("/")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_text, encoding="utf-8")


def write_sitemap(posts: list[build_blog.Post], registry: dict) -> None:
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    seen: set[str] = set()

    def add(path: str, priority: str, lastmod: str | None = None) -> None:
        if path in seen:
            return
        seen.add(path)
        url = ET.SubElement(urlset, "url")
        ET.SubElement(url, "loc").text = f"{SITE_URL}{path}"
        if lastmod:
            ET.SubElement(url, "lastmod").text = lastmod
        ET.SubElement(url, "priority").text = priority

    for path, priority in BASE_PAGES:
        add(path, priority)

    for page in published_pages(registry):
        add(page["slug"], "0.8" if page["type"] == "tool" else "0.7")

    for post in posts:
        add(post.url_path, "0.6", post.date.isoformat())

    ET.indent(urlset, space="  ")
    ET.ElementTree(urlset).write(ROOT / "sitemap.xml", encoding="utf-8", xml_declaration=True)


def build_blog_pages(posts: list[build_blog.Post]) -> None:
    build_blog.validate_unique_posts(posts)
    build_blog.BLOG_DIR.mkdir(exist_ok=True)
    for generated_page in build_blog.BLOG_DIR.glob("*.html"):
        generated_page.unlink()

    (ROOT / "blog.html").write_text(build_blog.render_blog_index(posts), encoding="utf-8")
    (build_blog.BLOG_DIR / "archive.html").write_text(build_blog.render_archive(posts), encoding="utf-8")
    for post in posts:
        post.output_path.write_text(build_blog.render_post(post), encoding="utf-8")


def main() -> None:
    registry = load_registry()
    posts = build_blog.load_posts()
    build_blog_pages(posts)

    for page in published_pages(registry):
        if page["slug"] == "/tools/":
            write_page(page, render_tools_hub(page, registry))
        elif page["slug"] == "/tools/barbell-plate-calculator.html":
            write_page(page, render_calculator_page(page, registry))
        elif page.get("type") == "tool":
            write_page(page, render_standard_tool_page(page, registry))

    write_sitemap(posts, registry)
    print(
        f"Built {len(posts)} blog post(s), "
        f"{len(published_pages(registry))} published SEO page(s), "
        f"and sitemap.xml at {datetime.now(UTC).isoformat(timespec='seconds')}"
    )


if __name__ == "__main__":
    main()
