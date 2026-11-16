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
| Cascade OPP-002 ≠ MTG-002 initiative | Partner-lead enrichment vs hospital buying-group outbound — prevents false duplicate flags |

---

## Technical Decisions

| Decision | Rationale |
|---|---|
| No custom backend / no custom MCP | Keeps scope fit for a ~3-hour interview build |
| Standard Salesforce objects only | Portable, easier to demo, avoids org-specific customization debt |
| Synthetic data for demo | Repeatable scenarios; no real customer data |
| Local SF CLI (`discovery-dev`) for seeding/inspection only | Useful for prep; not the same as Claude runtime CRM access |
| Clearly labeled Granola fixtures as fallback | Demo reliability if Granola access is unavailable |
| Distinguish implemented vs planned in docs | Credibility in interview; no vaporware claims |

---

## Integration Assumptions (Must Validate)

| Assumption | Current status | If invalid |
|---|---|---|
| Claude can access Salesforce at runtime via a supported connection | **Unvalidated** | Demo reads/writes against pre-seeded org only if a real connection is configured; otherwise show proposal flow with fixtures and document write path as planned |
| Salesforce CLI alias `discovery-dev` is authenticated locally | **Validated Connected** (username `discovery-dev authenticated Salesforce user`) | Re-authenticate only if connection expires |
| Granola is available to Claude for meeting retrieval | **Unvalidated** | Use `data/granola_meetings.json` fixtures, clearly labeled synthetic |
| Meetings / Gong emails appear as Salesforce Tasks | **Demo convention** | Seed Tasks that represent those activities |
| Required Opportunity fields are Name, AccountId, StageName, CloseDate (typical) | **Validated:** Name, StageName, CloseDate required; AccountId createable but nillable | Keep AccountId populated in fixtures |

---

## Demo Data Shape (Planned)

- 3 Accounts
- 8 Contacts
- 4 Opportunities
- 10 Tasks
- 4–6 Opportunity Contact Roles
- 4 Granola-style discovery/networking meeting records
- 10 Tasks = 4 meeting + 6 Gong email

### Scenario Mapping (Planned)

| Scenario | Intended outcome | Meeting |
|---|---|---|
| Strong legitimate opportunity | CREATE (allow despite MEDDPICC gaps) | MTG-001 |
| Early-stage legitimate opportunity | CREATE WITH GAPS (still allow proceed) | MTG-002 |
| Existing / matching Opportunity | EXISTING OPPORTUNITY (no auto-duplicate) | MTG-003 |
| Weak / nonexistent opportunity | Decline create; explain lack of opportunity (not “missing MEDDPICC”) | MTG-004 |

---

## Explicit Non-Claims

Until implemented and tested, do **not** claim:

- Live Granola transcript retrieval works
- Claude automatically has Salesforce access because the CLI is logged in
- Opportunity creation works end-to-end
- Any specific Salesforce picklist value or required-field set without org validation

---

## Open Questions for Next Phase

1. Which supported Salesforce runtime connection will the Skill use?
2. Can Granola meeting data be accessed in the demo Claude environment?
3. What are the actual required fields and picklist values in `discovery-dev`?
4. Should Opportunity Contact Roles be created in the happy-path demo, or Opportunity-only for simplicity?
5. What StageName and default CloseDate heuristic should the Skill propose when the meeting lacks a timeline?

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
| 2026-11-12 | Full 30-record import verified in `discovery-dev`; end-of-day checkpoint in `docs/checkpoint.md` |
