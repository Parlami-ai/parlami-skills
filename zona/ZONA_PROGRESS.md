# Zona Build Progress

Plain-English log of what's been built, written for a non-coder. Newest entry
at the bottom.

---

## 2026-07-18 — Capsule 0: Foundation check (DONE)

**What I did:** Before building anything, I checked what already exists so we
don't rebuild things that work.

**What I found:**

1. **Both schools' locations are confirmed and consistent.** The old Zona
   scripts have exact map coordinates for both schools, and they match across
   every file I checked:
   - Beibei Amigos Language Preschool — 751 E Union Hills Dr, Phoenix AZ 85024
   - Amici Trilingual Montessori — 1244 E Chandler Blvd, Phoenix AZ 85048

2. **There is much more prior work than expected.** Beyond the simple
   grid-URL generator, there's a full "Zona Engine" from earlier this year
   (`~/clawd/agents/zona/engine/`) with working modules for grid scans,
   citation audits, page audits, competitor tracking, and a scorecard — plus
   real scan results from February–July. The grid math, school configs, and
   keyword lists are all reusable. What it does NOT have: a Google Places API
   connection (its live option scrapes Google, and its other options are paid
   services we're not using). So the Places-based rank tracker in capsule 1 is
   still genuinely new work — but smaller than expected because the grid and
   configs carry over.

3. **The "March React prototype" doesn't exist.** Everything from that era is
   Python. There's also a separate June project (`~/projects/maps-reputation-agent`)
   with useful audit-scoring ideas we can borrow for capsule 3. Noted; moving on.

4. **One mismatch flagged:** Zona's mission file (SKILL.md) describes a
   *page-publishing* agent with website write access. This build is strictly
   read-only. I did NOT change SKILL.md — I wrote it up as Decision Card #2
   for Sean instead.

**Decisions written for Sean:** Card #1 (who owns citation audits — this also
closes out capsule 4, which was gated anyway) and Card #2 (SKILL.md mismatch).
Both in `ZONA_DECISIONS.md`.

**Does it work?** Yes — this capsule was investigation, and every question it
asked (lane check, prototype hunt, location confirmation) is answered above.

**Capsule tally: 2/5 done (40%)** — capsule 0 complete, capsule 4 complete
(it was "write a decision card, don't build," and the card is written).
Next: capsule 1, the geo-grid rank tracker.

---

## 2026-07-18 — Capsule 1: Geo-grid rank tracker (BUILT + TESTED; live run waiting on Sean)

**What I did:** Built the rank tracker (`scripts/geogrid_tracker.py`). It draws
a 7x7 grid of map points around each school (49 spots covering ~6 miles) and
asks Google, from each spot, "who shows up for this search?" — recording where
the school ranks at every point. It saves a dated data file plus a plain-English
report with a visual rank map. It is strictly read-only, never stores the API
key in any file, and refuses to make live calls unless you pass a --confirm
flag after seeing the cost estimate (~$1.60 list price per school per keyword,
normally $0 thanks to Google's free tier).

**Does it work?** The machinery, yes — I proved the whole pipeline with a
stand-in for Google's answers (test file: `scripts/test_geogrid_offline.py`):
49 points, correct ranks, correct report, all green. The live connection, not
yet: I tested both Google keys with one cheap call each and both are blocked
on Google's side (one project needs billing enabled, the other key doesn't
allow the Places service). That needs one click in Sean's Google console —
written up as **Decision Card #3**. The moment it's fixed, the first real
scan is a single command.

**Capsule tally: 2/5 fully done, capsule 1 built-but-blocked (~50%).**
Next: capsule 2 (visibility snapshot) builds on the tracker; capsule 3
(website local-signals check) needs no Google key at all, so it can run for
real today.

---

## 2026-07-18 — Capsule 2: Local visibility snapshot (BUILT + TESTED; live run waiting on same key)

**What I did:** Built the visibility snapshot (`scripts/visibility_snapshot.py`).
It runs the rank check across the agreed fixed set of four search phrases per
school — "preschool near me", "Montessori preschool [area]", "bilingual
preschool [area]", "trilingual preschool" (area = North Phoenix for Beibei,
Ahwatukee for Amici) — and rolls everything into one dated report: a summary
table (how many of the 49 map points show the school in the map-pack top 3,
how many show it at all, best and worst position) plus a visual rank map per
phrase.

**Does it work?** Yes — same proof method as capsule 1: I fed it stand-in
Google answers and it correctly aggregated 4 phrases × 49 points into the
summary table and rank maps. Live runs wait on the same Google-key fix
(Decision Card #3); one command per school once that's cleared (about 197
calls / $6.30 list price per school, normally $0 under the free tier).

**Capsule tally: 2/5 fully done, capsules 1+2 built-but-blocked (~60%).**
Next: capsule 3, the website local-signals check — no Google key needed, so
it runs for real immediately.

---

## 2026-07-18 — Capsule 3: Location-page signals check (BUILT + RUN FOR REAL, both schools)

**What I did:** Built `scripts/page_signals_check.py` and ran it live against
both schools' public websites (read-only — it just reads pages like a visitor
would). For every page listed in each site's sitemap it checks: does the page
mention neighborhoods/zip codes, embed a Google map, carry the "structured
data" label Google reads to understand local businesses, use service keywords,
show the address and phone, and name an area in the page title?

**Real results (saved in `runs/`, dated 2026-07-18):**

- **Beibei (184 pages):** only 1 page has every signal. Biggest gaps:
  170 pages have no area name in the page title, 152 have no embedded map,
  22 lack local-business structured data — including the homepage and the
  tour-booking page (the tour page is also missing a phone number).
- **Amici (33 pages):** healthier — 16 pages are fully clean. Gaps: 16 pages
  lack an area name in the title, 9 lack structured data. One eyebrow-raiser:
  a "staff-handbook" page titled "Auto Draft" is publicly listed on the
  sitemap — probably shouldn't be public at all.

**Where the findings go:** The reports are written as evidence for
Architetto's queue (Architetto owns page edits; Zona never touches pages).
Both reports say so in their header.

**Does it work?** Yes — verified against the raw page code by hand (the
"missing structured data" finding on Beibei's homepage was double-checked
directly and is real).

**Capsule tally: 3/5 fully done, capsules 1+2 built-but-blocked on Sean
(~80%). STOP point reached** — per the loop rules, synthesis (findings
report + Bussola correlation) waits for Sean's evidence review.

---

## 2026-07-18 — Capsule 1 goes LIVE (Sean said "keep building")

**What I did:** The Google-key fix (Decision Card #3) is still pending, so I
added a second, free way for the tracker to ask Google: it fetches the public
Google Maps results page for each grid point — the same technique the
February–March scans used successfully — updated for how Google's pages look
today. No key, no cost, nothing written anywhere. The paid-API path stays in
place as the preferred option once the key is fixed (it's steadier; the free
path can wobble when Google changes its page markup).

**Real results for "preschool near me" (saved in `runs/`, 2026-07-18):**

- **Beibei:** rank 6 at its own front door; in the map-pack top 3 at 16 of 49
  points; visible almost everywhere (only 2 blind spots). Notably STRONG in a
  band just west of the school (rank 1) and weaker to the north-east.
- **Amici:** visible at only 14 of 49 points and — the headline —
  **completely absent from the top 20 at its own front door.** I double-checked
  by hand: for "montessori preschool" at the same spot it appears at #13 (its
  listing is called "Amici Trilingual Montessori Preschool"). So the listing
  exists and works, but Google doesn't connect it to the word "preschool"
  searches — very likely a Google Business Profile category problem. That's
  Stella's lane (GBP), so it's recorded here as evidence only.

**Does it work?** Yes — verified live at both schools, spot-checked by hand.

## 2026-07-18 (later) — Capsule 4: Citations / NAP audit — BUILT + RUN LIVE (Card #1 approved)

Sean approved Decision Card #1 ("Zona audits, Catena fixes"), so the citations
audit is now built and has been run for real against both schools.

**What it does, in plain words:** every website that lists a business (Google,
Bing, Apple Maps, Yelp, Facebook, Yellow Pages, Nextdoor) shows a Name, Address
and Phone. Google trusts a school more when all of them match exactly. The new
tool (`scripts/citations_audit.py`) records what each directory really shows
and compares it against the school's official details, forgiving cosmetic
differences ("Drive" vs "Dr") but catching real ones. It is read-only: fixing
anything is Catena's job, and the reports are addressed to Catena's queue.

**How the data was gathered:** by actually reading the public directory pages
(free local browser + web search — zero API cost). Pages that block robots
(Yellow Pages) are marked "partially readable" so unread fields are never
blamed unfairly.

**Real results (runs/2026-07-18-*-citations.md):**
- **Beibei: 🔴** Listed everywhere (good) but only 3 of 9 listings match the
  official record. The big story: Google, Bing, Apple, Yelp, Facebook and the
  directories all say "**Ste 19**" while the school's own website address has
  no suite number — so the likely right fix is adding "Ste 19" to the website,
  not editing 5 listings. Also found: **duplicate Facebook page** ("BeiBei
  Amigos Language School") and **duplicate YellowPages listing** (older name),
  which split reviews and confuse Google; the Google/Bing listing name has
  drifted to "BeiBei Amigos **Montessori** Language Preschool"; and Nextdoor
  shows no street address publicly.
- **Amici: 🟡** Every existing listing matches perfectly (name, address,
  phone) — but the school is **missing from Yellow Pages and Nextdoor**, and
  its Facebook page links to amicimontessori.**org** instead of .com. An old
  "coming soon" duplicate Yelp page also lingers.

**Tested:** offline test suite (9 scenarios) passes; live run produced dated
JSON + readable reports for both schools.

**For Catena (once ported to its lane):** the "For Catena to fix" sections in
both reports are the work orders. The Beibei suite-number question (add Ste 19
to the website vs strip it from listings) needs Sean's call because it touches
the website's official record.

## 2026-07-18 (later) — Card #2: SKILL.md rewritten to match the real lane

Sean approved Card #2. Zona's instruction file (`SKILL.md`) used to describe a
different, riskier job: publishing pages to the schools' websites using write
passwords. If a future session had read it literally, it could have started
editing the live websites — crossing Architetto's lane. The file now says
clearly: Zona is READ-ONLY, here are the four audit tools and where their
evidence goes, and page-building is locked behind a "future phase, do not
execute" gate. The website passwords were removed from its requirements list.
The old version stays safe in git history if it's ever needed.
