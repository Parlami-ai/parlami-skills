# 🚀 Onboarding a New Client — 30-Minute Setup Guide

This guide walks you through setting up Parlami for a new school client.

---

## Step 1: Gather Client Info (10 min)

Before touching anything, collect:

### School Information
- [ ] School name(s) — legal name + common name
- [ ] Physical address(es)
- [ ] Phone number(s)
- [ ] Website URL(s)
- [ ] Programs offered (ages, curriculum, languages)
- [ ] Target neighborhoods / zip codes
- [ ] Key differentiators (what makes them unique?)
- [ ] Tuition range (helps set audience targeting)

### Logins & API Access
- [ ] Google Ads account ID (10-digit number)
- [ ] Google Analytics 4 property ID
- [ ] Google Business Profile (GMB) access
- [ ] Google Search Console access
- [ ] WordPress login (if applicable)
- [ ] Airtable account (or create one)
- [ ] Existing social media accounts

---

## Step 2: Create Client Config (5 min)

Copy the template and fill in all variables:

```bash
cp client.config.example.yml clients/{{CLIENT_SLUG}}.config.yml
```

Edit `clients/{{CLIENT_SLUG}}.config.yml` with real values.

> Every `{{VARIABLE}}` in the skill files maps to a key in this config.

---

## Step 3: Connect APIs (10 min)

### Google Ads
1. Client shares Manager Account access (or add as admin)
2. Add to `.env`: `GOOGLE_ADS_CUSTOMER_ID`, `GOOGLE_ADS_DEVELOPER_TOKEN`
3. Test: `python scripts/test_google_ads_connection.py`

### Google Analytics 4
1. Client adds service account as Viewer in GA4
2. Service account: `~/.openclaw/secrets/google-service-account.json`
3. Add property IDs to config

### Airtable
1. Create new Airtable base from template (link TBD)
2. Add `AIRTABLE_API_TOKEN` to `.env`
3. Copy base IDs to config

### Google Business Profile
1. Request Manager access via GMB dashboard
2. Note the location ID (from GMB API or URL)

---

## Step 4: Configure Agent Skill Files (5 min)

Run the config substitution script:

```bash
python scripts/configure_client.py --config clients/{{CLIENT_SLUG}}.config.yml
```

This replaces all `{{VARIABLE}}` placeholders in skill files with real values and outputs to `clients/{{CLIENT_SLUG}}/`.

---

## Step 5: First Run

### Annunci (Google Ads)
1. Audit existing campaigns: `python clients/{{CLIENT_SLUG}}/annunci/scripts/audit.py`
2. Pull conversion tracking status
3. Review first daily report

### Spia (SEO)
1. Connect Google Search Console
2. Pull 90-day keyword performance baseline
3. Identify top 10 keyword opportunities

### Bussola (Analytics)
1. Verify GA4 is receiving data
2. Pull 30-day traffic baseline
3. Set up conversion events if missing

---

## Checklist: Go-Live Requirements

Before any agent takes action:

- [ ] Conversion tracking verified (GA4 ↔ Google Ads)
- [ ] Google Ads campaigns reviewed and understood
- [ ] Approval Queue set up (Airtable)
- [ ] Client briefed on approval flow
- [ ] Emergency pause procedure confirmed (who to call if something goes wrong)

---

## The Approval Queue

**Nothing goes live without client approval.**

All agent actions that touch the public are staged as **Drafts** in Airtable:

| Action Type | Who Creates | Who Approves |
|-------------|-------------|--------------|
| Blog post | Penna | Client |
| Social post | Piazza | Client |
| GMB post | Stella | Client |
| Ad copy change | Annunci | Client |
| Email campaign | Lettera | Client |
| Budget change | Annunci | Client (+ budget limit) |

Client approves with one click. Agent executes immediately after approval.

---

## Support

Built with ❤️ by Parlami.ai  
Questions: parlami.ai
