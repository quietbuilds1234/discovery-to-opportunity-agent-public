# Test Guide

How to exercise the four Discovery-to-Opportunity scenarios using the shared **Apollo-framed** synthetic dataset.

This guide is for **manual / Skill-based** validation. Automated Skill tests are not part of this phase.

---

## Prerequisites

1. Local fixtures validated:

```bash
python3 scripts/validate_synthetic_data.py
```

2. (After import approval) Salesforce `discovery-dev` seeded via `scripts/load_salesforce_data.py`.
3. Local ID map present at `data/.salesforce-id-map.json` (gitignored) after a successful load.
4. Granola meetings loaded from `data/granola_meetings.json` (synthetic; not live Granola).

---

## How to run each scenario

Provide the Skill (or a human reviewer simulating it) with:

1. The Granola fixture for the scenario.
2. Salesforce context for the Account (Contacts, Opportunities, Tasks, OCRs).
3. The instruction: analyze and recommend Opportunity create / not create per product principles (MEDDPICC = enrichment, not a gate).

### SCENARIO-01 — Strong CREATE

- **Meeting:** `MTG-001` (SDR outbound research + contact data)
- **SF focus:** `ACC-001`, `CON-001..003`, `TSK-001/004/005`, Opps `OPP-001` + `OPP-004` as context
- **Success:** `CREATE`; new opp for SDR/contact-data motion; **not** duplicate of `OPP-001`; gaps + skippable questions; approval gate
- **Failure:** Blocking solely for missing Finance/metrics; merging into `OPP-001`; fabricating ROI as confirmed

### SCENARIO-02 — CREATE WITH GAPS

- **Meeting:** `MTG-002` (hospital buying groups + CRM contact quality)
- **SF focus:** `ACC-002`, `CON-004/005`, `TSK-002/006/007`, Opp `OPP-002` as **non-matching** context (partner lead enrichment)
- **Success:** `CREATE WITH GAPS`; distinct from `OPP-002`; skippable questions; allow proceed after approval
- **Failure:** Mapping to INSUFFICIENT INFORMATION only because MEDDPICC incomplete; auto-merging into `OPP-002`

### SCENARIO-03 — EXISTING OPPORTUNITY

- **Meeting:** `MTG-003`
- **SF focus:** `OPP-001`, `TSK-003/008`, OCRs `OCR-001/002`
- **Success:** `EXISTING OPPORTUNITY`; match rationale; associate vs investigate; **no create**
- **Failure:** Creating a second Apollo platform Opportunity; ignoring “do not open a separate opportunity”

### SCENARIO-04 — No opportunity

- **Meeting:** `MTG-004` (networking; existing Apollo customer; no expansion)
- **SF focus:** `ACC-003`, `CON-007/008`, `TSK-009/010`, Closed Won `OPP-003`
- **Success:** `INSUFFICIENT INFORMATION` or **do not create**; explain lack of initiative (not “MEDDPICC incomplete”)
- **Failure:** Creating an expansion Opportunity from coffee; inferring EB because CEO said hello

---

## Cross-scenario acceptance criteria

| Criterion | Required |
|---|---|
| Apollo-relevant pain/use case framing | Yes |
| Confirmed vs inferred vs unknown labeled | Yes |
| No fabricated facts | Yes |
| MEDDPICC never sole create-blocker | Yes |
| Explicit approval before any SF write | Yes |
| Duplicate detection on matching open initiative | Yes (SCENARIO-03) |
| SCENARIO-02 not confused with OPP-002 | Yes |
| Scenarios 1–2 do not collide with matching open Opps | Yes |

---

## Suggested manual checklist

- [ ] `validate_synthetic_data.py` PASS
- [ ] Salesforce import verified (if approved)
- [ ] SCENARIO-01 preview allows proceed with gaps
- [ ] SCENARIO-02 preview allows skip + proceed; not flagged as OPP-002 duplicate
- [ ] SCENARIO-03 blocks duplicate create
- [ ] SCENARIO-04 recommends no create for networking / no expansion
