# Data Dictionary

Synthetic B2B demo dataset for the Discovery-to-Opportunity Agent, framed around **Apollo** (sales intelligence / GTM platform) selling into realistic prospect accounts.

All people, companies, emails, and Gong links are fictional. Domains use reserved `example.com` / `example.org` patterns.

Working ICP assumptions (not official Apollo thresholds): B2B orgs with sales/SDR/RevOps motions, Salesforce CRM usage, and pain around prospecting, enrichment, buyer identification, segmentation, or pipeline generation.

---

## Synthetic key conventions

| Object | Key pattern | Examples |
|---|---|---|
| Account | `ACC-00N` | ACC-001 … ACC-003 |
| Contact | `CON-00N` | CON-001 … CON-008 |
| Opportunity | `OPP-00N` | OPP-001 … OPP-004 |
| Task | `TSK-00N` | TSK-001 … TSK-010 |
| Opportunity Contact Role | `OCR-00N` | OCR-001 … |
| Granola meeting | `MTG-00N` | MTG-001 … MTG-004 |
| Gong activity id | `gong-act-…` | Local uniqueness only |
| Granola meeting id | `granola-syn-mtg-00N` | Local fixture id only |

**Never submit synthetic keys to Salesforce as Ids.** Salesforce Ids are generated on insert and stored only in the local gitignored map `data/.salesforce-id-map.json`.

---

## Datasets

### `accounts.json` → Salesforce Account

| Field | SF field | Notes |
|---|---|---|
| account_key | — | Internal only |
| Name | Name | Required |
| Website | Website | |
| Industry | Industry | Picklist |
| Type | Type | Picklist (org-validated) |
| Description | Description | Apollo-prospect positioning |
| BillingCity | BillingCity | |
| BillingState | BillingState | Full state name (e.g. Texas) |
| BillingStateCode | BillingStateCode | ISO-style code (e.g. TX); required when State/Country picklists enabled |
| BillingCountry | BillingCountry | e.g. United States |
| BillingCountryCode | BillingCountryCode | e.g. US; set whenever BillingState/StateCode is populated |
| NumberOfEmployees | NumberOfEmployees | Integer |

**Address note (`discovery-dev`):** State and Country Picklists are enabled (`BillingCountryCode` / `BillingStateCode` are restricted picklists). Country must be set before state. Use `US` + `TX`/`OR`/`IL` codes with matching full names.

### `contacts.json` → Salesforce Contact

| Field | SF field | Notes |
|---|---|---|
| contact_key | — | Internal only |
| FirstName | FirstName | |
| LastName | LastName | Required |
| Title | Title | GTM mix: EB / champion / user / ops evaluator — do not infer role from title alone |
| Email | Email | |
| Phone | Phone | |
| account_key | AccountId | Resolved via ID map on import |

### `opportunities.json` → Salesforce Opportunity

Apollo-relevant deal names and descriptions. Required SF fields validated against `discovery-dev`.

### `tasks.json` → Salesforce Task (Gong activity model)

| Field | SF field | Notes |
|---|---|---|
| activity_kind | — | Internal: `Meeting` or `Email` |
| TaskSubtype | TaskSubtype | Meetings → `Task` (no Meeting subtype in org); emails → `Email` |
| linked_meeting_key | — | Meeting tasks only |

**Org note:** Task has no `Type` field on `discovery-dev`.

### `granola_meetings.json` (local only)

Full transcripts for Apollo-relevant discovery/networking conversations. Not imported to Salesforce.

### Task mix

- 4 meeting Tasks (`TSK-001`, `TSK-002`, `TSK-003`, `TSK-009`) ↔ `MTG-001`…`MTG-004`
- 6 Gong email Tasks (`TSK-004`…`TSK-008`, `TSK-010`)

---

## Record relationships

```text
ACC-001 Meridian Robotics (B2B robotics seller; Salesforce; growing SDR/AE org)
  ├─ CON-001 VP Sales, CON-002 SDR Manager, CON-003 Sales Ops Manager
  ├─ OPP-001 Apollo Sales Intelligence Platform (open) ← OCR-001/002; TSK-003/008; MTG-003
  ├─ OPP-004 Standalone contact-data vendor (Closed Lost) ← OCR-005
  └─ MTG-001 / TSK-001 (+ TSK-004/005) → SCENARIO-01 new SDR outbound / contact-data opp

ACC-002 Cascade Health Partners (B2B healthcare services selling into providers)
  ├─ CON-004 VP Sales, CON-005 Senior SDR, CON-006 RevOps Manager
  ├─ OPP-002 Apollo Partner Lead Enrichment (open, incomplete) ← OCR-003
  └─ MTG-002 / TSK-002 (+ TSK-006/007) → SCENARIO-02 hospital buying-group opp (NOT OPP-002)

ACC-003 Northwind Retail Group (B2B wholesale + enterprise retail partnerships; Apollo customer)
  ├─ CON-007 Head of Strategic Partnerships, CON-008 CEO
  ├─ OPP-003 Apollo Sales Intelligence Platform (Closed Won) ← OCR-004
  └─ MTG-004 / TSK-009 (+ TSK-010) → SCENARIO-04 networking / no new opportunity
```

### Initiative distinction (Cascade)

| Record | Initiative |
|---|---|
| OPP-002 | Enrich partner-referral inbound leads before SDR outreach |
| MTG-002 / SCENARIO-02 | Map hospital/clinic buying groups + improve CRM contact quality for direct outbound |

---

## ID mapping process (post-import)

Insert order: Accounts → Contacts → Opportunities → Tasks → OpportunityContactRoles  
Write `data/.salesforce-id-map.json` (gitignored) after each successful create; resume by skipping already-mapped keys.
