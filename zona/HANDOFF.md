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
| 1 | Geo-grid rank tracker | 🟡 BUILT + ran both schools, but on the **free Google-Maps-scrape** (`--provider curl`), NOT the specified Places API — see card #4; `runs/*-geogrid-*.md` |
| 2 | Visibility snapshot | 🟡 BUILT + ran 4 keywords both schools, same scrape path (not Places API — card #4); `runs/*-visibility-snapshot.md` |
| 3 | Location-page relevance check | ✅ DONE — run live both schools; evidence in `runs/*-page-signals.md` (Architetto) |
| 4 | Citations/NAP audit | ✅ DONE — card #1 approved 2026-07-18; built + run live both schools; evidence in `runs/*-citations.md` (Catena) |

Decision cards: #1 ✅ approved+built, #2 ✅ approved+done (SKILL.md now
matches the read-only lane), #3 ⏳ the Places-API path Sean was asked to
unblock (needs his Google console click — agent has no session into his
account), #4 ⏳ NEW — was it OK to run capsules 1+2 on a free Maps scrape
instead of waiting for card #3? (method substitution, ToS-adjacent).

⚠️ **Two automated loops committed to this single branch today** (this Zona
loop + a parallel Luciano loop). No work was lost, but they swept each other's
uncommitted files into mislabeled commits (e.g. `citations_audit.py` landed in
a commit titled "capsule 1"). Recommend not running both concurrently on one
branch — either can revert the other between a read and a write.

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

All four measurement capsules have code + saved output, and cards #1/#2 are
fully done. But capsules 1+2 are **done-with-an-open-decision, not a clean ✅**:
they ran on a free Google-Maps scrape, not the Places API the task specified.
So the build loop's STOP condition is *effectively* met, pending three things
that are all Sean's to decide:

1. **Card #4 (method): accept the scraped data, or re-run on Places?** The task
   said "Places API … (no paid SERP APIs; if needed → decision card)." Both
   keys were blocked, which correctly fired card #3. A parallel loop then routed
   *around* the block by scraping Google Maps. That data is usable and free, but
   it's noisier (ranks wobble ±1-3 run-to-run) and ToS-adjacent. Sean picks:
   keep the scrape as the method, or clear card #3 and re-run on Places for
   steadier numbers.
2. **Card #3 (the approved path):** enable billing on the Places key's project
   (or add Places API to key 2). Then capsules 1+2 re-run cleanly:
   ```bash
   cd ~/parlami-skills/zona/scripts
   python3 geogrid_tracker.py --school beibei --test-call --confirm
   python3 visibility_snapshot.py --school beibei --confirm
   python3 visibility_snapshot.py --school amici  --confirm
   ```
   (~500 calls ≈ $16 list price, expected $0 under Google's monthly free tier.)
3. **Evidence review → unblock synthesis.** Per the loop spec, synthesis (a
   combined findings report + Bussola correlation) must not start until Sean
   reviews the evidence in `runs/`. Keep that review to measured facts — one
   clean pattern to look at, stated without a proposed cause (diagnosis IS the
   deferred synthesis): **Amici tops "trilingual preschool" (rank 1 at 49/49
   grid points) but for the generic "preschool near me" is in the top-3 map
   pack at 0/49 points — though still visible in the top 20 at 14/49, best
   rank 5.** What that means and who fixes it is Sean's synthesis call, not a
   finding to assert here.
