# Salesforce Retrieval Strategy (Hosted MCP / SOQL)

CRM **read** path for Opportunity recommendation and AE handoff quality.  
**Meeting identification uses packaged fixtures only — no Salesforce queries before the rep confirms the meeting.**

This Skill uses **one** Claude Salesforce connector: Hosted MCP **`sobject-all`** (reads + mutations). Connector choice, Free-plan limit, and delete risk are documented in project **`docs/architecture.md`**. This file covers **retrieval / SOQL only**. Writes remain behind explicit approval; **never delete**.

## Hosted MCP read tools (exact names)

| Tool | Role |
|---|---|
| `mcp__Salesforce__soqlQuery` | Primary SOQL (full query **string**; no Apex binds) |
| `mcp__Salesforce__find` | Optional targeted find |
| `mcp__Salesforce__getRelatedRecords` | Related records when useful |
| `mcp__Salesforce__listRecentSobjectRecords` | Recent records when useful |
| `mcp__Salesforce__getObjectSchema` | Fields / picklists before create preview |
| `mcp__Salesforce__getUserInfo` | Connected user identity when helpful |

**`soqlQuery` constraint:** pass a complete SOQL string. It does **not** document a separate bind-variable parameter.

**Do not use Apex-style binds** such as `:accountId`, `:accountName`, `:attendeeEmails`.  
Build literals (quoted strings / Id values / IN lists) before calling `mcp__Salesforce__soqlQuery`.

Do not use hypothetical names (`describe_sobject`, etc.). Writes: `salesforce-writes.md`.

## Safe SOQL string construction

Before inserting any runtime value into the query string:

1. **Strings (Name, Email, LIKE patterns):** wrap in single quotes. Escape each embedded apostrophe by doubling it (`O'Brien` → `'O''Brien'`).  
2. **Ids (AccountId, WhatId, OpportunityId):** 15/18-char Salesforce Ids are unquoted alphanumeric — validate shape (`^[a-zA-Z0-9]{15}([a-zA-Z0-9]{3})?$`) before interpolating; never paste untrusted free text as an Id.  
3. **LIKE patterns:** escape `'` as above; escape literal `%` / `_` in user input with `\` if treating them as literals; for “contains name” use `'%' + escapedName + '%'`. Do not pass an unescaped raw pattern.  
4. **IN lists:** build `('a','b')` or `('001...','001...')` with each element escaped/validated.  
5. **Empty IN lists:** SOQL `IN ()` is invalid. If emails and names are both empty → **skip B1** (treat as zero Contacts). If only one list is non-empty → omit the empty side (`Email IN (...)` **or** `Name IN (...)`, not `OR` with an empty list). If candidate Opp Ids is empty → **skip D1**.  
6. Never concatenate unsanitized rep free-text into SOQL.

Illustrative helper (pseudocode):

```text
soql_str(s)  = "'" + s.replace("'", "''") + "'"
soql_like(s) = "'" + "%" + s.replace("'", "''").replace("%","\\%").replace("_","\\_") + "%" + "'"
soql_in_strs(vals) = "(" + ", ".join(soql_str(v) for v in vals) + ")"   # only if vals non-empty
soql_in_ids(ids)   = "(" + ", ".join(ids) + ")"   # only if ids non-empty and each validates as SF Id
```

---

## Sequence (after meeting confirmation)

| Step | Purpose | Typical MCP calls |
|---|---|---|
| 0 | Confirm meeting from `fixtures/granola_meetings.json` | **0 SF calls** |
| 1 | Analyze full transcript locally | **0 SF calls** |
| A | Resolve Account | 1 targeted Account query |
| B | Resolve attendee Contacts on that Account | 1 Contact query (batched) — skip if no emails/names |
| C | Load Opportunities for duplicate / initiative check | 1–2 Opportunity queries |
| D | Optional: OCRs for candidate matching Opp(s) | 0–1 OCR query — skip if no candidate Ids |
| E | Optional: recent Tasks on Account (and matching Opp if any) | 0–1 Task query |
| — | Reuse results for the rest of the Skill run | **no repeats** |

Skip D/E when buying interest is clearly none (e.g. networking-only) and Account resolution already suffices to explain “no create.” Prefer accuracy when duplicate risk or handoff quality needs the evidence.

## Session cache (avoid repeats)

Within one Skill run, keep and reuse:

- `accountId`, Account Name  
- Contact Id ↔ name/email map for attendees  
- Opportunity list for the Account (open + relevant closed)  
- Any OCR / Task rows already fetched  

Do **not** re-query the same Account/Contacts/Opportunities unless the rep corrects the Account match or MCP returned an error and a retry is warranted.

## Error handling

| Situation | Behavior |
|---|---|
| Zero Account matches | Say so; ask rep to clarify company name. Do **not** invent CRM. |
| Multiple / ambiguous Account matches | List Name + Id (+ Website if available); ask rep to choose before Contacts/Opps. |
| Zero Contacts / skipped empty IN | Continue with Unknown stakeholders; ask only if OCR preview needs them. |
| Multiple Contacts for one attendee | Prefer Email match; else ask rep. |
| Empty Opportunity results (0 rows) | Valid “no Opps on Account” for duplicate check — still allow CREATE if meeting shows initiative; do **not** invent Opps. |
| Opportunity / Task query **failure** | State failure; **never** treat failure as “no Opportunity exists” (unlike empty success). Ask rep or retry once. |
| Incomplete / ambiguous CRM | Ask rep (Rep clarification); do not guess. |

Evidence labels stay distinct: **Meeting** | **CRM** | **Rep clarification**.

---

## Documented SOQL (literal query strings for `soqlQuery`)

Examples use Meridian demo values. At runtime, substitute with escaped/validated literals from the confirmed meeting + prior query results. Pass the **full string** to `mcp__Salesforce__soqlQuery`.

### A1 — Account by exact Name (preferred first)

```soql
SELECT Id, Name, Website, Industry, Type
FROM Account
WHERE Name = 'Meridian Robotics'
LIMIT 5
```

Construction: `WHERE Name = ` + `soql_str(account_name)`.

### A2 — Account fallback (partial Name) — only if A1 returns 0

```soql
SELECT Id, Name, Website, Industry, Type
FROM Account
WHERE Name LIKE '%Meridian Robotics%'
ORDER BY Name
LIMIT 10
```

Construction: `WHERE Name LIKE ` + `soql_like(account_name)`. Still ask the rep if >1 row.

### B1 — Contacts for meeting attendees (single query)

After `accountId` is known. Prefer Email when the fixture has emails; otherwise Name.  
**Skip entirely** if both attendee email and name lists are empty.

```soql
SELECT Id, AccountId, FirstName, LastName, Name, Email, Title
FROM Contact
WHERE AccountId = 001XXXXXXXXXXXXXXX
  AND (
    Email IN ('jordan.blake@meridian-robotics.example.com', 'sam.rivera@meridian-robotics.example.com', 'casey.nguyen@meridian-robotics.example.com')
    OR Name IN ('Jordan Blake', 'Sam Rivera', 'Casey Nguyen')
  )
LIMIT 20
```

Construction notes:

- `AccountId = ` + validated Id (unquoted).  
- Build `Email IN (...)` only if emails non-empty; `Name IN (...)` only if names non-empty.  
- If both non-empty: `( Email IN (...) OR Name IN (...) )`.  
- If only emails: `AND Email IN (...)`. If only names: `AND Name IN (...)`.  
- Escape each string with `soql_str`.

**Fields:** Id, Name/Email (match), Title (display only — **do not infer buying role**).  
**Dropped:** `Phone`.

### C1 — Opportunities on Account (open + capped history)

Prefer **two short queries** when an Account may have a long closed history. Demo Accounts are small; either pattern is acceptable.

**C1a — all open Opportunities (required for duplicate check)**

```soql
SELECT Id, AccountId, Name, StageName, CloseDate, Amount,
       Description, NextStep, IsClosed, IsWon, LastModifiedDate
FROM Opportunity
WHERE AccountId = 001XXXXXXXXXXXXXXX
  AND IsClosed = false
ORDER BY CloseDate ASC
LIMIT 20
```

**C1b — recent closed context only**

```soql
SELECT Id, AccountId, Name, StageName, CloseDate, Amount,
       Description, NextStep, IsClosed, IsWon, LastModifiedDate
FROM Opportunity
WHERE AccountId = 001XXXXXXXXXXXXXXX
  AND IsClosed = true
ORDER BY CloseDate DESC
LIMIT 10
```

**Single-query alternative** (small Accounts; still capped):

```soql
SELECT Id, AccountId, Name, StageName, CloseDate, Amount,
       Description, NextStep, IsClosed, IsWon, LastModifiedDate
FROM Opportunity
WHERE AccountId = 001XXXXXXXXXXXXXXX
ORDER BY IsClosed ASC, CloseDate DESC
LIMIT 25
```

Construction: substitute validated `accountId`.  
**Dropped from list queries:** `Type`, `LeadSource`, `CreatedDate`, `Handoff_Notes__c` (fetch on a candidate Opp Id only if needed).

### D1 — OpportunityContactRoles for candidate Opp(s) only

**Skip if** candidate Opp Id list is empty. Cap Ids (e.g. top 1–3).

```soql
SELECT Id, OpportunityId, ContactId, Role, IsPrimary
FROM OpportunityContactRole
WHERE OpportunityId IN ('006XXXXXXXXXXXXXXX', '006YYYYYYYYYYYYYYY')
LIMIT 50
```

Construction: `WHERE OpportunityId IN ` + `soql_in_ids(candidate_ids)`.

### E1 — Recent Tasks on Account (optional)

```soql
SELECT Id, Subject, ActivityDate, Description, WhoId, WhatId, TaskSubtype
FROM Task
WHERE WhatId = 001XXXXXXXXXXXXXXX
ORDER BY ActivityDate DESC NULLS LAST
LIMIT 15
```

### E2 — Tasks on a matching Opportunity (optional)

```soql
SELECT Id, Subject, ActivityDate, Description, WhoId, WhatId, TaskSubtype
FROM Task
WHERE WhatId = 006XXXXXXXXXXXXXXX
ORDER BY ActivityDate DESC NULLS LAST
LIMIT 10
```

---

## How duplicate detection uses this data

1. From the **meeting transcript**, extract initiative / use case / product scope / timing / stakeholder language.  
2. From **C1**, compare each Account Opportunity’s Name, Description, NextStep, Stage, open/closed status.  
3. Same initiative → `EXISTING OPPORTUNITY` (surface Id/Name/Stage; associate vs investigate; **no new create**).  
4. Different initiative on same Account (e.g. SDR pilot vs AE platform; hospital buying groups vs partner-lead enrichment) → allow CREATE path.  
5. Optional **D1/E1/E2** only to strengthen or refute a borderline match.  
6. Failed Opportunity query ≠ “safe to create.”

### MTG-001 ↔ MTG-005 (same SDR / contact-data initiative)

| CRM state when analyzing | Meeting | Expected behavior |
|---|---|---|
| No open Opp for SDR/contact-data pilot (seeded demo; only OPP-001 platform + OPP-004 Closed Lost) | MTG-001 or MTG-005 | **CREATE** path (005: confirm initiative still active first). Do **not** merge into OPP-001. |
| Open Opp already exists for the SDR/contact-data pilot (e.g. after MTG-001 was created) | MTG-005 | **EXISTING OPPORTUNITY** — associate/update handoff; **do not** create a second SDR Opp. |
| Same as row above | MTG-001 (historical) | Confirm status; if Opp exists → EXISTING; if still none and initiative active → CREATE (prefer pointing rep at MTG-005 if newer). |

---

## Queries explicitly avoided

- Any Salesforce query before meeting confirmation  
- Apex bind variables (`:name`) — **unsupported** by Hosted MCP `soqlQuery` as documented  
- Org-wide Account / Contact / Opportunity scans  
- One MCP call per Contact when B1 can batch  
- `IN ()` empty lists  
- Re-fetching the same AccountId’s Opps later in the same run  
- Broad Task history unrelated to the resolved Account / candidate Opp  

---

## Live MCP testing required

Until exercised through Claude’s Hosted MCP connection, treat as **unverified**:

- `soqlQuery` accepts the constructed string as expected  
- Apostrophe escaping and LIKE wildcards behave as intended  
- `IN` lists and Id literals parse correctly  
- `ORDER BY … NULLS LAST` supported in the org/API version  
- End-to-end Account → Contact → Opportunity retrieval for demo Accounts  

Do **not** claim live SOQL success without that run.

---

## Writes

Approval-gated create / OCR / verify using exact mutation tools is documented in **`salesforce-writes.md`**. Never delete.
