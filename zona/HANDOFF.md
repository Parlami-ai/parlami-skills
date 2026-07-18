# Zona Build — Handoff

**Updated:** 2026-07-18 (after cycle 3 of the build loop)

## Where we are

Activating Zona (agent #14) as a READ-ONLY local-SEO auditor/tracker for the
legacy swarm (Beibei Amigos + Amici). Repo: `~/parlami-skills/zona/`.
Never touches parlami-ads-saas; never writes to GBP/website/citations.

Capsules (from `~/loops/zona-loop.md`):

| # | Capsule | State |
|---|---------|-------|
| 0 | Foundation check | ✅ DONE — see ZONA_PROGRESS.md |
| 1 | Geo-grid rank tracker | 🟡 BUILT + offline-tested; live run blocked on Decision Card #3 (Google key) |
| 2 | Visibility snapshot | 🟡 BUILT + offline-tested; blocked on same card |
| 3 | Location-page relevance check | ⬜ next up — needs no Google key, can run live |
| 4 | Citations/NAP audit | ✅ gated by design — Decision Card #1 written, nothing built |

## Key facts a fresh session needs

- Schools: Beibei = 751 E Union Hills Dr, Phoenix AZ 85024 (33.6617, -112.0694);
  Amici = 1244 E Chandler Blvd, Phoenix AZ 85048 (33.3062, -111.9822).
  Hard-coded (public info) in `scripts/geogrid_tracker.py` SCHOOLS dict.
- Both Google keys in `~/.bashrc` are blocked server-side (billing / API
  restrictions) — details + fix in ZONA_DECISIONS.md card #3. Read keys from
  env at runtime only; never write them to files.
- Offline tests: `cd zona/scripts && python3 test_geogrid_offline.py` (plus an
  inline stub test for the snapshot — pattern is: monkeypatch
  `geogrid_tracker.get_json`).
- Reusable prior art: full Zona Engine at `~/clawd/agents/zona/engine/`
  (citations/pages/competitors modules — relevant if card #1 approves audits);
  audit-scoring ideas in `~/projects/maps-reputation-agent/src/auditEngine.js`.
- Commits are local-only (no push), one per capsule, on the repo's single
  branch.

## Single next step

Build capsule 3: read-only crawl of both schools' websites flagging missing
local signals (area names, map embed, LocalBusiness schema, service keywords),
output → `zona/runs/` + findings framed as evidence for Architetto's queue.
Then run it for real for both schools (no key needed) and commit.

After capsule 3: STOP per loop spec — synthesis phase needs Sean's review.
Sean gates pending: Decision Cards #1–#3 in ZONA_DECISIONS.md.
