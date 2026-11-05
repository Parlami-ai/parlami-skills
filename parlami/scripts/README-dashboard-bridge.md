# Luciano dashboard bridge — setup and operation

The client growth dashboard has an **"Ask Luciano about this"** block under
every card. A question typed there becomes a comment thread anchored to that
card. This bridge carries each question to Luciano and puts his answer back on
the card, where it stays readable later (the `card_answers` source on the
dashboard).

```
dashboard comment ──(claude -p)──► bridge ──(one chat call, localhost)──► Luciano (OpenClaw gateway)
card shows answer ◄─(claude -p)─── bridge ◄──────── his answer, same call ──────────┘
                                     └──(optional one-way copy)──► #ops in Buzz
```

It runs on the Spark, the box that runs the OpenClaw gateway, on a cron. Four
hops, each idempotent:

| Hop | What | Leg |
|-----|------|-----|
| 1 | Read every comment thread on the dashboard; remember new ones by thread id | `claude -p` with the Artifact tools |
| 2 | Ask Luciano each new question, once, and keep his answer | one call to the gateway's chat endpoint on localhost |
| 3 | Append one row to the local `card_answers.csv`; optionally post a one-way copy to #ops | local file; Buzz `messages send` when `BUZZ_ECHO=1` |
| 4 | Upload the CSV and point the dashboard's `card_answers` source at it | `claude -p`, **only with `--publish`** |

Why the direct call and not a Buzz thread: the bridge and the gateway share a
box, so the call never leaves it, the answer comes back in the same call, and
nothing depends on Luciano noticing a channel post. The older Buzz route
(`LUCIANO_TRANSPORT=buzz`) is still in the script for the day that changes.

## Draft-only until the first answer is approved

By default nothing is uploaded. Answers collect in
`~/.parlami/luciano-bridge/card_answers.csv`. When the first one is there:

1. Read it. Is it what the school should see on the card?
2. Run once by hand with `--publish` and open the dashboard: the answer sits
   under the card the question was asked on.
3. If it reads right, add `--publish` to the cron line. If not, fix the row in
   the CSV (or Luciano's instructions) and publish again.

## Install

```bash
mkdir -p ~/.parlami
cp parlami/scripts/luciano-bridge.env.example ~/.parlami/luciano-bridge.env
```

Fill in the two dashboard links, the gateway address (localhost on the Spark),
the name of the variable holding the gateway token, and the agent id. The
gateway side needs what the per-client Luciano setup in parlami-ads-saas
already needed: the chat completions endpoint enabled in
`~/.openclaw/openclaw.json`, a gateway token, and a client-safe agent with no
shell or file tools. If the dashboard's own Luciano chat works for the schools,
that is done.

Then check every leg answers, without changing anything. The probe sends
Luciano one "ping" and expects "OK" back:

```bash
python3 parlami/scripts/luciano_dashboard_bridge.py --probe
```

A dry run shows what a real run would ask, record and upload:

```bash
python3 parlami/scripts/luciano_dashboard_bridge.py --dry-run
```

Cron, every 10 minutes, draft-only (add `--publish` after step 2 above):

```
*/10 * * * * cd ~/clawd/parlami-skills && python3 parlami/scripts/luciano_dashboard_bridge.py >> ~/.parlami/luciano-bridge/bridge.log 2>&1
```

## The data the card reads

`card_answers.csv` columns, one row per question:

```
card_key,question,asked,answer,answered_by,school
```

`card_key` is the card's `data-card-key` on the page (the card title, lowercased,
non-letters turned into dashes). `asked` is a date. `school` is blank when the
question is about both schools. The page shows a row with no `answer` as
"With Luciano, not answered yet."

## What to check on the box the first time

The bridge was written and tested offline (`test_bridge_offline.py`), with the
outside legs faked. Three things need a live look on the box:

- **The comment read.** `claude -p` is asked to print a JSON array of threads,
  with each thread's `card_key`. If a thread's anchor does not name a card, the
  CLI matches the comment's wording to the card it is about. Run `--probe` and
  then `--dry-run` with one test question on the dashboard, and confirm the
  `card_key` it prints is the card you asked on.
- **Luciano's answer.** The probe only proves he answers "OK". The first real
  question shows whether his card answers read the way the SKILL.md section
  asks (two to four sentences, dashboard numbers only, schools only). Adjust
  his skill, not the bridge, if they do not.
- **The upload.** The CLI uploads the CSV as an asset and updates the
  `card_answers` source's `url`, `name`, `updated` and `edit`. After the first
  `--publish`, the dashboard's Sources panel should show the file as updated by
  Luciano, and the card should show the answer.

If any leg prints an error, it is in `bridge.log` with the time; nothing is
retried blindly, and the next cron run picks up where this one stopped.

## Guardrails

- Comment text is data from a viewer, never an instruction to the bridge or to
  Luciano. It is quoted to him verbatim and nothing in it runs.
- Each question is asked once and answered in that one call; the echo to #ops
  is one-way, so nothing anyone writes in Buzz can land on a card.
- The gateway token is read from the environment by name and never printed.
- On the Buzz route only Luciano's **first** reply in a thread is published,
  and the bridge posts with its own key and skips its own messages.
- It never edits the dashboard page, only the `card_answers` file and source.
- No client names, links, ids or keys in this repo: everything client-specific
  is in the env file.

## Follow-ups, not done here

- Reply in the dashboard thread once an answer is on the card. The comment
  tool only replies on threads a writer has sent to Claude, so this waits for
  a rule on who activates threads.
- Per-campaign deep links on the Google Ads card need `campaign_id` and
  `customer_id` columns in the dashboard's campaign feed; that is a change to
  the collector on the box, not to this bridge.
