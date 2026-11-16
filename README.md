# Discovery-to-Opportunity Agent

A Claude Skill that helps a sales representative turn a discovery meeting into a well-structured Salesforce Opportunity — with CRM context, MEDDPICC enrichment, duplicate detection, and explicit human approval before any write.

Interview framing: synthetic demo data models **Apollo** (sales intelligence / GTM) prospects and discovery conversations.

> **Status:** Apollo synthetic dataset imported into Salesforce `discovery-dev` (30 records verified). Claude ↔ Salesforce MCP **not connected yet**. See [docs/checkpoint.md](docs/checkpoint.md) for the latest handoff.

---

## Business Problem

After discovery meetings, reps have rich context about pain, stakeholders, and buying intent — but turning that into a Salesforce Opportunity is slow and error-prone. They must review notes, look up Accounts and Contacts, check for existing deals, map unstructured conversation into CRM fields, and figure out what qualification gaps matter next.

That friction leads to incomplete CRM data, inconsistent Opportunity records, and unnecessary admin work.

## Proposed Solution

An intelligent sales operations assistant (Claude Skill) that:

1. Ingests discovery meeting information (Granola when available; otherwise labeled synthetic fixtures).
2. Retrieves related Salesforce Account, Contact, Opportunity, Task, and Opportunity Contact Role context.
3. Proposes a structured Opportunity with mapped fields and a MEDDPICC assessment.
4. Flags duplicates, gaps, and recommended follow-up questions.
5. Creates the Opportunity in Salesforce only after explicit rep approval.

MEDDPICC is used to enrich and guide — not to block legitimate Opportunity creation.

## Intended Users

Individual Account Executives / sales representatives using Claude after a discovery meeting.

The experience should feel conversational and assistive, not like a rigid form or compliance checklist.

## High-Level Architecture

```text
Rep (Claude) → Discovery-to-Opportunity Skill
                 ├── Meeting context (Granola or synthetic fixtures)
                 ├── Decision & qualification references (MEDDPICC, field mapping)
                 └── Salesforce (standard objects; runtime connection TBD)
                        Account | Contact | Opportunity | Task | OpportunityContactRole
```

- **Claude Skill** is the user experience and orchestration layer.
- **Salesforce** is the primary external system for real CRM reads/writes.
- **Local Salesforce CLI** (`discovery-dev`) supports development and synthetic data seeding only; it does not automatically grant Claude runtime CRM access.
- **No custom backend or custom MCP server** in this interview scope.

See [docs/architecture.md](docs/architecture.md) for more detail.

## Planned Functionality

| Capability | Phase |
|---|---|
| Project context, architecture, demo decisions | **Current** |
| Synthetic CRM + meeting fixtures and test scenarios | Planned |
| Claude Skill with decision framework and field mapping | Planned |
| Salesforce org validation and data load scripts | Planned |
| Runtime Salesforce create (with explicit approval) | Planned |
| Demo script and sales user guide | Planned |

## Technology Assumptions

- Claude Skill for the agent experience
- Salesforce Developer Org + Salesforce CLI alias `discovery-dev`
- Standard Salesforce objects only
- Synthetic data for a fictional sales environment
- Granola meeting access is assumed but must be validated; fixtures used if unavailable
- Private GitHub repository; no secrets in source control

## Repository Layout (Planned)

```text
discovery-to-opportunity-agent/
├── skill/discovery-to-opportunity/   # Claude Skill (planned)
├── data/                           # Synthetic fixtures (planned)
├── tests/                          # Scenarios & expected outcomes (planned)
├── docs/                           # Architecture & demo docs
├── scripts/load_salesforce_data/   # Org seeding (planned)
├── PROJECT_CONTEXT.md              # Full requirements
└── README.md
```

## Documentation

| Doc | Purpose |
|---|---|
| [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) | Full requirements, principles, workflow |
| [docs/architecture.md](docs/architecture.md) | Architecture overview |
| [docs/demo-decisions.md](docs/demo-decisions.md) | Assumptions and design decisions |

## What Is Explicitly Out of Scope (for now)

- Building the Skill implementation
- Creating or modifying Salesforce records
- Custom backends / custom MCP servers
- Claiming Granola or Salesforce runtime access works before verification
