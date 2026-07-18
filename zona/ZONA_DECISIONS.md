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

**Status:** WAITING ON SEAN. Per the build rules, nothing citation-related
gets built until this is decided.

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

**Status:** WAITING ON SEAN. SKILL.md is untouched in the meantime.
