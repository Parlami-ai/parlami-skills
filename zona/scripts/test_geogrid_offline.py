#!/usr/bin/env python3
"""Offline end-to-end test for geogrid_tracker.py.

Stubs the Google Places HTTP layer with deterministic fake responses so the
whole pipeline (grid → per-point ranking → JSON + findings output) can be
verified without an API key or network. No live calls, no cost.
"""

import json
import tempfile
from pathlib import Path

import geogrid_tracker as gt

SCHOOL = gt.SCHOOLS["beibei"]
FAKE_PLACE_ID = "fake-beibei-place-id"


def fake_get_json(url, params):
    if url == gt.PLACES_FINDPLACE:
        return {"status": "OK", "candidates": [{
            "place_id": FAKE_PLACE_ID,
            "name": SCHOOL["name"],
            "formatted_address": SCHOOL["address"],
        }]}
    # Nearby Search: rank depends on distance from school — closer = better.
    lat, lng = map(float, params["location"].split(","))
    dist = abs(lat - SCHOOL["lat"]) * 69.0 + abs(lng - SCHOOL["lng"]) * 54.6
    rank = min(1 + int(dist / 0.9), 25)  # rank 1 at center, worse farther out
    results = [{"place_id": f"competitor-{i}", "name": f"Competitor {i}"}
               for i in range(1, rank)]
    results.insert(rank - 1, {"place_id": FAKE_PLACE_ID, "name": SCHOOL["name"]})
    return {"status": "OK", "results": results[:25]}


def main():
    gt.get_json = fake_get_json

    cand = gt.resolve_place_id(SCHOOL, "fake-key")
    assert cand["place_id"] == FAKE_PLACE_ID, "place_id resolution broken"

    points = gt.generate_grid(SCHOOL["lat"], SCHOOL["lng"], 3.0, 7)
    assert len(points) == 49

    for p in points:
        rank, n, top3 = gt.rank_at_point(p, "preschool near me", FAKE_PLACE_ID,
                                         SCHOOL["name"], "fake-key", 3000)
        p["rank"], p["results_returned"], p["top3"] = rank, n, top3

    center = next(p for p in points if p["row"] == 3 and p["col"] == 3)
    corner = next(p for p in points if p["row"] == 0 and p["col"] == 0)
    assert center["rank"] == 1, f"center should rank 1, got {center['rank']}"
    assert corner["rank"] is None or corner["rank"] > center["rank"], \
        "corner should rank worse than center"

    md = gt.findings_text(SCHOOL, "preschool near me", points, 7)
    assert "Beibei" in md and "top 3" in md and "```" in md

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "test.json"
        out.write_text(json.dumps({"points": points}, indent=2))
        loaded = json.loads(out.read_text())
        assert len(loaded["points"]) == 49

    print("OFFLINE E2E OK — grid 49 pts, center rank 1, corner rank",
          gt.rank_label(corner["rank"]), "— findings + JSON round-trip verified")
    print()
    print(gt.grid_ascii(points, 7))


if __name__ == "__main__":
    main()
