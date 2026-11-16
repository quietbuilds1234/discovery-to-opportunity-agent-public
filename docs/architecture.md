# Architecture Overview

Initial architecture for the Discovery-to-Opportunity Agent. This document describes the intended design for a lightweight interview demo. It distinguishes planned components from what is implemented today.

**Status:** Foundation only. No Skill runtime, Salesforce write path, or data loaders are implemented yet.

---

## Design Intent

Build a conversational Claude Skill that orchestrates:

1. Meeting intelligence intake
2. Salesforce CRM context retrieval
3. Opportunity proposal + MEDDPICC enrichment
4. Duplicate / gap analysis
5. Explicit human-approved Salesforce writes

Optimize for a credible live demo within a short interview assignment. Prefer Skill-native orchestration and standard Salesforce objects over custom infrastructure.

---

## System Context

```text
┌─────────────────────────────────────────────────────────────┐
│ Rep in Claude                                               │
│  └─ Discovery-to-Opportunity Skill                          │
│       ├─ SKILL.md + references (decision, MEDDPICC, fields) │
│       ├─ Meeting source                                     │
│       │    ├─ Granola (if verified at runtime)              │
│       │    └─ Synthetic fixtures (demo / fallback)          │
│       └─ Salesforce runtime connection (TBD / to validate)  │
│            └─ Account, Contact, Opportunity, Task, OCR      │
└─────────────────────────────────────────────────────────────┘

Local development (not Claude runtime):
  Salesforce CLI (alias: discovery-dev)
    └─ Seed / inspect synthetic org data via scripts (planned)
```

### Important Boundary

Local Salesforce CLI authentication does **not** automatically provide Salesforce access to Claude at runtime. The Skill must use a supported Salesforce runtime connection for live CRM reads and writes. Until that connection is chosen and tested, treat CRM write capability as planned.

---

## Component Responsibilities

| Component | Responsibility | Status |
|---|---|---|
| Claude Skill (`skill/discovery-to-opportunity/`) | Conversation UX, orchestration, preview, approval gate | Planned |
| Skill references | Decision outcomes, MEDDPICC rules, field mapping | Planned |
| Meeting fixtures (`data/granola_meetings.json`) | Repeatable discovery inputs when Granola is unavailable | Planned |
| Synthetic CRM data (`data/*.json`) | Demo Accounts, Contacts, Opps, Tasks, OCRs | Planned |
| Salesforce org | Source of truth for CRM state in the demo | Assumed available via `discovery-dev` |
| Load scripts (`scripts/load_salesforce_data/`) | Push synthetic data into the Developer Org | Planned |
| Custom backend / custom MCP | — | **Out of scope** |

---

## Core Runtime Flow

```text
1. Skill start (post-discovery)
2. Load meeting context (Granola or labeled fixture)
3. Resolve Account + Contacts
4. Read Salesforce context (Account, Contacts, Opps, Tasks, OCRs)
5. Duplicate / existing Opportunity check
6. Joint analysis: meeting + CRM history
7. Map fields → Opportunity draft
8. MEDDPICC assessment (Confirmed | Inferred | Unknown | At Risk)
9. Present preview + gaps + follow-up questions + warnings
10. Rep answers, skips, proceeds, or declines
11. Validate Salesforce-required fields
12. Explicit approval
13. Create Opportunity (+ Opportunity Contact Roles if approved)
14. Return record Id + link
```

Writes occur only after step 12.

---

## Decision Outcomes (Architecture View)

| Outcome | Agent behavior | Blocks create? |
|---|---|---|
| CREATE | Propose Opportunity; surface MEDDPICC gaps as recommendations | No (needs approval) |
| CREATE WITH GAPS | Same, with stronger follow-up questions; still allow proceed | No (needs approval) |
| EXISTING OPPORTUNITY | Surface match; ask to associate/investigate; never auto-duplicate | Yes until resolved |
| INSUFFICIENT INFORMATION | Cannot identify Account, describe Opportunity, or satisfy mandatory SF fields | Yes |

Missing MEDDPICC alone must **not** map to INSUFFICIENT INFORMATION.

---

## Data Architecture

### Salesforce (standard objects)

- **Account** — company context
- **Contact** — stakeholders
- **Opportunity** — proposed/created deal
- **Task** — meetings and Gong-style email activity (demo assumption)
- **OpportunityContactRole** — stakeholder roles on the deal

Field availability, required fields, and picklists must be validated in the Developer Org before write implementation.

### Synthetic fixtures

JSON fixtures under `data/` mirror the demo org and meeting inputs for offline reasoning, tests, and demos when live systems are unavailable.

### Information confidence

The Skill should label facts as:

- **Confirmed** — supported by meeting and/or CRM evidence
- **Inferred** — reasonable interpretation; not confirmed
- **Unknown** — not present
- **At Risk** — conflicting, stale, or weakly supported

Never present inferred values as confirmed CRM facts.

---

## Integration Strategy (Open)

| Integration | Role | Validation needed |
|---|---|---|
| Salesforce runtime (Claude) | Live CRM read/write | Confirm supported connection path for Skills; test read + approved write |
| Salesforce CLI (`discovery-dev`) | Local seed/inspect | Confirm org alias and object/field metadata |
| Granola | Meeting transcript/summary/attendees | Confirm Claude access; otherwise use fixtures |

No invented APIs or fabricated responses. If an integration is unverified, document it as planned and use fixtures.

---

## Security and Trust

- Private repository
- No credentials, tokens, or secrets in source control
- Explicit rep approval before any CRM write
- Prefer least-privilege Salesforce access for the demo user
- Use fictional synthetic data only (no real customer PII)

---

## Non-Goals (Interview Scope)

- Custom application backend
- Custom MCP server
- Full sales methodology enforcement engine
- Multi-rep / manager dashboards
- Non-standard Salesforce objects or heavy customization

---

## Next Architecture Steps (After Review)

1. Define synthetic data model and four demo scenarios.
2. Draft Skill `SKILL.md` + reference docs aligned to this flow.
3. Validate Salesforce metadata (required fields, picklists) in `discovery-dev`.
4. Confirm Claude → Salesforce runtime connection approach.
5. Confirm or fall back from Granola access.
