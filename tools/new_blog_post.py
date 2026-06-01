#!/usr/bin/env python3
"""Create a dated Markdown draft for a new Rack Math blog post."""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content" / "blog"


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "rack-math-post"


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python3 tools/new_blog_post.py "Post title" [YYYY-MM-DD]')

    title = sys.argv[1]
    post_date = sys.argv[2] if len(sys.argv) > 2 else date.today().isoformat()
    slug = slugify(title)
    path = CONTENT_DIR / f"{post_date}-{slug}.md"

    if path.exists():
        raise SystemExit(f"{path} already exists")

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""---
title: "{title}"
description: "A short Rack Math post about weight lifting calculator tips, barbell plate loading, and workout tracking."
date: "{post_date}"
slug: "{slug}"
---

# {title}

Write the post here.
""",
        encoding="utf-8",
    )
    print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
