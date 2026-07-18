#!/usr/bin/env python3
"""Zona geo-grid rank tracker (read-only).

Generates an NxN coordinate grid around a school and, at each grid point, asks
the Google Places API (Nearby Search) for businesses matching a keyword. The
school's position in that list is a proxy for its Google Maps "map pack" rank
as seen from that location.

READ-ONLY: never writes to GBP, websites, or citations.
Metered: every live run requires --confirm and prints the cost estimate first.
The API key is read from the environment at runtime (GOOGLE_PLACES_API_KEY,
falling back to GOOGLE_API_KEY) and is never written to any output file.

Two providers:
  --provider places  Google Places API (preferred; needs Decision Card #3 cleared)
  --provider curl    free Google Maps fetch, no key — modernized port of the
                     proven Feb-Mar scanner (2 plain GETs per grid point,
                     2s delay). Listing names/order can shift with Google's
                     markup; treat as a stopgap until Places is unblocked.

Usage:
  python3 geogrid_tracker.py --school sunshine --keyword "preschool near me" --estimate
  python3 geogrid_tracker.py --school sunshine --test-call --confirm
  python3 geogrid_tracker.py --school sunshine --provider curl --confirm
"""

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

# School data is NOT hard-coded here — this is a client-agnostic SaaS repo.
# Each school's public business info (name/address/phone/lat/lng/aliases) is
# loaded at runtime from a gitignored config, `zona/clients/<slug>.config.yml`
# (template: zona/clients/example.config.yml). See client_config.py.
import client_config

# Miles-per-degree at the configured latitude band. These are set for the
# ~33.5°N Phoenix band; if you onboard schools far from that latitude, the
# longitude figure drifts — recompute MILES_PER_DEG_LNG = 69.17 * cos(lat).
MILES_PER_DEG_LAT = 69.0
MILES_PER_DEG_LNG = 54.6

PLACES_NEARBY = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PLACES_FINDPLACE = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"

# Google "Nearby Search" list price per call (Pro SKU). Actual spend is usually
# $0 because Google's monthly free tier covers thousands of calls, but the
# estimate is shown at list price to be safe.
PRICE_PER_CALL = 0.032

RESULT_LIMIT = 20  # one Nearby Search page; rank beyond 20 recorded as ">20"


def api_key():
    key = os.environ.get("GOOGLE_PLACES_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        sys.exit("No GOOGLE_PLACES_API_KEY / GOOGLE_API_KEY in environment.")
    return key


def get_json(url, params):
    qs = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{url}?{qs}", timeout=30) as resp:
        return json.load(resp)


def generate_grid(center_lat, center_lng, radius_miles, grid_size):
    lat_off = radius_miles / MILES_PER_DEG_LAT
    lng_off = radius_miles / MILES_PER_DEG_LNG
    half = (grid_size - 1) / 2
    points = []
    for row in range(grid_size):
        for col in range(grid_size):
            fr = (row - half) / half if half else 0
            fc = (col - half) / half if half else 0
            points.append({
                "row": row,
                "col": col,
                "lat": round(center_lat + fr * lat_off, 6),
                "lng": round(center_lng + fc * lng_off, 6),
            })
    return points


UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0.0.0 Safari/537.36")


def http_get(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def curl_ranked_names(lat, lng, keyword):
    """Free no-key path: fetch the Maps search shell for this coordinate, then
    the data endpoint it references, and pull the ranked business list out of
    the payload. Names are anchored on Google's CID pairs ("0x...:0x...","Name")
    — the payload shape observed live 2026-07-18."""
    shell = http_get(
        f"https://www.google.com/maps/search/{urllib.parse.quote(keyword)}"
        f"/@{lat},{lng},14z")
    m = re.search(r'<link href="(/search\?tbm=map[^"]+)"', shell)
    if not m:
        raise RuntimeError("Maps shell page had no tbm=map data link "
                           "(Google markup changed or request blocked)")
    body = http_get("https://www.google.com" + html.unescape(m.group(1)))
    names, seen = [], set()
    for match in re.finditer(r'"0x[0-9a-f]+:0x[0-9a-f]+","((?:[^"\\]|\\.){3,80})"', body):
        n = match.group(1).encode().decode("unicode_escape", errors="replace")
        if n not in seen:
            seen.add(n)
            names.append(n)
    return names[:RESULT_LIMIT]


def curl_rank_at_point(point, keyword, school):
    names = curl_ranked_names(point["lat"], point["lng"], keyword)
    rank = None
    for i, n in enumerate(names, 1):
        low = n.lower()
        if any(a in low for a in school["aliases"]):
            rank = i
            break
    return rank, len(names), names[:3]


def resolve_place_id(school, key):
    """One Find Place call to pin down the school's canonical place_id."""
    data = get_json(PLACES_FINDPLACE, {
        "input": f"{school['name']} {school['address']}",
        "inputtype": "textquery",
        "fields": "place_id,name,formatted_address",
        "key": key,
    })
    status = data.get("status")
    if status != "OK" or not data.get("candidates"):
        raise RuntimeError(f"Find Place failed: status={status} error={data.get('error_message', '')}")
    return data["candidates"][0]


def rank_at_point(point, keyword, place_id, school_name, key, radius_m):
    data = get_json(PLACES_NEARBY, {
        "location": f"{point['lat']},{point['lng']}",
        "radius": radius_m,
        "keyword": keyword,
        "key": key,
    })
    status = data.get("status")
    if status not in ("OK", "ZERO_RESULTS"):
        raise RuntimeError(f"Nearby Search failed: status={status} error={data.get('error_message', '')}")
    results = data.get("results", [])[:RESULT_LIMIT]
    rank = None
    for i, r in enumerate(results, 1):
        if r.get("place_id") == place_id or r.get("name", "").lower() == school_name.lower():
            rank = i
            break
    top3 = [r.get("name", "?") for r in results[:3]]
    return rank, len(results), top3


def rank_label(rank):
    if rank is None:
        return f">{RESULT_LIMIT}"
    return str(rank)


def provenance_note(provider):
    """A source + confidence banner for the human-readable reports, so nobody
    over-trusts preview-grade scraped ranks (Decision Card #4)."""
    if provider == "curl":
        return (
            "> **Source: free Google Maps read (preview-grade).** No API key "
            "used. Exact per-cell ranks can wobble ±1–3 between runs, so treat "
            "the **map-pack counts and the overall pattern** as reliable and "
            "individual cell numbers as approximate. Re-run on the Places API "
            "(Decision Card #3) for steady, terms-clean numbers.")
    return ("> **Source: Google Places API.** Steady, repeatable, "
            "terms-of-service-clean data.")


def grid_ascii(points, grid_size):
    """Plain-text grid: rows of rank labels, school center in the middle."""
    lines = []
    for row in range(grid_size):
        cells = []
        for col in range(grid_size):
            p = next(x for x in points if x["row"] == row and x["col"] == col)
            label = rank_label(p.get("rank")) if "rank" in p else "?"
            cells.append(f"{label:>4}")
        lines.append(" ".join(cells))
    return "\n".join(lines)


def findings_text(school, keyword, points, grid_size, provider="places"):
    ranked = [p["rank"] for p in points if p.get("rank") is not None]
    total = len(points)
    in_top3 = sum(1 for r in ranked if r <= 3)
    in_top10 = sum(1 for r in ranked if r <= 10)
    missing = total - len(ranked)
    center = next(p for p in points if p["row"] == grid_size // 2 and p["col"] == grid_size // 2)

    lines = [
        f"# Geo-grid rank check: {school['name']}",
        f"Keyword: \"{keyword}\" — {grid_size}x{grid_size} grid — {date.today().isoformat()}",
        "",
        provenance_note(provider),
        "",
        "## What this means, in plain English",
        "",
        f"We checked {total} points on a map around the school and asked Google",
        f"\"{keyword}\" at each one. The number is where the school appears in the",
        "results seen from that spot (1 = first). Lower is better; \">20\" means",
        "the school didn't show in the first 20 results there.",
        "",
        f"- Right at the school: rank {rank_label(center.get('rank'))}",
        f"- In the top 3 (the 'map pack'): {in_top3} of {total} points",
        f"- In the top 10: {in_top10} of {total} points",
        f"- Not visible in top {RESULT_LIMIT}: {missing} of {total} points",
        "",
        "## Rank grid (north at top, school at center)",
        "",
        "```",
        grid_ascii(points, grid_size),
        "```",
        "",
        "## Who wins the map pack near the school",
        "",
    ]
    top3 = center.get("top3", [])
    if top3:
        for i, name in enumerate(top3, 1):
            lines.append(f"{i}. {name}")
    else:
        lines.append("(no results returned at center point)")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Zona geo-grid rank tracker (read-only)")
    ap.add_argument("--school", choices=client_config.available_schools() or None,
                    required=True, metavar="SLUG",
                    help="client slug — zona/clients/<slug>.config.yml")
    ap.add_argument("--keyword", default="preschool near me")
    ap.add_argument("--grid-size", type=int, default=7)
    ap.add_argument("--radius", type=float, default=3.0, help="grid radius in miles")
    ap.add_argument("--search-radius-m", type=int, default=3000,
                    help="Nearby Search radius in meters at each point")
    ap.add_argument("--provider", choices=["places", "curl"], default="places",
                    help="places = Places API (needs working key); "
                         "curl = free no-key Maps fetch (stopgap)")
    ap.add_argument("--delay", type=float, default=None,
                    help="seconds between grid points (default 0.15 places / 2.0 curl)")
    ap.add_argument("--estimate", action="store_true", help="print cost estimate and exit")
    ap.add_argument("--test-call", action="store_true",
                    help="make ONE Find Place call to verify the key works, then exit")
    ap.add_argument("--confirm", action="store_true",
                    help="required for any live API call")
    ap.add_argument("--out-dir", default=str(Path(__file__).resolve().parent.parent / "runs"))
    args = ap.parse_args()

    school = client_config.load_school(args.school)
    delay = args.delay if args.delay is not None else (2.0 if args.provider == "curl" else 0.15)
    n_calls = args.grid_size ** 2 + 1  # +1 Find Place
    est = 0.0 if args.provider == "curl" else n_calls * PRICE_PER_CALL

    print(f"School: {school['name']}  Provider: {args.provider}")
    print(f"Keyword: \"{args.keyword}\"  Grid: {args.grid_size}x{args.grid_size}  Radius: {args.radius} mi")
    if args.provider == "curl":
        print(f"API calls: 0 (free no-key path)  Estimated cost: $0.00")
    else:
        print(f"API calls: {n_calls}  Estimated list-price cost: ${est:.2f} "
              f"(usually $0 — covered by Google's monthly free tier)")

    if args.estimate:
        return
    if not args.confirm:
        sys.exit("Live runs need --confirm. Use --estimate to preview cost.")

    place_id = None
    if args.provider == "places":
        key = api_key()
        if args.test_call:
            cand = resolve_place_id(school, key)
            print(f"TEST CALL OK — found: {cand['name']} @ {cand['formatted_address']}")
            print(f"place_id: {cand['place_id']}")
            return
        cand = resolve_place_id(school, key)
        place_id = cand["place_id"]
        print(f"Resolved place_id for {cand['name']}")
    elif args.test_call:
        rank, n, top3 = curl_rank_at_point(
            {"lat": school["lat"], "lng": school["lng"]}, args.keyword, school)
        print(f"TEST CALL OK — {n} listings at school center; "
              f"school rank {rank_label(rank)}; top3: {top3}")
        return

    points = generate_grid(school["lat"], school["lng"], args.radius, args.grid_size)
    for i, p in enumerate(points, 1):
        if args.provider == "curl":
            rank, n_results, top3 = curl_rank_at_point(p, args.keyword, school)
        else:
            rank, n_results, top3 = rank_at_point(
                p, args.keyword, place_id, school["name"], key, args.search_radius_m)
        p["rank"] = rank
        p["results_returned"] = n_results
        p["top3"] = top3
        print(f"  point {i}/{len(points)} ({p['row']},{p['col']}): rank {rank_label(rank)}")
        time.sleep(delay)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = date.today().isoformat()
    slug = args.keyword.replace(" ", "_")
    base = out_dir / f"{stamp}-{args.school}-geogrid-{slug}"

    payload = {
        "school": school["name"],
        "school_key": args.school,
        "provider": args.provider,
        "place_id": place_id,
        "keyword": args.keyword,
        "grid_size": args.grid_size,
        "radius_miles": args.radius,
        "search_radius_m": args.search_radius_m,
        "generated": datetime.now().isoformat(),
        "points": points,
    }
    base.with_suffix(".json").write_text(json.dumps(payload, indent=2))
    base.with_suffix(".md").write_text(
        findings_text(school, args.keyword, points, args.grid_size, args.provider))
    print(f"Saved: {base}.json / .md")


if __name__ == "__main__":
    main()
