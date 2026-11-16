# Changelog — discovery-to-opportunity

All notable Skill package releases are documented here.  
Version is also recorded in `SKILL.md` frontmatter as `metadata.version` (Agent Skills / Claude Skills convention).

## [0.3.0] — 2026-11-16

First approval-gated Salesforce Opportunity creation and AE discovery handoff Skill package.

### Included

- **Discovery workflow** — confirm meeting from packaged simulated Granola fixtures → full transcript analysis → short Layer A coaching → Opportunity + AE handoff preview → explicit approval → create/verify
- **Outcomes** — CREATE, CREATE WITH GAPS, EXISTING OPPORTUNITY, DO NOT CREATE (INSUFFICIENT INFORMATION); BANT/MEDDPICC coaching (not gates)
- **Duplicate / initiative detection** — including MTG-001 → MTG-005 continuation (EXISTING if SDR Opp already present; never merge into AE-platform OPP-001)
- **Salesforce reads** — Hosted MCP `sobject-all`; confirm-first SOQL (`references/salesforce-retrieval.md`)
- **Writes (instructional)** — approval-gated `createSobjectRecord` for Opportunity (with `Handoff_Notes__c`) and OpportunityContactRole; OCR defaults omit Role/`IsPrimary` without evidence; never delete; verify before claiming success (`references/salesforce-writes.md`)

### Validation for this release

| Performed | Result |
|---|---|
| `scripts/validate_synthetic_data.py` | PASS |
| `tests/test_write_workflow_guards.py` (approval, duplicate re-check, OCR safeguards, handoff failure paths, MTG-001→MTG-005 EXISTING) | 30 tests PASS |
| Fixture/expected-outcome alignment for five demo meetings | Documented in repo tests/scenarios |

| Not performed | Notes |
|---|---|
| Live Claude MCP Opportunity create | Instructional path only |
| Live OCR / `Handoff_Notes__c` persistence + post-write verification | Not executed in a Claude session for this release tag |
