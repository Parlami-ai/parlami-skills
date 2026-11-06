#!/usr/bin/env python3
"""Offline test for luciano_dashboard_bridge.py: no network, no claude, no buzz.

Fakes the outside legs (the Claude CLI, the OpenClaw gateway and the Buzz CLI) and checks that
a question flows comment -> Buzz -> answer -> CSV row exactly once, that
re-running changes nothing, and that nothing uploads without --publish.
Run it before trusting any change to the bridge:  python3 test_bridge_offline.py
"""

import json
import tempfile
from pathlib import Path

import luciano_dashboard_bridge as b

# Verify actual subprocess environment, not only the wrapper's arguments.
import os
from unittest.mock import patch
with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "synthetic-test", "ANTHROPIC_AUTH_TOKEN": "synthetic-test"}):
    with patch.object(b.subprocess, "run") as child:
        child.return_value.returncode = 0
        child.return_value.stdout = '{"result":"[]"}'
        assert b.claude_headless({"CLAUDE_BIN": "claude"}, "read only") == []
        child_env = child.call_args.kwargs["env"]
        assert "ANTHROPIC_API_KEY" not in child_env
        assert "ANTHROPIC_AUTH_TOKEN" not in child_env
        assert os.environ["ANTHROPIC_API_KEY"] == "synthetic-test"

# ---- pure helpers -----------------------------------------------------------

env = b.parse_env_file('# comment\nDASHBOARD_URL="https://claude.ai/code/artifact/x"\nBUZZ_CHANNEL_ID=abc \n\nBAD LINE\n')
assert env == {"DASHBOARD_URL": "https://claude.ai/code/artifact/x", "BUZZ_CHANNEL_ID": "abc"}, env

assert b.extract_json('Here you go:\n```json\n[{"a": 1}]\n```\nDone.') == [{"a": 1}]
assert b.extract_json('{"result": "[]"}') == {"result": "[]"}
assert b.extract_json("no json here") is None
assert b.extract_json("") is None

assert b.slugify("From visit to enrollment · last 4 weeks") == "from-visit-to-enrollment-last-4-weeks"
assert b.slugify("Luciano's read: what to do about it") == "luciano-s-read-what-to-do-about-it"

base_env = {
    "DASHBOARD_URL": "https://claude.ai/code/artifact/x",
    "DASHBOARD_STORE_URL": "https://claude.ai/artifact/y",
    "BUZZ_CHANNEL_ID": "chan-1",
    "BUZZ_SELF_PUBKEY": "AAAA",
    "BUZZ_NAMES": "bbbb=Luciano,cccc=Sean",
    "HOME": "/nowhere",
}
# default transport is the gateway on this box
oc = b.load_config(env_path=None, environ={**base_env, "OPENCLAW_URL": "http://127.0.0.1:18789",
                                             "OPENCLAW_TOKEN_ENV": "OPENCLAW_BRIDGE_TEST_TOKEN",
                                             "OPENCLAW_BRIDGE_TEST_TOKEN": "t0k", "OPENCLAW_AGENT": "parlami"})
assert oc["LUCIANO_TRANSPORT"] == "openclaw"
assert b.check_config(oc) == [], b.check_config(oc)
assert b.chat_completions_url("http://127.0.0.1:18789") == "http://127.0.0.1:18789/v1/chat/completions"
assert b.chat_completions_url("https://spark.example.ts.net/v1/") == "https://spark.example.ts.net/v1/chat/completions"
assert b.is_gateway_url("http://localhost:18789") and b.is_gateway_url("https://x.ts.net")
assert not b.is_gateway_url("http://plain.example.com") and not b.is_gateway_url("")

bad = dict(oc, OPENCLAW_URL="http://plain.example.com", OPENCLAW_TOKEN_ENV="lower", OPENCLAW_AGENT="bad agent!")
assert len(b.check_config(bad)) == 3, b.check_config(bad)
echo_bad = dict(oc, BUZZ_ECHO="1", BUZZ_CHANNEL_ID="")
assert b.check_config(echo_bad) == ["BUZZ_ECHO is on but BUZZ_CHANNEL_ID is empty"], b.check_config(echo_bad)

# the older Buzz route still configures
cfg = b.load_config(env_path=None, environ={**base_env, "LUCIANO_TRANSPORT": "buzz"})
assert b.check_config(cfg) == [], b.check_config(cfg)

# own-message detection: by pubkey, or by the marker when no pubkey is configured
assert b.is_own_message(cfg, {"pubkey": "aaaa", "content": "anything"})
assert b.is_own_message({}, {"pubkey": "zzzz", "content": f"  {b.BRIDGE_MARKER} Dashboard question"})
assert not b.is_own_message(cfg, {"pubkey": "bbbb", "content": "The dip is seasonal."})

assert b.answerer_name(cfg, "cccc") == "Sean"
assert b.answerer_name(cfg, "bbbb") == "Luciano"
assert b.answerer_name(cfg, "unknown") == "Luciano"

thread = b.normalize_thread({"thread_id": "t1", "card_title": "Tours booked per week", "card_key": None,
                             "question": "Why did October dip?", "asked": "2026-11-04T10:00:00Z", "author": "Ana"})
assert thread["card_key"] == "tours-booked-per-week" and thread["asked"] == "2026-11-04", thread
assert b.normalize_thread({"thread_id": "t2"}) is None  # no question -> unusable

msg = b.render_question(thread)
assert msg.startswith(b.BRIDGE_MARKER) and "Why did October dip?" in msg and "both schools" in msg

root = "ev-root"
msgs = [
    {"id": root, "content": msg, "pubkey": "aaaa", "created_at": 1},
    {"id": "ev-2", "content": "   ", "pubkey": "bbbb", "created_at": 2},
    {"id": "ev-3", "content": "October is the half-term dip; the same happened last year.", "pubkey": "bbbb", "created_at": 3},
    {"id": "ev-4", "content": "A later follow-up that must not be published.", "pubkey": "cccc", "created_at": 4},
]
picked = b.pick_answer(cfg, root, msgs)
assert picked["answer"].startswith("October is") and picked["answered_by"] == "Luciano", picked
assert b.pick_answer(cfg, root, msgs[:2]) is None

# ---- the whole run, with both outside legs faked --------------------------

calls = {"claude": [], "buzz": []}


def fake_run_cmd(args, stdin_text=None, env=None, timeout=0, unset_env=()):
    if args[0] == "claude":
        calls["claude"].append(stdin_text)
        if "ArtifactComments" in stdin_text:
            return json.dumps({"result": json.dumps([
                {"thread_id": "t1", "card_title": "Tours booked per week", "card_key": "tours-booked-per-week",
                 "question": "Why did October dip?", "asked": "2026-11-04", "author": "Ana", "resolved": False},
                {"thread_id": "t9", "card_title": "Year by year", "card_key": "year-by-year",
                 "question": "old one", "asked": "2026-10-01", "resolved": True},
            ])})
        return json.dumps({"result": '{"ok": true, "asset_url": "/_blob/new", "version": 3}'})
    if args[0] == "buzz":
        calls["buzz"].append(args)
        if args[1:3] == ["messages", "send"]:
            assert "--content" in args and "-" in args and "Why did October dip?" in stdin_text
            return json.dumps({"accepted": True, "event_id": root})
        if args[1:3] == ["messages", "thread"]:
            return json.dumps(msgs if calls["buzz_answered"] else msgs[:1])
    raise AssertionError(f"unexpected command {args}")


calls["buzz_answered"] = False
b.run_cmd = fake_run_cmd
cfg["CLAUDE_BIN"], cfg["BUZZ_BIN"] = "claude", "buzz"

with tempfile.TemporaryDirectory() as tmp:
    state = b.State(tmp)

    # run 1: the question is read and posted; no answer yet; nothing written.
    assert b.hop_read(cfg, state, dry_run=False) == 1
    assert "t9" not in state.threads  # resolved before we saw it: handled by hand
    assert b.hop_ask(cfg, state, dry_run=False) == 1
    assert state.threads["t1"]["buzz_event"] == root
    assert b.hop_collect(cfg, state, dry_run=False) == 0
    assert not state.csv_path.exists()
    assert b.hop_publish(cfg, state, publish=True, dry_run=False) == 0

    # run 2: Luciano replied. One row lands in the CSV; still no upload without --publish.
    calls["buzz_answered"] = True
    b.hop_read(cfg, state, dry_run=False)
    assert b.hop_ask(cfg, state, dry_run=False) == 0  # not posted twice
    assert b.hop_collect(cfg, state, dry_run=False) == 1
    rows = state.csv_rows()
    assert rows == [{"card_key": "tours-booked-per-week", "question": "Why did October dip?", "asked": "2026-11-04",
                     "answer": "October is the half-term dip; the same happened last year.",
                     "answered_by": "Luciano", "school": ""}], rows
    n_claude = len(calls["claude"])
    assert b.hop_publish(cfg, state, publish=False, dry_run=False) == 0
    assert len(calls["claude"]) == n_claude  # draft-only: the CLI was not asked to upload

    # run 3: --publish uploads once, and a fourth run uploads nothing again.
    assert b.hop_publish(cfg, state, publish=True, dry_run=False) == 1
    assert state.data["uploaded_rows"] == 1
    assert "card_answers" in calls["claude"][-1] and str(state.csv_path) in calls["claude"][-1]
    assert b.hop_collect(cfg, state, dry_run=False) == 0
    assert b.hop_publish(cfg, state, publish=True, dry_run=False) == 0
    assert len(state.csv_rows()) == 1

    # state survives a restart (a fresh cron process)
    again = b.State(tmp)
    assert again.threads["t1"]["row_written"] and again.data["uploaded_rows"] == 1

    # a CSV with commas and quotes in the answer still parses back to the same text
    again.append_row({"card_key": "k", "question": 'She asked, "why?"', "asked": "2026-11-05",
                      "answer": "Because, simply, it works.\nSecond line.", "answered_by": "Sean", "school": "A"})
    assert again.csv_rows()[-1]["answer"] == "Because, simply, it works.\nSecond line."
    assert again.csv_rows()[-1]["question"] == 'She asked, "why?"'

    # dry-run touches nothing
    fresh = b.State(tmp + "/dry")
    b.hop_read(cfg, fresh, dry_run=True)
    assert fresh.threads == {} and not fresh.path.exists()

# ---- the default route: one gateway call, answer kept, one-way echo ---------

import io
import urllib.request

gateway = {"calls": []}


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def fake_urlopen(req, timeout=0):
    body = json.loads(req.data.decode())
    gateway["calls"].append({"url": req.full_url, "headers": dict(req.header_items()), "body": body})
    assert "user" not in body  # fresh gateway session every call
    text = "OK" if body["messages"][-1]["content"] == "ping" else "October is the half-term dip; last year did the same."
    return FakeResponse(json.dumps({"choices": [{"message": {"content": text}}]}).encode())


urllib.request.urlopen = fake_urlopen
oc["CLAUDE_BIN"], oc["BUZZ_BIN"], oc["BUZZ_ECHO"] = "claude", "buzz", "1"
calls["buzz"] = []

with tempfile.TemporaryDirectory() as tmp:
    state = b.State(tmp)
    assert b.hop_read(oc, state, dry_run=False) == 1
    assert b.hop_ask(oc, state, dry_run=False) == 1
    call = gateway["calls"][-1]
    assert call["url"] == "http://127.0.0.1:18789/v1/chat/completions", call["url"]
    assert call["body"]["model"] == "openclaw:parlami"
    assert call["headers"].get("X-openclaw-agent-id") == "parlami", call["headers"]
    assert call["headers"].get("Authorization") == "Bearer t0k"
    assert "Why did October dip?" in call["body"]["messages"][-1]["content"]
    t = state.threads["t1"]
    assert t["answer"].startswith("October is") and t["answered_by"] == "Luciano" and t["buzz_event"] == "openclaw"

    assert b.hop_collect(oc, state, dry_run=False) == 1
    assert state.csv_rows()[0]["answer"] == "October is the half-term dip; last year did the same."
    assert b.hop_echo(oc, state, dry_run=False) == 1
    sent = [c for c in calls["buzz"] if c[1:3] == ["messages", "send"]]
    assert len(sent) == 1 and "--reply-to" not in sent[0]
    # a second pass asks, records and echoes nothing again
    assert b.hop_ask(oc, state, dry_run=False) == 0
    assert b.hop_collect(oc, state, dry_run=False) == 0
    assert b.hop_echo(oc, state, dry_run=False) == 0
    assert len(gateway["calls"]) == 1
    # echo off: nothing posted to Buzz at all
    quiet = dict(oc, BUZZ_ECHO="0")
    s2 = b.State(tmp + "/quiet")
    b.hop_read(quiet, s2, dry_run=False); b.hop_ask(quiet, s2, dry_run=False); b.hop_collect(quiet, s2, dry_run=False)
    assert b.hop_echo(quiet, s2, dry_run=False) == 0 and len(calls["buzz"]) == 1
    # draft-only still holds on this route
    assert b.hop_publish(oc, state, publish=False, dry_run=False) == 0

print("bridge offline test: all checks passed")
