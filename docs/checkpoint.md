# Project Checkpoint — 2026-11-12

Concise handoff for the next session. Confirmed facts only.

---

## Git state (this workspace)

| Item | Status |
|---|---|
| Branch | `main` |
| Commits | **None yet** — working tree is entirely untracked |
| Tracked remote | `origin/main` reported as **[gone]** / not usable yet |
| Claude integration branch | Handled in a **separate Git branch** (not in this working tree today) |

**Note:** Do not commit `data/.salesforce-id-map.json`, `.env`, or OAuth secrets (already covered by `.gitignore`).

---

## Confirmed completed today

### Synthetic data
- Apollo-aligned fixtures complete under `data/`
- Local validation: `python3 scripts/validate_synthetic_data.py` → PASS
- Four scenarios documented: CREATE / CREATE WITH GAPS / EXISTING OPPORTUNITY / INSUFFICIENT INFORMATION
- MEDDPICC remains enrichment only (not a creation gate)

### Salesforce `discovery-dev` import
| Object | Count | Verified |
|---|---|---|
| Accounts | 3 | Yes |
| Contacts | 8 | Yes (Account links) |
| Opportunities | 4 | Yes (Account links) |
| Tasks | 10 (4 meeting / 6 email) | Yes (WhoId / WhatId) |
| Opportunity Contact Roles | 5 | Yes |
| **Total** | **30** | Yes |

- Local ID map: `data/.salesforce-id-map.json` (gitignored) — **30 Ids**
- Loader: `scripts/load_salesforce_data.py` (REST JSON create; resume/skip mapped keys)

### Salesforce → Claude prep (external)
- Salesforce **read** External App configured
- OAuth credentials/keys **saved for tomorrow** (not in repo)
- Claude has **NOT** been connected or authenticated to the Salesforce MCP server yet

---

## Explicitly not done

- [ ] Claude authenticated to Salesforce MCP
- [ ] Runtime CRM reads/writes from Claude Skill proven end-to-end
- [ ] Granola live access validated (fixtures remain the demo source of truth)
- [ ] Claude Skill implementation (`skill/discovery-to-opportunity/`)
- [ ] Initial git commit / branch strategy for this repo’s main line
- [ ] Demo script / sales user guide polish

---

## Tomorrow — recommended next steps

1. **Claude ↔ Salesforce MCP connection**
   - Use the saved External App OAuth credentials
   - Authenticate Claude to the Salesforce MCP server
   - Prove **read** access against the seeded `discovery-dev` records (Accounts/Contacts/Opps/Tasks)

2. **Smoke-test with fixtures**
   - Pick SCENARIO-01 (`MTG-001`) and confirm Claude can pull matching CRM context for Meridian Robotics
   - Confirm no writes occur until explicit rep approval (Skill behavior still planned)

3. **Continue on the Claude integration branch**
   - Keep MCP/auth work on the separate integration branch
   - Avoid mixing secrets into this repo

4. **Optional repo hygiene (this workspace)**
   - First commit of docs + fixtures + scripts (still no secrets / no ID map)
   - Align with however the Claude integration branch is managed

### Suggested tomorrow kickoff commands

```bash
# Confirm local fixtures still valid
python3 scripts/validate_synthetic_data.py

# Confirm mapped Salesforce Ids still resolve (read-only)
python3 scripts/load_salesforce_data.py --verify
```

Then proceed with Claude MCP OAuth / connection (outside this loader).

---

## Quick pointers

| Need | Where |
|---|---|
| Requirements | `PROJECT_CONTEXT.md` |
| Architecture | `docs/architecture.md` |
| Decisions / metadata notes | `docs/demo-decisions.md` |
| Scenarios | `tests/scenarios.md`, `tests/expected_outcomes.json` |
| Data dictionary | `data/data-dictionary.md` |
| Import / resume loader | `scripts/load_salesforce_data.py` |
