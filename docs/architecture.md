# Architecture Overview

Architecture for the Discovery-to-Opportunity Agent interview demo. Distinguishes **implemented** vs **planned** pieces.

**Status:** Synthetic CRM seeded in `discovery-dev`. One Skill under `skill/discovery-to-opportunity/` — conversational BDR→AE handoff (confirm meeting → analyze → targeted CRM reads → clarify → Opportunity + `Handoff_Notes__c` preview → explicit approval → create/verify). Live CRM uses **one Salesforce Hosted MCP connector** (`sobject-all`). **Writes require explicit approval; delete is never allowed.**

---

## Design Intent

Build a conversational Claude Skill that:

1. Confirms the right discovery meeting with the salesperson
2. Reads full transcript (simulated Granola) + Salesforce CRM (Hosted MCP)
3. Judges buying interest (create / clarify / existing / none)
4. Asks a few high-leverage questions (BANT + MEDDPICC coaching — not gates)
5. Previews a clean Opportunity **and** a detailed AE Discovery Handoff in `Opportunity.Handoff_Notes__c`
6. Requires explicit approval before any Salesforce write (Opp create, OCR, `Handoff_Notes__c`)

Optimize for a credible live demo. Prefer Skill-native orchestration and standard Salesforce objects over custom infrastructure.

---

## Salesforce Hosted MCP connection (`sobject-all`)

**Canonical connector endpoint (Claude custom connector):**

`https://api.salesforce.com/platform/mcp/v1/platform/sobject-all`

### Why one connector

Salesforce publishes separate Hosted MCP surfaces, including:

| Endpoint family | Capabilities (high level) |
|---|---|
| `sobject-reads` | Read / query operations only |
| `sobject-mutations` | Record create / update (and related mutation tools) |
| `sobject-all` | Combined read **and** mutation capabilities, **including deletion** |

Claude’s **Free plan limits the user to one custom connector**. Maintaining separate Claude connectors for `sobject-reads` and `sobject-mutations` was not possible under that limit. We therefore consolidated into **one** `sobject-all` connection so the full Discovery-to-Opportunity workflow (retrieve → approve → create Opp / OCRs / handoff field → verify) can run through a single Claude connector.

This is an **intentional implementation decision driven by the Free-plan connector limit**, not a Salesforce technical requirement that forces `sobject-all`.

### Tradeoffs and Skill guardrails

- **Benefit:** One Claude connector supports both CRM retrieval and approved writes.
- **Risk:** `sobject-all` is broader than reads-only; **delete operations may be exposed**. Do **not** claim deletes are disabled at the MCP/server layer unless independently verified.
- **Skill policy (mandatory):**
  - **Never** invoke Salesforce **delete** operations under any circumstances.
  - Use only operations needed for: retrieval (SOQL/read), Opportunity **create**, Opportunity Contact Role **create**, and updating **`Handoff_Notes__c`** (plus post-create verification reads).
  - **Explicit BDR approval** is required before any write; analyzing a meeting is not approval.
- Prefer least-privilege Salesforce **user** permissions and field-level security for the connected org user wherever possible (defense in depth alongside Skill policy).

### Connector vs Claude session

Having the `sobject-all` MCP server / connector **configured** is not the same as Claude being **authenticated and connected** in a given chat. Runtime CRM access still depends on the user’s Claude session successfully using that connector. Do not store Consumer Keys, Client Secrets, tokens, or other credentials in this repository.

---

## System Context

```text
┌──────────────────────────────────────────────────────────────┐
│ Rep in Claude.ai                                             │
│  └─ Discovery-to-Opportunity Skill (uploaded package)        │
│       ├─ SKILL.md + references + examples                    │
│       ├─ fixtures/granola_meetings.json  ← simulated Granola │
│       └─ Salesforce Hosted MCP (sobject-all)                 │
│            reads + approved writes (never delete)            │
│            Account | Contact | Opportunity | Task | OCR      │
└──────────────────────────────────────────────────────────────┘

Repo / local development (not automatically visible to Claude.ai):
  data/granola_meetings.json     ← canonical meeting dataset (source of truth)
  data/*.json                    ← CRM seed fixtures
  scripts/load_salesforce_data.py
  Salesforce CLI alias discovery-dev
```

### Important boundaries

1. **Claude.ai cannot read the local Cursor repo.** Meeting data used at runtime must be **inside the Skill package** (`fixtures/granola_meetings.json`).
2. **No live Granola integration.** Fixtures simulate Granola for demos.
3. **Local Salesforce CLI auth ≠ Claude runtime CRM access.** Skill CRM access is via the Hosted MCP `sobject-all` connector.
4. **Writes only after explicit approval.** Never delete. MCP may expose broader mutation tools; the Skill must not use them.

---

## Component Responsibilities

| Component | Responsibility | Status |
|---|---|---|
| Claude Skill (`skill/discovery-to-opportunity/`) v0.3.0 | Orchestration, preview, approval gate, write instructions | **Implemented** (Skill package) |
| Packaged meeting fixtures (`skill/.../fixtures/granola_meetings.json`) | Simulated Granola accessible after Skill install | **Implemented** (must match canonical) |
| Canonical meetings (`data/granola_meetings.json`) | Repo source of truth; keep Skill copy in sync | **Implemented** |
| Skill references | Decision, qualification, field mapping, retrieval, writes | **Implemented** |
| Synthetic CRM JSON (`data/*.json`) | Seed / offline mirror of demo org | **Implemented** |
| Salesforce org | CRM truth for demo | **Seeded** (`discovery-dev`, pre–MTG-005 parity caveat) |
| Salesforce Hosted MCP (`sobject-all`) | One Claude connector: reads + mutations | **Configured for Claude** — session auth still per-chat; **not wired into this Cursor session** |
| Load script | Seed org | **Implemented** |
| Skill write path | Exact tools in `salesforce-writes.md`; Opp + OCR + `Handoff_Notes__c`; verify; **never delete** | **Implemented in Skill instructions**; local write-guard mocks PASS; **live Claude write smoke not executed** |
| Salesforce retrieval SOQL | Confirm-first, Account-scoped reads | **Documented** in `salesforce-retrieval.md` |
| Custom backend / custom MCP | — | **Out of scope** |
| Live Granola API | — | **Not used** |

---

## Core Runtime Flow

```text
1. User asks to run opp skill / review a Granola meeting
2. Skill loads fixtures/granola_meetings.json; proposes best match  ← no SF queries yet
3. User confirms meeting (title, date, Account, attendees)
4. Full transcript analysis (local)
5. Targeted Salesforce MCP reads: Account → Contacts → Opportunities (+ optional OCR/Tasks)
   See skill/.../references/salesforce-retrieval.md
6. Buying-interest + initiative/duplicate decision
7. One-at-a-time clarifications when useful (Rep clarification)
8. Opportunity preview (concise Description) + Handoff Notes → `Handoff_Notes__c`
9. Explicit BDR approval (required; never automatic)
10. Create Opportunity + OCRs + populate Handoff_Notes__c (MCP mutations via `sobject-all`; Skill-gated)
11. Verify created records; report Ids/links
```

Default chat stays Layer A (short). Layer B detail on request. Writes use the same `sobject-all` connector after approval; never delete. See Salesforce Hosted MCP section above.

---

## Decision Outcomes

| Outcome | Blocks create? |
|---|---|
| CREATE | No (needs explicit approval before write) |
| CREATE WITH GAPS | No (needs explicit approval before write) |
| EXISTING OPPORTUNITY | Yes until resolved |
| INSUFFICIENT INFORMATION / DO NOT CREATE | Yes |

Missing MEDDPICC alone must **not** map to INSUFFICIENT INFORMATION.

---

## Data Architecture

### Meeting intelligence (simulated Granola)

- Packaged path: `skill/discovery-to-opportunity/fixtures/granola_meetings.json`
- Canonical path: `data/granola_meetings.json`
- Contents: MTG-001 … MTG-005 (transcript, attendees, summary, action items, linked Task key)
- Dates: October–November 2026; newest = MTG-005 (Nov 12) for “recent meeting” demos
- Not Salesforce objects; simulated Granola only

### Salesforce (standard objects)

Account, Contact, Opportunity, Task, OpportunityContactRole — live via MCP; seeded from `data/*.json`.

### Confidence labels

Confirmed | Inferred | Unknown | At Risk — never present inferences as confirmed CRM facts.

---

## Security and Trust

- Private repository
- No credentials, Consumer Keys, Client Secrets, or tokens in source control
- Explicit approval before any CRM write
- Never invoke Salesforce delete (Skill policy; MCP delete disablement **not** independently verified)
- Prefer least-privilege Salesforce user / FLS for the connected user
- Fictional synthetic data only

---

## Non-Goals (interview scope)

- Custom application backend
- Custom MCP server
- Separate Claude connectors for `sobject-reads` + `sobject-mutations` (blocked by Free-plan one-connector limit)
- Live Granola product integration
- Full methodology enforcement engine

---

## Packaging note

Canonical Claude package source: **`skill/discovery-to-opportunity/`**. For install, zip the **contents** so **`SKILL.md` is at the ZIP root** (see `INSTALL.md`). Keep `skill/discovery-to-opportunity.zip` synchronized when cutting a release. Decisions / validation log: `docs/demo-decisions.md`.

## Validation vs next steps

**Already done locally:** synthetic-data validator; 30 write-workflow guard tests; fixture/expected-outcome alignment for all five scenarios (MTG-003/004 reviewed read-only; MTG-001→MTG-005 EXISTING variant automated).

**Next (Claude session with `sobject-all` connected):**

1. Smoke-test MCP **reads** (Account/Contact/Opportunity for Meridian).
2. Install/upload Skill v0.3.0 per `INSTALL.md`.
3. Walk MTG-001 … MTG-005 (recent → MTG-005).
4. With **explicit** approval only: Opp create + OCR + `Handoff_Notes__c` + verification reads; never delete.
