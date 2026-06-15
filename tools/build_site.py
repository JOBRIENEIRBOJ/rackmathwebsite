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
    ("/workouts/", "0.9"),
    ("/exercises/", "0.9"),
    ("/programs/", "0.8"),
    ("/for/", "0.8"),
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
    workout_links = [
        ("All workouts", f"{prefix}workouts/"),
        ("3-Day Beginner Full Body", f"{prefix}workouts/3-day-beginner-full-body.html"),
        ("Beginner Barbell Workout", f"{prefix}workouts/beginner-barbell-workout.html"),
        ("5x5 Workout Tracker", f"{prefix}workouts/5x5-workout-tracker.html"),
        ("4-Day Upper Lower", f"{prefix}workouts/4-day-upper-lower.html"),
        ("Push Pull Legs", f"{prefix}workouts/push-pull-legs.html"),
        ("Barbell-Only Plan", f"{prefix}workouts/barbell-only-workout-plan.html"),
        ("Garage Gym Plan", f"{prefix}workouts/garage-gym-workout-plan.html"),
        ("Beginner Powerlifting", f"{prefix}workouts/beginner-powerlifting-program.html"),
        ("Strength and Hypertrophy", f"{prefix}workouts/strength-hypertrophy-program.html"),
        ("2-Day Beginner Strength", f"{prefix}workouts/2-day-beginner-strength-plan.html"),
        ("First Day at the Gym", f"{prefix}workouts/first-day-at-the-gym-workout.html"),
        ("Dumbbell and Barbell", f"{prefix}workouts/dumbbell-barbell-workout.html"),
    ]
    exercise_links = [
        ("All exercises", f"{prefix}exercises/"),
        ("Bench Press", f"{prefix}exercises/bench-press.html"),
        ("Barbell Squat", f"{prefix}exercises/barbell-squat.html"),
        ("Deadlift", f"{prefix}exercises/deadlift.html"),
        ("Overhead Press", f"{prefix}exercises/overhead-press.html"),
        ("Barbell Row", f"{prefix}exercises/barbell-row.html"),
        ("Romanian Deadlift", f"{prefix}exercises/romanian-deadlift.html"),
        ("Front Squat", f"{prefix}exercises/front-squat.html"),
        ("Incline Bench Press", f"{prefix}exercises/incline-bench-press.html"),
        ("Close-Grip Bench Press", f"{prefix}exercises/close-grip-bench-press.html"),
        ("Barbell Hip Thrust", f"{prefix}exercises/barbell-hip-thrust.html"),
        ("Pull-Up", f"{prefix}exercises/pull-up.html"),
        ("Lat Pulldown", f"{prefix}exercises/lat-pulldown.html"),
        ("Dumbbell Bench Press", f"{prefix}exercises/dumbbell-bench-press.html"),
        ("Goblet Squat", f"{prefix}exercises/goblet-squat.html"),
        ("Leg Press", f"{prefix}exercises/leg-press.html"),
        ("Cable Row", f"{prefix}exercises/cable-row.html"),
        ("Dumbbell Row", f"{prefix}exercises/dumbbell-row.html"),
        ("Barbell Curl", f"{prefix}exercises/barbell-curl.html"),
        ("Skull Crusher", f"{prefix}exercises/skull-crusher.html"),
        ("Bulgarian Split Squat", f"{prefix}exercises/bulgarian-split-squat.html"),
    ]
    persona_links = [
        ("All lifter types", f"{prefix}for/"),
        ("Garage Gyms", f"{prefix}for/garage-gyms.html"),
        ("Beginners", f"{prefix}for/beginners.html"),
        ("Powerlifters", f"{prefix}for/powerlifters.html"),
        ("Strength Coaches", f"{prefix}for/strength-coaches.html"),
        ("Personal Trainers", f"{prefix}for/personal-trainers.html"),
        ("Home Gym Lifters", f"{prefix}for/home-gym-lifters.html"),
        ("kg Gyms", f"{prefix}for/kg-gyms.html"),
    ]
    program_links = [
        ("All programs", f"{prefix}programs/"),
        ("3-Day Beginner Barbell", f"{prefix}programs/3-day-beginner-barbell-program.html"),
        ("5x5 Beginner Strength", f"{prefix}programs/5x5-beginner-strength-program.html"),
        ("Garage Gym Strength", f"{prefix}programs/garage-gym-strength-program.html"),
        ("Upper Lower Strength Hypertrophy", f"{prefix}programs/upper-lower-strength-hypertrophy.html"),
    ]
    tools_current = ' aria-current="page"' if current == "tools" else ""
    tools_dropdown = "\n".join(f'          <a href="{href}">{label}</a>' for label, href in tool_links)
    workouts_current = ' aria-current="page"' if current == "workouts" else ""
    workouts_dropdown = "\n".join(f'          <a href="{href}">{label}</a>' for label, href in workout_links)
    exercises_current = ' aria-current="page"' if current == "exercises" else ""
    exercises_dropdown = "\n".join(f'          <a href="{href}">{label}</a>' for label, href in exercise_links)
    persona_current = ' aria-current="page"' if current == "for" else ""
    persona_dropdown = "\n".join(f'          <a href="{href}">{label}</a>' for label, href in persona_links)
    programs_current = ' aria-current="page"' if current == "programs" else ""
    programs_dropdown = "\n".join(f'          <a href="{href}">{label}</a>' for label, href in program_links)
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
        </div>""",
        f"""        <div class="nav-dropdown"{workouts_current}>
          <button class="nav-dropdown-trigger" type="button">Workouts</button>
          <div class="nav-dropdown-menu">
{workouts_dropdown}
          </div>
        </div>""",
        f"""        <div class="nav-dropdown"{exercises_current}>
          <button class="nav-dropdown-trigger" type="button">Exercises</button>
          <div class="nav-dropdown-menu">
{exercises_dropdown}
          </div>
        </div>""",
        f"""        <div class="nav-dropdown"{persona_current}>
          <button class="nav-dropdown-trigger" type="button">For</button>
          <div class="nav-dropdown-menu">
{persona_dropdown}
          </div>
        </div>""",
        f"""        <div class="nav-dropdown"{programs_current}>
          <button class="nav-dropdown-trigger" type="button">Programs</button>
          <div class="nav-dropdown-menu">
{programs_dropdown}
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
        <a href="{prefix}workouts/">Workouts</a>
        <a href="{prefix}exercises/">Exercises</a>
        <a href="{prefix}for/">For</a>
        <a href="{prefix}programs/">Programs</a>
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


def workout_library() -> dict[str, dict]:
    return {
        "/workouts/3-day-beginner-full-body.html": {
            "who": "New lifters who want three simple full-body sessions per week.",
            "schedule": "Monday, Wednesday, Friday or any three non-consecutive days.",
            "days": [
                ("Day 1", [("Goblet Squat or Barbell Squat", "3", "8", "90 sec", "Start light and smooth."), ("Bench Press", "3", "8", "2 min", "Leave 2 reps in reserve."), ("Cable Row", "3", "10", "90 sec", "Control the return."), ("Romanian Deadlift", "2", "10", "90 sec", "Hinge without rushing.")]),
                ("Day 2", [("Deadlift", "2", "5", "2-3 min", "Reset each rep."), ("Overhead Press", "3", "8", "2 min", "Keep ribs down."), ("Lat Pulldown", "3", "10", "90 sec", "Pull elbows down."), ("Split Squat", "3", "8/side", "90 sec", "Use balance support if needed.")]),
                ("Day 3", [("Barbell Squat", "3", "8", "2 min", "Match Monday or add small weight."), ("Incline Dumbbell Press", "3", "10", "90 sec", "Stop before form breaks."), ("Barbell Row", "3", "8", "2 min", "Brace before each rep."), ("Plank", "3", "30 sec", "60 sec", "Keep breathing.")]),
            ],
        },
        "/workouts/beginner-barbell-workout.html": {
            "who": "Beginners ready to learn the main barbell patterns.",
            "schedule": "Three days per week with at least one rest day between sessions.",
            "days": [
                ("Workout A", [("Barbell Squat", "3", "5", "2-3 min", "Add weight only when reps are clean."), ("Bench Press", "3", "5", "2-3 min", "Use a spotter or safeties."), ("Barbell Row", "3", "8", "2 min", "Pull to lower ribs."), ("Lat Pulldown or Assisted Pull-Up", "2", "10", "90 sec", "Extra back volume."), ("Optional Curl", "2", "10", "60 sec", "Keep it easy.")]),
                ("Workout B", [("Deadlift", "3", "5", "2-3 min", "Reset the bar each rep."), ("Overhead Press", "3", "5", "2 min", "Squeeze glutes."), ("Lat Pulldown or Pull-Up", "3", "8", "90 sec", "Use assistance if needed."), ("Farmer Carry", "3", "30 sec", "90 sec", "Walk tall.")]),
            ],
        },
        "/workouts/5x5-workout-tracker.html": {
            "who": "Lifters who want a simple strength template built around sets of five.",
            "schedule": "Alternate A and B three days per week.",
            "days": [
                ("Workout A", [("Barbell Squat", "5", "5", "2-4 min", "Same weight across sets."), ("Bench Press", "5", "5", "2-4 min", "Track every set."), ("Barbell Row", "5", "5", "2-3 min", "Keep torso position consistent.")]),
                ("Workout B", [("Barbell Squat", "5", "5", "2-4 min", "Reduce if recovery lags."), ("Overhead Press", "5", "5", "2-3 min", "Small jumps work best."), ("Deadlift", "1", "5", "3-5 min", "One heavy set after warmups.")]),
            ],
        },
        "/workouts/4-day-upper-lower.html": {
            "who": "Intermediate beginners who can train four days per week.",
            "schedule": "Upper, Lower, rest, Upper, Lower, rest, rest.",
            "days": [
                ("Upper 1", [("Bench Press", "4", "6", "2 min", "Main press."), ("Barbell Row", "4", "8", "2 min", "Main pull."), ("Overhead Press", "3", "8", "90 sec", "Moderate load."), ("Lat Pulldown", "3", "10", "90 sec", "Full range.")]),
                ("Lower 1", [("Barbell Squat", "4", "6", "2-3 min", "Main squat."), ("Romanian Deadlift", "3", "8", "2 min", "Hinge focus."), ("Leg Press", "3", "10", "90 sec", "Controlled reps."), ("Calf Raise", "3", "12", "60 sec", "Optional.")]),
                ("Upper 2", [("Incline Bench Press", "3", "8", "2 min", "Second press."), ("Cable Row", "3", "10", "90 sec", "Squeeze back."), ("Dumbbell Bench Press", "3", "10", "90 sec", "Accessory press."), ("Curl", "2", "12", "60 sec", "Optional.")]),
                ("Lower 2", [("Deadlift", "3", "5", "3 min", "Main pull."), ("Front Squat", "3", "6", "2 min", "Light and upright."), ("Bulgarian Split Squat", "3", "8/side", "90 sec", "Single-leg work."), ("Plank", "3", "45 sec", "60 sec", "Brace.")]),
            ],
        },
        "/workouts/push-pull-legs.html": {
            "who": "Lifters who like organizing training by movement type.",
            "schedule": "Three to six days per week depending on recovery.",
            "days": [
                ("Push", [("Bench Press", "4", "6", "2 min", "Main press."), ("Overhead Press", "3", "8", "2 min", "Second press."), ("Incline Dumbbell Press", "3", "10", "90 sec", "Accessory."), ("Skull Crusher", "2", "12", "60 sec", "Triceps.")]),
                ("Pull", [("Deadlift or Romanian Deadlift", "3", "5-8", "2-3 min", "Choose one hinge."), ("Barbell Row", "4", "8", "2 min", "Main row."), ("Lat Pulldown", "3", "10", "90 sec", "Vertical pull."), ("Barbell Curl", "2", "12", "60 sec", "Biceps.")]),
                ("Legs", [("Barbell Squat", "4", "6", "2-3 min", "Main squat."), ("Leg Press", "3", "10", "90 sec", "Volume."), ("Bulgarian Split Squat", "3", "8/side", "90 sec", "Single-leg."), ("Calf Raise", "3", "12", "60 sec", "Optional.")]),
            ],
        },
        "/workouts/barbell-only-workout-plan.html": {
            "who": "Lifters with a barbell, plates, rack, and bench.",
            "schedule": "Three days per week.",
            "days": [
                ("Day 1", [("Back Squat", "4", "5", "2-3 min", "Main lift."), ("Bench Press", "4", "5", "2-3 min", "Main press."), ("Barbell Row", "4", "8", "2 min", "Pulling volume.")]),
                ("Day 2", [("Deadlift", "3", "5", "3 min", "Main pull."), ("Overhead Press", "4", "5", "2 min", "Main press."), ("Front Squat", "3", "6", "2 min", "Light squat."), ("Pendlay Row", "3", "8", "2 min", "Back volume without machines.")]),
                ("Day 3", [("Back Squat", "3", "8", "2 min", "Volume."), ("Close-Grip Bench Press", "3", "8", "2 min", "Accessory press."), ("Romanian Deadlift", "3", "8", "2 min", "Hinge volume.")]),
            ],
        },
        "/workouts/garage-gym-workout-plan.html": {
            "who": "Home and garage gym lifters with limited plates or equipment.",
            "schedule": "Three days per week with flexible exercise swaps.",
            "days": [
                ("Workout A", [("Barbell Squat", "3", "6", "2-3 min", "Use available jumps."), ("Bench Press", "3", "6", "2-3 min", "Use safeties."), ("Barbell Row", "3", "10", "2 min", "No machines needed."), ("Loaded Carry", "3", "30 sec", "90 sec", "Use dumbbells if available.")]),
                ("Workout B", [("Deadlift", "3", "5", "3 min", "Plate inventory matters."), ("Overhead Press", "3", "6", "2 min", "Small jumps help."), ("Romanian Deadlift", "3", "8", "2 min", "Back-off hinge."), ("Push-Up", "3", "AMRAP", "90 sec", "Stop short of failure.")]),
            ],
        },
        "/workouts/beginner-powerlifting-program.html": {
            "who": "Beginners who want to focus on squat, bench press, and deadlift.",
            "schedule": "Three days per week.",
            "days": [
                ("Squat Focus", [("Barbell Squat", "4", "5", "3 min", "Main lift."), ("Bench Press", "3", "6", "2 min", "Secondary."), ("Romanian Deadlift", "3", "8", "2 min", "Posterior chain."), ("Plank", "3", "45 sec", "60 sec", "Brace.")]),
                ("Bench Focus", [("Bench Press", "4", "5", "3 min", "Main lift."), ("Barbell Row", "4", "8", "2 min", "Upper back."), ("Close-Grip Bench Press", "3", "8", "2 min", "Triceps."), ("Lat Pulldown", "3", "10", "90 sec", "Back volume.")]),
                ("Deadlift Focus", [("Deadlift", "4", "3", "3-5 min", "Main lift."), ("Front Squat", "3", "6", "2 min", "Squat variation."), ("Overhead Press", "3", "6", "2 min", "Pressing."), ("Barbell Curl", "2", "12", "60 sec", "Optional.")]),
            ],
        },
        "/workouts/strength-hypertrophy-program.html": {
            "who": "Lifters who want heavy work and enough volume to build muscle.",
            "schedule": "Four days per week.",
            "days": [
                ("Upper Strength", [("Bench Press", "4", "4", "3 min", "Heavy press."), ("Barbell Row", "4", "6", "2 min", "Heavy pull."), ("Overhead Press", "3", "6", "2 min", "Secondary."), ("Pull-Up", "3", "AMRAP", "2 min", "Back.")]),
                ("Lower Strength", [("Barbell Squat", "4", "4", "3 min", "Heavy squat."), ("Deadlift", "3", "3", "3 min", "Heavy pull."), ("Leg Press", "3", "8", "2 min", "Volume."), ("Plank", "3", "60 sec", "60 sec", "Core.")]),
                ("Upper Hypertrophy", [("Incline Bench Press", "3", "10", "90 sec", "Chest."), ("Cable Row", "3", "12", "90 sec", "Back."), ("Dumbbell Bench Press", "3", "10", "90 sec", "Press."), ("Curl", "3", "12", "60 sec", "Arms.")]),
                ("Lower Hypertrophy", [("Front Squat", "3", "8", "2 min", "Quads."), ("Romanian Deadlift", "3", "10", "2 min", "Hamstrings."), ("Bulgarian Split Squat", "3", "10/side", "90 sec", "Single-leg."), ("Calf Raise", "3", "15", "60 sec", "Optional.")]),
            ],
        },
        "/workouts/2-day-beginner-strength-plan.html": {
            "who": "Busy beginners who can train twice per week.",
            "schedule": "Two non-consecutive days per week.",
            "days": [
                ("Day 1", [("Barbell Squat", "3", "5", "2-3 min", "Main lift."), ("Bench Press", "3", "5", "2-3 min", "Press."), ("Barbell Row", "3", "8", "2 min", "Pull."), ("Romanian Deadlift", "2", "8", "2 min", "Hinge volume."), ("Plank", "2", "30 sec", "60 sec", "Core.")]),
                ("Day 2", [("Deadlift", "2", "5", "3 min", "Main lift."), ("Overhead Press", "3", "5", "2 min", "Press."), ("Lat Pulldown", "3", "10", "90 sec", "Pull."), ("Split Squat", "3", "8/side", "90 sec", "Legs."), ("Dumbbell Bench Press", "2", "10", "90 sec", "Extra pressing volume.")]),
            ],
        },
        "/workouts/first-day-at-the-gym-workout.html": {
            "who": "New lifters who want a low-pressure first session.",
            "schedule": "One first-day session, then repeat or move to a beginner plan.",
            "days": [
                ("First Day", [("Treadmill Walk", "1", "8 min", "-", "Warm up and look around."), ("Goblet Squat", "2", "8", "90 sec", "Light practice."), ("Machine Chest Press", "2", "10", "90 sec", "Controlled reps."), ("Seated Cable Row", "2", "10", "90 sec", "Easy pull."), ("Romanian Deadlift", "2", "8", "90 sec", "Light hinge.")]),
            ],
        },
        "/workouts/dumbbell-barbell-workout.html": {
            "who": "Lifters who want barbell main lifts plus dumbbell accessories.",
            "schedule": "Three days per week.",
            "days": [
                ("Day 1", [("Barbell Squat", "3", "6", "2-3 min", "Main lift."), ("Dumbbell Bench Press", "3", "10", "90 sec", "Accessory press."), ("Dumbbell Row", "3", "10/side", "90 sec", "Back."), ("Goblet Squat", "2", "12", "90 sec", "Volume.")]),
                ("Day 2", [("Deadlift", "3", "5", "3 min", "Main pull."), ("Overhead Press", "3", "6", "2 min", "Press."), ("Dumbbell Romanian Deadlift", "3", "10", "90 sec", "Hinge."), ("Curl", "2", "12", "60 sec", "Optional.")]),
                ("Day 3", [("Bench Press", "3", "6", "2-3 min", "Main press."), ("Front Squat", "3", "6", "2 min", "Squat variation."), ("Lat Pulldown", "3", "10", "90 sec", "Pull."), ("Bulgarian Split Squat", "2", "8/side", "90 sec", "Single-leg.")]),
            ],
        },
    }


def render_workout_table(days: list[tuple[str, list[tuple[str, str, str, str, str]]]]) -> str:
    sections = []
    for day_name, exercises in days:
        rows = "\n".join(
            f"              <tr><td>{escape(exercise)}</td><td>{sets}</td><td>{reps}</td><td>{rest}</td><td>{escape(notes)}</td></tr>"
            for exercise, sets, reps, rest, notes in exercises
        )
        sections.append(
            f"""        <article class="workout-day">
          <h3>{escape(day_name)}</h3>
          <div class="responsive-table">
            <table>
              <thead><tr><th>Exercise</th><th>Sets</th><th>Reps</th><th>Rest</th><th>Notes</th></tr></thead>
              <tbody>
{rows}
              </tbody>
            </table>
          </div>
        </article>"""
        )
    return "\n".join(sections)


def render_training_evidence_section() -> str:
    return """      <section class="section evidence-section" aria-labelledby="evidence-heading">
        <div class="section-heading">
          <p class="eyebrow">Evidence basis</p>
          <h2 id="evidence-heading">How these workout templates choose volume and effort.</h2>
          <p>These templates use conservative weekly volume targets so the plan is useful without pretending every lifter needs maximal volume on day one.</p>
        </div>
        <div class="evidence-grid">
          <article>
            <h3>Weekly sets</h3>
            <p>For muscle growth, most templates aim the main trained muscles toward the lower-to-middle end of a practical hypertrophy range first, then let lifters add volume only when recovery and performance are good.</p>
          </article>
          <article>
            <h3>Hard-set effort</h3>
            <p>Most work sets should feel challenging but repeatable, roughly RPE 7-9. Failure is RPE 10 and should be used sparingly, not as the default for every exercise.</p>
          </article>
          <article>
            <h3>Strength work</h3>
            <p>Strength-focused lifts use heavier, more specific work with longer rest. The goal is clean practice under meaningful load, not turning every session into a max test.</p>
          </article>
          <article>
            <h3>Recovery adjustment</h3>
            <p>If joints, soreness, sleep, motivation, or performance trend down, reduce weekly volume before adding more sets. Moderate recovery issues may justify a 10-20% reduction; poor recovery may need 20-30%.</p>
          </article>
        </div>
        <div class="responsive-table evidence-table">
          <table>
            <thead><tr><th>Training level</th><th>Default weekly hard sets per muscle</th><th>How to use it</th></tr></thead>
            <tbody>
              <tr><td>Beginner</td><td>6-10</td><td>Learn technique and recover well before adding sets.</td></tr>
              <tr><td>Intermediate</td><td>10-16</td><td>Add sets only when performance is stable.</td></tr>
              <tr><td>Advanced</td><td>12-20+</td><td>Use higher volumes selectively for muscles that recover well.</td></tr>
            </tbody>
          </table>
        </div>
        <p class="evidence-note">Sources: <a href="https://acsm.org/resistance-training-guidelines-update-2026/">ACSM updated resistance training guidance</a>, <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC8884877/">Baz-Valle et al. 2022 systematic review on resistance training volume and hypertrophy</a>, and <a href="https://pubmed.ncbi.nlm.nih.gov/28755103/">Ralston et al. 2017 meta-analysis on weekly set volume and strength gain</a>. These pages are general fitness education, not medical advice.</p>
      </section>"""


def workout_volume_profiles() -> dict[str, list[tuple[str, str, str]]]:
    beginner = [
        ("Chest / pressing", "6-9 hard sets", "Lower-to-middle beginner hypertrophy range."),
        ("Back / pulling", "6-10 hard sets", "At least as much pulling as pressing."),
        ("Quads", "6-10 hard sets", "Enough practice without excessive soreness."),
        ("Hamstrings / glutes", "4-8 hard sets", "Conservative hinge volume for recovery."),
        ("Core / arms", "2-6 direct sets", "Optional support work, not the main driver."),
    ]
    strength = [
        ("Competition/main lifts", "6-12 specific sets", "Frequent practice with submaximal effort."),
        ("Back / pulling", "8-14 hard sets", "Supports pressing and barbell positions."),
        ("Quads", "8-14 hard sets", "Enough squat exposure for strength and size."),
        ("Hamstrings / glutes", "6-10 hard sets", "Deadlift and hinge work without burying recovery."),
        ("Accessories", "4-10 direct sets", "Added only where recovery allows."),
    ]
    intermediate = [
        ("Chest / pressing", "10-14 hard sets", "Middle of the intermediate growth range."),
        ("Back / pulling", "12-16 hard sets", "Higher target because back tolerates volume well."),
        ("Quads", "10-14 hard sets", "Split across multiple sessions."),
        ("Hamstrings / glutes", "8-12 hard sets", "Hinge plus squat-pattern overlap."),
        ("Arms / delts / core", "4-10 direct sets", "Kept moderate to protect recovery."),
    ]
    first_day = [
        ("Whole body", "8-10 total practice sets", "This is an orientation session, not a full hypertrophy week."),
        ("Effort", "RPE 5-7", "Stop well before failure while learning equipment."),
        ("Progression", "Repeat or move to a beginner plan", "Build weekly volume after the first session feels familiar."),
    ]
    return {
        "/workouts/3-day-beginner-full-body.html": beginner,
        "/workouts/beginner-barbell-workout.html": beginner,
        "/workouts/5x5-workout-tracker.html": strength,
        "/workouts/4-day-upper-lower.html": intermediate,
        "/workouts/push-pull-legs.html": intermediate,
        "/workouts/barbell-only-workout-plan.html": beginner,
        "/workouts/garage-gym-workout-plan.html": beginner,
        "/workouts/beginner-powerlifting-program.html": strength,
        "/workouts/strength-hypertrophy-program.html": intermediate,
        "/workouts/2-day-beginner-strength-plan.html": beginner,
        "/workouts/first-day-at-the-gym-workout.html": first_day,
        "/workouts/dumbbell-barbell-workout.html": beginner,
    }


def render_workout_volume_section(page: dict) -> str:
    rows = "\n".join(
        f"              <tr><td>{escape(area)}</td><td>{escape(target)}</td><td>{escape(reason)}</td></tr>"
        for area, target, reason in workout_volume_profiles()[page["slug"]]
    )
    return f"""      <section class="section workout-volume-section" aria-labelledby="volume-target-heading">
        <div class="section-heading">
          <p class="eyebrow">Volume target</p>
          <h2 id="volume-target-heading">Why this plan fits the set-volume guidance.</h2>
          <p>The weekly targets below keep the plan inside the practical ranges from the evidence section: enough hard sets to grow or build strength, but not so much that recovery becomes the limiting factor.</p>
        </div>
        <div class="responsive-table">
          <table>
            <thead><tr><th>Area</th><th>Target in this template</th><th>Why</th></tr></thead>
            <tbody>
{rows}
            </tbody>
          </table>
        </div>
      </section>"""


def render_workouts_hub(page: dict, registry: dict) -> str:
    prefix = prefix_for(page["slug"])
    workouts = [item for item in registry["pages"] if item.get("section") == "workouts" and item.get("type") == "workout"]
    cards = "\n".join(
        f"""          <a class="tool-card" href="{prefix + item["slug"].lstrip("/")}">
            <span class="tool-card-kicker">{escape(item.get("eyebrow", "Workout template"))}</span>
            <h2>{escape(item["h1"])}</h2>
            <p>{escape(item["description"])}</p>
            <span class="tool-card-action">Open workout</span>
          </a>"""
        for item in workouts
    )
    body = f"""    <main>
      <section class="page-hero seo-hero">
        <p class="eyebrow">{escape(page["eyebrow"])}</p>
        <h1>{escape(page["h1"])}</h1>
        <p>{escape(page["summary"])}</p>
        <div class="hero-actions">
          <a class="button primary" href="{app_href(page["appRoute"])}" data-rm-app-link data-rm-event="app_deeplink_clicked">{escape(page["primaryCta"])}</a>
          <a class="button secondary" href="{prefix}tools/barbell-plate-calculator.html">Try plate calculator</a>
        </div>
      </section>

      <section class="section tool-grid" aria-label="RackMath workout templates">
{cards}
      </section>
    </main>"""
    return page_shell(page, body, current="workouts")


def render_workout_page(page: dict, registry: dict) -> str:
    prefix = prefix_for(page["slug"])
    data = workout_library()[page["slug"]]
    related = render_related_links(page, registry, prefix)
    body = f"""    <main>
      <section class="page-hero seo-hero">
        <p class="eyebrow">{escape(page.get("eyebrow", "Workout template"))}</p>
        <h1>{escape(page["h1"])}</h1>
        <p>{escape(page.get("summary", page["description"]))}</p>
        <div class="hero-actions">
          <a class="button primary" href="{app_href(page["appRoute"])}" data-rm-app-link data-rm-event="template_started">{escape(page["primaryCta"])}</a>
          <a class="button secondary" href="{prefix}tools/barbell-plate-calculator.html">Calculate plates</a>
        </div>
      </section>

      <section class="section workout-overview">
        <article>
          <p class="eyebrow">Who it is for</p>
          <h2>{escape(data["who"])}</h2>
        </article>
        <article>
          <p class="eyebrow">Weekly schedule</p>
          <h2>{escape(data["schedule"])}</h2>
        </article>
      </section>

      <section class="section workout-plan" aria-labelledby="workout-table-heading">
        <div class="section-heading">
          <p class="eyebrow">Workout table</p>
          <h2 id="workout-table-heading">The complete plan.</h2>
        </div>
{render_workout_table(data["days"])}
      </section>

{render_workout_volume_section(page)}

      <section class="section workout-guidance-grid">
        <article>
          <p class="eyebrow">Starting weights</p>
          <h2>Start lighter than you think.</h2>
          <p>Choose weights you can complete with clean reps and about two reps left in reserve. If the movement is new, use the empty bar, dumbbells, or a machine variation first.</p>
        </article>
        <article>
          <p class="eyebrow">Progression</p>
          <h2>Add weight after clean sessions.</h2>
          <p>When all prescribed sets and reps feel controlled, add the smallest practical jump next time. If form breaks, repeat the load or reduce it slightly.</p>
        </article>
        <article>
          <p class="eyebrow">Warmups</p>
          <h2>Ramp up before the work sets.</h2>
          <p>Use a few lighter sets before the first heavy barbell lift of the day. The warmup calculator can turn your working weight into practical jumps.</p>
        </article>
        <article>
          <p class="eyebrow">Substitutions</p>
          <h2>Swap by movement pattern.</h2>
          <p>Keep the same pattern when you substitute: squat for squat, press for press, row for row, hinge for hinge. Track the swap so the next session still makes sense.</p>
        </article>
      </section>

      <section class="section seo-content-grid">
        <article>
          <p class="eyebrow">Common mistakes</p>
          <h2>Do not turn week one into a max test.</h2>
          <p>The goal is repeatable training. Avoid adding weight too quickly, skipping warmups, changing every exercise at once, or taking every set to failure.</p>
        </article>
        <article>
          <p class="eyebrow">RackMath handoff</p>
          <h2>The page gives the plan. The app runs it.</h2>
          <p>Open this workout in RackMath when you want saved exercises, exact plates, timers, history, and progression ready before the next set.</p>
        </article>
      </section>

{render_training_evidence_section()}

      <section class="section related-pages" aria-labelledby="related-heading">
        <div class="section-heading">
          <p class="eyebrow">Related</p>
          <h2 id="related-heading">Tools that pair with this plan.</h2>
        </div>
        <div class="related-grid">
{related}
        </div>
      </section>

      <section class="final-cta">
        <p class="eyebrow">Ready to run it?</p>
        <h2>Start this workout in RackMath with weights, plates, timers, and history.</h2>
        <div class="hero-actions">
          <a class="button primary" href="{app_href(page["appRoute"])}" data-rm-app-link data-rm-event="template_started">{escape(page["primaryCta"])}</a>
        </div>
      </section>
    </main>"""
    return page_shell(page, body, current="workouts")


def exercise_library() -> dict[str, dict]:
    barbell_examples = [
        ("95 lb", "25 per side"),
        ("135 lb", "45 per side"),
        ("185 lb", "45 + 25 per side"),
        ("225 lb", "45 + 45 per side"),
    ]
    data = {
        "/exercises/bench-press.html": ("Chest, triceps, front delts", "Barbell, bench, rack", "Horizontal press", "Beginner to intermediate", barbell_examples),
        "/exercises/barbell-squat.html": ("Quads, glutes, adductors, trunk", "Barbell, rack", "Squat", "Beginner to intermediate", barbell_examples),
        "/exercises/deadlift.html": ("Glutes, hamstrings, back, grip", "Barbell, plates", "Hinge", "Intermediate", barbell_examples),
        "/exercises/overhead-press.html": ("Shoulders, triceps, upper back", "Barbell, rack", "Vertical press", "Beginner to intermediate", [("45 lb", "empty bar"), ("65 lb", "10 per side"), ("95 lb", "25 per side"), ("135 lb", "45 per side")]),
        "/exercises/barbell-row.html": ("Lats, upper back, rear delts, biceps", "Barbell, plates", "Horizontal pull", "Beginner to intermediate", barbell_examples),
        "/exercises/romanian-deadlift.html": ("Hamstrings, glutes, back", "Barbell, plates", "Hinge", "Beginner to intermediate", barbell_examples),
        "/exercises/front-squat.html": ("Quads, upper back, trunk", "Barbell, rack", "Squat", "Intermediate", barbell_examples),
        "/exercises/incline-bench-press.html": ("Upper chest, triceps, front delts", "Barbell, incline bench, rack", "Incline press", "Beginner to intermediate", barbell_examples),
        "/exercises/close-grip-bench-press.html": ("Triceps, chest, front delts", "Barbell, bench, rack", "Horizontal press", "Intermediate", barbell_examples),
        "/exercises/barbell-hip-thrust.html": ("Glutes, hamstrings", "Barbell, bench or pad", "Hip extension", "Beginner to intermediate", barbell_examples),
        "/exercises/pull-up.html": ("Lats, upper back, biceps", "Pull-up bar", "Vertical pull", "Beginner to advanced", []),
        "/exercises/lat-pulldown.html": ("Lats, upper back, biceps", "Cable pulldown", "Vertical pull", "Beginner", []),
        "/exercises/dumbbell-bench-press.html": ("Chest, triceps, front delts", "Dumbbells, bench", "Horizontal press", "Beginner", []),
        "/exercises/goblet-squat.html": ("Quads, glutes, trunk", "Dumbbell or kettlebell", "Squat", "Beginner", []),
        "/exercises/leg-press.html": ("Quads, glutes, adductors", "Leg press machine", "Squat pattern", "Beginner", []),
        "/exercises/cable-row.html": ("Lats, upper back, rear delts, biceps", "Cable row", "Horizontal pull", "Beginner", []),
        "/exercises/dumbbell-row.html": ("Lats, upper back, rear delts, biceps", "Dumbbell, bench", "Horizontal pull", "Beginner", []),
        "/exercises/barbell-curl.html": ("Biceps, forearms", "Barbell or EZ bar", "Elbow flexion", "Beginner", [("45 lb", "empty bar"), ("65 lb", "10 per side"), ("75 lb", "15 per side"), ("95 lb", "25 per side")]),
        "/exercises/skull-crusher.html": ("Triceps", "EZ bar or dumbbells, bench", "Elbow extension", "Intermediate", []),
        "/exercises/bulgarian-split-squat.html": ("Quads, glutes, adductors", "Dumbbells or bodyweight, bench", "Single-leg squat", "Intermediate", []),
    }
    return {
        slug: {
            "muscles": muscles,
            "equipment": equipment,
            "pattern": pattern,
            "difficulty": difficulty,
            "plate_examples": examples,
        }
        for slug, (muscles, equipment, pattern, difficulty, examples) in data.items()
    }


def exercise_cue_library() -> dict[str, dict]:
    return {
        "/exercises/bench-press.html": {
            "grip": "Use a grip that lets forearms stack close to vertical at the bottom. Wrap the thumb and squeeze the bar.",
            "feet": "Plant feet firmly and keep them quiet. Use leg drive without letting hips leave the bench.",
            "back_chest": "Set shoulder blades back and down, keep upper back tight, and lift the chest toward the bar.",
            "rom": "Lower to a consistent touch point on the lower-to-mid chest, then press until elbows are locked without shrugging.",
            "speed": "Use a controlled lower and a strong press. Pause or slow the bottom if the bar bounces.",
            "elbows_knees": "Keep elbows roughly 45-75 degrees from the torso rather than aggressively tucked or fully flared.",
            "mistakes": ["Bouncing off the chest", "Losing upper-back tightness", "Wrists bending far back", "Hips lifting off the bench"],
            "refs": ["general", "rom", "tempo", "bench"],
        },
        "/exercises/barbell-squat.html": {
            "grip": "Grip the bar evenly and pull it into the upper back so the torso feels braced before unracking.",
            "feet": "Use a stance around shoulder width with toes slightly out. Keep the whole foot rooted through the rep.",
            "back_chest": "Brace the trunk, keep the chest proud, and let the torso angle match your squat style without collapsing.",
            "rom": "Descend as low as you can control while keeping balance and foot pressure. Aim for at least thighs near parallel when mobility allows.",
            "speed": "Lower under control, keep tension in the bottom, and stand up with steady pressure through the floor.",
            "elbows_knees": "Track knees in the same direction as toes. Do not let them cave inward as fatigue rises.",
            "mistakes": ["Knees collapsing inward", "Heels lifting", "Relaxing at the bottom", "Good-morning the bar out of the hole"],
            "refs": ["general", "rom", "tempo", "squat"],
        },
        "/exercises/deadlift.html": {
            "grip": "Grip just outside the legs with arms straight. Pull slack out of the bar before it leaves the floor.",
            "feet": "Set feet around hip width with the bar over midfoot. Push the floor away instead of yanking with the arms.",
            "back_chest": "Brace hard, keep lats tight, and hold a consistent trunk position as the bar passes the knees.",
            "rom": "Start from the floor or blocks, stand tall with hips and knees extended, then return the bar with control.",
            "speed": "Create tension before the pull, then accelerate smoothly. Reset between reps if position drifts.",
            "elbows_knees": "Keep elbows straight and knees tracking over the feet. Do not hitch or rebend knees at lockout.",
            "mistakes": ["Jerking the bar from a loose setup", "Letting the bar drift forward", "Bending the elbows", "Overextending the low back at lockout"],
            "refs": ["general", "tempo", "hinge"],
        },
        "/exercises/overhead-press.html": {
            "grip": "Grip just outside shoulder width with wrists stacked over elbows as much as possible.",
            "feet": "Stand with feet about hip width and squeeze glutes so the torso does not lean back excessively.",
            "back_chest": "Brace ribs down, keep chest tall, and move the head slightly back so the bar can travel close.",
            "rom": "Start near the upper chest or shoulders and press overhead until elbows are locked and biceps are near the ears.",
            "speed": "Use a controlled start and a strong finish. Avoid turning every rep into a push press unless programmed.",
            "elbows_knees": "Point elbows slightly forward at the start. Keep knees locked for a strict press.",
            "mistakes": ["Leaning back to finish reps", "Pressing around the face in a long arc", "Losing rib position", "Letting wrists fold back"],
            "refs": ["general", "rom", "tempo"],
        },
        "/exercises/barbell-row.html": {
            "grip": "Use a grip just outside the legs or around bench-press width, depending on comfort and target.",
            "feet": "Stand around hip width and keep weight balanced over midfoot.",
            "back_chest": "Hinge until the torso is inclined, brace, and keep the chest open without cranking the neck up.",
            "rom": "Pull the bar toward the lower ribs or upper abdomen, then lower until arms are long without losing position.",
            "speed": "Pull crisply, pause briefly if needed, and lower under control instead of dropping the bar.",
            "elbows_knees": "Drive elbows back toward the hips. Keep knees softly bent and stable.",
            "mistakes": ["Standing up as the set gets hard", "Using a big torso swing", "Shrugging every rep", "Letting the low back relax"],
            "refs": ["general", "rom", "tempo", "hinge"],
        },
        "/exercises/romanian-deadlift.html": {
            "grip": "Grip just outside the thighs and keep arms long like straps connecting you to the bar.",
            "feet": "Use hip-width feet and keep pressure through midfoot and heel.",
            "back_chest": "Brace, keep lats tight, and maintain a consistent trunk position while hips move back.",
            "rom": "Lower until hamstrings limit the hinge or the back position would change, then stand by driving hips forward.",
            "speed": "Use a slow, controlled lower and a smooth return. This lift should not bounce off the bottom.",
            "elbows_knees": "Keep elbows straight and knees slightly bent but not turning the lift into a squat.",
            "mistakes": ["Reaching for the floor at the expense of back position", "Too much knee bend", "Letting the bar drift away", "Rushing the eccentric"],
            "refs": ["general", "rom", "tempo", "hinge"],
        },
        "/exercises/front-squat.html": {
            "grip": "Use a clean grip or cross-arm grip that lets the bar sit on the front delts, not in the hands.",
            "feet": "Use a squat stance with the whole foot planted and toes slightly out.",
            "back_chest": "Keep elbows high, chest tall, and torso braced so the bar does not roll forward.",
            "rom": "Squat as deep as you can control while keeping elbows high and heels down.",
            "speed": "Descend under control, stay tight in the bottom, and drive up without letting the chest dump forward.",
            "elbows_knees": "Elbows stay high; knees track with toes rather than caving inward.",
            "mistakes": ["Dropping elbows", "Holding the bar in the hands", "Heels lifting", "Collapsing forward out of the bottom"],
            "refs": ["general", "rom", "tempo", "squat"],
        },
        "/exercises/incline-bench-press.html": {
            "grip": "Use a secure grip close to your flat bench grip, adjusting until forearms stack well near the bottom.",
            "feet": "Plant feet and keep hips on the bench throughout the set.",
            "back_chest": "Set shoulder blades, keep chest up, and avoid shrugging shoulders toward the ears.",
            "rom": "Lower to the upper chest with control, then press up and slightly back over the shoulders.",
            "speed": "Control the descent and press smoothly. Do not bounce from the upper chest.",
            "elbows_knees": "Let elbows travel under the bar with moderate flare, not pinned to the ribs or straight out sideways.",
            "mistakes": ["Turning it into a flat bench by over-arching", "Touching too low", "Flaring hard at the bottom", "Losing foot pressure"],
            "refs": ["general", "rom", "tempo", "bench"],
        },
        "/exercises/close-grip-bench-press.html": {
            "grip": "Use a narrower-than-normal grip, usually around shoulder width, while keeping wrists comfortable.",
            "feet": "Plant feet firmly and keep the same stable bench setup as a regular bench press.",
            "back_chest": "Keep shoulder blades set and chest lifted so the shoulders stay controlled.",
            "rom": "Lower to the lower chest or sternum area, then press to full elbow extension.",
            "speed": "Use a controlled lower and steady press. Let triceps work without crashing into the bottom.",
            "elbows_knees": "Keep elbows closer to the torso than a standard bench, but do not force them against the ribs.",
            "mistakes": ["Grip too narrow for wrists", "Elbows flaring suddenly", "Losing the touch point", "Shoulders rolling forward"],
            "refs": ["general", "rom", "tempo", "bench"],
        },
        "/exercises/barbell-hip-thrust.html": {
            "grip": "Hold the bar to keep it centered over the hips. Use a pad if pressure distracts from the lift.",
            "feet": "Set feet so shins are close to vertical at the top. Keep the whole foot down.",
            "back_chest": "Upper back rests on the bench, ribs stay down, and pelvis finishes slightly tucked rather than overarched.",
            "rom": "Lower hips under control, then extend until hips are fully open without hyperextending the low back.",
            "speed": "Drive up smoothly, pause briefly at the top, and lower with control.",
            "elbows_knees": "Keep knees tracking over feet instead of collapsing inward or drifting wildly outward.",
            "mistakes": ["Feet too far forward or too tucked", "Overarching the low back", "Not reaching full hip extension", "Letting the bar roll"],
            "refs": ["general", "tempo", "hip_thrust"],
        },
        "/exercises/pull-up.html": {
            "grip": "Use a shoulder-width to slightly wider grip that feels strong and shoulder-friendly.",
            "feet": "Keep legs quiet. Cross feet only if it helps prevent swinging.",
            "back_chest": "Start by setting the shoulders, then pull the chest toward the bar without craning the neck.",
            "rom": "Use a controlled hang at the bottom and pull until chin clears the bar or chest approaches it.",
            "speed": "Pull smoothly and lower with control. Avoid kicking or bouncing unless training a separate dynamic skill.",
            "elbows_knees": "Drive elbows down toward the ribs. Keep knees from swinging forward to create momentum.",
            "mistakes": ["Half reps from the top", "Kipping unintentionally", "Shrugging into the ears", "Losing control of the bottom"],
            "refs": ["general", "rom", "tempo", "pull_up"],
        },
        "/exercises/lat-pulldown.html": {
            "grip": "Use a grip around shoulder width to moderately wide. Choose the grip that lets shoulders move comfortably.",
            "feet": "Plant feet and lock thighs under the pad so the torso stays stable.",
            "back_chest": "Lean back only slightly, keep chest tall, and avoid turning the movement into a row.",
            "rom": "Pull the bar toward the upper chest, then let arms lengthen overhead with control.",
            "speed": "Pull down smoothly, pause briefly near the chest, and control the return.",
            "elbows_knees": "Drive elbows down and slightly back. Keep knees still under the pad.",
            "mistakes": ["Pulling behind the neck", "Leaning far back", "Using momentum", "Stopping short at the top"],
            "refs": ["general", "rom", "tempo", "lat_pulldown"],
        },
        "/exercises/dumbbell-bench-press.html": {
            "grip": "Hold dumbbells with wrists stacked and palms angled slightly if that feels better on shoulders.",
            "feet": "Plant feet and keep hips on the bench.",
            "back_chest": "Set shoulder blades, keep chest up, and keep dumbbells balanced over the forearms.",
            "rom": "Lower until upper arms reach a comfortable depth, then press until arms are extended without clanking weights.",
            "speed": "Lower under control and press smoothly. Keep both dumbbells moving together.",
            "elbows_knees": "Use a moderate elbow angle rather than fully flared or pinned to the ribs.",
            "mistakes": ["Letting dumbbells drift too wide", "Overstretching the bottom", "Pressing unevenly", "Losing shoulder position"],
            "refs": ["general", "rom", "tempo", "bench"],
        },
        "/exercises/goblet-squat.html": {
            "grip": "Hold the dumbbell or kettlebell tight against the chest with elbows pointing down.",
            "feet": "Use a comfortable squat stance with toes slightly out and the whole foot planted.",
            "back_chest": "Stay tall, brace, and keep the weight close so the torso does not fold.",
            "rom": "Squat as deep as you can control, then stand without shifting onto the toes.",
            "speed": "Lower smoothly, pause if needed to own the bottom, and stand with steady pressure.",
            "elbows_knees": "Let elbows travel between the knees. Knees track in line with toes.",
            "mistakes": ["Weight drifting away from chest", "Heels lifting", "Knees caving", "Relaxing at the bottom"],
            "refs": ["general", "rom", "tempo", "squat"],
        },
        "/exercises/leg-press.html": {
            "grip": "Use the handles to keep hips anchored, not to pull the body into a rounded position.",
            "feet": "Place feet where you can use a stable full-foot press. Start around shoulder width and adjust for comfort.",
            "back_chest": "Keep hips and back supported by the pad. Do not let the pelvis tuck hard at the bottom.",
            "rom": "Lower until you reach a controlled depth before the hips roll or heels lift, then press without locking violently.",
            "speed": "Control the lower, pause lightly if needed, and press evenly through both feet.",
            "elbows_knees": "Track knees with toes and avoid letting them cave inward under load.",
            "mistakes": ["Lowering so far the pelvis rolls up", "Locking knees aggressively", "Pressing through toes only", "Uneven foot pressure"],
            "refs": ["general", "rom", "tempo", "squat"],
        },
        "/exercises/cable-row.html": {
            "grip": "Choose a handle that lets wrists stay neutral and shoulders move freely.",
            "feet": "Brace feet on the platform and keep the torso stable.",
            "back_chest": "Sit tall with chest open, then row without turning the movement into a big lean-back.",
            "rom": "Reach forward enough to lengthen the back, then pull handles toward the torso with shoulder blades moving naturally.",
            "speed": "Pull smoothly, pause near the body, and control the cable forward.",
            "elbows_knees": "Drive elbows back without shrugging. Keep knees softly bent and still.",
            "mistakes": ["Excessive torso swing", "Shrugging", "Cutting the reach short", "Curling the handle instead of rowing"],
            "refs": ["general", "rom", "tempo"],
        },
        "/exercises/dumbbell-row.html": {
            "grip": "Hold the dumbbell firmly with wrist neutral.",
            "feet": "Use a split stance or bench support that keeps you balanced.",
            "back_chest": "Brace the torso and keep shoulders square rather than twisting every rep.",
            "rom": "Let the arm reach long at the bottom, then row toward the hip or lower ribs.",
            "speed": "Pull with control and lower slowly enough to feel the back working.",
            "elbows_knees": "Drive the elbow back toward the hip. Keep the support-side knee stable.",
            "mistakes": ["Rotating the torso to cheat", "Shrugging toward the ear", "Using too much momentum", "Shortening the bottom"],
            "refs": ["general", "rom", "tempo", "hinge"],
        },
        "/exercises/barbell-curl.html": {
            "grip": "Use a shoulder-width underhand grip. Keep wrists mostly neutral instead of letting them collapse back.",
            "feet": "Stand balanced with feet around hip width.",
            "back_chest": "Keep chest tall, ribs controlled, and upper arms close to the torso.",
            "rom": "Curl from straight or nearly straight elbows to a strong top contraction without the shoulders taking over.",
            "speed": "Lift smoothly and lower under control. The lowering half should not be a drop.",
            "elbows_knees": "Keep elbows near the sides and knees still. Do not dip the knees to start reps.",
            "mistakes": ["Swinging the hips", "Letting elbows drift far forward", "Cutting the lower half short", "Using wrist extension to finish"],
            "refs": ["general", "rom", "tempo"],
        },
        "/exercises/skull-crusher.html": {
            "grip": "Use an EZ bar or dumbbells with a grip that keeps wrists comfortable.",
            "feet": "Plant feet and keep the body stable on the bench.",
            "back_chest": "Keep shoulder blades set and upper arms angled slightly back if that feels better on elbows.",
            "rom": "Lower toward the forehead or just behind the head, then extend elbows without letting shoulders drift wildly.",
            "speed": "Lower slowly and extend smoothly. Avoid dive-bombing the bottom.",
            "elbows_knees": "Keep elbows relatively narrow and pointed upward; avoid flaring them out hard.",
            "mistakes": ["Elbows flaring wide", "Turning it into a pullover", "Dropping too fast", "Using a grip that irritates wrists"],
            "refs": ["general", "rom", "tempo"],
        },
        "/exercises/bulgarian-split-squat.html": {
            "grip": "Hold dumbbells at the sides or use bodyweight until balance is consistent.",
            "feet": "Set the front foot far enough forward that the heel stays down and balance feels repeatable.",
            "back_chest": "Keep torso braced. A slight forward lean is fine if hips and front foot stay controlled.",
            "rom": "Lower until the front leg reaches a strong, comfortable depth, then drive through the front foot.",
            "speed": "Use a slow descent and controlled rise. Do not bounce off the bottom.",
            "elbows_knees": "Track the front knee with the toes; avoid knee cave or wobbling under fatigue.",
            "mistakes": ["Front foot too close", "Pushing mostly off the back leg", "Knee collapsing inward", "Rushing reps to keep balance"],
            "refs": ["general", "rom", "tempo", "squat"],
        },
    }


def technique_references() -> dict[str, tuple[str, str]]:
    return {
        "general": ("ACSM resistance training guidance", "https://acsm.org/resistance-training-guidelines-update-2026/"),
        "technique": ("Resistance training technique review", "https://pmc.ncbi.nlm.nih.gov/articles/PMC10801605/"),
        "rom": ("Range-of-motion review", "https://pubmed.ncbi.nlm.nih.gov/34170576/"),
        "tempo": ("Movement tempo review", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8310485/"),
        "squat": ("Squat biomechanics review", "https://pmc.ncbi.nlm.nih.gov/articles/PMC10987311/"),
        "bench": ("Bench press variation and grip literature", "https://pmc.ncbi.nlm.nih.gov/articles/PMC5504579/"),
        "hinge": ("Hip hinge and neutral spine study", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8402067/"),
        "pull_up": ("Pull-up scapular kinematics study", "https://pmc.ncbi.nlm.nih.gov/articles/PMC4916995/"),
        "lat_pulldown": ("Lat pulldown grip-width study", "https://pubmed.ncbi.nlm.nih.gov/24662157/"),
        "hip_thrust": ("Barbell hip thrust biomechanics", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8006986/"),
    }


def render_exercise_cues(cues: dict) -> str:
    mistake_items = "\n".join(f"              <li>{escape(item)}</li>" for item in cues["mistakes"])
    fields = [
        ("Grip", cues["grip"]),
        ("Feet", cues["feet"]),
        ("Back and chest", cues["back_chest"]),
        ("Range of motion", cues["rom"]),
        ("Speed", cues["speed"]),
        ("Elbows and knees", cues["elbows_knees"]),
    ]
    rows = "\n".join(
        f"""            <div>
              <dt>{escape(label)}</dt>
              <dd>{escape(copy)}</dd>
            </div>"""
        for label, copy in fields
    )
    return f"""        <div class="exercise-technique-block">
          <h3>Position and movement cues</h3>
          <dl class="exercise-cue-list">
{rows}
          </dl>
        </div>
        <div class="exercise-mistake-block">
          <h3>Common mistakes</h3>
          <ul class="feature-list">
{mistake_items}
          </ul>
        </div>"""


def render_exercise_references(cues: dict) -> str:
    refs = technique_references()
    keys = ["technique", *cues["refs"]]
    seen: set[str] = set()
    links = []
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        label, href = refs[key]
        links.append(f'          <a class="related-card" href="{href}">{escape(label)}</a>')
    return "\n".join(links)


def render_exercises_hub(page: dict, registry: dict) -> str:
    prefix = prefix_for(page["slug"])
    exercises = [item for item in registry["pages"] if item.get("section") == "exercises" and item.get("type") == "exercise"]
    cards = "\n".join(
        f"""          <a class="tool-card" href="{prefix + item["slug"].lstrip("/")}">
            <span class="tool-card-kicker">{escape(item.get("eyebrow", "Exercise guide"))}</span>
            <h2>{escape(item["h1"])}</h2>
            <p>{escape(item["description"])}</p>
            <span class="tool-card-action">Open guide</span>
          </a>"""
        for item in exercises
    )
    body = f"""    <main>
      <section class="page-hero seo-hero">
        <p class="eyebrow">{escape(page["eyebrow"])}</p>
        <h1>{escape(page["h1"])}</h1>
        <p>{escape(page["summary"])}</p>
        <div class="hero-actions">
          <a class="button primary" href="{app_href(page["appRoute"])}" data-rm-app-link data-rm-event="app_deeplink_clicked">{escape(page["primaryCta"])}</a>
          <a class="button secondary" href="{prefix}workouts/3-day-beginner-full-body.html">Browse workouts</a>
        </div>
      </section>

      <section class="section tool-grid" aria-label="RackMath exercise guides">
{cards}
      </section>
    </main>"""
    return page_shell(page, body, current="exercises")


def render_plate_examples(exercise: dict) -> str:
    if not exercise["plate_examples"]:
        return ""
    rows = "\n".join(
        f"              <tr><td>{weight}</td><td>{setup}</td></tr>"
        for weight, setup in exercise["plate_examples"]
    )
    return f"""      <section class="section table-section" aria-labelledby="plate-example-heading">
        <div class="section-heading">
          <p class="eyebrow">Plate examples</p>
          <h2 id="plate-example-heading">Common barbell loading examples.</h2>
          <p>Use these as quick references. For custom plates, collars, kg plates, or specialty bars, use the RackMath plate calculator.</p>
        </div>
        <div class="responsive-table">
          <table>
            <thead><tr><th>Target</th><th>45 lb bar setup</th></tr></thead>
            <tbody>
{rows}
            </tbody>
          </table>
        </div>
      </section>"""


def render_exercise_page(page: dict, registry: dict) -> str:
    prefix = prefix_for(page["slug"])
    exercise = exercise_library()[page["slug"]]
    cues = exercise_cue_library()[page["slug"]]
    related = render_related_links(page, registry, prefix)
    references = render_exercise_references(cues)
    body = f"""    <main>
      <section class="page-hero seo-hero">
        <p class="eyebrow">{escape(page.get("eyebrow", "Exercise guide"))}</p>
        <h1>{escape(page["h1"])}</h1>
        <p>{escape(page.get("summary", page["description"]))}</p>
        <div class="hero-actions">
          <a class="button primary" href="{app_href(page["appRoute"])}" data-rm-app-link data-rm-event="app_deeplink_clicked">{escape(page["primaryCta"])}</a>
          <a class="button secondary" href="{prefix}tools/warmup-set-calculator.html">Plan warmups</a>
        </div>
      </section>

      <section class="section exercise-guide-panel" aria-labelledby="exercise-guide-heading">
        <div class="exercise-guide-header">
          <div>
            <p class="eyebrow">At a glance</p>
            <h2 id="exercise-guide-heading">How to use this lift in training.</h2>
          </div>
          <dl class="exercise-meta-list">
            <div><dt>Muscles</dt><dd>{escape(exercise["muscles"])}</dd></div>
            <div><dt>Equipment</dt><dd>{escape(exercise["equipment"])}</dd></div>
            <div><dt>Pattern</dt><dd>{escape(exercise["pattern"])}</dd></div>
            <div><dt>Difficulty</dt><dd>{escape(exercise["difficulty"])}</dd></div>
          </dl>
        </div>

{render_exercise_cues(cues)}

        <div class="exercise-guide-copy">
          <div>
            <h3>How to practice it</h3>
            <p>Start each set by finding the same setup: stable feet, balanced grip or handles, a braced trunk, and a repeatable start position. Stop the set when the lift no longer looks like the first good rep.</p>
            <p>For a heavy barbell lift, use the empty bar, then a few smaller jumps before your working weight. For dumbbells or machines, use one or two lighter feeler sets.</p>
          </div>
          <div>
            <h3>Loading and progression</h3>
            <p>Use 3-6 reps for strength practice, 6-12 reps for most muscle-building work, and 10-15+ reps for lighter accessories or skill practice.</p>
            <p>Pick a load that feels like RPE 7-8 on the final set. Add weight only when the target reps, range of motion, and positions stay consistent.</p>
          </div>
        </div>

        <div class="exercise-tracking-note">
          <h3>Track it in RackMath</h3>
          <p>RackMath keeps previous weights, reps, RPE, plates, warmups, and PRs connected to the exercise so the next session starts with context.</p>
        </div>
      </section>

{render_plate_examples(exercise)}

      <section class="section related-pages" aria-labelledby="related-heading">
        <div class="section-heading">
          <p class="eyebrow">Related</p>
          <h2 id="related-heading">Use this exercise in a plan.</h2>
        </div>
        <div class="related-grid">
{related}
        </div>
      </section>

      <section class="section related-pages" aria-labelledby="technique-reference-heading">
        <div class="section-heading">
          <p class="eyebrow">Technique references</p>
          <h2 id="technique-reference-heading">Literature used to shape these cues.</h2>
          <p>These cues are general education for healthy lifters. Use pain, injury history, mobility, and coaching feedback to adjust technique when needed.</p>
        </div>
        <div class="related-grid">
{references}
        </div>
      </section>

      <section class="final-cta">
        <p class="eyebrow">Ready to track it?</p>
        <h2>Open RackMath to log sets, load plates, and watch progress over time.</h2>
        <div class="hero-actions">
          <a class="button primary" href="{app_href(page["appRoute"])}" data-rm-app-link data-rm-event="app_deeplink_clicked">{escape(page["primaryCta"])}</a>
        </div>
      </section>
    </main>"""
    return page_shell(page, body, current="exercises")


def feature_library() -> dict[str, dict]:
    return {
        "/features/barbell-plate-calculator.html": {
            "problem": "Plate math interrupts the set when the target, bar, or unit changes.",
            "solution": "RackMath calculates the load per side, shows the exact plate stack, and keeps that answer connected to the workout you are running.",
            "highlights": [
                "Works for pound and kilogram gyms.",
                "Accounts for bar weight before building the plate stack.",
                "Pairs with warmups, saved workouts, and exercise history.",
            ],
            "free_link": "/tools/barbell-plate-calculator.html",
            "free_label": "Try the free calculator",
        },
        "/features/custom-plate-calculator.html": {
            "problem": "Generic calculators assume your gym has a perfect plate inventory.",
            "solution": "RackMath can match your actual plates, bars, collars, and preferred loading choices so the answer fits the equipment in front of you.",
            "highlights": [
                "Useful for garage gyms, kg gyms, specialty bars, and limited plate sets.",
                "Reduces awkward jumps when smaller plates are missing.",
                "Keeps your setup available whenever you open the app.",
            ],
            "free_link": "/tools/lb-kg-plate-converter.html",
            "free_label": "Convert lb and kg loads",
        },
        "/features/warmup-planner.html": {
            "problem": "Warmups are easy to skip, overdo, or improvise poorly.",
            "solution": "RackMath turns a working weight into practical warmup jumps so the first hard set is prepared without wasting energy.",
            "highlights": [
                "Builds jumps from the target working weight.",
                "Keeps warmups lighter than the work that matters.",
                "Pairs naturally with barbell plate loading.",
            ],
            "free_link": "/tools/warmup-set-calculator.html",
            "free_label": "Try the warmup calculator",
        },
        "/features/workout-tracker.html": {
            "problem": "A workout log is only useful if it makes the next set easier to run.",
            "solution": "RackMath keeps sets, reps, weight, RPE, notes, plates, and history together so training context is ready before the next session.",
            "highlights": [
                "Log working sets without losing momentum.",
                "Review previous loads and rep targets quickly.",
                "Connect plate math, warmups, PRs, and progression.",
            ],
            "free_link": "/workouts/3-day-beginner-full-body.html",
            "free_label": "Browse free workouts",
        },
        "/features/ai-workout-builder.html": {
            "problem": "A blank workout plan makes beginners guess and makes experienced lifters repeat setup work.",
            "solution": "RackMath can draft a plan from your goal, schedule, equipment, and experience, then let you edit and track it.",
            "highlights": [
                "Starts from goal and availability instead of a blank page.",
                "Creates a trackable structure, not just loose text.",
                "Works alongside the free evidence-based templates.",
            ],
            "free_link": "/tools/ai-workout-builder.html",
            "free_label": "Preview the AI builder",
        },
        "/features/workout-plan-importer.html": {
            "problem": "Useful plans often live in screenshots, notes, PDFs, spreadsheets, or messages.",
            "solution": "RackMath helps turn outside programming into structured workouts you can run, edit, and track.",
            "highlights": [
                "Bring coach programming into a trackable flow.",
                "Convert written exercises, sets, and reps into workout structure.",
                "Keep imported plans tied to history and progression.",
            ],
            "free_link": "/tools/workout-plan-importer.html",
            "free_label": "Preview the importer",
        },
        "/features/pr-tracker.html": {
            "problem": "A PR number loses meaning if you forget the reps, RPE, body context, or exercise variation.",
            "solution": "RackMath keeps personal records and estimated maxes connected to the exact sets that created them.",
            "highlights": [
                "Track rep PRs and estimated one rep maxes.",
                "See progress without testing true maxes constantly.",
                "Connect PRs to exercises, workouts, and training blocks.",
            ],
            "free_link": "/tools/one-rep-max-calculator.html",
            "free_label": "Estimate a one rep max",
        },
        "/features/program-progress.html": {
            "problem": "Progression breaks when you cannot quickly tell what workout, load, or target comes next.",
            "solution": "RackMath keeps the program moving with saved sessions, repeatable progressions, and context from prior workouts.",
            "highlights": [
                "Know what session comes next.",
                "Repeat, progress, or adjust loads with history visible.",
                "Turn static templates into a recurring training flow.",
            ],
            "free_link": "/workouts/5x5-workout-tracker.html",
            "free_label": "Open a progression template",
        },
    }


def render_feature_page(page: dict, registry: dict) -> str:
    prefix = prefix_for(page["slug"])
    feature = feature_library()[page["slug"]]
    related = render_related_links(page, registry, prefix)
    highlight_items = "\n".join(f"              <li>{escape(item)}</li>" for item in feature["highlights"])
    free_href = f"{prefix}{feature['free_link'].lstrip('/')}"
    body = f"""    <main>
      <section class="page-hero seo-hero">
        <p class="eyebrow">{escape(page.get("eyebrow", "RackMath feature"))}</p>
        <h1>{escape(page["h1"])}</h1>
        <p>{escape(page.get("summary", page["description"]))}</p>
        <div class="hero-actions">
          <a class="button primary" href="{app_href(page["appRoute"])}" data-rm-app-link data-rm-event="app_deeplink_clicked">{escape(page["primaryCta"])}</a>
          <a class="button secondary" href="{free_href}">{escape(feature["free_label"])}</a>
        </div>
      </section>

      <section class="section feature-proof-grid">
        <article>
          <p class="eyebrow">Problem</p>
          <h2>{escape(feature["problem"])}</h2>
        </article>
        <article>
          <p class="eyebrow">RackMath answer</p>
          <h2>{escape(feature["solution"])}</h2>
        </article>
      </section>

      <section class="section seo-content-grid">
        <article>
          <p class="eyebrow">What it helps with</p>
          <h2>Make the useful answer part of the workout.</h2>
          <ul class="feature-list">
{highlight_items}
          </ul>
        </article>
        <article>
          <p class="eyebrow">Why it belongs in the app</p>
          <h2>The website gives the generic value. RackMath saves the recurring workflow.</h2>
          <p>Free pages are best for quick answers. The app is where those answers become saved setups, workout history, progression, and repeatable training decisions.</p>
        </article>
      </section>

      <section class="section workout-guidance-grid">
        <article>
          <p class="eyebrow">Before the set</p>
          <h2>Know what to load or perform.</h2>
          <p>RackMath reduces the tiny decisions that slow down training: bar choice, plate math, warmup jumps, workout order, and target loads.</p>
        </article>
        <article>
          <p class="eyebrow">During the set</p>
          <h2>Keep logging simple.</h2>
          <p>The best tracker is the one that does not pull attention away from lifting. RackMath keeps set entry direct and uses saved context whenever possible.</p>
        </article>
        <article>
          <p class="eyebrow">After the set</p>
          <h2>Turn the result into next time.</h2>
          <p>History, PRs, RPE, and progression matter because they guide the next session. RackMath keeps those signals attached to the work that produced them.</p>
        </article>
        <article>
          <p class="eyebrow">Free value</p>
          <h2>Start on the public page.</h2>
          <p>Use the related free tool or template first. Open RackMath when you want to save, personalize, and repeat it.</p>
        </article>
      </section>

      <section class="section related-pages" aria-labelledby="related-heading">
        <div class="section-heading">
          <p class="eyebrow">Related</p>
          <h2 id="related-heading">Feature pages, tools, and templates that connect.</h2>
        </div>
        <div class="related-grid">
{related}
        </div>
      </section>

      <section class="final-cta">
        <p class="eyebrow">Ready to use it?</p>
        <h2>Open RackMath to save this flow inside your actual training.</h2>
        <div class="hero-actions">
          <a class="button primary" href="{app_href(page["appRoute"])}" data-rm-app-link data-rm-event="app_deeplink_clicked">{escape(page["primaryCta"])}</a>
        </div>
      </section>
    </main>"""
    return page_shell(page, body, current="features")


def persona_library() -> dict[str, dict]:
    return {
        "/for/garage-gyms.html": {
            "problem": "Garage gyms rarely have the perfect commercial-gym plate inventory. You may have one bar, mismatched pairs, limited change plates, or no easy way to make the exact jump a program asks for.",
            "outcome": "RackMath helps you make practical loading decisions from the equipment you actually own, then saves that setup so the next workout starts faster.",
            "quick": [("Main friction", "Limited or uneven plates"), ("Best first tool", "Custom plate setup"), ("Good public start", "Garage gym workout plan")],
            "steps": [
                ("Save the real setup", "Enter the bars, collars, and plates in your garage instead of using a default commercial inventory."),
                ("Load the closest useful weight", "When the exact target is not possible, use the closest loadable option and keep the session moving."),
                ("Keep warmups realistic", "Build warmup jumps around the smallest plates you own so the ramp-up does not waste energy."),
                ("Repeat the session", "Track the workout so next time you know what was loaded, what moved well, and what should progress."),
            ],
        },
        "/for/beginners.html": {
            "problem": "Beginners are usually not short on effort. The hard part is knowing what to do next: which workout to follow, what plates to load, how to warm up, and whether a lift looked good enough to add weight.",
            "outcome": "RackMath reduces the number of decisions in the first months of lifting so beginners can practice consistently and see progress without guessing.",
            "quick": [("Main friction", "Too many decisions"), ("Best first tool", "Beginner workout template"), ("Good public start", "First day at the gym")],
            "steps": [
                ("Pick a simple plan", "Start with a beginner template and repeat it long enough to learn the lifts."),
                ("Learn the setup", "Use the exercise pages for grip, feet, range of motion, speed, and common mistakes."),
                ("Load the bar confidently", "Type the target weight and let RackMath show the plates per side."),
                ("Progress slowly", "Track completed sets and only add weight when reps stay controlled."),
            ],
        },
        "/for/powerlifters.html": {
            "problem": "Powerlifting sessions are simple on paper, but the details matter: exact plates, warmup jumps, top-set history, rep PRs, and attempt decisions all affect the day.",
            "outcome": "RackMath keeps squat, bench, and deadlift work organized so lifters can spend less attention on arithmetic and more attention on execution.",
            "quick": [("Main friction", "Precise SBD loading"), ("Best first tool", "Attempt calculator"), ("Good public start", "Beginner powerlifting program")],
            "steps": [
                ("Plan the top set", "Use recent training numbers to choose realistic targets for squat, bench, and deadlift."),
                ("Build warmups", "Ramp from the empty bar to working weight with jumps that prepare you without stealing energy."),
                ("Track the result", "Log load, reps, RPE, and notes so future attempt decisions have context."),
                ("Review PRs", "Use estimated maxes and rep PRs as signals instead of maxing out every session."),
            ],
        },
        "/for/strength-coaches.html": {
            "problem": "Coaching gets harder when the plan lives in one place and the athlete executes it somewhere else. Plate math, substitutions, and missed context can slow the session down.",
            "outcome": "RackMath helps turn written programming into trackable sessions athletes can run with clearer loads, warmups, and progress context.",
            "quick": [("Main friction", "Plan execution"), ("Best first tool", "Workout importer"), ("Good public start", "Workout plan importer")],
            "steps": [
                ("Import the plan", "Convert written programming into structured workouts with exercises, sets, reps, and targets."),
                ("Reduce loading questions", "Give athletes exact plate setups and warmup guidance before they get to the rack."),
                ("Keep context attached", "Track completed work, notes, and PRs so the next session is easier to adjust."),
                ("Repeat the workflow", "Use saved sessions and progress history to reduce admin work over a training block."),
            ],
        },
        "/for/personal-trainers.html": {
            "problem": "A live training session moves quickly. Trainers need to choose loads, adjust exercises, explain technique, and record progress without letting the phone become the session.",
            "outcome": "RackMath keeps common lifting decisions close at hand so trainers can spend more time coaching and less time calculating or searching.",
            "quick": [("Main friction", "Live-session decisions"), ("Best first tool", "Workout builder"), ("Good public start", "Warmup calculator")],
            "steps": [
                ("Prepare the session", "Build or import a simple workout before the client starts lifting."),
                ("Choose practical loads", "Use plate math and warmup jumps to move quickly between sets."),
                ("Coach the exercise", "Use exercise pages for clear setup cues and common mistakes when a lift needs explanation."),
                ("Save progress", "Track sets, reps, load, and notes so the next appointment starts with context."),
            ],
        },
        "/for/home-gym-lifters.html": {
            "problem": "Home gyms are efficient, but they also force constraints: limited machines, limited plates, one rack, and no coach watching every set.",
            "outcome": "RackMath helps home gym lifters make simple equipment-aware choices and keep training history organized between solo sessions.",
            "quick": [("Main friction", "Limited equipment"), ("Best first tool", "Custom plate calculator"), ("Good public start", "Barbell-only plan")],
            "steps": [
                ("Match the equipment", "Start with workouts that fit a rack, bench, barbell, dumbbells, or the gear you actually have."),
                ("Calculate loadable targets", "When a program asks for a weight you cannot build, choose a practical nearby load."),
                ("Use simple substitutions", "Swap by movement pattern when equipment is missing: squat, hinge, press, row, or pull."),
                ("Keep history visible", "Track work sets so training alone still has direction next time."),
            ],
        },
        "/for/kg-gyms.html": {
            "problem": "Metric gyms should not have to work around pound-based assumptions. Bar weights, plate jumps, and program conversions all need to make sense in kilograms.",
            "outcome": "RackMath supports kg-first plate loading and conversion workflows so metric lifters can train without translating every set by hand.",
            "quick": [("Main friction", "kg loading and conversion"), ("Best first tool", "lb/kg converter"), ("Good public start", "Plate calculator in kg")],
            "steps": [
                ("Switch units", "Set RackMath to kilograms and choose the bar that matches your gym."),
                ("Load metric plates", "Use kg plates directly instead of converting every set back from pounds."),
                ("Convert imported targets", "Translate pound-based programs into practical kg loads when needed."),
                ("Save the setup", "Keep your kg plates and bar defaults ready for future workouts."),
            ],
        },
    }


def render_persona_hub(page: dict, registry: dict) -> str:
    prefix = prefix_for(page["slug"])
    personas = [item for item in registry["pages"] if item.get("section") == "for" and item.get("type") == "persona"]
    cards = "\n".join(
        f"""          <a class="tool-card" href="{prefix + item["slug"].lstrip("/")}">
            <span class="tool-card-kicker">{escape(item.get("eyebrow", "For lifters"))}</span>
            <h2>{escape(item["h1"])}</h2>
            <p>{escape(item["description"])}</p>
            <span class="tool-card-action">Open page</span>
          </a>"""
        for item in personas
    )
    body = f"""    <main>
      <section class="page-hero seo-hero">
        <p class="eyebrow">{escape(page["eyebrow"])}</p>
        <h1>{escape(page["h1"])}</h1>
        <p>{escape(page["summary"])}</p>
        <div class="hero-actions">
          <a class="button primary" href="{app_href(page["appRoute"])}" data-rm-app-link data-rm-event="app_deeplink_clicked">{escape(page["primaryCta"])}</a>
          <a class="button secondary" href="{prefix}tools/barbell-plate-calculator.html">Try plate calculator</a>
        </div>
      </section>

      <section class="section tool-grid" aria-label="RackMath persona pages">
{cards}
      </section>
    </main>"""
    return page_shell(page, body, current="for")


def render_persona_page(page: dict, registry: dict) -> str:
    prefix = prefix_for(page["slug"])
    data = persona_library()[page["slug"]]
    related = render_related_links(page, registry, prefix)
    quick_rows = "\n".join(
        f"""            <div>
              <dt>{escape(label)}</dt>
              <dd>{escape(value)}</dd>
            </div>"""
        for label, value in data["quick"]
    )
    workflow_steps = "\n".join(
        f"""          <li>
            <span>{index}</span>
            <div>
              <h3>{escape(title)}</h3>
              <p>{escape(copy)}</p>
            </div>
          </li>"""
        for index, (title, copy) in enumerate(data["steps"], start=1)
    )
    body = f"""    <main>
      <section class="page-hero seo-hero">
        <p class="eyebrow">{escape(page.get("eyebrow", "For lifters"))}</p>
        <h1>{escape(page["h1"])}</h1>
        <p>{escape(page.get("summary", page["description"]))}</p>
        <div class="hero-actions">
          <a class="button primary" href="{app_href(page["appRoute"])}" data-rm-app-link data-rm-event="app_deeplink_clicked">{escape(page["primaryCta"])}</a>
          <a class="button secondary" href="{prefix}for/">All lifter types</a>
        </div>
      </section>

      <section class="section persona-playbook" aria-labelledby="persona-playbook-heading">
        <article class="persona-main-copy">
          <p class="eyebrow">Use case</p>
          <h2 id="persona-playbook-heading">What RackMath solves here.</h2>
          <p>{escape(data["problem"])}</p>
          <p>{escape(data["outcome"])}</p>
        </article>
        <aside class="persona-facts" aria-label="Quick summary">
          <p class="eyebrow">Quick read</p>
          <dl>
{quick_rows}
          </dl>
        </aside>
      </section>

      <section class="section persona-workflow" aria-labelledby="persona-workflow-heading">
        <div class="section-heading">
          <p class="eyebrow">Workflow</p>
          <h2 id="persona-workflow-heading">How to use RackMath for this.</h2>
        </div>
        <ol>
{workflow_steps}
        </ol>
      </section>

      <section class="section seo-content-grid">
        <article>
          <p class="eyebrow">Free value</p>
          <h2>Start with public tools and templates.</h2>
          <p>Use RackMath pages for plate math, warmups, workouts, exercise guidance, and planning before you ever need to save a workflow.</p>
        </article>
        <article>
          <p class="eyebrow">App handoff</p>
          <h2>Open RackMath when the workflow repeats.</h2>
          <p>The app is where saved setups, workout history, PRs, imports, custom equipment, and progress context become useful session after session.</p>
        </article>
      </section>

      <section class="section related-pages" aria-labelledby="related-heading">
        <div class="section-heading">
          <p class="eyebrow">Related</p>
          <h2 id="related-heading">Tools and pages for this workflow.</h2>
        </div>
        <div class="related-grid">
{related}
        </div>
      </section>

      <section class="final-cta">
        <p class="eyebrow">Ready to make it repeatable?</p>
        <h2>Open RackMath to save the setup, run the workout, and keep progress moving.</h2>
        <div class="hero-actions">
          <a class="button primary" href="{app_href(page["appRoute"])}" data-rm-app-link data-rm-event="app_deeplink_clicked">{escape(page["primaryCta"])}</a>
        </div>
      </section>
    </main>"""
    return page_shell(page, body, current="for")


def program_library() -> dict[str, dict]:
    return {
        "/programs/3-day-beginner-barbell-program.html": {
            "duration": "8 weeks",
            "frequency": "3 days per week",
            "level": "Beginner",
            "progression": "Weeks 1-2 are practice weeks. Weeks 3-6 add small load jumps when every set is clean. Weeks 7-8 repeat, reduce, or test rep PRs based on recovery.",
            "starting": "Start each main lift with a load you could do for 2-3 more clean reps on the final set. Beginners should start lighter than pride wants.",
            "missed": "If you miss reps once, repeat the same load next time. If you miss twice, reduce that lift by 5-10% and build back with cleaner reps.",
            "deload": "Use week 5 or any week after poor recovery as a lighter week: reduce working weights by 5-10% or reduce accessory sets by 20%.",
            "finish": "Move on after 8 weeks when the lifts feel familiar, warmups are routine, and you have a clear history of loads to progress from.",
            "adjustment": "If soreness, motivation, sleep, or performance drops for more than a week, repeat loads or reduce weekly sets by about 10-20%.",
            "phases": [("Weeks 1-2", "Learn the lifts and leave reps in reserve."), ("Weeks 3-6", "Add small jumps after clean sessions."), ("Weeks 7-8", "Consolidate progress and repeat loads when needed.")],
            "days": [
                ("Day 1", [("Barbell Squat", "3", "5", "2-3 min", "Start light and repeatable."), ("Bench Press", "3", "5", "2-3 min", "Use safeties or a spotter."), ("Barbell Row", "3", "8", "2 min", "Pull to lower ribs."), ("Plank", "3", "30-45 sec", "60 sec", "Brace and breathe.")]),
                ("Day 2", [("Deadlift", "2", "5", "3 min", "Reset each rep."), ("Overhead Press", "3", "5", "2 min", "Keep ribs down."), ("Lat Pulldown or Pull-Up", "3", "8-10", "90 sec", "Use assistance if needed."), ("Split Squat", "2", "8/side", "90 sec", "Controlled reps.")]),
                ("Day 3", [("Front Squat or Light Squat", "3", "6", "2 min", "Practice position."), ("Incline Bench Press", "3", "8", "2 min", "Stop before form breaks."), ("Romanian Deadlift", "3", "8", "2 min", "Slow lower."), ("Cable Row", "3", "10", "90 sec", "Full reach and pull.")]),
            ],
        },
        "/programs/5x5-beginner-strength-program.html": {
            "duration": "8-12 weeks",
            "frequency": "3 days per week, alternating A and B",
            "level": "Beginner strength",
            "progression": "Alternate Workout A and B for 8-12 weeks. Add small jumps only after all 5x5 sets are completed with consistent technique.",
            "starting": "Start with conservative 5x5 loads: roughly a weight you could perform for 8-10 reps fresh, not a true 5-rep max.",
            "missed": "If you miss one set, repeat the same load next time. If you miss the same lift twice, reduce that lift by 5-10% and rebuild.",
            "deload": "After 4-6 hard weeks, or when bar speed and recovery drop, reduce working weights by 10% for one week before building again.",
            "finish": "Move on when linear load jumps are no longer repeatable for several lifts, or after 12 weeks of consistent training history.",
            "adjustment": "If you miss reps twice at the same load, reduce that lift by 5-10% and build back up.",
            "phases": [("Weeks 1-2", "Find conservative 5x5 starting loads."), ("Weeks 3-8", "Add small jumps after completed sessions."), ("Weeks 9-12", "Keep progressing, deload, or transition when stalls repeat.")],
            "days": [
                ("Workout A", [("Barbell Squat", "5", "5", "2-4 min", "Same weight across sets."), ("Bench Press", "5", "5", "2-4 min", "Track every set."), ("Barbell Row", "5", "5", "2-3 min", "Keep torso consistent.")]),
                ("Workout B", [("Barbell Squat", "5", "5", "2-4 min", "Reduce if recovery lags."), ("Overhead Press", "5", "5", "2-3 min", "Small jumps work best."), ("Deadlift", "1", "5", "3-5 min", "One heavy set after warmups."), ("Lat Pulldown", "3", "8", "90 sec", "Optional back volume.")]),
            ],
        },
        "/programs/garage-gym-strength-program.html": {
            "duration": "8 weeks",
            "frequency": "3 days per week",
            "level": "Beginner to intermediate",
            "progression": "Run the program for 8 weeks using the closest loadable increases your garage setup allows. Repeat loads when jumps are too large.",
            "starting": "Choose starting weights that leave 2-3 reps in reserve, especially if your smallest plate jump is larger than a commercial gym jump.",
            "missed": "If the next available jump is too heavy, stay at the prior load and add cleaner reps, slower eccentrics, or an extra week before increasing.",
            "deload": "Use week 5 or any week after poor recovery to reduce main lift loads by 5-10% and keep accessories easy.",
            "finish": "Move on after 8 weeks when you know which jumps are realistic with your plate inventory and which lifts need smaller progressions.",
            "adjustment": "If limited plates force a larger jump, repeat the prior load for more confident reps before increasing.",
            "phases": [("Weeks 1-2", "Map your real plate jumps and establish baselines."), ("Weeks 3-6", "Progress with closest loadable increases."), ("Weeks 7-8", "Repeat hard jumps or push rep quality before moving on.")],
            "days": [
                ("Day 1", [("Back Squat", "4", "5", "2-3 min", "Main lift."), ("Bench Press", "4", "5", "2-3 min", "Use safeties."), ("Barbell Row", "4", "8", "2 min", "Back volume.")]),
                ("Day 2", [("Deadlift", "3", "5", "3 min", "Main pull."), ("Overhead Press", "4", "5", "2 min", "Smallest jump available."), ("Front Squat", "3", "6", "2 min", "Light squat practice."), ("Loaded Carry", "3", "30 sec", "90 sec", "Use available implements.")]),
                ("Day 3", [("Back Squat", "3", "8", "2 min", "Volume work."), ("Close-Grip Bench Press", "3", "8", "2 min", "Accessory press."), ("Romanian Deadlift", "3", "8", "2 min", "Hinge volume."), ("Barbell Curl", "2", "12", "60 sec", "Optional.")]),
            ],
        },
        "/programs/upper-lower-strength-hypertrophy.html": {
            "duration": "8-12 weeks",
            "frequency": "4 days per week",
            "level": "Intermediate",
            "progression": "Run 8-12 weeks. Progress main lifts with small load jumps and accessories by adding reps first, then load. Keep most sets around RPE 7-9.",
            "starting": "Start main lifts around a confident RPE 7-8. Accessories should feel productive but not threaten the next heavy session.",
            "missed": "If a main lift misses its target twice, reduce that lift by 5-10%. If accessories stall, keep load and rebuild reps before increasing.",
            "deload": "After 4-6 weeks, or when recovery trends down, reduce total sets by 10-20% and keep loads submaximal for one week.",
            "finish": "Move on after 8-12 weeks when main lift progress slows or you need a new emphasis for weak muscle groups.",
            "adjustment": "Hold volume steady for 4-6 weeks before adding sets. Reduce volume 10-20% when recovery trends down.",
            "phases": [("Weeks 1-4", "Establish loads and accumulate quality volume."), ("Weeks 5-8", "Progress main lifts and accessories where recovery is good."), ("Weeks 9-12", "Continue, deload, or shift emphasis based on progress.")],
            "days": [
                ("Upper Strength", [("Bench Press", "4", "4", "3 min", "Heavy press."), ("Barbell Row", "4", "6", "2 min", "Heavy pull."), ("Overhead Press", "3", "6", "2 min", "Secondary press."), ("Pull-Up", "3", "AMRAP", "2 min", "Stop before failure.")]),
                ("Lower Strength", [("Barbell Squat", "4", "4", "3 min", "Heavy squat."), ("Deadlift", "3", "3", "3-5 min", "Heavy pull."), ("Leg Press", "3", "8", "2 min", "Controlled volume."), ("Plank", "3", "60 sec", "60 sec", "Core.")]),
                ("Upper Hypertrophy", [("Incline Bench Press", "3", "10", "90 sec", "Chest volume."), ("Cable Row", "3", "12", "90 sec", "Back volume."), ("Dumbbell Bench Press", "3", "10", "90 sec", "Pressing volume."), ("Barbell Curl", "3", "12", "60 sec", "Arms.")]),
                ("Lower Hypertrophy", [("Front Squat", "3", "8", "2 min", "Quad focus."), ("Romanian Deadlift", "3", "10", "2 min", "Hamstrings."), ("Bulgarian Split Squat", "3", "10/side", "90 sec", "Single-leg."), ("Calf Raise", "3", "15", "60 sec", "Optional.")]),
            ],
        },
    }


def render_program_hub(page: dict, registry: dict) -> str:
    prefix = prefix_for(page["slug"])
    programs = [item for item in registry["pages"] if item.get("section") == "programs" and item.get("type") == "program"]
    cards = "\n".join(
        f"""          <a class="tool-card" href="{prefix + item["slug"].lstrip("/")}">
            <span class="tool-card-kicker">{escape(item.get("eyebrow", "Program"))}</span>
            <h2>{escape(item["h1"])}</h2>
            <p>{escape(item["description"])}</p>
            <span class="tool-card-action">Open program</span>
          </a>"""
        for item in programs
    )
    body = f"""    <main>
      <section class="page-hero seo-hero">
        <p class="eyebrow">{escape(page["eyebrow"])}</p>
        <h1>{escape(page["h1"])}</h1>
        <p>{escape(page["summary"])}</p>
        <div class="hero-actions">
          <a class="button primary" href="{app_href(page["appRoute"])}" data-rm-app-link data-rm-event="app_deeplink_clicked">{escape(page["primaryCta"])}</a>
          <a class="button secondary" href="{prefix}workouts/">Browse workouts</a>
        </div>
      </section>

      <section class="section tool-grid" aria-label="RackMath public programs">
{cards}
      </section>
    </main>"""
    return page_shell(page, body, current="programs")


def render_program_page(page: dict, registry: dict) -> str:
    prefix = prefix_for(page["slug"])
    data = program_library()[page["slug"]]
    related = render_related_links(page, registry, prefix)
    phase_rows = "\n".join(
        f"""          <li>
            <span>{escape(phase)}</span>
            <p>{escape(copy)}</p>
          </li>"""
        for phase, copy in data["phases"]
    )
    body = f"""    <main>
      <section class="page-hero seo-hero">
        <p class="eyebrow">{escape(page.get("eyebrow", "Program"))}</p>
        <h1>{escape(page["h1"])}</h1>
        <p>{escape(page.get("summary", page["description"]))}</p>
        <div class="hero-actions">
          <a class="button primary" href="{app_href(page["appRoute"])}" data-rm-app-link data-rm-event="template_started">{escape(page["primaryCta"])}</a>
          <a class="button secondary" href="{prefix}programs/">All programs</a>
        </div>
      </section>

      <section class="section exercise-summary-grid">
        <article><span>Duration</span><strong>{escape(data["duration"])}</strong></article>
        <article><span>Frequency</span><strong>{escape(data["frequency"])}</strong></article>
        <article><span>Level</span><strong>{escape(data["level"])}</strong></article>
        <article><span>Program type</span><strong>Multi-week progression</strong></article>
      </section>

      <section class="section program-roadmap" aria-labelledby="program-roadmap-heading">
        <div class="section-heading">
          <p class="eyebrow">Roadmap</p>
          <h2 id="program-roadmap-heading">How this program changes over time.</h2>
          <p>A workout tells you what to do today. This program tells you how to repeat, progress, and adjust those workouts across multiple weeks.</p>
        </div>
        <ol>
{phase_rows}
        </ol>
      </section>

      <section class="section seo-content-grid">
        <article>
          <p class="eyebrow">Starting weights</p>
          <h2>Begin with room to progress.</h2>
          <p>{escape(data["starting"])}</p>
        </article>
        <article>
          <p class="eyebrow">Progression rule</p>
          <h2>Progress when the work is clean.</h2>
          <p>{escape(data["progression"])}</p>
        </article>
      </section>

      <section class="section workout-plan" aria-labelledby="program-table-heading">
        <div class="section-heading">
          <p class="eyebrow">Workout rotation</p>
          <h2 id="program-table-heading">The sessions you repeat inside the program.</h2>
          <p>Run the days in order, rest at least one day after hard lower-body sessions when possible, and use warmup sets before the first heavy barbell lift.</p>
        </div>
{render_workout_table(data["days"])}
      </section>

      <section class="section seo-content-grid">
        <article>
          <p class="eyebrow">Missed reps</p>
          <h2>Do not force bad reps into progress.</h2>
          <p>{escape(data["missed"])}</p>
        </article>
        <article>
          <p class="eyebrow">Deload rule</p>
          <h2>Reduce stress before recovery collapses.</h2>
          <p>{escape(data["deload"])}</p>
        </article>
      </section>

      <section class="section seo-content-grid">
        <article>
          <p class="eyebrow">When to finish</p>
          <h2>Move on when the program has done its job.</h2>
          <p>{escape(data["finish"])}</p>
        </article>
        <article>
          <p class="eyebrow">RackMath handoff</p>
          <h2>The page gives the plan. The app keeps track of the next workout.</h2>
          <p>Open the program in RackMath when you want the next session, exact plates, previous loads, warmups, and progression decisions saved for you.</p>
        </article>
      </section>

      <section class="section program-app-builder" aria-labelledby="program-builder-heading">
        <div>
          <p class="eyebrow">Custom program builder</p>
          <h2 id="program-builder-heading">RackMath can build the full progression from your current strength.</h2>
          <p>In the app, you can use your current or estimated 1RM to create a custom program, calculate every training week, set planned progression, and estimate where new PRs may land by the end of the block.</p>
        </div>
        <div class="program-builder-list">
          <span>1RM-based starting loads</span>
          <span>Week-by-week progression</span>
          <span>Projected PR targets</span>
          <span>Saved next workouts</span>
        </div>
      </section>

{render_training_evidence_section()}

      <section class="section related-pages" aria-labelledby="related-heading">
        <div class="section-heading">
          <p class="eyebrow">Related</p>
          <h2 id="related-heading">Tools and guides for this program.</h2>
        </div>
        <div class="related-grid">
{related}
        </div>
      </section>

      <section class="final-cta">
        <p class="eyebrow">Ready to run it?</p>
        <h2>Open RackMath to save this program, calculate plates, track sessions, and keep progression moving.</h2>
        <div class="hero-actions">
          <a class="button primary" href="{app_href(page["appRoute"])}" data-rm-app-link data-rm-event="template_started">{escape(page["primaryCta"])}</a>
        </div>
      </section>
    </main>"""
    return page_shell(page, body, current="programs")


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

    priority_by_type = {
        "hub": "0.8",
        "tool": "0.8",
        "workout": "0.7",
        "exercise": "0.7",
        "feature": "0.7",
    }
    for page in published_pages(registry):
        add(page["slug"], priority_by_type.get(page["type"], "0.6"))

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
        elif page["slug"] == "/workouts/":
            write_page(page, render_workouts_hub(page, registry))
        elif page["slug"] == "/exercises/":
            write_page(page, render_exercises_hub(page, registry))
        elif page["slug"] == "/for/":
            write_page(page, render_persona_hub(page, registry))
        elif page["slug"] == "/programs/":
            write_page(page, render_program_hub(page, registry))
        elif page["slug"] == "/tools/barbell-plate-calculator.html":
            write_page(page, render_calculator_page(page, registry))
        elif page.get("type") == "tool":
            write_page(page, render_standard_tool_page(page, registry))
        elif page.get("type") == "workout":
            write_page(page, render_workout_page(page, registry))
        elif page.get("type") == "exercise":
            write_page(page, render_exercise_page(page, registry))
        elif page.get("type") == "feature":
            write_page(page, render_feature_page(page, registry))
        elif page.get("type") == "persona":
            write_page(page, render_persona_page(page, registry))
        elif page.get("type") == "program":
            write_page(page, render_program_page(page, registry))

    write_sitemap(posts, registry)
    print(
        f"Built {len(posts)} blog post(s), "
        f"{len(published_pages(registry))} published SEO page(s), "
        f"and sitemap.xml at {datetime.now(UTC).isoformat(timespec='seconds')}"
    )


if __name__ == "__main__":
    main()
