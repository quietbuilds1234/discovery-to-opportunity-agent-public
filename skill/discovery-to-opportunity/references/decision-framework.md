# Decision Framework

After meeting confirmation, full-transcript analysis, and CRM context, choose **one** primary outcome.

## Salesperson-facing outcomes ↔ internal codes

| Conversational label | Internal / demo code | Typical next action |
|---|---|---|
| Opportunity identified | `CREATE` | Clarifying questions (sparingly) → Opportunity + AE handoff preview → explicit approval |
| Potential opportunity — needs clarification | `CREATE WITH GAPS` | One-at-a-time clarifications → preview when enough → explicit approval |
| Existing Opportunity found | `EXISTING OPPORTUNITY` | Show match; associate/investigate; **no new create** |
| No opportunity identified | `INSUFFICIENT INFORMATION` / DO NOT CREATE | Brief explanation; optional one clarifying question |

Preserve demo anchors: MTG-001→CREATE, MTG-002→CREATE WITH GAPS, MTG-003→EXISTING OPPORTUNITY, MTG-004→DO NOT CREATE, MTG-005→CREATE (after initiative-status confirmation; continuation of MTG-001).

## Meeting recency + initiative status

- Rank fixtures by `start_time`. “Recent/latest” → newest matching meeting (demo: **MTG-005** on Nov 12, 2026).
- If the selected meeting is **historical** relative to a newer same-initiative meeting (e.g. MTG-001 when MTG-005 exists), **confirm initiative status** before proposing create: still active / already in CRM / stalled / use newer meeting instead.
- Continuation meetings (MTG-005): confirm no open Opp already covers the SDR pilot before CREATE; never merge into OPP-001.

## Buying-interest test (before create)

Ask: Did the **customer** demonstrate a meaningful business problem, Apollo-relevant use case, and some signal of evaluation/next-step interest?

- Seller-only pitching without customer engagement ≠ buying interest.
- Networking / “no expansion” / social catch-up → No opportunity identified.
- Clear pain + use case + next step with gaps → Opportunity identified or Needs clarification (not “no opportunity”).

## CREATE (Opportunity identified)

**When:** Legitimate Apollo-relevant buying initiative; Account identifiable; Opportunity describable.

**Does not require:** Complete BANT or MEDDPICC.

## CREATE WITH GAPS (Potential opportunity — needs clarification)

**When:** Legitimate need/interest, but material context is thin (budget owner, metrics, timing, process, etc.).

**Behavior:** Ask high-leverage questions one at a time; allow skip; still allow proceed to preview/approval. Incomplete BANT/MEDDPICC is **not** a hard stop.

## Initiative comparison (duplicate detection)

Compare **meeting initiative** to each Account Opportunity using CRM fields from the retrieval pass (Name, Description, NextStep, StageName, IsClosed/IsWon) plus transcript language:

| Decision | When |
|---|---|
| Genuinely **new** initiative | Clear buying interest; no open Opp covers the same problem/use case/product decision |
| **Existing** Opportunity (same initiative) | Open Opp matches problem/product/decision path — even if meeting date differs |
| **New** initiative at Account with other Opps | Shared Account/contacts alone is **not** a duplicate (e.g. SDR pilot vs AE platform) |
| **Potential** / needs clarification | Buying signals exist but material context is thin |
| **No** opportunity | Networking / no buying interest |

Do **not** treat different meeting dates as separate Opportunities by themselves.  
Do **not** merge initiatives merely because they share an Account or stakeholders.

## EXISTING OPPORTUNITY

**When:** An open Opportunity covers the **same buying initiative** (same problem/product decision — not merely same Account).

**Behavior:** Surface Name/Stage/Amount/Id + key activity. Ask associate vs investigate. **Never auto-create a duplicate.**

**Same-initiative signals:** “same evaluation/deal,” matching product name, ongoing proposal/security path, stakeholder says do not open a second Opp.

**Different-initiative signals:** “different thread,” different use case (SDR pilot vs AE platform; hospital buying groups vs partner-lead enrichment).

## INSUFFICIENT INFORMATION / DO NOT CREATE

**When:**

- No meaningful business problem, use case, or buying initiative; or
- Account cannot be identified; or
- Opportunity cannot be described / required SF fields unresolvable.

**Not valid sole reasons:** Incomplete BANT or MEDDPICC.

## Blocking summary

| Blocks new Opportunity create? | Reason |
|---|---|
| Yes | Same-initiative duplicate unresolved |
| Yes | No buying initiative / networking-only |
| Yes | Unidentifiable Account or required SF fields |
| Yes | No explicit rep approval of the final Opportunity + OCR preview |
| No | Incomplete BANT |
| No | Incomplete MEDDPICC |

## Evidence sources

- **Meeting** — fixture transcript / summary (`MTG-*`)
- **CRM** — Salesforce Id + Name/fields via Hosted MCP
- **Rep clarification** — answers given in the chat

Never present Inferred as Confirmed.
