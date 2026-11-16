# Discovery-to-Opportunity Agent — Project Context

This document is the source of truth for project requirements, business context, assumptions, workflow, and product principles. Prefer this file when resolving ambiguity during implementation.

---

## 1. Project Goal

Build a Claude Skill that helps an individual sales representative turn a discovery meeting into a well-structured Salesforce Opportunity.

The rep uses Claude after a discovery meeting. The Skill analyzes meeting information, reviews relevant Salesforce CRM context, proposes an Opportunity, identifies qualification gaps using MEDDPICC, and creates the Opportunity in Salesforce only after explicit rep approval.

The experience should feel like an intelligent sales operations assistant, not a rigid CRM data-entry tool.

### Interview framing — Apollo

This project is an interview assignment for **Apollo**, a B2B sales intelligence and GTM platform (contact/company intelligence, prospecting, enrichment, buyer identification, sales signals, pipeline productivity).

Synthetic demo data should represent realistic Apollo prospects — companies with sales/SDR/RevOps motions and Salesforce usage — discussing Apollo-relevant problems (manual research, bad contact data, finding decision-makers, outbound efficiency, CRM hygiene, segmentation, pipeline generation). Do not invent official Apollo ICP size/industry thresholds; treat ICP notes as working assumptions unless independently verified.

---

## 2. Business Problem

Sales representatives often finish discovery meetings with valuable information about a prospect's business needs, pain points, stakeholders, and potential buying intent.

Translating that information into a Salesforce Opportunity requires manual work:

- Reviewing meeting transcripts and notes.
- Looking up Account and Contact information.
- Reviewing previous Salesforce activities and communications.
- Determining whether an Opportunity already exists.
- Translating unstructured conversation into structured CRM fields.
- Identifying qualification gaps and determining what to ask next.

This creates friction for sales reps, inconsistent CRM data, incomplete Opportunity records, and unnecessary administrative overhead.

The opportunity is to use an AI agent to connect meeting intelligence with existing CRM context, structure the information, and assist with Opportunity creation.

---

## 3. Solution Vision

The Discovery-to-Opportunity Agent should:

- Reduce administrative work following discovery calls.
- Bring together meeting intelligence and existing CRM context.
- Help reps capture meaningful Opportunity information while the conversation is fresh.
- Improve CRM data quality without forcing reps through rigid qualification checklists.
- Proactively identify missing information and recommend relevant follow-up questions.
- Identify existing Opportunities and potential duplicates.
- Keep the sales representative in control of all CRM write operations.

The goal is not to automate sales judgment. The goal is to make it easier for reps to capture, structure, and act on information they already have.

---

## 4. Target User

An individual Account Executive or sales representative using Claude after a discovery meeting.

The Skill should feel conversational and assistive, not like a form the rep has to complete.

The agent should be opinionated enough to identify missing information, potential risks, and recommended next steps, but flexible enough to support how sales representatives actually work.

### Design Philosophy

Prioritize rep productivity and adoption over rigid process enforcement.

Do not build a compliance bot or a qualification gatekeeper.

---

## 5. Critical Product Principles

**MEDDPICC is an enrichment framework, NOT a gatekeeper for Opportunity creation.**

Do not prevent legitimate Opportunity creation simply because budget, Economic Buyer, metrics, decision process, or other MEDDPICC information is unknown.

The agent should:

- Help reps identify missing context through suggested follow-up questions.
- Allow reps to answer questions, skip them, or proceed with creation.
- Distinguish confirmed information from inferred or unknown information.
- Explain why additional information could be useful.
- Never fabricate information or present assumptions as confirmed facts.
- Never create an Opportunity without explicit rep approval.
- Detect potential duplicate Opportunities before creation.
- Preserve the rep's control over the final decision.

The goal is to encourage better CRM data, not enforce perfect qualification.

---

## 6. Technical Assumptions

- The user experience is a Claude Skill.
- Salesforce is the external CRM.
- Reps use Claude and Granola.
- Granola is assumed to be integrated with Claude, but actual access must be validated.
- Salesforce meetings and Gong sales emails are assumed to be logged as Salesforce Tasks.
- Use standard Salesforce objects only.
- Use synthetic data for the demo.
- Salesforce CLI is installed and authenticated locally with the alias `discovery-dev`.
- The GitHub repository is private.
- Do not store credentials, tokens, passwords, or secrets in the repository.

### Important Integration Distinction

Salesforce CLI authentication in the local development environment does not automatically provide Salesforce access to Claude at runtime.

The finished Skill must use a supported Salesforce runtime connection or integration to perform actual CRM reads and writes.

Do not invent integrations, fabricate API responses, or claim functionality works unless it has been implemented and tested.

If Granola data cannot be accessed directly, use clearly labeled synthetic meeting fixtures for repeatable testing and demos.

Salesforce should remain the primary external system demonstrating actual integration.

### Development Constraints

- Keep implementation lightweight and appropriate for an approximately three-hour interview assignment.
- Do not create a custom backend or custom MCP server.
- Do not introduce unnecessary dependencies.
- Do not build features before the architecture and requirements are established.
- Do not expose credentials or personal information.
- Clearly distinguish implemented functionality from planned functionality.
- Optimize for a compelling, credible live demo.

---

## 7. Core Workflow

1. Rep launches the Skill in Claude after a discovery meeting.
2. Retrieve discovery meeting information, including transcript, attendees, summary, and action items.
3. Identify the Salesforce Account and relevant Contacts.
4. Retrieve Salesforce context:
   - Account information.
   - Related Contacts.
   - Existing and historical Opportunities.
   - Relevant Salesforce Tasks.
   - Historical Opportunity Contact Roles where useful.
5. Identify existing or potentially duplicate Opportunities.
6. Analyze the meeting and CRM history together.
7. Map known information to Salesforce Opportunity fields.
8. Assess MEDDPICC components as: Confirmed, Inferred, Unknown, or At Risk.
9. Identify important qualification gaps and suggest useful follow-up questions.
10. Present an Opportunity preview to the rep, including:
    - Proposed Opportunity name.
    - Account.
    - Relevant Contacts.
    - Potential business problem and use case.
    - Proposed Salesforce fields.
    - MEDDPICC assessment.
    - Important unknowns and risks.
    - Recommended follow-up questions.
    - Existing Opportunity or duplicate warnings.
11. Allow the rep to answer selected questions, skip questions, proceed, or decline.
12. Validate Salesforce-required fields.
13. Obtain explicit rep approval.
14. Create the Opportunity and appropriate Opportunity Contact Roles if supported and approved.
15. Return the Salesforce record ID and link.

---

## 8. Decision Outcomes

| Outcome | Meaning |
|---|---|
| **CREATE** | A legitimate potential opportunity exists. Present the proposed Opportunity and MEDDPICC gaps as recommendations. |
| **CREATE WITH GAPS** | A legitimate opportunity exists, but important qualification context is missing. Offer follow-up questions while allowing the rep to proceed. |
| **EXISTING OPPORTUNITY** | A potentially matching Opportunity exists. Show it to the rep and ask whether to associate activity with it or investigate further. Never automatically create a duplicate. |
| **INSUFFICIENT INFORMATION** | Essential information is missing to reliably identify the Account, meaningfully describe the Opportunity, or populate mandatory Salesforce fields. |

### Important Rule

Missing MEDDPICC information alone must never result in **INSUFFICIENT INFORMATION**.

Only genuine Salesforce requirements, unresolved duplicate risk, missing essential information, or lack of rep approval should block creation.

---

## 9. Salesforce Objects

Use standard Salesforce objects only.

### Account

Name, Website, Industry, Type, Description, BillingCity, BillingState, NumberOfEmployees

### Contact

FirstName, LastName, Title, Email, Phone, AccountId

### Opportunity

Name, AccountId, StageName, CloseDate, Amount, Type, LeadSource, Description, NextStep

### Task

Subject, Status, Priority, ActivityDate, Description, WhoId, WhatId

### OpportunityContactRole

OpportunityId, ContactId, Role, IsPrimary

Validate actual Salesforce field availability, required fields, and picklist values in the Developer Org before implementing writes.

Do not assume every field is required or every picklist value is available.

---

## 10. Synthetic Data and Testing

The project uses a fictional sales environment.

### Planned Data Volume

- 3 Accounts
- 8 Contacts
- 4 Opportunities
- 10 Salesforce Tasks
- 4–6 Opportunity Contact Roles
- 4 synthetic Granola-style meeting records (including one networking / no-opportunity meeting)
- 10 Salesforce Tasks total: 4 meeting + 6 Gong email

### Test Scenarios

1. **Strong legitimate opportunity** — Clear business pain, use case, engaged stakeholder, and credible next step. Allow creation even with MEDDPICC gaps.
2. **Early-stage legitimate opportunity** — Potential need and interest, but missing Economic Buyer, Metrics, timeline, and other qualification information. Still allow creation if the rep wants it.
3. **Existing Opportunity** — A potentially matching deal already exists. Identify it and avoid automatic duplicate creation.
4. **Weak or nonexistent opportunity** — No meaningful business need or credible potential sales opportunity. Explain concerns without confusing missing qualification with lack of opportunity.

---

## 11. Planned Repository Structure

```text
discovery-to-opportunity-agent/
├── skill/
│   └── discovery-to-opportunity/
│       ├── SKILL.md
│       ├── references/
│       │   ├── qualification-rules.md
│       │   ├── salesforce-field-mapping.md
│       │   └── decision-framework.md
│       └── examples/
├── data/
│   ├── accounts.json
│   ├── contacts.json
│   ├── opportunities.json
│   ├── tasks.json
│   ├── opportunity_contact_roles.json
│   ├── granola_meetings.json
│   └── data-dictionary.md
├── tests/
│   ├── scenarios.md
│   ├── expected_outcomes.json
│   └── test-guide.md
├── docs/
│   ├── README.md
│   ├── architecture.md
│   ├── demo-decisions.md
│   ├── sales-user-guide.md
│   ├── one-pager.md
│   └── demo-script.md
├── scripts/
│   └── load_salesforce_data/
├── PROJECT_CONTEXT.md
└── README.md
```

Small adjustments are allowed if technically justified. Avoid unnecessary complexity.

---

## 12. Status Notes

- Foundation documentation is established first.
- Skill implementation, synthetic data, Salesforce seeding, and demo artifacts are planned for later phases.
- Do not create or modify Salesforce records until that phase is explicitly approved.
- Distinguish clearly between **implemented** and **planned** functionality in all user-facing docs.
