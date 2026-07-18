# Zona Build — Handoff

**Updated:** 2026-07-18 (second session — decision cards #1 and #2 built out
after Sean's "keep building each card in order")

## Where we are

Zona (agent #14) is live as a READ-ONLY local-SEO auditor/tracker for the
legacy swarm (Beibei Amigos + Amici). Repo: `~/parlami-skills/zona/`.
Never touches parlami-ads-saas; never writes to GBP/website/citations.

| # | Capsule | State |
|---|---------|-------|
| 0 | Foundation check | ✅ DONE |
| 1 | Geo-grid rank tracker | ✅ DONE — run live both schools via free `--provider curl` path; `runs/*-geogrid-*.md`. Places API still preferred once card #3 clears |
| 2 | Visibility snapshot | ✅ DONE — full 4-keyword live run both schools via `--provider curl`; `runs/*-visibility-snapshot.md` |
| 3 | Location-page relevance check | ✅ DONE — run live both schools; evidence in `runs/*-page-signals.md` (Architetto) |
| 4 | Citations/NAP audit | ✅ DONE — card #1 approved 2026-07-18; built + run live both schools; evidence in `runs/*-citations.md` (Catena) |

Decision cards: #1 ✅ approved+built, #2 ✅ approved+done (SKILL.md now
matches the read-only lane), #3 ⏳ approved in principle but needs Sean's own
Google console click (agent has no session into his Google account).

## Key facts a fresh session needs

- Schools: Beibei = 751 E Union Hills Dr, Phoenix AZ 85024, +1-602-996-4990;
  Amici = 1244 E Chandler Blvd, Phoenix AZ 85048, +1-480-336-3364.
  Canonical NAP lives in `scripts/citations_audit.py` SCHOOLS dict (and
  geogrid_tracker.py for lat/lng).
- ⚠️ Open NAP question for Sean: every directory shows Beibei at "**Ste 19**"
  but the website's own markup has no suite. Fix direction (add to site vs
  strip from listings) is Sean's call — see runs/2026-07-18-beibei-citations.md.
- Citation observations are recorded in `observed/<school>-citations.json`
  via `citations_audit.py --record` (supports --absent, --partial, --note).
  Re-audit anytime: `python3 citations_audit.py --school <school>` — offline,
  free, deterministic.
- Live directory reads used the gstack headless browser
  (`~/.claude/skills/gstack/browse/dist/browse`, needs `~/.bun/bin` on PATH).
  Google/Bing/Apple Maps + Facebook + Nextdoor render fine headless;
  YellowPages is Cloudflare-blocked (recorded as "partial" from search index).
- Both Google keys in `~/.bashrc` re-tested 2026-07-18: still blocked
  server-side (key 1 = billing not enabled; key 2 = Places API not allowed).
- Offline tests: `python3 test_geogrid_offline.py` and
  `python3 test_citations_offline.py` in `scripts/`.
- Commits are local-only (no push), one per capsule/card, single branch.

## Single next step

**All 5 capsules are now built and run live with real saved output** (capsules
1+2 used the free `--provider curl` path today; Places API stays preferred once
card #3 is cleared, for steadier data). **The build loop's STOP condition is
met.** The one remaining thing is Sean's review — two threads for him:

1. **Evidence review → unblock synthesis.** Per the loop spec, the synthesis
   phase (a combined findings report + Bussola correlation) must not start until
   Sean reviews the evidence now sitting in `runs/`. Headline for that review:
   **Amici is invisible for "preschool near me" at its own front door (0/49
   map-pack) while dominating "trilingual preschool"** — a probable GBP
   primary-category fix for Stella.
2. **Card #3 (optional upgrade, not a blocker anymore).** Enabling billing on
   the Places key's project lets capsules 1+2 re-run on the steadier paid path:
   ```bash
   cd ~/parlami-skills/zona/scripts
   python3 geogrid_tracker.py --school beibei --test-call --confirm
   python3 visibility_snapshot.py --school beibei --confirm
   python3 visibility_snapshot.py --school amici  --confirm
   ```
   (~500 calls ≈ $16 list price, expected $0 under Google's monthly free tier.)
