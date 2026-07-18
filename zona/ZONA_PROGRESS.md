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
