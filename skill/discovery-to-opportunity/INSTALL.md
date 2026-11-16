# Installing the Discovery-to-Opportunity Skill in Claude.ai

## What this package contains

```text
discovery-to-opportunity/
├── SKILL.md                          # Required entry point (metadata.version)
├── CHANGELOG.md                      # Version history
├── INSTALL.md                        # This file
├── fixtures/
│   └── granola_meetings.json         # Required — simulated Granola meetings
├── references/
│   ├── decision-framework.md
│   ├── qualification-rules.md
│   ├── salesforce-field-mapping.md
│   ├── salesforce-retrieval.md
│   └── salesforce-writes.md
└── examples/
    └── scenario-guide.md
```

## Architectural split

| Capability | Source in Claude.ai |
|---|---|
| Meeting intelligence (simulated Granola) | Packaged `fixtures/granola_meetings.json` |
| CRM reads + approved writes | **One** Salesforce Hosted MCP connector: **`sobject-all`** |
| Exact MCP tools | See `references/salesforce-retrieval.md` + `references/salesforce-writes.md` (`mcp__Salesforce__soqlQuery`, `createSobjectRecord`, …) |
| Product UX | confirm → analyze → CRM reads → clarify → preview → **explicit approve** → create Opp (with `Handoff_Notes__c`) → OCRs → verify |

There is **no live Granola integration**. Fixtures simulate Granola for demos.

Canonical dataset for the repo remains `data/granola_meetings.json`. The Skill copy under `fixtures/` must stay in sync when meetings change. Claude.ai does **not** read the repo’s root `data/` folder.

### Salesforce MCP connector (do not use two connectors)

Configure **one** Claude custom connector:

`https://api.salesforce.com/platform/mcp/v1/platform/sobject-all`

- Free plan allows **only one** custom connector — do **not** add separate `sobject-reads` + `sobject-mutations` connectors.
- **Safety rules (mandatory):** explicit BDR approval of the **shown** preview before any mutation (`createSobjectRecord` / update tools); prefer `Handoff_Notes__c` on Opportunity **create**; OCR only for **existing** Contacts; no new Contacts; no title-inferred Roles; **never** invoke Salesforce delete; no Consumer Keys, Client Secrets, or tokens in this package.
- Configured connector ≠ authenticated Claude session — confirm the connector is connected in the chat before CRM tools.
- Exact MCP tool names: `references/salesforce-retrieval.md` + `references/salesforce-writes.md`. Broader connector rationale (optional, outside this package): repo `docs/architecture.md`.

## Package / upload checklist

The **`skill/discovery-to-opportunity/` folder** is the canonical package source. A release ZIP may be rebuilt from that folder; do not ship a stale archive.

1. From `skill/discovery-to-opportunity/`, zip the **contents** so **`SKILL.md` is at the ZIP root** (also include `CHANGELOG.md`, `INSTALL.md`, `fixtures/`, `references/`, `examples/`).
2. Confirm `fixtures/granola_meetings.json` is inside the package (not optional).
3. Confirm all five `references/*.md` files and `examples/scenario-guide.md` are included.
4. Upload/install as a Claude Skill using Claude.ai’s Skill installation flow.
5. Ensure the Claude Salesforce connector points at **`sobject-all`** (see above) for the demo org.
6. Prefer least-privilege Salesforce user permissions / FLS for the connected user.

**Validation:** Local package/tests for v0.3.0 are listed in `CHANGELOG.md`. Live Opportunity create + post-write verification require a Claude chat with `sobject-all` connected and **explicit** create approval — do not run writes from install alone.

## Verify after install

Ask Claude:

```text
Using the discovery-to-opportunity skill, list the meeting_key values
available in fixtures/granola_meetings.json.
```

Expected: `MTG-001` … `MTG-005` (Oct–Nov 2026; newest = `MTG-005`).

Then (reads + preview only):

```text
Analyze MTG-001. Load the packaged fixture and pull Salesforce context
for Meridian Robotics via MCP. Recommend an outcome and Opportunity preview.
Do not write to Salesforce until I explicitly approve.
```

## Common failure: missing fixtures

If Claude cannot find meetings, the Skill was likely uploaded **without** the `fixtures/` folder. Re-package including `fixtures/granola_meetings.json` and reinstall.
