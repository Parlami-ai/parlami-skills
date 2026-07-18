#!/usr/bin/env python3
"""Zona location-page relevance check (read-only).

Crawls a school's public pages (from its WordPress page sitemap) and flags
missing LOCAL signals on each page:

  - area/neighborhood names and target zip codes
  - an embedded Google map
  - LocalBusiness/Preschool structured data (schema.org JSON-LD)
  - service keywords (preschool, Montessori, bilingual, ...)
  - NAP basics (address fragment, phone number)

Strictly read-only: plain GET requests with a polite delay, no logins, no
writes anywhere. No API key needed. Findings are saved as EVIDENCE for
Architetto's queue — Zona never edits pages itself.

Usage:
  python3 page_signals_check.py --school beibei
  python3 page_signals_check.py --school amici --max-pages 40
"""

import argparse
import json
import re
import time
import urllib.request
from datetime import date, datetime
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (compatible; ZonaLocalSEOAudit/1.0; read-only)"

SITES = {
    "beibei": {
        "name": "Beibei Amigos Language Preschool",
        "base": "https://www.beibeiamigos.com",
        "sitemap": "https://www.beibeiamigos.com/page-sitemap.xml",
        "address_fragments": ["751 E", "Union Hills"],
        "phone_fragments": ["602-996-4990", "6029964990", "(602) 996-4990"],
        "areas": ["north phoenix", "moon valley", "sunnyslope", "north mountain",
                  "north glendale", "north central", "desert ridge", "deer valley",
                  "paradise valley", "85024", "85050", "85054", "85085", "85254", "85331"],
        "services": ["preschool", "bilingual", "mandarin", "spanish", "immersion",
                     "language", "daycare", "montessori"],
    },
    "amici": {
        "name": "Amici Trilingual Montessori",
        "base": "https://amicimontessori.com",
        "sitemap": "https://amicimontessori.com/page-sitemap.xml",
        "address_fragments": ["1244 E", "Chandler Blvd"],
        "phone_fragments": [],  # filled from page discovery; absence flagged per page
        "areas": ["ahwatukee", "chandler", "south tempe", "tempe", "ocotillo",
                  "estrella", "laveen", "west chandler", "foothills", "85048",
                  "85044", "85045", "85226", "85286"],
        "services": ["preschool", "trilingual", "montessori", "mandarin",
                     "spanish", "immersion", "language", "daycare"],
    },
}

SCHEMA_TYPES = ["LocalBusiness", "Preschool", "ChildCare", "School",
                "EducationalOrganization"]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def sitemap_urls(sitemap_url):
    xml = fetch(sitemap_url)
    return re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)


def audit_page(url, site):
    html = fetch(url)
    low = html.lower()

    areas_found = sorted({a for a in site["areas"] if a in low})
    services_found = sorted({s for s in site["services"] if s in low})

    has_map = bool(re.search(
        r'<iframe[^>]+(google\.com/maps|maps\.google)', html, re.I))

    schema_found = []
    for block in re.findall(
            r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>',
            html, re.S | re.I):
        for t in SCHEMA_TYPES:
            if f'"{t}"' in block and t not in schema_found:
                schema_found.append(t)

    has_address = any(f.lower() in low for f in site["address_fragments"])
    has_phone = (any(f.lower() in low for f in site["phone_fragments"])
                 if site["phone_fragments"]
                 else bool(re.search(r'\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}', html)))

    title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    title = re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else ""
    title_local = any(a in title.lower() for a in site["areas"])

    missing = []
    if not areas_found:
        missing.append("no area/neighborhood names")
    if not has_map:
        missing.append("no embedded Google map")
    if not schema_found:
        missing.append("no LocalBusiness/School structured data")
    if not services_found:
        missing.append("no service keywords")
    if not has_address:
        missing.append("no street address")
    if not has_phone:
        missing.append("no phone number")
    if not title_local:
        missing.append("page title has no area name")

    return {
        "url": url,
        "title": title,
        "areas_found": areas_found,
        "services_found": services_found,
        "has_map_embed": has_map,
        "schema_types": schema_found,
        "has_address": has_address,
        "has_phone": has_phone,
        "title_has_area": title_local,
        "missing_signals": missing,
    }


def findings_md(site, pages, errors):
    total = len(pages)
    clean = [p for p in pages if not p["missing_signals"]]
    community = [p for p in pages if "/communities/" in p["url"]]

    def count_missing(signal):
        return sum(1 for p in pages if signal in p["missing_signals"])

    signals = ["no embedded Google map", "no LocalBusiness/School structured data",
               "no street address", "no phone number",
               "page title has no area name", "no area/neighborhood names",
               "no service keywords"]

    lines = [
        f"# Location-page signals check: {site['name']}",
        f"Date: {date.today().isoformat()} — {total} pages checked "
        f"({len(community)} community pages)",
        "",
        "**FOR ARCHITETTO'S QUEUE — evidence only.** Zona is read-only and has",
        "not changed anything. Each item below is a page-improvement opportunity",
        "for Architetto to consider; local signals on pages feed Google's local",
        "ranking, so fixing them supports the map-pack goals Zona tracks.",
        "",
        "## Summary, in plain English",
        "",
        f"- {len(clean)} of {total} pages already have every local signal we check.",
    ]
    for s in signals:
        n = count_missing(s)
        if n:
            lines.append(f"- {n} of {total} pages: {s}.")
    if errors:
        lines.append(f"- {len(errors)} pages could not be fetched (listed at bottom).")
    lines += ["", "## Pages with the most gaps first", ""]
    for p in sorted(pages, key=lambda x: -len(x["missing_signals"])):
        if not p["missing_signals"]:
            continue
        lines.append(f"### {p['url']}")
        lines.append(f"- Title: {p['title'] or '(none)'}")
        lines.append(f"- Missing: {'; '.join(p['missing_signals'])}")
        if p["areas_found"]:
            lines.append(f"- Areas mentioned: {', '.join(p['areas_found'][:6])}")
        lines.append("")
    if errors:
        lines += ["## Fetch errors", ""]
        lines += [f"- {u}: {e}" for u, e in errors]
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Zona page-signals check (read-only)")
    ap.add_argument("--school", choices=sorted(SITES), required=True)
    ap.add_argument("--max-pages", type=int, default=0, help="0 = all pages")
    ap.add_argument("--delay", type=float, default=0.5)
    ap.add_argument("--out-dir", default=str(Path(__file__).resolve().parent.parent / "runs"))
    args = ap.parse_args()

    site = SITES[args.school]
    urls = sitemap_urls(site["sitemap"])
    if args.max_pages:
        urls = urls[:args.max_pages]
    print(f"{site['name']}: {len(urls)} pages to check")

    pages, errors = [], []
    for i, url in enumerate(urls, 1):
        try:
            pages.append(audit_page(url, site))
        except Exception as e:
            errors.append((url, str(e)))
        if i % 20 == 0 or i == len(urls):
            print(f"  {i}/{len(urls)} pages checked")
        time.sleep(args.delay)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / f"{date.today().isoformat()}-{args.school}-page-signals"
    base.with_suffix(".json").write_text(json.dumps({
        "school": site["name"],
        "school_key": args.school,
        "generated": datetime.now().isoformat(),
        "pages_checked": len(pages),
        "fetch_errors": [{"url": u, "error": e} for u, e in errors],
        "pages": pages,
    }, indent=2))
    base.with_suffix(".md").write_text(findings_md(site, pages, errors))
    print(f"Saved: {base}.json / .md")
    gaps = sum(1 for p in pages if p["missing_signals"])
    print(f"Result: {gaps} of {len(pages)} pages have at least one missing local signal")


if __name__ == "__main__":
    main()
