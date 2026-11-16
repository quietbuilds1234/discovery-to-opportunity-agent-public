# Test Scenarios

Shared synthetic dataset for the Discovery-to-Opportunity Agent, framed as an **Apollo** AE turning discovery into Salesforce Opportunities.

All scenarios use the same `data/` fixtures. MEDDPICC gaps never by themselves mean “do not create.”

---

## SCENARIO-01 — Strong legitimate opportunity

| Field | Value |
|---|---|
| **Objective** | Propose Opportunity creation when Apollo-relevant pain, use case, engaged stakeholders, and next step are clear — even with MEDDPICC gaps. |
| **Expected outcome** | `CREATE` |
| **Account** | `ACC-001` Meridian Robotics |
| **Contacts** | `CON-001` Jordan Blake (VP Sales), `CON-002` Sam Rivera (SDR Manager), `CON-003` Casey Nguyen (Sales Ops) |
| **Opportunities (context)** | `OPP-001` Apollo platform for AE team (different initiative), `OPP-004` Closed Lost contact-data vendor |
| **Tasks** | Meeting `TSK-001`; emails `TSK-004`, `TSK-005` |
| **Granola meeting** | `MTG-001` — SDR outbound research burden + Salesforce contact hygiene |
| **MEDDPICC gaps** | Full Economic Buyer / Finance unknown; Paper Process unknown; quantified $ ROI incomplete; Competition only lightly mentioned |
| **Why it matters** | Enrichment ≠ gatekeeping. Missing Finance sign-off must not block a legitimate Apollo pilot-oriented Opportunity. |

### Expected agent behavior

- Identify Meridian account and GTM attendees.
- Propose a **new** Opportunity for SDR outbound / contact-data productivity (not the AE platform deal in `OPP-001`).
- Do **not** treat `OPP-001` as a duplicate of this initiative.
- Show MEDDPICC gaps + skippable follow-up questions.
- Allow proceed after explicit approval.

---

## SCENARIO-02 — Early-stage opportunity with gaps

| Field | Value |
|---|---|
| **Objective** | Allow creation when Apollo interest and need exist but qualification is thin. |
| **Expected outcome** | `CREATE WITH GAPS` |
| **Account** | `ACC-002` Cascade Health Partners |
| **Contacts** | `CON-004` Avery Patel (VP Sales), `CON-005` Riley Chen (Senior SDR); `CON-006` Quinn Morgan (RevOps) absent |
| **Opportunities (context)** | `OPP-002` Apollo **Partner Lead Enrichment** — clearly different initiative |
| **Tasks** | Meeting `TSK-002`; emails `TSK-006`, `TSK-007` |
| **Granola meeting** | `MTG-002` — hospital/clinic buying-group identification + CRM contact quality |
| **MEDDPICC gaps** | Metrics, Economic Buyer, Decision Process, Paper Process, Competition largely UNKNOWN; Champion not confirmed; timeline uncertain |
| **Why it matters** | Early Apollo deals are common. Agent should coach, not block — and must not confuse this with `OPP-002`. |

### Expected agent behavior

- Propose a new Opportunity for hospital-account buying-group / enrichment use case.
- **Do not** flag as duplicate of `OPP-002` (partner-sourced lead enrichment).
- Label many MEDDPICC fields UNKNOWN/INFERRED with evidence.
- Offer skippable follow-up questions; allow proceed without answering all after approval.

---

## SCENARIO-03 — Existing Opportunity

| Field | Value |
|---|---|
| **Objective** | Detect matching open Apollo deal and prevent automatic second create. |
| **Expected outcome** | `EXISTING OPPORTUNITY` |
| **Account** | `ACC-001` Meridian Robotics |
| **Contacts** | `CON-001`, `CON-002`, `CON-003` |
| **Opportunities** | **`OPP-001` Meridian Robotics - Apollo Sales Intelligence Platform** |
| **Tasks** | Meeting `TSK-003`; email `TSK-008` |
| **Granola meeting** | `MTG-003` |
| **MEDDPICC gaps** | Finance / full Economic Buyer still open — not the reason to block |
| **Why it matters** | Duplicate Opportunities corrupt pipeline forecasts. |

### Expected agent behavior

- Match meeting topic to `OPP-001` by account + Apollo platform initiative language.
- Surface historical Tasks/`OPP-001` context.
- Ask associate vs investigate — **never auto-create a duplicate**.

---

## SCENARIO-04 — No legitimate sales opportunity

| Field | Value |
|---|---|
| **Objective** | Distinguish “no opportunity” from “opportunity with MEDDPICC gaps.” |
| **Expected outcome** | `INSUFFICIENT INFORMATION` **or** explicit recommendation **not to create** |
| **Account** | `ACC-003` Northwind Retail Group (existing Apollo customer; B2B wholesale + enterprise partnerships) |
| **Contacts** | `CON-007` Taylor Brooks (Partnerships), `CON-008` Morgan Ellis (CEO, social only) |
| **Opportunities (context)** | `OPP-003` Closed Won Apollo platform (historical) |
| **Tasks** | Meeting `TSK-009`; email `TSK-010` |
| **Granola meeting** | `MTG-004` networking coffee — no expansion initiative |
| **MEDDPICC gaps** | N/A framing — absence of a buying initiative, not missing qualification on a real deal |
| **Why it matters** | Prevents junk Opportunities from networking with existing customers. |

### Expected agent behavior

- Recognize networking / relationship maintenance only.
- Explain lack of business problem, new Apollo use case, and buying intent.
- Do **not** create a new Opportunity.
- Do **not** justify primarily as “MEDDPICC incomplete.”

---

## Scenario × fixture map

| Scenario | Meeting | Account | Primary create target? |
|---|---|---|---|
| SCENARIO-01 | MTG-001 | ACC-001 | New Opp (SDR outbound / contact data) |
| SCENARIO-02 | MTG-002 | ACC-002 | New Opp (hospital buying groups) — not OPP-002 |
| SCENARIO-03 | MTG-003 | ACC-001 | None — use existing OPP-001 |
| SCENARIO-04 | MTG-004 | ACC-003 | None — do not create |
