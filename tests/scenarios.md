# Test Scenarios

Shared synthetic dataset for the Discovery-to-Opportunity Agent — a conversational **BDR→AE Opportunity handoff** assistant for Apollo.

All scenarios use the same fixtures (canonical `data/`; Skill runtime uses packaged `fixtures/granola_meetings.json`). Incomplete BANT/MEDDPICC never by themselves means “do not create.”

**Default UX:** confirm meeting (no SF yet) → transcript → Account-scoped CRM reads → buying-interest/initiative decision → one clarification at a time → Opportunity preview + Handoff Notes (`Handoff_Notes__c`) → explicit approval → planned create/verify (writes gated).

**Fixture timeline:** Oct 8–Nov 12, 2026 (demo “today” ≈ Nov 16, 2026). Most recent meeting: `MTG-005`. “Recent Granola meeting” → prefer newest matching by `start_time`. Historical / continuation meetings require **initiative-status confirmation** before proposing create. Proposed Close Dates must be **future vs today**.

This document covers **five** scenarios and how to exercise them. It is for **manual / Skill-based** validation. Machine-readable expectations live in `tests/expected_outcomes.json`. Automated Skill E2E tests are not part of this phase; write-path policy is covered by `tests/test_write_workflow_guards.py`.

---

## Prerequisites

1. Local fixtures validated:

```bash
python3 scripts/validate_synthetic_data.py
```

2. (After import approval) Salesforce `discovery-dev` seeded via `scripts/load_salesforce_data.py`.
3. Local ID map present at `data/.salesforce-id-map.json` (gitignored) after a successful load.
4. Meeting intelligence from packaged Skill fixtures (or canonical `data/granola_meetings.json` for local review) — synthetic; not live Granola.
5. Confirm packaged fixture still matches canonical when preparing a Claude install:

```bash
python3 -c "from pathlib import Path; a=Path('data/granola_meetings.json').read_bytes(); b=Path('skill/discovery-to-opportunity/fixtures/granola_meetings.json').read_bytes(); print('match', a==b)"
```

---

## How to run each scenario

Provide the Skill (or a human reviewer simulating it) with:

1. A natural prompt (e.g. “run the opp skill…” or an explicit `MTG-00N`).
2. Confirm the meeting when the Skill asks (title/date/Account/attendees).
3. Packaged fixture + Salesforce MCP context for the Account.
4. Expect Layer A conversation first; Layer B only if requested.
5. Outcomes per product principles (BANT/MEDDPICC = coaching, not a gate; explicit approval; no writes until approved).

---

## SCENARIO-01 — Strong legitimate opportunity

| Field | Value |
|---|---|
| **Objective** | Propose Opportunity creation when Apollo-relevant pain, use case, engaged stakeholders, and next step are clear — even with MEDDPICC gaps. |
| **Expected outcome** | `CREATE` (conversational: Opportunity identified) |
| **Account** | `ACC-001` Meridian Robotics |
| **Contacts** | `CON-001` Jordan Blake (VP Sales), `CON-002` Sam Rivera (SDR Manager), `CON-003` Casey Nguyen (Sales Ops) |
| **Opportunities (context)** | `OPP-001` Apollo platform for AE team (different initiative), `OPP-004` Closed Lost contact-data vendor |
| **Tasks** | Meeting `TSK-001`; emails `TSK-004`, `TSK-005` |
| **Granola meeting** | `MTG-001` (Oct 14) — SDR outbound research burden + Salesforce contact hygiene |
| **MEDDPICC gaps** | Full Economic Buyer / Finance unknown; Paper Process unknown; quantified $ ROI incomplete; Competition only lightly mentioned |
| **Why it matters** | Enrichment ≠ gatekeeping. Missing Finance sign-off must not block a legitimate Apollo pilot-oriented Opportunity. |

### Manual run focus

- **Meeting:** `MTG-001` (SDR outbound research + contact data)
- **SF focus:** `ACC-001`, `CON-001..003`, `TSK-001/004/005`, Opps `OPP-001` + `OPP-004` as context
- **Success:** `CREATE`; new opp for SDR/contact-data motion; **not** duplicate of `OPP-001`; gaps + skippable questions; approval gate
- **Failure:** Blocking solely for missing Finance/metrics; merging into `OPP-001`; fabricating ROI as confirmed

### Expected agent behavior

- Confirm the meeting with the user before full analysis.
- Analyze the **full transcript**; identify buying interest.
- Resolve Meridian Account/Contacts via Salesforce MCP.
- Propose a **new** Opportunity for SDR outbound / contact-data productivity (not the AE platform deal in `OPP-001`).
- Ask high-leverage clarifications **one at a time** (skippable); do not dump MEDDPICC tables by default.
- Present Opportunity preview + Handoff Notes (`Handoff_Notes__c`); keep Description concise; require explicit approval before writes.
- Because `MTG-005` continues this initiative, confirm initiative status if the rep selects this older meeting.

---

## SCENARIO-02 — Early-stage opportunity with gaps

| Field | Value |
|---|---|
| **Objective** | Allow creation when Apollo interest and need exist but qualification is thin. |
| **Expected outcome** | `CREATE WITH GAPS` (conversational: Potential opportunity — needs clarification) |
| **Account** | `ACC-002` Cascade Health Partners |
| **Contacts** | `CON-004` Avery Patel (VP Sales), `CON-005` Riley Chen (Senior SDR); `CON-006` Quinn Morgan (RevOps) absent |
| **Opportunities (context)** | `OPP-002` Apollo **Partner Lead Enrichment** — clearly different initiative |
| **Tasks** | Meeting `TSK-002`; emails `TSK-006`, `TSK-007` |
| **Granola meeting** | `MTG-002` (Oct 21) — hospital/clinic buying-group identification + CRM contact quality |
| **MEDDPICC gaps** | Metrics, Economic Buyer, Decision Process, Paper Process, Competition largely UNKNOWN; Champion not confirmed; timeline uncertain |
| **Why it matters** | Early Apollo deals are common. Agent should coach, not block — and must not confuse this with `OPP-002`. |

### Manual run focus

- **Meeting:** `MTG-002` (hospital buying groups + CRM contact quality)
- **SF focus:** `ACC-002`, `CON-004/005`, `TSK-002/006/007`, Opp `OPP-002` as **non-matching** context (partner lead enrichment)
- **Success:** `CREATE WITH GAPS`; distinct from `OPP-002`; skippable questions; allow proceed after approval
- **Failure:** Mapping to INSUFFICIENT INFORMATION only because MEDDPICC incomplete; auto-merging into `OPP-002`

### Expected agent behavior

- Confirm meeting; assess early buying signals.
- Conversationally state **needs clarification**; ask one question at a time.
- Propose a new Opportunity for hospital buying-group / enrichment use case.
- **Do not** flag as duplicate of `OPP-002`.
- Allow skip; still offer preview + AE handoff; approval required before writes.

---

## SCENARIO-03 — Existing Opportunity

| Field | Value |
|---|---|
| **Objective** | Detect matching open Apollo deal and prevent automatic second create. |
| **Expected outcome** | `EXISTING OPPORTUNITY` (conversational: Existing Opportunity found) |
| **Account** | `ACC-001` Meridian Robotics |
| **Contacts** | `CON-001`, `CON-002`, `CON-003` |
| **Opportunities** | **`OPP-001` Meridian Robotics - Apollo Sales Intelligence Platform** |
| **Tasks** | Meeting `TSK-003`; email `TSK-008` |
| **Granola meeting** | `MTG-003` (Oct 28) |
| **MEDDPICC gaps** | Finance / full Economic Buyer still open — not the reason to block |
| **Why it matters** | Duplicate Opportunities corrupt pipeline forecasts. |

### Manual run focus

- **Meeting:** `MTG-003`
- **SF focus:** `OPP-001`, `TSK-003/008`, OCRs `OCR-001/002`
- **Success:** `EXISTING OPPORTUNITY`; match rationale; associate vs investigate; **no create**
- **Failure:** Creating a second Apollo platform Opportunity; ignoring “do not open a separate opportunity”

### Expected agent behavior

- Match meeting topic to `OPP-001` by account + Apollo platform initiative language.
- Surface historical Tasks/`OPP-001` context.
- Ask associate vs investigate — **never auto-create a duplicate**.

---

## SCENARIO-04 — No legitimate sales opportunity

| Field | Value |
|---|---|
| **Objective** | Distinguish “no opportunity” from “opportunity with MEDDPICC gaps.” |
| **Expected outcome** | `INSUFFICIENT INFORMATION` / DO NOT CREATE (conversational: No opportunity identified) |
| **Account** | `ACC-003` Northwind Retail Group (existing Apollo customer; B2B wholesale + enterprise partnerships) |
| **Contacts** | `CON-007` Taylor Brooks (Partnerships), `CON-008` Morgan Ellis (CEO, social only) |
| **Opportunities (context)** | `OPP-003` Closed Won Apollo platform (historical) |
| **Tasks** | Meeting `TSK-009`; email `TSK-010` |
| **Granola meeting** | `MTG-004` (Oct 8) networking coffee — no expansion initiative |
| **MEDDPICC gaps** | N/A framing — absence of a buying initiative, not missing qualification on a real deal |
| **Why it matters** | Prevents junk Opportunities from networking with existing customers. |

### Manual run focus

- **Meeting:** `MTG-004` (Oct 8; networking; existing Apollo customer; no expansion)
- **SF focus:** `ACC-003`, `CON-007/008`, `TSK-009/010`, Closed Won `OPP-003`
- **Success:** `INSUFFICIENT INFORMATION` or **do not create**; explain lack of initiative (not “MEDDPICC incomplete”)
- **Failure:** Creating an expansion Opportunity from coffee; inferring EB because CEO said hello

### Expected agent behavior

- Recognize networking / relationship maintenance only.
- Explain lack of business problem, new Apollo use case, and buying intent.
- Do **not** create a new Opportunity.
- Do **not** justify primarily as “MEDDPICC incomplete.”

---

## SCENARIO-05 — Recent continuation of prior initiative

| Field | Value |
|---|---|
| **Objective** | Handle a progressed follow-up of a previously identified initiative; confirm status before create. |
| **Expected outcome** | `CREATE` after initiative-status confirmation (conversational: Opportunity identified — confirm initiative status) |
| **Account** | `ACC-001` Meridian Robotics |
| **Contacts** | `CON-001`, `CON-002`, `CON-003` |
| **Opportunities (context)** | `OPP-001` (different initiative); no open Opp for SDR pilot yet |
| **Tasks** | Meeting `TSK-011`; prior context `TSK-001`/`TSK-004`/`TSK-005` |
| **Granola meeting** | `MTG-005` (Nov 12) — SDR pilot scoping continuation of `MTG-001` |
| **Why it matters** | “Recent meeting” demo path; shows progression without inventing a CRM Opp or merging into `OPP-001`. |

### Manual run focus

- **Meeting:** `MTG-005` (Nov 12; most recent fixture; SDR pilot scoping)
- **SF focus:** `ACC-001`, `TSK-011`, context `MTG-001`/`OPP-001`
- **Success (demo default):** Prefer on “recent meeting”; confirm initiative status; `CREATE` separate from `OPP-001`; future Close Date
- **Success (post–MTG-001 create):** If open SDR/contact-data Opp already exists → `EXISTING OPPORTUNITY`; **no second create**
- **Failure:** Merging into `OPP-001`; duplicating an existing SDR Opp; creating without status confirm when continuation/history applies; past Close Date

### Expected agent behavior

- Prefer this meeting when the user asks for their **recent** Meridian / Granola meeting.
- Confirm initiative still active and not already created in CRM.
- **If no open SDR/contact-data Opp:** propose CREATE separate from `OPP-001` (demo default).
- **If an open SDR/contact-data Opp already exists** (e.g. after MTG-001 was created): treat as **EXISTING OPPORTUNITY** — do **not** create a duplicate.
- Close Date future vs Nov 16, 2026 (e.g. early Jan 2027) with confirmation if needed.

---

## Scenario × fixture map

| Scenario | Meeting | Date | Account | Primary create target? |
|---|---|---|---|---|
| SCENARIO-01 | MTG-001 | Oct 14 | ACC-001 | New Opp (SDR outbound / contact data) |
| SCENARIO-02 | MTG-002 | Oct 21 | ACC-002 | New Opp (hospital buying groups) — not OPP-002 |
| SCENARIO-03 | MTG-003 | Oct 28 | ACC-001 | None — use existing OPP-001 |
| SCENARIO-04 | MTG-004 | Oct 8 | ACC-003 | None — do not create |
| SCENARIO-05 | MTG-005 | Nov 12 | ACC-001 | New Opp (same SDR pilot as MTG-001; confirm status) |

---

## Cross-scenario acceptance criteria

| Criterion | Required |
|---|---|
| Apollo-relevant pain/use case framing | Yes |
| Confirmed vs inferred vs unknown labeled | Yes |
| No fabricated facts | Yes |
| MEDDPICC never sole create-blocker | Yes |
| Explicit approval before any SF write | Yes |
| Meeting confirmation before full analysis | Yes |
| Layer A default; Layer B on request | Yes |
| Handoff Notes (`Handoff_Notes__c`) previewed when create-path | Yes (SCENARIO-01/02/05); Description stays concise |
| Duplicate detection on matching open initiative | Yes (SCENARIO-03) |
| SCENARIO-02 not confused with OPP-002 | Yes |
| Scenarios 1–2 do not collide with matching open Opps | Yes |

---

## Suggested manual checklist

- [ ] `python3 scripts/validate_synthetic_data.py` PASS
- [ ] `python3 tests/test_write_workflow_guards.py` PASS (mocked write guards; no SF calls)
- [ ] Packaged `fixtures/granola_meetings.json` matches `data/granola_meetings.json`
- [ ] Salesforce import verified (if approved) — note: local fixtures include `TSK-011` / date updates; live org may need re-seed for parity
- [ ] SCENARIO-01 preview allows proceed with gaps
- [ ] SCENARIO-02 preview allows skip + proceed; not flagged as OPP-002 duplicate
- [ ] SCENARIO-03 blocks duplicate create
- [ ] SCENARIO-04 recommends no create for networking / no expansion
- [ ] SCENARIO-05 “recent meeting” → MTG-005; initiative-status confirm; CREATE (or EXISTING if SDR Opp already present)
- [ ] Live Claude: approval required before `createSobjectRecord`; verify after create; never delete
