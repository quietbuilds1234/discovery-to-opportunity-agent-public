# Salesforce Write Workflow (Hosted MCP `sobject-all`)

Write path for Opportunity + OpportunityContactRole + `Handoff_Notes__c` after **explicit** rep approval.  
Connector architecture: project `docs/architecture.md`. Retrieval/SOQL: `salesforce-retrieval.md`. Field mapping: `salesforce-field-mapping.md`.

**Deletion may be available through the connected `sobject-all` MCP server, but it is outside this Skill’s permitted workflow.** The Skill must **never** use deletion and must **not** delete Salesforce records under any circumstances. Do not invent or invoke delete tools.

## Actual connected MCP tools

Use these **exact** tool names (do not invent aliases like `describe_sobject`, `create_record`, `update_record`):

### Read

| Tool | Use |
|---|---|
| `mcp__Salesforce__soqlQuery` | Primary SOQL retrieval (full query string; no Apex binds) |
| `mcp__Salesforce__find` | Optional targeted find when appropriate |
| `mcp__Salesforce__getRelatedRecords` | Related records when useful |
| `mcp__Salesforce__listRecentSobjectRecords` | Recent records when useful |
| `mcp__Salesforce__getObjectSchema` | Fields + picklists (e.g. StageName, OCR Role) before create |

### Create

| Tool | Inputs |
|---|---|
| `mcp__Salesforce__createSobjectRecord` | `sobject-name` (string), `body` (object) |

### Update

| Tool | Inputs |
|---|---|
| `mcp__Salesforce__updateSobjectRecord` | `sobject-name`, `id`, `body` |
| `mcp__Salesforce__updateRelatedRecord` | Related-record updates when applicable |

### Identity

| Tool | Use |
|---|---|
| `mcp__Salesforce__getUserInfo` | Connected user context when helpful |

Prefer `createSobjectRecord` for new Opp / OCR. Prefer putting `Handoff_Notes__c` on the **initial Opportunity create** `body` (avoid a separate update unless create rejected the field).

---

## Mandatory approval gate

**Order:**

1. Meeting confirm + transcript analysis  
2. CRM retrieval (reads only)  
3. Qualify + duplicate detection  
4. Clarification questions  
5. Complete Opportunity + OCR + AE handoff **preview** (Opp fields + associations; full `Handoff_Notes__c` reviewable before approve)  
6. Ask for **explicit** approval of **that** preview  
7. **Only then** call `createSobjectRecord` for Opportunity  
8. Create OCRs for existing Contacts  
9. Verify via read tools (`soqlQuery` / related reads)  
10. Report Ids / success / partial failures  

**Rules:**

- **No mutation tool** before explicit approval of the **exact** Opportunity + OCR preview:  
  `mcp__Salesforce__createSobjectRecord`, `mcp__Salesforce__updateSobjectRecord`, `mcp__Salesforce__updateRelatedRecord`.  
- Approval applies to that **specific preview**. If Name, StageName, CloseDate, AccountId, Amount, Description, NextStep, `Handoff_Notes__c`, or OCR associations change materially → obtain approval again before any mutation.  
- Do **not** treat “looks good,” “thanks,” or general agreement as create approval. Require clear create intent (e.g. “yes, create it,” “approved — create the Opportunity”).  
- Analyzing a meeting is **not** approval.  
- **Do not enter the write path** for `EXISTING OPPORTUNITY` or `DO NOT CREATE` / `INSUFFICIENT INFORMATION` (no new Opportunity create).  
- Write path assumes BANT/MEDDPICC coaching and AE handoff preview already ran in Layer A/B — writes do not replace qualification.

---

## Opportunity create

### Pre-create guards (after approval, before mutation)

1. Confirm approval still applies to the current preview (no material edits since approval).  
2. **Re-check duplicate Opportunities** with a read (`mcp__Salesforce__soqlQuery` open Opps on AccountId): if a same-initiative open Opp now exists → **stop**; switch to EXISTING; do **not** create.  
3. Confirm required fields Name, StageName, CloseDate are present and valid; AccountId present when Account was confirmed.

### Schema / picklists

Before first create in a session (or when Stage/Role unsure):

1. Call `mcp__Salesforce__getObjectSchema` for `Opportunity` (and `OpportunityContactRole` when proposing Roles).  
2. Use **only valid `StageName` picklist values** from schema.  
3. MCP schema may **not** expose definitive createable/updateable or FLS flags — **do not** assume every schema field is writable. Handle permission / validation / FLS errors explicitly.

### Required fields (Opportunity)

| Field | Rule |
|---|---|
| `Name` | Required — from initiative; ask if unclear |
| `StageName` | Required — valid picklist value only |
| `CloseDate` | Required — future vs today; ask if unknown; never invent silently |
| `AccountId` | Include when Account resolved and confirmed |

**Do not invent values** to satisfy required fields. If a required field is unknown → ask the rep or **stop before creation**.

### Optional fields

Populate only when supported by meeting evidence, CRM, or rep clarification: `Amount`, `Type`, `LeadSource`, `NextStep`, etc.

### Description vs handoff

- `Description` — **concise** business need / use case only.  
- `Handoff_Notes__c` — full structured AE handoff (headings in `SKILL.md` / field-mapping). Stay ≤ 32,768 chars.  
- Prefer `Handoff_Notes__c` **in the same create `body`** as Name/StageName/CloseDate/AccountId.

### Example create shape

```json
{
  "sobject-name": "Opportunity",
  "body": {
    "Name": "Meridian Robotics - SDR Outbound & Contact Data Pilot",
    "AccountId": "001XXXXXXXXXXXXXXX",
    "StageName": "Prospecting",
    "CloseDate": "2027-01-31",
    "Description": "SDR research time and contact-data quality pilot for mid-market warehouse outbound.",
    "NextStep": "Pilot scoping / field-mapping for staged Salesforce write-back.",
    "Handoff_Notes__c": "=== Executive Summary ===\n..."
  }
}
```

Tool: `mcp__Salesforce__createSobjectRecord`.

---

## Opportunity Contact Roles

**Only after** Opportunity create returns a Salesforce Id.  
**Only** Contacts that (a) already exist in Salesforce with a resolved Contact Id, and (b) appeared on the **approved** OCR preview.

1. Query existing OCRs for that Opportunity via `mcp__Salesforce__soqlQuery` — skip any `ContactId` already linked (no duplicate OCRs).  
2. For each approved preview Contact with a resolved Salesforce `ContactId`:  
   `mcp__Salesforce__createSobjectRecord` with `sobject-name: "OpportunityContactRole"`.  
3. Required: `OpportunityId`, `ContactId`.  
4. **Default create body:** `OpportunityId` + `ContactId` only.  
   - Include `Role` only when transcript/CRM/rep clarification **establishes** a valid picklist Role (not job title, not attendance alone).  
   - Include `IsPrimary: true` only when the **approved preview** explicitly designates that Contact as primary **and** evidence supports it. Otherwise **omit** `IsPrimary` (do not default it to true).  
5. **Do not** create new Contacts (`sobject-name: "Contact"` is forbidden in this workflow).  
6. If an attendee has **no** Salesforce Contact Id → skip OCR for them; do **not** auto-create a Contact.  
7. **Do not** infer Role from job title alone.  
8. **Do not** map Champion → Economic Buyer or Decision Maker.  
9. If Role is unclear → omit Role (still create OCR with OpportunityId + ContactId if association is warranted) rather than inventing.

Default example (Role / IsPrimary omitted — safest when evidence is incomplete):

```json
{
  "sobject-name": "OpportunityContactRole",
  "body": {
    "OpportunityId": "006XXXXXXXXXXXXXXX",
    "ContactId": "003XXXXXXXXXXXXXXX"
  }
}
```

Only when Role **and** primary designation are evidenced **and** on the approved preview:

```json
{
  "sobject-name": "OpportunityContactRole",
  "body": {
    "OpportunityId": "006XXXXXXXXXXXXXXX",
    "ContactId": "003XXXXXXXXXXXXXXX",
    "Role": "Decision Maker",
    "IsPrimary": true
  }
}
```

---

## Verification (required before claiming success)

After creates:

1. `mcp__Salesforce__soqlQuery` (or `find` / related reads) the Opportunity by Id — confirm Name, AccountId, StageName, CloseDate, and `Handoff_Notes__c` as expected for the approved preview.  
2. Query `OpportunityContactRole` where `OpportunityId = …` — confirm associations.  
3. Report **full success** only when: create returned an Id **and** verification reads succeed for Opp + intended OCRs.  
4. Partial OCR success → report **partial success** (Opp Id + which OCRs ok/failed) — never label as full success.  
5. Never claim success from a create tool response alone without verification reads.

---

## Error handling and partial failures

| Situation | Behavior |
|---|---|
| Opportunity create fails | Do **not** create OCRs. Report error. Keep preview for the rep. |
| Opportunity succeeds; OCR fails | Preserve Opportunity. Report which OCR associations succeeded/failed. Do not delete the Opp. |
| Ambiguous timeout on create | **Do not** blind-retry create. Query Salesforce first (Name/Account/recent Opps) to see if the record exists. If found, treat as created and continue to OCR/verify; if not found, report failure and wait for rep guidance. |
| `Handoff_Notes__c` rejected on create | Do **not** silently drop the handoff. Report the error; preserve drafted notes; optionally retry Opp without handoff only if rep approves, then attempt `mcp__Salesforce__updateSobjectRecord` for `Handoff_Notes__c` with re-approval if material. |
| Permission / validation / FLS error | Surface Salesforce message; do not invent alternate field values. |
| Partial failure recovery | **Never** delete to “undo.” Deletion may exist on the MCP server but is outside this Skill’s workflow — do not invent or invoke delete tools. |

---

## Permissions and schema limitations

- `getObjectSchema` informs fields and picklists; it may **not** prove FLS or createable flags.  
- Do not claim all schema fields are writable.  
- Prefer least-privilege Salesforce user configuration for the connected org user (org-side; outside this Skill package).
