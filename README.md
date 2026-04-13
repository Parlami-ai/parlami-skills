# 📣 Parlami.ai — Agent Skills Library

> The AI marketing team for schools. Drop in your API keys. Get more enrollments.

Parlami replaces a $1,000–$2,000/month marketing agency with a 15-agent AI swarm that runs 24/7 — optimizing Google Ads, SEO, social media, email, reviews, content, and more.

**These skill files are the brain of each agent.** They define what each agent knows, what it does, and how it does it.

---

## 🤖 The 15-Agent Team

| Agent | Emoji | Role |
|-------|-------|------|
| [Annunci](./annunci/SKILL.md) | 📣 | Google Ads — the revenue engine, tip of the spear |
| [Spia](./spia/SKILL.md) | 🕵️ | SEO intelligence — GSC, keyword research, content gaps |
| [Musa](./musa/SKILL.md) | 🎨 | Creative engine — images, graphics, ad assets |
| [Architetto](./architetto/SKILL.md) | 🏗️ | Website architecture — speed, UX, conversion optimization |
| [Bussola](./bussola/SKILL.md) | 🧭 | Analytics — GA4, attribution, ROI dashboard |
| [Zona](./zona/SKILL.md) | 📍 | Local SEO — Google Business Profile, GeoGrid rankings |
| [Stella](./stella/SKILL.md) | ⭐ | Reviews — GMB reputation, review generation |
| [Catena](./catena/SKILL.md) | ⛓️ | Digital PR — backlinks, HARO, domain authority |
| [Penna](./penna/SKILL.md) | 🖊️ | Content — blog posts, landing pages, SEO writing |
| [Piazza](./piazza/SKILL.md) | 🏛️ | Social media — organic posts, community management |
| [Faccia](./faccia/SKILL.md) | 😄 | Facebook & Meta Ads — targeting, retargeting |
| [Lettera](./lettera/SKILL.md) | ✉️ | Email — nurture sequences, tour follow-ups |
| [Portale](./portale/SKILL.md) | 🚪 | Funnel optimization — CRO, form conversion |
| [Regista](./regista/SKILL.md) | 🎬 | Video — ads, Reels, testimonials |
| [Luciano](./parlami/SKILL.md) | 🎯 | Orchestration — strategy, coordination, reporting |

---

## 🚀 Quick Start — New Client in 30 Minutes

See [ONBOARDING.md](./ONBOARDING.md) for the complete setup guide.

**Short version:**
1. Copy `client.config.example.yml` → `client.config.yml`
2. Fill in all `{{CLIENT_*}}` variables
3. Drop in Google Ads, GA4, Airtable API keys
4. Run the first daily report

---

## 🏗️ Architecture

```
parlami-skills/
├── README.md               ← You are here
├── ONBOARDING.md           ← New client setup guide
├── client.config.example.yml  ← Template for client variables
├── annunci/
│   ├── SKILL.md            ← Agent brain (instructions + workflows)
│   └── scripts/            ← Python/bash automation scripts
├── spia/
│   └── SKILL.md
├── musa/
│   └── SKILL.md
... (all 15 agents)
```

---

## 💡 How It Works

Each `SKILL.md` is loaded into an AI agent session at startup. The agent reads it, becomes that specialist, and executes its workflows autonomously.

**The loop:**
- Agents run on a schedule (daily, weekly, monthly)
- They pull live data from APIs (Google Ads, GA4, GMB, Airtable)
- They take actions within their role
- Anything that touches the public (posting, publishing, changing budgets) goes to an **Approval Queue** first
- A human clicks approve. Then it goes live.

**You stay in control. The agents do the work.**

---

## 🔑 Variables Reference

All `{{VARIABLE}}` placeholders in the skill files are replaced with real values from `client.config.yml` when onboarding a new client.

Key variables:
- `{{SCHOOL1_NAME}}` / `{{SCHOOL2_NAME}}` — Your school names
- `{{CLIENT_WEBSITE}}` — Primary website
- `{{GOOGLE_ADS_CUSTOMER_ID}}` — Your Google Ads account
- `{{GA4_PROPERTY_ID_SCHOOL1}}` — Google Analytics 4 property
- `{{AIRTABLE_BASE_ID}}` — Airtable campaign planning base

Full reference: [client.config.example.yml](./client.config.example.yml)

---

## 📐 The Franchise Rule

> Every agent's identity, tasks, and workflows are codified into portable `SKILL.md` files. The system spins up for a new client by dropping in their API keys and config. No hardcoded logic. No rebuilding from scratch.

This is how Parlami scales to 100+ schools.

---

## 🛡️ What Agents Can't Do Without Human Approval

- Publish blog posts
- Post to social media
- Change Google Ads budgets or bids
- Send emails to parents
- Respond to reviews
- Purchase anything

Everything outbound requires a human click in the Approval Queue.

---

## 📬 Built by Parlami.ai

Questions? Reach out at [parlami.ai](https://parlami.ai)

*Replacing $1K/month agencies, one school at a time.*
