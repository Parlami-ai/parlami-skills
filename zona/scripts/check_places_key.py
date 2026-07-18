#!/usr/bin/env python3
"""Places API key preflight — the push-button check for Decision Card #3.

Zona's geo-grid + visibility capsules need a working Google Places API key.
This tool tests every Places-capable key it can find in the environment with
ONE cheap Find Place call each, classifies exactly what's wrong (billing off /
API not enabled / invalid key / OK), and prints the precise fix. Run it again
after fixing to confirm — a green line means capsules 1+2 can run live on the
Places provider.

Client-agnostic: uses a generic test query, touches no client data, reads keys
from the environment only (never prints or writes key values).

Usage:
  python3 check_places_key.py            # show which keys exist + how to run
  python3 check_places_key.py --confirm  # make the 1-call-per-key live test
"""

import argparse
import json
import os
import urllib.parse
import urllib.request

FINDPLACE = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
# Generic, client-free probe query.
TEST_QUERY = "coffee shop near Phoenix AZ"

# Env vars that may hold a Places-capable key, best candidate first.
CANDIDATE_ENV_VARS = [
    "GOOGLE_PLACES_API_KEY",
    "GOOGLE_API_KEY",
    "SKILL_GOPLACES_API_KEY",
    "SKILL_LOCAL_PLACES_API_KEY",
]

# Map Google's response to a plain-English diagnosis + exact fix.
FIXES = {
    "OK": ("✅ WORKS", "Ready — run capsules 1+2 with --provider places."),
    "BILLING": (
        "🔴 billing not enabled",
        "Enable billing on this key's Google Cloud project:\n"
        "      https://console.cloud.google.com/project/_/billing/enable\n"
        "      (Google requires a card on file even for the free tier.)"),
    "NOT_AUTHORIZED": (
        "🔴 Places API not enabled for this key",
        "Add 'Places API' to this key's allowed APIs in the console:\n"
        "      APIs & Services → Credentials → (this key) → API restrictions,\n"
        "      OR enable the API: APIs & Services → Library → Places API → Enable."),
    "INVALID": (
        "🔴 invalid key",
        "This key string is not a valid Google API key — it may be a "
        "placeholder or from a different product. Use a real Maps/Places key."),
    "OTHER": ("🔴 denied", "See the raw error above and Google's Maps docs."),
}


def classify(err_msg):
    m = (err_msg or "").lower()
    if "enable billing" in m or "billing" in m:
        return "BILLING"
    if "not authorized" in m or "api restrictions" in m or "not enabled" in m:
        return "NOT_AUTHORIZED"
    if "invalid" in m:
        return "INVALID"
    return "OTHER"


def probe(key):
    """One Find Place call. Returns (code, raw_error)."""
    qs = urllib.parse.urlencode({
        "input": TEST_QUERY, "inputtype": "textquery",
        "fields": "place_id", "key": key})
    try:
        with urllib.request.urlopen(f"{FINDPLACE}?{qs}", timeout=30) as resp:
            data = json.load(resp)
    except Exception as e:  # network / HTTP error, not an API verdict
        return "OTHER", f"request failed: {e}"
    status = data.get("status")
    if status in ("OK", "ZERO_RESULTS"):
        return "OK", ""
    return classify(data.get("error_message", "")), data.get("error_message", "")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--confirm", action="store_true",
                    help="make the live 1-call-per-key test (each call ~$0, "
                         "covered by Google's free tier)")
    args = ap.parse_args()

    present = [(v, os.environ.get(v)) for v in CANDIDATE_ENV_VARS
               if os.environ.get(v)]
    print("Places API key preflight (Decision Card #3)\n")
    if not present:
        print("No Places-capable key found in the environment. Expected one of:")
        for v in CANDIDATE_ENV_VARS:
            print(f"  - {v}")
        return

    print(f"Found {len(present)} candidate key(s): "
          + ", ".join(v for v, _ in present))
    if not args.confirm:
        print(f"\nEach key would get ONE Find Place call (query: \"{TEST_QUERY}\","
              " ~$0).\nRe-run with --confirm to test them live.")
        return

    print()
    any_ok = False
    for var, key in present:
        code, raw = probe(key)
        label, fix = FIXES[code]
        print(f"${var}: {label}")
        if code == "OK":
            any_ok = True
        else:
            if raw:
                print(f"    Google says: {raw}")
            print(f"    Fix: {fix}")
        print()

    if any_ok:
        print("At least one key works. Capsules 1+2 can run live on Places:")
        print("    python3 visibility_snapshot.py --school <slug> --confirm")
    else:
        print("No working Places key yet. Fix ONE of the keys above "
              "(billing is usually the quickest), then re-run this to confirm.")


if __name__ == "__main__":
    main()
