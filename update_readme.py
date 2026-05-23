#!/usr/bin/env python3
"""
Sci-Fi Movie Tracker — fetches recently released and upcoming sci-fi movies
from TMDB and writes a styled README.md to the repo root.
"""

import os
import requests
from datetime import datetime, timedelta

# ── Config ──────────────────────────────────────────────────────────────────
TMDB_API_KEY = os.environ["TMDB_API_KEY"]
TMDB_BASE    = "https://api.themoviedb.org/3"
IMAGE_BASE   = "https://image.tmdb.org/t/p/w300"
SCIFI_GENRE  = 878  # TMDB genre ID for Science Fiction
RESULTS_PER_SECTION = 10


# ── Helpers ──────────────────────────────────────────────────────────────────
def tmdb_get(path: str, params: dict) -> dict:
    params = {"api_key": TMDB_API_KEY, "language": "en-US", **params}
    r = requests.get(f"{TMDB_BASE}{path}", params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def fmt_date(date_str: str) -> str:
    """2024-11-01  →  Nov 1, 2024"""
    if not date_str:
        return "TBA"
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%b %-d, %Y")
    except ValueError:
        return date_str


def poster_md(movie: dict) -> str:
    path  = movie.get("poster_path")
    title = movie.get("title", "Poster")
    if path:
        return f'<img src="{IMAGE_BASE}{path}" alt="{title}" width="120"/>'
    return "_(no poster)_"


def overview_sentence(movie: dict) -> str:
    """Return the first sentence of the overview, capped at 160 chars."""
    text = (movie.get("overview") or "No synopsis available.").strip()
    end  = text.find(". ")
    sentence = text[: end + 1] if end != -1 else text
    if len(sentence) > 160:
        sentence = sentence[:157].rstrip() + "..."
    return sentence or "No synopsis available."


def fetch_section(params: dict) -> list:
    data = tmdb_get("/discover/movie", params)
    return data.get("results", [])[:RESULTS_PER_SECTION]


def build_table(movies: list) -> str:
    if not movies:
        return "_No movies found for this period._\n"

    rows = [
        "| | Title | Released | Synopsis |",
        "|---|---|---|---|",
    ]
    for m in movies:
        poster   = poster_md(m)
        title    = m.get("title", "Unknown")
        tmdb_id  = m.get("id")
        link     = f"[{title}](https://www.themoviedb.org/movie/{tmdb_id})"
        date     = fmt_date(m.get("release_date", ""))
        synopsis = overview_sentence(m)
        rows.append(f"| {poster} | {link} | {date} | {synopsis} |")

    return "\n".join(rows) + "\n"


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    today      = datetime.utcnow().date()
    month_ago  = today - timedelta(days=30)
    three_ago  = today - timedelta(days=90)
    six_ahead  = today + timedelta(days=180)
    tomorrow   = today + timedelta(days=1)

    print("Fetching recently released sci-fi movies...")
    recent = fetch_section({
        "with_genres": SCIFI_GENRE,
        "primary_release_date.gte": str(month_ago),
        "primary_release_date.lte": str(today),
        "sort_by": "release_date.desc",
        "page": 1,
    })

    print("Fetching trending sci-fi movies (last 90 days)...")
    popular = fetch_section({
        "with_genres": SCIFI_GENRE,
        "primary_release_date.gte": str(three_ago),
        "primary_release_date.lte": str(today),
        "sort_by": "popularity.desc",
        "page": 1,
    })

    print("Fetching upcoming sci-fi movies...")
    upcoming = fetch_section({
        "with_genres": SCIFI_GENRE,
        "primary_release_date.gte": str(tomorrow),
        "primary_release_date.lte": str(six_ahead),
        "sort_by": "primary_release_date.asc",
        "page": 1,
    })

    updated_at = datetime.utcnow().strftime("%B %-d, %Y at %H:%M UTC")

    readme = f"""# 🚀 Sci-Fi Movie Tracker

> Automatically updated every Monday at 08:00 UTC via GitHub Actions + [TMDB](https://www.themoviedb.org/).

**Last updated:** {updated_at}

---

## 🆕 Recently Released _(last 30 days)_

{build_table(recent)}
---

## 🔥 Trending Right Now _(last 90 days, by popularity)_

{build_table(popular)}
---

## 📅 Coming Soon _(next 6 months)_

{build_table(upcoming)}
---

<sub>Data provided by <a href="https://www.themoviedb.org/">TMDB</a>. This product uses the TMDB API but is not endorsed or certified by TMDB.</sub>
"""

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(readme)

    print(f"✅ README.md written ({len(readme):,} chars)")


if __name__ == "__main__":
    main()
