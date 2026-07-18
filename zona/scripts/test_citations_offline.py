#!/usr/bin/env python3
"""Offline test for citations_audit.py — no network, no files written outside
a temp check. Verifies the NAP normalizer forgives cosmetic differences,
catches real mismatches, and the audit scores/segments correctly."""

import citations_audit as ca

canonical = ca.SCHOOLS["beibei"]

# 1. Cosmetic differences must count as CONSISTENT.
cosmetic = {"name": "Beibei Amigos",  # alias
            "address": "751 East Union Hills Drive, Phoenix, Arizona 85024",
            "phone": "(602) 996-4990"}
cmp = ca.compare_nap(canonical, cosmetic)
assert cmp["consistent"], f"cosmetic variant wrongly flagged: {cmp['mismatches']}"

# 2. A genuinely wrong phone must be caught.
wrong_phone = dict(cosmetic, phone="602-996-4999")
cmp = ca.compare_nap(canonical, wrong_phone)
assert not cmp["consistent"] and cmp["mismatches"][0]["field"] == "phone"

# 3. A different business name must be caught.
wrong_name = dict(cosmetic, name="Sunshine Daycare Center")
assert not ca.compare_nap(canonical, wrong_name)["consistent"]

# 4. Full audit: 1 consistent + 1 inconsistent + 1 checked-absent core
#    + rest unchecked → red (missing core), correct counts.
observed = {
    "yelp": cosmetic,
    "yellowpages": dict(cosmetic, phone="602-111-2222"),
    "bing_places": {"absent": True, "checked": "2026-07-18"},
}
result = ca.audit("beibei", observed)
s = result["summary"]
assert s["citations_count"] == 2, s
assert s["consistent_count"] == 1, s
assert s["inconsistency_count"] == 1, s
assert s["missing_core"] == ["bing_places"], s
assert s["segment"] == "red", s
assert s["checked_count"] == 3, s

# 5. Markdown renders with the Catena fix section and no crashes.
md = ca.render_markdown(result)
assert "For Catena to fix" in md and "yellowpages" in md
assert "For Catena to create/claim" in md and "bing_places" in md

# 6. All-good scenario → green.
all_good = {d: dict(cosmetic) for d in ca.EXPECTED_DIRECTORIES}
assert ca.audit("beibei", all_good)["summary"]["segment"] == "green"

print("OFFLINE CITATIONS TEST OK — cosmetic-tolerant, mismatch-strict, "
      "segments + Catena report verified")
