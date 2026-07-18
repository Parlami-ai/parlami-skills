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
