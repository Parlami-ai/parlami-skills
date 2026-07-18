# Zona — Decisions Needed From Sean

Things Zona found that need a human decision. Nothing here has been built or
changed — these are questions, not actions.

---

## Decision Card #1 — Who owns citations/NAP audits: Zona or Catena?

**What this is about:** "Citations" are the listings of the school's Name,
Address, and Phone number across the web (Yelp, care.com, Yellow Pages, etc.).
When they don't match exactly, Google trusts the business less and ranks it
lower on Maps.

**The question:** Should Zona *audit* citations (read-only: find mismatches and
report them) while Catena *fixes* them? Or does Catena own the whole thing?

**What exists already:** The old Zona Engine (`~/clawd/agents/zona/engine/`)
has a working citations audit module (`zona.py citations`), so if you say
"Zona audits, Catena fixes," most of the code already exists and just needs
porting.

**Recommendation:** Zona audits (read-only evidence), Catena builds/fixes.
That matches how Zona hands evidence to Architetto for page fixes.

**Status:** ✅ APPROVED by Sean 2026-07-18 ("keep building each card in
order"). Built same day: `scripts/citations_audit.py`, run live for both
schools → `runs/2026-07-18-*-citations.md`. Zona audits; fixes route to
Catena.

---

## Decision Card #2 — SKILL.md describes a different (write-enabled) Zona

**What this is about:** The current `zona/SKILL.md` describes Zona as a
*community page builder* that publishes pages to WordPress using write
credentials (WP_BEIBEI / WP_AMICI app passwords). This build activates Zona as
a **read-only auditor/tracker** — it never writes to the website, GBP, or
citations. Those lanes belong to Architetto, Stella, and Catena.

**The question:** Should SKILL.md be rewritten to match the read-only
audit/tracking lane, or should the page-builder mission stay on the books as a
future phase (with the audit lane added alongside it)?

**Why it matters:** If a future agent session reads SKILL.md as-is, it could
reasonably start publishing WordPress pages — crossing Architetto's lane and
using write credentials this build was told never to touch.

**Recommendation:** Rewrite SKILL.md to make read-only audit/tracking the
active mission and demote page-building to a "future, gated" section.

**Status:** ✅ APPROVED by Sean 2026-07-18 ("keep building each card in
order"). SKILL.md rewritten same day: read-only audit/tracking is the active
mission; page-builder demoted to a gated "future phase" section; WP write
credentials removed from required_secrets. Old version preserved in git
history.

---

## Decision Card #3 — Google Places API needs one click in your Google console

**What this is about:** The geo-grid rank tracker is built and fully tested,
but it can't make live calls yet. I tested both Google keys on this machine
with one cheap call each (2026-07-18):

- **Key 1 (GOOGLE_PLACES_API_KEY):** Google says its cloud project has
  *billing not enabled*. Google requires a card on file even for free-tier
  usage. Error: "You must enable Billing on the Google Cloud Project."
- **Key 2 (GOOGLE_API_KEY):** Google says the key's *API restrictions* don't
  include the Places API.

**What you'd need to do (either one works):**
1. Enable billing on Key 1's project at
   https://console.cloud.google.com/project/_/billing/enable — OR —
2. Add "Places API" to Key 2's allowed-APIs list in the console's
   credentials page.

**Cost reality:** Our full run (both schools, all keywords from capsules 1+2)
is about 500 calls ≈ $16 at list price, but Google's monthly free tier
(thousands of free Places calls) should make actual spend **$0**. Every run
still shows its estimate and requires a --confirm flag.

**Recommendation:** Option 1 (enable billing on the dedicated Places key's
project) — it keeps Places usage on its own key.

**Status:** APPROVED in principle 2026-07-18, but the click itself needs
Sean's Google login — the agent re-tested both keys 2026-07-18 (still blocked,
same two errors) and has no browser session into Sean's Google Cloud Console.
**This is the one remaining human step.** Once done, the recipe at the bottom
of HANDOFF.md runs capsules 1+2 live.

---

## Decision Card #4 — Capsules 1+2 ran on a free Google-Maps scrape, not the Places API you specified

**What this is about:** The build task said the rank tracker should use the
**Google Places API** ("no paid SERP APIs; if needed → decision card"). When
both Google keys came back blocked (that's Card #3), a parallel build loop
brought back an older, **free** method instead: it fetches Google Maps search
pages directly and reads the ranked business list out of the page
(`--provider curl`). Capsules 1 and 2 were then run on that free method for
both schools, and the results are saved in `runs/`.

**The question:** Is that free-scrape data good enough to count capsules 1+2 as
"done," or do you want them re-run on the official Places API once Card #3 is
cleared?

**Trade-offs, plainly:**
- **Free scrape (what we have now):** costs $0, works today, gives a clear
  picture. But the numbers wobble a little run-to-run (a rank might read 6 one
  time and 8 the next at the edges of the map), and reading Google Maps pages
  this way is against Google's terms of service — low-risk at this tiny volume,
  but worth you knowing.
- **Places API (the specified path):** steadier, repeatable numbers and fully
  above-board, but needs the one Google console click from Card #3 first.

**Recommendation:** Treat the current scraped runs as a **preview** — good
enough to see the lay of the land and start your evidence review — and re-run
capsules 1+2 on the Places API once Card #3 is cleared, so the numbers we act
on and hand to other agents are the steady, terms-clean ones.

**Status:** WAITING ON SEAN. Nothing to undo either way — the free-run reports
stay in `runs/`; clearing Card #3 just lets us regenerate them on the paid path.
