# Demo Decisions and Assumptions

Documents important product, technical, and demo assumptions for the Discovery-to-Opportunity Agent. Update this file when decisions change.

---

## Product Decisions

| Decision | Rationale |
|---|---|
| Claude Skill as the UX | Matches the interview brief; conversational, no custom UI needed |
| Apollo interview framing for synthetic data | Demo prospects and discovery pain should match sales-intelligence / GTM use cases, not generic SaaS |
| MEDDPICC as enrichment, not a gate | Improves CRM quality without blocking legitimate deals; higher adoption |
| Explicit approval before Salesforce writes | Keeps the rep in control; avoids accidental/duplicate CRM pollution |
| Four decision outcomes (CREATE, CREATE WITH GAPS, EXISTING OPPORTUNITY, INSUFFICIENT INFORMATION) | Covers strong, early, duplicate, and weak cases without overcomplicating |
| Missing MEDDPICC ≠ INSUFFICIENT INFORMATION | Only SF requirements, unresolved duplicates, missing essentials, or no approval block creation |
| Conversational assistant tone | Feels like sales ops help, not a form or compliance checklist |
| Layer A short UX / Layer B on request | Salesperson simplicity; hide MEDDPICC tables unless needed |
| BANT + MEDDPICC as coaching | Inform questions/handoff; incomplete qualification ≠ auto-block |
| AE Handoff → `Handoff_Notes__c` | Keep Description concise; rich AE narrative in Opportunity Long Text Area (32,768). Prefer set on Opp create; Classic Note not required |
| Meeting confirmation step | Prevents analyzing the wrong fixture before full analysis |
| Cascade OPP-002 ≠ MTG-002 initiative | Partner-lead enrichment vs hospital buying-group outbound — prevents false duplicate flags |

---

## Technical Decisions

| Decision | Rationale |
|---|---|
| No custom backend / no custom MCP | Keeps scope fit for a ~3-hour interview build |
| One Claude Salesforce connector: `sobject-all` | Free plan allows only one custom connector; cannot split `sobject-reads` + `sobject-mutations`. Tradeoffs (incl. delete risk) in `docs/architecture.md` |
| Never invoke Salesforce delete | Broader `sobject-all` surface may expose delete; Skill forbids it (MCP disablement not independently verified) |
| Standard Salesforce objects only | Portable, easier to demo, avoids org-specific customization debt |
| Synthetic data for demo | Repeatable scenarios; no real customer data |
| Local SF CLI (`discovery-dev`) for seeding/inspection only | Useful for prep; not the same as Claude runtime CRM access |
| Clearly labeled Granola fixtures as fallback | Demo reliability if Granola access is unavailable |
| Distinguish implemented vs planned in docs | Credibility in interview; no vaporware claims |

---

## Integration Assumptions (Must Validate)

| Assumption | Current status | If invalid |
|---|---|---|
| Claude can access Salesforce via Hosted MCP `sobject-all` | **Connector configured**; session connection still required per chat | If disconnected, Skill cannot read/write CRM; use fixtures for meeting side only |
| Salesforce CLI alias `discovery-dev` is authenticated locally | **Validated Connected** (username `discovery-dev authenticated Salesforce user`) | Re-authenticate only if connection expires |
| Granola is available to Claude for meeting retrieval | **Not used live** | Simulate via Skill-packaged `fixtures/granola_meetings.json` (canonical: `data/granola_meetings.json`) |
| Meetings / Gong emails appear as Salesforce Tasks | **Demo convention** | Seed Tasks that represent those activities |
| Required Opportunity fields are Name, AccountId, StageName, CloseDate (typical) | **Validated:** Name, StageName, CloseDate required; AccountId createable but nillable | Keep AccountId populated in fixtures |

---

## Demo Data Shape

Canonical local fixtures under `data/` (Skill meetings also packaged under `skill/discovery-to-opportunity/fixtures/`):

- 3 Accounts
- 8 Contacts
- 4 Opportunities
- 11 Tasks (5 meeting + 6 Gong email) — includes `TSK-011` for MTG-005
- 5 Opportunity Contact Roles
- 5 Granola-style discovery/networking meeting records (Oct–Nov 2026; newest = MTG-005)

### Seeded `discovery-dev` import (verified 2026-11-12)

| Object | Count | Notes |
|---|---|---|
| Accounts | 3 | Verified |
| Contacts | 8 | Account links verified |
| Opportunities | 4 | Account links verified |
| Tasks | 10 | Pre–MTG-005 seed (4 meeting / 6 email) |
| Opportunity Contact Roles | 5 | Verified |
| **Total** | **30** | Local ID map: `data/.salesforce-id-map.json` (gitignored) |

Loader: `scripts/load_salesforce_data.py` (REST JSON create; resume/skip mapped keys).  
**Parity note (2026-11-16):** Local fixtures were retimed and gained MTG-005 / TSK-011; **live org was not re-imported** for date/`TSK-011` parity — re-seed when CRM demo dates must match fixtures.

### Scenario Mapping

| Scenario | Intended outcome | Meeting |
|---|---|---|
| Strong legitimate opportunity | CREATE (allow despite MEDDPICC gaps) | MTG-001 (Oct 14) |
| Early-stage legitimate opportunity | CREATE WITH GAPS (still allow proceed) | MTG-002 (Oct 21) |
| Existing / matching Opportunity | EXISTING OPPORTUNITY (no auto-duplicate) | MTG-003 (Oct 28) |
| Weak / nonexistent opportunity | Decline create; explain lack of opportunity (not “missing MEDDPICC”) | MTG-004 (Oct 8) |
| Progressed continuation / recent meeting | CREATE after initiative-status confirmation | MTG-005 (Nov 12; newest) |

Human runbook: `tests/scenarios.md`. Machine expectations: `tests/expected_outcomes.json`.

---

## Project status & resumption (migrated from retired checkpoint)

### Confirmed done

- Apollo-aligned synthetic data under `data/`; packaged Granola copy must stay in sync for Claude.ai
- Five scenarios: CREATE / CREATE WITH GAPS / EXISTING OPPORTUNITY / DO NOT CREATE / continuation CREATE (MTG-005)
- MEDDPICC remains enrichment only (not a creation gate)
- One Hosted MCP connector configured **for Claude**: `sobject-all` (session still must be connected per chat)
- Skill **v0.3.0**: confirm-first retrieval + approval-gated write workflow with exact MCP tool names; handoff → `Handoff_Notes__c`
- Skill policy: explicit approval before writes; **never delete** (MCP-layer delete disablement **not** independently verified)
- Local automated write-guard suite (approval, duplicate re-check, OCR safeguards, handoff failure paths, MTG-001→MTG-005 EXISTING)

### Validation performed (evidence)

| Check | Evidence |
|---|---|
| Fixture integrity | `validate_synthetic_data.py` PASS |
| Write-safety behavior (mocked MCP) | `test_write_workflow_guards.py` — 30 tests PASS |
| MTG-001→MTG-005 after SDR Opp exists | Automated: EXISTING; no second create/update |
| MTG-003 ↔ OPP-001 / MTG-004 networking | Fixture + `expected_outcomes.json` alignment reviewed (no dedicated unittest) |
| Pre–MTG-005 org seed | 30-record `discovery-dev` import verified 2026-11-12 |

### Not executed

- Live Claude Hosted MCP Opportunity **create**, OCR **create**, `Handoff_Notes__c` persistence, or post-write **verification**
- Live MCP reads from **this Cursor session** (Salesforce MCP tools are not available here — Claude connector ≠ Cursor MCP)
- Re-import of retimed fixtures + `TSK-011` into `discovery-dev`

### Open / unresolved

- [ ] Claude-session smoke: approved write path (Opp + OCR + `Handoff_Notes__c` + verify)
- [ ] Re-import / date parity for `discovery-dev` after Oct–Nov retiming + `TSK-011`
- [ ] Commit working-tree Skill/docs/tests on `feature/claude-salesforce-mcp` when approved
- [ ] Demo script / sales user guide polish
- Live Granola integration — **not planned**; simulated fixtures only

### Packaging

- Canonical source: **`skill/discovery-to-opportunity/`**; zip **contents** with `SKILL.md` at ZIP root (`INSTALL.md`)
- Claude.ai cannot read repo root `data/`; `fixtures/granola_meetings.json` is required in the package
- Do not commit `data/.salesforce-id-map.json`, `.env`, or OAuth secrets

### Workspace / git notes

- Branch in use: `feature/claude-salesforce-mcp` (tracks `origin/feature/claude-salesforce-mcp`); foundation commit exists; large uncommitted Skill/docs/test delta may still be local — verify `git status` before commit.
- Do not assume remotes without checking.

### Local kickoff commands

```bash
python3 scripts/validate_synthetic_data.py
python3 tests/test_write_workflow_guards.py
python3 scripts/load_salesforce_data.py --verify
python3 -c "from pathlib import Path; a=Path('data/granola_meetings.json').read_bytes(); b=Path('skill/discovery-to-opportunity/fixtures/granola_meetings.json').read_bytes(); print('match', a==b)"
```

---

## Claims boundary

Safe to state (with evidence above): local fixture validation; mocked write-safety coverage; Skill instructions for approval-gated create/OCR/handoff/verify; Claude connector choice `sobject-all`.

Do **not** state unless newly evidenced:

- Live Granola transcript retrieval
- Claude or Cursor CRM access solely because Salesforce CLI is logged in locally
- Successful live Opportunity / OCR / `Handoff_Notes__c` create or post-write verification
- Salesforce delete disabled at the MCP/server layer (Skill forbids delete; server disablement unverified)
- Cursor can call the same Hosted MCP tools as Claude without a Cursor-configured Salesforce MCP server

---

## Open Questions for Next Phase

1. ~~Which supported Salesforce runtime connection will the Skill use?~~ → **Decided:** Hosted MCP `sobject-all` (Free-plan one-connector limit). Details in `docs/architecture.md`.
2. ~~Can Granola meeting data be accessed in the demo Claude environment?~~ → **Decided:** No live Granola; packaged fixtures only.
3. What are the actual required fields and picklist values in `discovery-dev`? (partially validated — see metadata findings; StageName picklist still confirm at write time via `getObjectSchema`)
4. Should Opportunity Contact Roles be created in the happy-path demo, or Opportunity-only for simplicity? → **Skill default:** OCR create for **existing** matched Contacts after Opp create (see `salesforce-writes.md`).
5. What StageName and default CloseDate heuristic should the Skill propose when the meeting lacks a timeline? → CloseDate: future vs today; ask if unknown. StageName: only org-valid picklist values from schema.

---

## Salesforce metadata findings (`discovery-dev`)

| Topic | Finding | Dataset response |
|---|---|---|
| Account.Type | No `Customer - Prospect`; has `Prospect`, `Customer - Direct`, … | Use `Prospect` / `Customer - Direct` |
| Opportunity.Type | Values are `New Customer`, `Existing Customer - Upgrade`, etc. (not `New Business`) | Adjusted fixtures |
| Opportunity.LeadSource | `Web`, `Phone Inquiry`, `Partner Referral`, `Purchased List`, `Other` | Adjusted fixtures |
| Task.Type | **Field does not exist** | Local `activity_kind` only; omit Type on insert |
| Task.TaskSubtype | Createable; values include `Task`, `Email`, … **no Meeting** | Meetings → `TaskSubtype=Task`; emails → `Email` |
| OCR.Role | Includes Business User, Decision Maker, Technical Buyer, … | Fixtures use valid roles |
| Create permissions | Account, Contact, Opportunity, Task, OCR all createable | Import feasible after approval |
| Name conflicts | No matching synthetic Account/Contact/Opportunity names/emails found | Safe to insert as new records |

## Scenario 4 meeting coverage

SCENARIO-04 uses dedicated networking meeting `MTG-004` + meeting Task `TSK-009` (and follow-up email `TSK-010`). No new Opportunity should be created.

## Change Log

| Date | Change |
|---|---|
| 2026-11-12 | Initial demo decisions captured during foundation phase |
| 2026-11-12 | Added org metadata validation findings; adjusted picklists; documented Scenario 4 email-only design |
| 2026-11-12 | Expanded to 4 Granola meetings / 4 meeting Tasks / 6 emails; Scenario 4 is networking meeting-based |
| 2026-11-12 | Rewrote synthetic content for Apollo ICP (GTM personas, Apollo-relevant discovery, Cascade initiative split, Northwind B2B motion) |
| 2026-11-12 | Account import fix: State/Country picklists enabled — added BillingCountry/BillingCountryCode + full state names/codes |
| 2026-11-12 | Loader create path switched from fragile `sf data create record -v` to `sf api request rest` JSON body for all objects |
| 2026-11-12 | Full 30-record import verified in `discovery-dev` (pre–MTG-005 seed) |
| 2026-11-16 | Retired `docs/checkpoint.md`; still-relevant status/open work migrated into this file. Merged `tests/test-guide.md` into `tests/scenarios.md`. Removed stale Skill zip; package source = Skill folder |
| 2026-11-16 | Packaged simulated Granola into Skill `fixtures/`; Claude.ai cannot read repo `data/` |
| 2026-11-16 | Product UX refinement: meeting confirm, buying-interest outcomes, BANT+MEDDPICC coaching, AE handoff note; writes still off. Note createable; ContentNote not confirmed in org |
| 2026-11-16 | Retimed fixtures to Oct–Nov 2026; added MTG-005 (SDR pilot continuation). Local Opp CloseDates + Task ActivityDates updated for demo currency; **live SF org not modified** (re-import required later for CRM date parity). Recent-meeting + historical initiative-status rules documented |
| 2026-11-16 | AE handoff destination switched to `Opportunity.Handoff_Notes__c` (readable; create/update unverified). Classic Note no longer primary handoff path |
| 2026-11-16 | Confirm-first Salesforce retrieval SOQL documented; writes remain planned behind approval (CLI schema createable; MCP write E2E not tested). Not permanently read-only |
| 2026-11-16 | Consolidated Claude Salesforce MCP to `sobject-all` (Free-plan one-connector limit). Docs: never delete; approval before writes; secrets stay out of repo |
| 2026-11-16 | Skill write workflow documented with actual MCP tools (`mcp__Salesforce__createSobjectRecord`, `soqlQuery`, `getObjectSchema`, …); handoff on Opp create; OCR after; verify before success |
| 2026-11-16 | Docs/readiness pass: precise validation inventory; fixed stale “scaffolded / writes off” architecture status; noted Cursor session has no Salesforce MCP tools |
