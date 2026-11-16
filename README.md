# Discovery-to-Opportunity Agent

A Claude Skill that helps a BDR (or AE) turn a discovery meeting into a well-structured Salesforce Opportunity — with CRM context, BANT/MEDDPICC coaching, duplicate detection, and explicit human approval before any write.

Interview framing: synthetic demo data models **Apollo** (sales intelligence / GTM) prospects and discovery conversations.

**Version:** Skill package **v0.3.0** (`skill/discovery-to-opportunity/`, `metadata.version` in `SKILL.md`).

---

## Intended BDR workflow

1. Confirm the meeting (packaged simulated Granola fixtures — **no Salesforce queries yet**).
2. Analyze the full transcript; retrieve Account → Contacts → Opportunities (+ optional OCR/Tasks) via Hosted MCP.
3. Decide outcome: **CREATE** / **CREATE WITH GAPS** / **EXISTING OPPORTUNITY** / **DO NOT CREATE** (INSUFFICIENT INFORMATION).
4. Ask high-leverage clarifications **one at a time** (BANT + MEDDPICC coaching — not creation gates).
5. Preview Opportunity fields + OCR associations + full AE handoff in **`Handoff_Notes__c`**.
6. Require **explicit** approval of that preview → create Opp (with handoff) → OCRs for existing Contacts → verify reads.
7. **Never delete.** Do not create Contacts. Do not invent Role/`IsPrimary` from title or attendance alone.

Fixtures: Oct–Nov 2026 (5 meetings; newest `MTG-005`). CRM: **one** Salesforce Hosted MCP connector (`sobject-all`) — Free-plan one-connector limit; see [docs/architecture.md](docs/architecture.md).

There is **no live Granola integration**. Claude.ai cannot read the repo `data/` folder; meetings ship in `fixtures/granola_meetings.json`.

## Decision outcomes & scenarios

| Outcome | Meeting (demo) | Notes |
|---|---|---|
| CREATE | MTG-001 | New SDR/contact-data initiative; not OPP-001 (AE platform) |
| CREATE WITH GAPS | MTG-002 | Early need; not OPP-002 (partner-lead) |
| EXISTING OPPORTUNITY | MTG-003 | Same initiative as open OPP-001 |
| DO NOT CREATE | MTG-004 | Networking / no buying initiative |
| CREATE (or EXISTING) | MTG-005 | Continuation of MTG-001; EXISTING if SDR Opp already created |

Duplicate detection compares **initiative** (use case / scope / buying motion), not Account or Contact overlap alone. Details: `tests/scenarios.md`, `tests/expected_outcomes.json`.

## High-level architecture

```text
Rep (Claude.ai) → Discovery-to-Opportunity Skill v0.3.0
                    ├── fixtures/granola_meetings.json
                    ├── references (decision, qualification, mapping, retrieval, writes)
                    └── Salesforce Hosted MCP (sobject-all)
                           reads + approved writes; never delete
```

- **Salesforce CLI (`discovery-dev`)** — local seeding/inspection only; not Claude or Cursor runtime CRM access.
- **No custom backend / custom MCP server.**

Exact MCP tools: `mcp__Salesforce__soqlQuery`, `find`, `getRelatedRecords`, `listRecentSobjectRecords`, `getObjectSchema`, `getUserInfo`, `createSobjectRecord`, `updateSobjectRecord`, `updateRelatedRecord` (documented in Skill references).

## Validation status (precise)

| What was validated | How | Result |
|---|---|---|
| Synthetic fixture consistency (counts, keys, packaged≡canonical meetings) | `scripts/validate_synthetic_data.py` | PASS |
| Write-safety mocks (approval gate, duplicate re-check, OCR Role/`IsPrimary` omit rules, handoff reject/verify mismatch, timeouts, MTG-001→MTG-005 EXISTING variant) | `tests/test_write_workflow_guards.py` (30 tests) | PASS |
| MTG-003 / MTG-004 fixture↔expected-outcome alignment | Read-only fixture review vs `expected_outcomes.json` | Aligned (not a unittest module) |
| Org seed (pre–MTG-005) | `discovery-dev` import 2026-11-12 (30 records) | Verified then |
| Live Claude MCP Opportunity create + OCR + `Handoff_Notes__c` + post-write verify | — | **Not executed** |

## Technology assumptions

- Claude Skill (Claude.ai installable package), v0.3.0
- Salesforce Developer Org + CLI alias `discovery-dev` for seeding
- One Salesforce Hosted MCP connector: `sobject-all` (Claude Free-plan one-connector limit)
- Simulated Granola via packaged JSON (canonical copy in `data/granola_meetings.json`)
- Standard Salesforce objects + org field `Handoff_Notes__c`
- CloseDate: future vs demo “today” (~2026-11-16); ask if unknown
- Private GitHub repository; no secrets in source control

## Repository layout

```text
discovery-to-opportunity-agent/
├── skill/discovery-to-opportunity/   # Canonical Skill source (+ release ZIP)
│   ├── SKILL.md                   # metadata.version 0.3.0
│   ├── CHANGELOG.md
│   ├── INSTALL.md
│   ├── fixtures/granola_meetings.json
│   ├── references/
│   └── examples/
├── data/                          # Canonical fixtures + CRM seed JSON
├── tests/                         # scenarios, expected_outcomes, write-guard tests
├── docs/architecture.md
├── docs/demo-decisions.md
├── scripts/
├── PROJECT_CONTEXT.md
└── README.md
```

Package for Claude.ai: zip the **contents** of `skill/discovery-to-opportunity/` so **`SKILL.md` is at the ZIP root** (see `INSTALL.md`). Keep `skill/discovery-to-opportunity.zip` in sync when releasing.

## Documentation

| Doc | Purpose |
|---|---|
| [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) | Requirements source of truth |
| [docs/architecture.md](docs/architecture.md) | Architecture + `sobject-all` rationale |
| [docs/demo-decisions.md](docs/demo-decisions.md) | Decisions, fixture limits, validation log |
| [tests/scenarios.md](tests/scenarios.md) | Five scenarios + manual runbook |
| [skill/.../INSTALL.md](skill/discovery-to-opportunity/INSTALL.md) | Claude.ai install |
| [skill/.../CHANGELOG.md](skill/discovery-to-opportunity/CHANGELOG.md) | Skill release notes (v0.3.0) |

## Out of scope (v0.3.0)

- Live Granola product integration
- Salesforce **delete** (Skill-forbidden; MCP-layer disablement not independently verified)
- Separate Claude connectors for `sobject-reads` + `sobject-mutations`
- Custom backends / custom MCP servers
- Claiming Claude or Cursor can read the local repo `data/` directory
- Storing OAuth secrets in the repo
