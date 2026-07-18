#!/usr/bin/env python3
"""Zona citations / NAP audit (read-only) — capsule 4, Decision Card #1 approved:
Zona AUDITS citations, Catena FIXES them.

"Citations" are a business's listings across web directories (Google, Bing,
Apple Maps, Yelp, ...). Local SEO Pillar 1: the Name / Address / Phone (NAP)
on every listing must match the school's canonical NAP exactly — mismatches
erode Google's trust and Maps rank.

Two-part design, ported from the proven Zona Engine
(~/clawd/agents/zona/engine/zona_engine/{nap,citations,matcher}.py):

  1. OBSERVED listings are recorded (by an agent or human reading the public
     directory pages) into observed/<school>-citations.json via --record.
     The auditor NEVER fabricates listings: a directory not recorded as
     checked simply isn't scored; one checked and absent is "missing".
  2. The AUDIT itself is fully offline + deterministic: it normalizes cosmetic
     differences (Drive vs Dr, (602) 996-4990 vs 602.996.4990) and reports
     coverage, consistency, and field-level mismatches.

Strictly read-only: never creates, claims, or edits any listing — that is
Catena's lane. Output is dated evidence in runs/ addressed to Catena's queue.

Usage:
  # record what a directory's public page shows (listing found):
  python3 citations_audit.py --school beibei --record yelp \
      --name "..." --address "..." --phone "..." --url "..."
  # record that a directory was checked and has NO listing:
  python3 citations_audit.py --school beibei --record nextdoor --absent
  # run the audit over everything recorded:
  python3 citations_audit.py --school beibei
"""

import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path

ZONA_DIR = Path(__file__).resolve().parent.parent
OBSERVED_DIR = ZONA_DIR / "observed"
RUNS_DIR = ZONA_DIR / "runs"

# Canonical NAP — source of truth (matches each school's own site/schema markup;
# same values as the engine's clients/*.yaml). Public info, safe to hard-code.
SCHOOLS = {
    "beibei": {
        "name": "Beibei Amigos Language Preschool",
        "aliases": ["Beibei Amigos"],
        "address": "751 E Union Hills Dr, Phoenix AZ 85024",
        "phone": "+1-602-996-4990",
    },
    "amici": {
        "name": "Amici Trilingual Montessori",
        "aliases": ["Amici Montessori"],
        "address": "1244 E Chandler Blvd, Phoenix AZ 85048",
        "phone": "+1-480-336-3364",
    },
}

# Directories that matter for a US local business, most important first.
# The core three feed Google / Siri-Apple / Bing-Alexa ecosystems.
EXPECTED_DIRECTORIES = [
    "google_business_profile", "bing_places", "apple_maps", "yelp",
    "facebook", "yellowpages", "nextdoor",
]
CORE_DIRECTORIES = {"google_business_profile", "bing_places", "apple_maps"}

# ---------------------------------------------------------------- NAP compare
# (ported from zona_engine/nap.py + matcher.py)

_STREET_TYPES = {
    "street": "st", "avenue": "ave", "drive": "dr", "boulevard": "blvd",
    "road": "rd", "lane": "ln", "court": "ct", "place": "pl", "circle": "cir",
    "parkway": "pkwy", "highway": "hwy", "terrace": "ter", "trail": "trl",
}
_DIRECTIONALS = {"north": "n", "south": "s", "east": "e", "west": "w",
                 "northeast": "ne", "northwest": "nw",
                 "southeast": "se", "southwest": "sw"}
_UNIT_WORDS = {"suite": "ste", "ste": "ste", "unit": "ste", "apt": "ste"}
_STATES = {"arizona": "az"}
_STOPWORDS = {"the", "a", "an", "of", "in", "at", "and", "&", "llc", "inc"}


def normalize_phone(value):
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits


def normalize_address(value):
    s = str(value or "").lower().replace("#", " ste ")
    s = re.sub(r"\b(united states|usa)\b", " ", s)
    s = re.sub(r"[.,]", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    tokens = []
    for tok in s.split():
        tok = _STREET_TYPES.get(tok, _DIRECTIONALS.get(
            tok, _UNIT_WORDS.get(tok, _STATES.get(tok, tok))))
        tokens.append(tok)
    return " ".join(tokens)


def _norm_name(name):
    name = (name or "").lower().replace("&", " and ")
    name = re.sub(r"[^a-z0-9 ]+", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def name_matches(candidate, target, aliases=()):
    cand = _norm_name(candidate)
    if not cand:
        return False
    for t in [target, *aliases]:
        t_norm = _norm_name(t)
        if t_norm and (t_norm in cand or cand in t_norm):
            return True
        overlap = ({w for w in cand.split() if w not in _STOPWORDS}
                   & {w for w in t_norm.split() if w not in _STOPWORDS})
        if len(overlap) >= 2:
            return True
    return False


def compare_nap(canonical, listing):
    """Field-level match: {name, address, phone: bool, consistent, mismatches}.

    A blank observed field normally counts as a mismatch (the directory is
    missing that field). If the listing is marked "partial": true (the page
    could only be partially read, e.g. bot-blocked), blank fields are skipped
    instead of blamed — only what was actually observed gets compared.
    """
    partial = bool(listing.get("partial"))
    result = {"mismatches": []}

    result["name"] = name_matches(listing.get("name", ""), canonical["name"],
                                  canonical.get("aliases", ()))
    if not result["name"]:
        result["mismatches"].append({"field": "name", "canonical": canonical["name"],
                                     "observed": listing.get("name", "")})

    if partial and not listing.get("address"):
        result["address"] = True
    else:
        result["address"] = (normalize_address(listing.get("address", ""))
                             == normalize_address(canonical["address"]))
        if not result["address"]:
            result["mismatches"].append(
                {"field": "address", "canonical": canonical["address"],
                 "observed": listing.get("address", "")})

    if partial and not listing.get("phone"):
        result["phone"] = True
    else:
        result["phone"] = (normalize_phone(listing.get("phone", ""))
                           == normalize_phone(canonical["phone"]))
        if not result["phone"]:
            result["mismatches"].append(
                {"field": "phone", "canonical": canonical["phone"],
                 "observed": listing.get("phone", "")})

    result["consistent"] = result["name"] and result["address"] and result["phone"]
    return result

# ------------------------------------------------------------------ observed


def observed_path(school):
    return OBSERVED_DIR / f"{school}-citations.json"


def load_observed(school):
    path = observed_path(school)
    if not path.exists():
        return {}
    return json.loads(path.read_text()).get("listings", {})


def record_listing(school, directory, listing):
    OBSERVED_DIR.mkdir(exist_ok=True)
    listings = load_observed(school)
    listings[directory] = listing
    observed_path(school).write_text(
        json.dumps({"listings": listings}, indent=2) + "\n")

# --------------------------------------------------------------------- audit


def audit(school, observed):
    canonical = SCHOOLS[school]
    directories, inconsistencies, missing = [], [], []
    consistent = 0
    checked = {d: l for d, l in observed.items()}
    for d in EXPECTED_DIRECTORIES + [d for d in checked if d not in EXPECTED_DIRECTORIES]:
        listing = checked.get(d)
        core = d in CORE_DIRECTORIES
        extra = d not in EXPECTED_DIRECTORIES
        if listing is None:
            directories.append({"directory": d, "status": "unchecked", "core": core})
            continue
        if listing.get("absent"):
            missing.append(d)
            directories.append({"directory": d, "status": "missing", "core": core,
                                "checked": listing.get("checked")})
            continue
        cmp = compare_nap(canonical, listing)
        if cmp["consistent"]:
            consistent += 1
        else:
            for m in cmp["mismatches"]:
                inconsistencies.append({**m, "directory": d, "core": core})
        directories.append({
            "directory": d,
            "status": "consistent" if cmp["consistent"] else "inconsistent",
            "core": core, "extra": extra, "url": listing.get("url"),
            "checked": listing.get("checked"), "note": listing.get("note"),
            "partial": bool(listing.get("partial")),
            "fields": {k: cmp[k] for k in ("name", "address", "phone")},
        })

    present = [d for d in directories if d["status"] in ("consistent", "inconsistent")]
    checked_expected = [d for d in EXPECTED_DIRECTORIES
                        if observed.get(d) is not None]
    summary = {
        "citations_count": len(present),
        "expected_count": len(EXPECTED_DIRECTORIES),
        "checked_count": len(checked_expected),
        "unchecked": [d for d in EXPECTED_DIRECTORIES if observed.get(d) is None],
        "consistent_count": consistent,
        "coverage_pct": round(len([d for d in present if not d.get("extra")])
                              / len(EXPECTED_DIRECTORIES), 3),
        "consistency_pct": round(consistent / len(present), 3) if present else 0.0,
        "missing": missing,
        "missing_core": [d for d in missing if d in CORE_DIRECTORIES],
        "inconsistency_count": len(inconsistencies),
    }
    if summary["missing_core"] or (present and summary["consistency_pct"] < 0.75):
        summary["segment"] = "red"
    elif summary["inconsistency_count"] or summary["coverage_pct"] < 0.8:
        summary["segment"] = "yellow"
    else:
        summary["segment"] = "green"
    return {"school": school, "canonical": canonical, "directories": directories,
            "inconsistencies": inconsistencies, "summary": summary}

# ------------------------------------------------------------------- reports


SEGMENT_WORD = {"green": "🟢 healthy", "yellow": "🟡 needs attention", "red": "🔴 broken"}
STATUS_MARK = {"consistent": "🟢 matches", "inconsistent": "🔴 mismatch",
               "missing": "⚫ not listed", "unchecked": "· not checked yet"}


def render_markdown(result):
    s = result["summary"]
    c = result["canonical"]
    lines = [
        f"# 📍 Citations / NAP Audit — {c['name']}",
        f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by Zona"
        " (read-only audit). Evidence for **Catena's** fix queue — Zona never"
        " edits listings.*",
        "",
        f"**Overall health: {SEGMENT_WORD[s['segment']]}**",
        "",
        f"- Directories checked: {s['checked_count']}/{s['expected_count']}"
        + (f" (not yet checked: {', '.join(s['unchecked'])})" if s["unchecked"] else ""),
        f"- Listed on: {s['citations_count']} directories"
        f" ({s['coverage_pct']:.0%} of the expected set)",
        f"- Listings matching official NAP: {s['consistent_count']}/{s['citations_count']}"
        f" ({s['consistency_pct']:.0%})",
        f"- Field mismatches found: {s['inconsistency_count']}"
        + (f" — **missing from core directories: {', '.join(s['missing_core'])}**"
           if s["missing_core"] else ""),
        "",
        "## Official (canonical) NAP",
        f"- **Name:** {c['name']}",
        f"- **Address:** {c['address']}",
        f"- **Phone:** {c['phone']}",
        "",
        "## Directory-by-directory",
        "| Directory | Status | Notes |",
        "|-----------|--------|-------|",
    ]
    for d in result["directories"]:
        parts = []
        if d["status"] == "inconsistent":
            bad = [k for k, v in d.get("fields", {}).items() if not v]
            parts.append("differs: " + ", ".join(bad))
        elif d["status"] == "missing":
            parts.append("no listing found" + (" — CORE directory" if d["core"] else ""))
        elif d["status"] == "consistent" and d.get("extra"):
            parts.append("bonus directory (beyond expected set)")
        if d.get("partial"):
            parts.append("partially readable page — only visible fields compared")
        if d.get("note"):
            parts.append(d["note"])
        lines.append(f"| {d['directory']} | {STATUS_MARK[d['status']]} | {'; '.join(parts)} |")
    if result["inconsistencies"]:
        lines += ["", "## For Catena to fix (exact mismatches)"]
        for m in result["inconsistencies"]:
            lines.append(f"- **{m['directory']}** — {m['field']}: listing shows"
                         f" `{m['observed'] or '(blank)'}`,"
                         f" official is `{m['canonical']}`")
    if s["missing"]:
        lines += ["", "## For Catena to create/claim",
                  *[f"- {d}" + (" (CORE)" if d in CORE_DIRECTORIES else "")
                    for d in s["missing"]]]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--school", required=True, choices=sorted(SCHOOLS))
    ap.add_argument("--record", metavar="DIRECTORY",
                    help="record an observed listing instead of auditing")
    ap.add_argument("--name")
    ap.add_argument("--address")
    ap.add_argument("--phone")
    ap.add_argument("--url")
    ap.add_argument("--absent", action="store_true",
                    help="with --record: directory checked, no listing exists")
    ap.add_argument("--partial", action="store_true",
                    help="with --record: page only partially readable; "
                         "blank fields are skipped, not blamed")
    ap.add_argument("--note", help="with --record: free-text note shown in report")
    args = ap.parse_args()

    if args.record:
        listing = {"checked": date.today().isoformat()}
        if args.absent:
            listing["absent"] = True
        else:
            listing.update({"name": args.name or "", "address": args.address or "",
                            "phone": args.phone or "", "url": args.url or ""})
            if args.partial:
                listing["partial"] = True
        if args.note:
            listing["note"] = args.note
        record_listing(args.school, args.record, listing)
        print(f"recorded {args.record} for {args.school}"
              f" ({'ABSENT' if args.absent else listing.get('name')})")
        return

    observed = load_observed(args.school)
    if not observed:
        raise SystemExit(f"No observed listings recorded yet for {args.school} "
                         f"— use --record first (see --help).")
    result = audit(args.school, observed)
    RUNS_DIR.mkdir(exist_ok=True)
    stem = f"{date.today().isoformat()}-{args.school}-citations"
    (RUNS_DIR / f"{stem}.json").write_text(json.dumps(result, indent=2) + "\n")
    (RUNS_DIR / f"{stem}.md").write_text(render_markdown(result))
    s = result["summary"]
    print(f"{args.school}: {SEGMENT_WORD[s['segment']]} — "
          f"{s['citations_count']} listed, {s['consistent_count']} consistent, "
          f"{s['inconsistency_count']} mismatches, missing: {s['missing'] or 'none'}")
    print(f"saved: runs/{stem}.md + .json")


if __name__ == "__main__":
    main()
