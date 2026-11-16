# Discovery-to-Opportunity Agent

A Claude Skill that helps a BDR or AE turn a discovery meeting into a well-structured Salesforce Opportunity — with CRM context, BANT/MEDDPICC coaching, duplicate detection, and **explicit human approval before any write**.

**Interview framing:** Synthetic demo data models **Apollo** (sales intelligence / GTM) prospects — companies with sales/SDR/RevOps motions discussing prospecting, enrichment, buyer identification, outbound efficiency, and CRM hygiene. ICP notes are working assumptions, not official Apollo thresholds.

**Skill package:** **v0.3.0** (`skill/discovery-to-opportunity/`, `metadata.version` in `SKILL.md`).

### Problem

After discovery calls, reps still do heavy manual work: reviewing transcripts, looking up Accounts/Contacts/Opportunities, judging duplicates, structuring CRM fields, and writing AE handoff notes. That creates friction, inconsistent CRM data, and lost context. This Skill connects meeting intelligence with Salesforce so the rep can capture a clean Opportunity while the conversation is fresh — without turning Claude into a compliance gatekeeper.

---

## How it works

```text
Rep (Claude.ai) → Discovery-to-Opportunity Skill v0.3.0
                    ├── fixtures/granola_meetings.json   (simulated Granola; no live Granola)
                    ├── references/                     (decision, qualification, mapping, retrieval, writes)
                    └── Salesforce Hosted MCP           (sobject-all — one connector)
                           reads + approved writes; never delete
```

- **Meetings:** Packaged fixtures only. Claude.ai cannot read the repo `data/` folder.
- **CRM:** One Hosted MCP connector, `sobject-all`, because Claude Free plan allows only one custom connector. Details and tradeoffs: [docs/architecture.md](docs/architecture.md).
- **Local Salesforce CLI (`discovery-dev`):** Seeding/inspection only — not Claude (or Cursor) runtime CRM access.
- **No custom backend or custom MCP server.**

MCP tools used (documented in Skill references): `soqlQuery`, `find`, `getRelatedRecords`, `listRecentSobjectRecords`, `getObjectSchema`, `getUserInfo`, `createSobjectRecord`, `updateSobjectRecord`, `updateRelatedRecord`.

---

## Workflow

1. Confirm the meeting from packaged fixtures (**no Salesforce queries yet**).
2. Analyze the full transcript; retrieve Account → Contacts → Opportunities (optional OCR/Tasks).
3. Decide outcome: **CREATE** / **CREATE WITH GAPS** / **EXISTING OPPORTUNITY** / **DO NOT CREATE**.
4. Ask high-leverage clarifications **one at a time** (BANT + MEDDPICC as coaching — not creation gates).
5. Preview Opportunity fields + OCR associations + AE handoff in **`Handoff_Notes__c`** (keep Description concise).
6. Require **explicit** approval of that exact preview → re-check duplicates → create Opp (with handoff) → OCRs for existing Contacts → verify reads.
7. **Never delete.** Do not create Contacts. Do not invent Role / `IsPrimary` from title or attendance alone.

---

## Opportunity decisions & duplicates

| Outcome | Demo meeting | Notes |
|---|---|---|
| CREATE | MTG-001 | New SDR/contact-data initiative; not OPP-001 (AE platform) |
| CREATE WITH GAPS | MTG-002 | Early need; not OPP-002 (partner-lead) |
| EXISTING OPPORTUNITY | MTG-003 | Same initiative as open OPP-001 |
| DO NOT CREATE | MTG-004 | Networking / no buying initiative |
| CREATE or EXISTING | MTG-005 | Continuation of MTG-001; EXISTING if SDR Opp already created |

Duplicate detection compares **initiative** (use case / scope / buying motion), not Account or Contact overlap alone.

Missing BANT/MEDDPICC alone must **not** become DO NOT CREATE — use CREATE or CREATE WITH GAPS with coaching. Block only for missing essentials (no initiative / unidentifiable Account), unresolved same-initiative duplicate risk, unmet Salesforce requirements, or lack of approval.

Scenario detail: [tests/scenarios.md](tests/scenarios.md), [tests/expected_outcomes.json](tests/expected_outcomes.json).

---

## Write safeguards

- Explicit approval of the exact preview before any Salesforce create/update.
- Duplicate re-check immediately before write.
- OCR Role / `IsPrimary` omitted unless evidenced — never inferred from title alone.
- No Contact creation; no delete operations (Skill policy; MCP-layer delete disablement not independently verified).
- Post-write verify reads before claiming success; report partial failures accurately.
- Never fabricate CRM facts or present inferences as confirmed.

Policy lives in `skill/discovery-to-opportunity/references/salesforce-writes.md` and is covered by mocked tests (below).

---

## Architecture & key decisions

Concise defaults for this interview-scoped build:

| Decision | Why |
|---|---|
| Claude Skill (no custom UI/backend) | Matches brief; conversational UX |
| One MCP connector: `sobject-all` | Free-plan one-connector limit |
| Skill forbids delete | `sobject-all` may expose delete |
| MEDDPICC / BANT as coaching | Adoption over rigid gates |
| `Handoff_Notes__c` for AE narrative | Keep Description short |
| Synthetic fixtures | Repeatable demos; no real customer data |
| Standard Salesforce objects + `Handoff_Notes__c` | Portable demo org |

Full design: [docs/architecture.md](docs/architecture.md). Assumptions and validation log: [docs/demo-decisions.md](docs/demo-decisions.md).

---

## Install & demo

1. **Install the Skill** — Zip the **contents** of `skill/discovery-to-opportunity/` so **`SKILL.md` is at the ZIP root**, or use the checked-in `skill/discovery-to-opportunity.zip`. Follow [skill/discovery-to-opportunity/INSTALL.md](skill/discovery-to-opportunity/INSTALL.md).
2. **Connect Salesforce** — Configure one Claude custom connector: `https://api.salesforce.com/platform/mcp/v1/platform/sobject-all`. Connect it in the chat session before CRM steps.
3. **(Optional) Seed a demo org** — Local CLI alias `discovery-dev` + `scripts/load_salesforce_data.py` (Id map is gitignored). Validate fixtures first:

```bash
python3 scripts/validate_synthetic_data.py
python3 -m unittest tests.test_write_workflow_guards -v
```

4. **Run a scenario** — Confirm a meeting (e.g. MTG-001…005), walk the workflow, and stop at preview unless you intentionally approve a live write.

Fixtures: Oct–Nov 2026; newest meeting `MTG-005`. Demo “today” ≈ 2026-11-16 (CloseDate must be future vs today).

---

## Validation status

| What | How | Result |
|---|---|---|
| Synthetic fixture consistency (counts, keys, packaged ≡ canonical meetings) | `scripts/validate_synthetic_data.py` | PASS |
| Write-safety mocks (approval, duplicate re-check, OCR omit rules, handoff reject/verify mismatch, timeouts, MTG-001→MTG-005 EXISTING) | `tests/test_write_workflow_guards.py` (30 tests) | PASS |
| MTG-003 / MTG-004 fixture ↔ expected outcomes | Read-only review | Aligned |
| Org seed (pre–MTG-005) | `discovery-dev` import 2026-11-12 (30 records) | Verified then |
| Live Claude MCP Opportunity create + OCR + `Handoff_Notes__c` + post-write verify | — | **Not executed** |

### Release note — v0.3.0 (2026-11-16)

First approval-gated Opportunity + AE handoff Skill package: confirm → analyze → CRM reads → clarify → preview → explicit approve → create/verify instructions; five demo outcomes including MTG-005 continuation. Skill release detail: [skill/discovery-to-opportunity/CHANGELOG.md](skill/discovery-to-opportunity/CHANGELOG.md).

---

## Known limitations

- No live Granola product integration (fixtures only).
- Live Opportunity create / OCR / `Handoff_Notes__c` persistence and post-write verification in a Claude session were **not** executed for this release.
- Local fixture timeline includes MTG-005 / TSK-011; live org may need re-seed for date parity (see demo-decisions).
- Delete may exist on `sobject-all`; Skill forbids it — MCP-layer disablement not verified.
- Secrets, tokens, and `data/.salesforce-id-map.json` must stay out of the repo (see `.gitignore`).

---

## Repository layout

```text
discovery-to-opportunity-agent/
├── skill/discovery-to-opportunity/   # Skill source + discovery-to-opportunity.zip
│   ├── SKILL.md                   # metadata.version 0.3.0
│   ├── CHANGELOG.md · INSTALL.md
│   ├── fixtures/granola_meetings.json
│   ├── references/ · examples/
├── data/                          # Canonical fixtures + CRM seed JSON
├── tests/                         # scenarios, expected_outcomes, write-guard tests
├── docs/architecture.md
├── docs/demo-decisions.md
├── scripts/
└── README.md
```

## Documentation map

| Doc | Purpose |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Architecture + `sobject-all` rationale |
| [docs/demo-decisions.md](docs/demo-decisions.md) | Decisions, fixture limits, validation log |
| [tests/scenarios.md](tests/scenarios.md) | Five scenarios + manual runbook |
| [skill/.../INSTALL.md](skill/discovery-to-opportunity/INSTALL.md) | Claude.ai install |
| [skill/.../CHANGELOG.md](skill/discovery-to-opportunity/CHANGELOG.md) | Skill package release notes |
