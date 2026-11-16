# Salesforce Field Mapping + AE Handoff

Standard objects plus org custom field `Handoff_Notes__c`.  
**MCP:** one Claude connector — Hosted MCP **`sobject-all`** (see project `docs/architecture.md`).  
**Reads:** `salesforce-retrieval.md` (`mcp__Salesforce__soqlQuery`, `getObjectSchema`, …).  
**Writes:** `salesforce-writes.md` — `mcp__Salesforce__createSobjectRecord` / `updateSobjectRecord` only after explicit approval; **never delete**; **do not create Contacts**.

Use `mcp__Salesforce__getObjectSchema` for fields and picklists. Schema may omit createable/FLS flags — do not assume every field is writable; handle permission errors explicitly.

## Identifier rules

| Local key | Salesforce |
|---|---|
| `ACC-*` / `CON-*` / `OPP-*` / `TSK-*` / `OCR-*` | Resolve to 18-char Ids via MCP — never submit synthetic keys as Ids |
| `MTG-*` | Meeting fixture only — not a Salesforce object |

## Opportunity create body (after approval)

| Field | Required | Guidance |
|---|---|---|
| Name | **Yes** | `{Account} - {initiative}`; ask if unclear — do not invent |
| StageName | **Yes** | **Only** valid picklist values from `getObjectSchema` |
| CloseDate | **Yes** | Future vs today; ask if unknown |
| AccountId | When resolved | Confirmed Account Id |
| Amount | No | Only if evidenced |
| Type / LeadSource | No | Only if known |
| Description | No | **Concise** need/use case — not the full handoff |
| NextStep | No | From agreed next steps |
| **Handoff_Notes__c** | Product-required on create-path | Full AE handoff; prefer on **initial create** |

Also show **Business Need** in the conversational preview (maps into Description).

Allow the rep to edit proposed values before approval. Re-approve if material fields change after approval.

## AE Discovery Handoff → `Opportunity.Handoff_Notes__c`

| Property | Value |
|---|---|
| API Name | `Handoff_Notes__c` |
| Label | Handoff Notes |
| Type | Long Text Area; max **32,768** |
| Write | Prefer in Opportunity `createSobjectRecord` `body` |

### Handoff plain-text structure

```text
=== Executive Summary ===
...
=== Business Pain ===
...
=== Apollo Use Case ===
...
=== BANT ===
...
=== MEDDPICC ===
...
=== Stakeholders ===
...
=== Customer Goals and Objections ===
...
=== Commitments and Next Steps ===
...
=== Outstanding AE Discovery Questions ===
...
=== Evidence Sources ===
Meeting / CRM / Rep clarification
```

Label Confirmed / Inferred / Unknown. Never dump the raw transcript. If Salesforce rejects `Handoff_Notes__c`, report the error and preserve the draft — do not silently discard.

## OpportunityContactRole create body

| Field | Required | Guidance |
|---|---|---|
| OpportunityId | **Yes** | From successful Opp create |
| ContactId | **Yes** | Existing Contact only |
| Role | No | Valid picklist only; evidence-based; **not** from title or attendance alone; omit when unclear |
| IsPrimary | No | Omit by default; set true only when approved preview explicitly designates primary **and** evidence supports it |

Query existing OCRs before create; skip ContactIds already linked. Skip attendees without a Salesforce Contact Id — never auto-create Contacts. Do not map Champion → Economic Buyer / Decision Maker. Default OCR body is OpportunityId + ContactId only.

## Task interpretation

`[Gong]` subjects = CRM breadcrumbs — not transcript substitutes.
