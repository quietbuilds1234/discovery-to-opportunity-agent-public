# Scenario Guide (demo anchors)

Meetings load from **`fixtures/granola_meetings.json`** (simulated Granola in the Skill package).  
Dates span **October–November 2026** (demo “today” ≈ Nov 16, 2026). Most recent: **MTG-005**.

## Conversational flow reminder

1. Identify → confirm meeting (fixtures only; **no SF queries yet**)  
2. Analyze full transcript, then Account-scoped MCP reads  
3. Brief outcome (Opportunity identified / Needs clarification / Existing / None)  
4. One clarification question at a time when useful  
5. Opportunity preview + Handoff Notes (`Handoff_Notes__c`) → explicit approval  
6. Close Date must be **future vs today**; ask if timing unknown  
7. Description stays concise — full AE narrative only in Handoff Notes  
8. Writes only after explicit approval: `createSobjectRecord` Opp (with `Handoff_Notes__c`) → OCRs → verify (never delete; no new Contacts)  

## SCENARIO-01 — MTG-001 (Oct 14) → CREATE

- **Conversational:** Opportunity identified  
- **Meeting:** SDR outbound + contact-data hygiene (Meridian)  
- **CRM:** Open AE-platform Opp is a **different** initiative  
- **Do:** Confirm meeting → analyze → light clarifications → new Opp preview + AE handoff  
- **Don’t:** Merge with AE-platform Opp; don’t block for missing Finance/metrics alone  
- **Historical note:** A newer continuation exists (`MTG-005`). If the rep picks MTG-001, **confirm initiative status** before create (still active? already logged? prefer Nov 12 meeting?).

## SCENARIO-02 — MTG-002 (Oct 21) → CREATE WITH GAPS

- **Conversational:** Potential opportunity — needs clarification  
- **Meeting:** Hospital buying groups + CRM contact quality (Cascade)  
- **CRM:** Partner-lead enrichment Opp is a **different** thread  
- **Do:** One-at-a-time questions; allow skip; still offer preview  
- **Don’t:** Duplicate partner-lead Opp; don’t call it “no opportunity” just for thin MEDDPICC  

## SCENARIO-03 — MTG-003 (Oct 28) → EXISTING OPPORTUNITY

- **Conversational:** Existing Opportunity found  
- **Meeting:** Continues Apollo Sales Intelligence Platform evaluation  
- **Do:** Show matching Opp; associate/investigate  
- **Don’t:** Create a second Opp  

## SCENARIO-04 — MTG-004 (Oct 8) → DO NOT CREATE

- **Conversational:** No opportunity identified  
- **Meeting:** Networking; existing customer; no expansion  
- **Do:** Explain lack of buying initiative  
- **Don’t:** Force create; don’t blame “incomplete MEDDPICC”; CEO hello ≠ Economic Buyer  

## SCENARIO-05 — MTG-005 (Nov 12) → CREATE (demo) / EXISTING if SDR Opp present

- **Conversational:** Opportunity identified — confirm initiative status  
- **Meeting:** SDR pilot scoping continuation of MTG-001 (progressed; early-January start target)  
- **CRM (demo):** No open Opp for the SDR pilot; OPP-001 remains a **different** initiative → **CREATE**  
- **CRM (variant):** If SDR/contact-data Opp already exists after MTG-001 → **EXISTING OPPORTUNITY** (no duplicate)  
- **Do:** Confirm initiative status; Close Date future when creating  
- **Don’t:** Merge into OPP-001; don’t create a second SDR Opp if one already exists  

## Suggested Claude prompts

```text
I want to run the opp skill for my recent Granola meeting.
```

```text
Use MTG-001. Confirm the meeting, then analyze. Keep it conversational.
Do not write to Salesforce.
```

```text
Run the opp skill for the Meridian SDR pilot scoping meeting from November 12.
```
