#!/usr/bin/env python3
"""Zona local visibility snapshot (read-only).

Runs the geo-grid rank check across the FIXED keyword set for one school and
combines everything into a single dated snapshot: for each keyword and each of
the 49 grid points, was the school visible, and at what position?

Reuses geogrid_tracker.py for grid math and Places API calls. Same guardrails:
read-only, key from environment only, --confirm required for live calls.

Usage:
  python3 visibility_snapshot.py --school beibei --estimate
  python3 visibility_snapshot.py --school beibei --confirm
"""

import argparse
import json
import sys
import time
from datetime import date, datetime
from pathlib import Path

import geogrid_tracker as gt

# Fixed keyword set per school (loop spec). [area] filled per school locale:
# Beibei sits in North Phoenix, Amici in Ahwatukee (1244 E Chandler Blvd 85048).
KEYWORDS = {
    "beibei": [
        "preschool near me",
        "Montessori preschool North Phoenix",
        "bilingual preschool North Phoenix",
        "trilingual preschool",
    ],
    "amici": [
        "preschool near me",
        "Montessori preschool Ahwatukee",
        "bilingual preschool Ahwatukee",
        "trilingual preschool",
    ],
}


def snapshot_findings(school, results, grid_size):
    total = grid_size ** 2
    lines = [
        f"# Local visibility snapshot: {school['name']}",
        f"Date: {date.today().isoformat()} — {grid_size}x{grid_size} grid, "
        f"{len(results)} keywords",
        "",
        "## What this means, in plain English",
        "",
        f"For each search phrase below, we checked all {total} map points around",
        "the school. \"Visible\" means the school appeared somewhere in Google's",
        "first 20 results at that spot; \"map pack\" means it was in the top 3 —",
        "the three businesses Google shows on the map itself.",
        "",
        "| Search phrase | In map pack (top 3) | Visible (top 20) | Best | Worst seen |",
        "|---|---|---|---|---|",
    ]
    for kw, points in results.items():
        ranks = [p["rank"] for p in points if p.get("rank") is not None]
        top3 = sum(1 for r in ranks if r <= 3)
        visible = len(ranks)
        best = min(ranks) if ranks else None
        worst = max(ranks) if ranks else None
        lines.append(
            f"| {kw} | {top3}/{total} points | {visible}/{total} points | "
            f"{best if best else '—'} | {worst if worst else 'not visible'} |")
    lines += ["", "## Rank grids (north at top, school at center)", ""]
    for kw, points in results.items():
        lines += [f"### \"{kw}\"", "", "```",
                  gt.grid_ascii(points, grid_size), "```", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Zona visibility snapshot (read-only)")
    ap.add_argument("--school", choices=sorted(gt.SCHOOLS), required=True)
    ap.add_argument("--grid-size", type=int, default=7)
    ap.add_argument("--radius", type=float, default=3.0)
    ap.add_argument("--search-radius-m", type=int, default=3000)
    ap.add_argument("--provider", choices=["places", "curl"], default="places")
    ap.add_argument("--delay", type=float, default=None,
                    help="seconds between points (default 0.15 places / 2.0 curl)")
    ap.add_argument("--estimate", action="store_true")
    ap.add_argument("--confirm", action="store_true")
    ap.add_argument("--out-dir", default=str(Path(__file__).resolve().parent.parent / "runs"))
    args = ap.parse_args()

    school = gt.SCHOOLS[args.school]
    keywords = KEYWORDS[args.school]
    delay = args.delay if args.delay is not None else (2.0 if args.provider == "curl" else 0.15)
    n_calls = len(keywords) * args.grid_size ** 2 + 1
    est = 0.0 if args.provider == "curl" else n_calls * gt.PRICE_PER_CALL

    print(f"School: {school['name']}  Provider: {args.provider}")
    print(f"Keywords ({len(keywords)}): " + "; ".join(keywords))
    if args.provider == "curl":
        print("API calls: 0 (free no-key path)  Estimated cost: $0.00")
    else:
        print(f"API calls: {n_calls}  Estimated list-price cost: ${est:.2f} "
              f"(usually $0 — covered by Google's monthly free tier)")

    if args.estimate:
        return
    if not args.confirm:
        sys.exit("Live runs need --confirm. Use --estimate to preview cost.")

    place_id = None
    if args.provider == "places":
        key = gt.api_key()
        cand = gt.resolve_place_id(school, key)
        place_id = cand["place_id"]
        print(f"Resolved place_id for {cand['name']}")

    results = {}
    for kw in keywords:
        points = gt.generate_grid(school["lat"], school["lng"], args.radius, args.grid_size)
        print(f"Keyword: \"{kw}\"")
        for i, p in enumerate(points, 1):
            if args.provider == "curl":
                rank, n, top3 = gt.curl_rank_at_point(p, kw, school)
            else:
                rank, n, top3 = gt.rank_at_point(p, kw, place_id, school["name"],
                                                 key, args.search_radius_m)
            p["rank"], p["results_returned"], p["top3"] = rank, n, top3
            if i % 10 == 0 or i == len(points):
                print(f"  {i}/{len(points)} points done")
            time.sleep(delay)
        results[kw] = points

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / f"{date.today().isoformat()}-{args.school}-visibility-snapshot"
    payload = {
        "school": school["name"],
        "school_key": args.school,
        "provider": args.provider,
        "place_id": place_id,
        "grid_size": args.grid_size,
        "radius_miles": args.radius,
        "search_radius_m": args.search_radius_m,
        "generated": datetime.now().isoformat(),
        "keywords": results,
    }
    base.with_suffix(".json").write_text(json.dumps(payload, indent=2))
    base.with_suffix(".md").write_text(
        snapshot_findings(school, results, args.grid_size))
    print(f"Saved: {base}.json / .md")


if __name__ == "__main__":
    main()
