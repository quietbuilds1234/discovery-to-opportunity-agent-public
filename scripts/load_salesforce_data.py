#!/usr/bin/env python3
"""
Load synthetic fixtures into Salesforce alias discovery-dev.

SAFETY:
  Default mode is dry-run / plan only.
  Writes run only with: --execute --i-approve-writes

Never prints access tokens. Never sends synthetic keys as Salesforce Ids.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MAP_PATH = DATA / ".salesforce-id-map.json"
ORG_ALIAS = "discovery-dev"
API_VERSION = "v68.0"


def run_sf(args: list[str]) -> dict[str, Any]:
    cmd = ["sf", *args, "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"sf returned non-JSON (exit {proc.returncode}): {(proc.stderr or proc.stdout)[:500]}"
        ) from exc
    if proc.returncode != 0 or payload.get("status", 0) != 0:
        message = payload.get("message") or payload.get("error") or proc.stderr
        raise RuntimeError(f"sf command failed: {' '.join(cmd)}\n{message}")
    return payload


def load_json(name: str) -> list[dict[str, Any]]:
    with (DATA / name).open() as f:
        return json.load(f)


def empty_map() -> dict[str, dict[str, str]]:
    return {
        "accounts": {},
        "contacts": {},
        "opportunities": {},
        "tasks": {},
        "opportunity_contact_roles": {},
    }


def save_map(mapping: dict[str, dict[str, str]]) -> None:
    """Persist the full mapping. Never drops previously successful object Ids."""
    # Merge onto disk snapshot so concurrent/manual map edits are less likely to wipe history.
    merged = empty_map()
    if MAP_PATH.exists():
        existing = json.loads(MAP_PATH.read_text())
        for key in merged:
            merged[key].update(existing.get(key, {}))
    for key in merged:
        merged[key].update(mapping.get(key, {}))
        mapping[key] = dict(merged[key])
    MAP_PATH.write_text(json.dumps(merged, indent=2) + "\n")
    print(f"Wrote local ID map → {MAP_PATH} (gitignored)")


def extract_created_id(payload: dict[str, Any]) -> str | None:
    """Normalize sf api request rest --json response shapes."""
    result = payload.get("result", payload)
    if isinstance(result, dict):
        if result.get("id"):
            return result["id"]
        body = result.get("body")
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                body = None
        if isinstance(body, dict) and body.get("id"):
            return body["id"]
        # Some CLI versions nest under result.data / result.response
        for nest_key in ("data", "response"):
            nested = result.get(nest_key)
            if isinstance(nested, dict) and nested.get("id"):
                return nested["id"]
            if isinstance(nested, str):
                try:
                    nested_obj = json.loads(nested)
                except json.JSONDecodeError:
                    nested_obj = None
                if isinstance(nested_obj, dict) and nested_obj.get("id"):
                    return nested_obj["id"]
    return None


def create_record(sobject: str, fields: dict[str, Any]) -> str:
    """
    Create a Salesforce record via REST JSON body (not fragile CLI -v key=value pairs).

    Uses: sf api request rest /services/data/{ver}/sobjects/{SObject} -X POST -b @file.json
    """
    endpoint = f"/services/data/{API_VERSION}/sobjects/{sobject}"
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        prefix=f"sf-{sobject}-",
        delete=False,
        encoding="utf-8",
    ) as tmp:
        json.dump(fields, tmp, ensure_ascii=False)
        tmp_path = Path(tmp.name)

    try:
        # Pass body file via argv list (no shell) so punctuation is never re-parsed.
        result = run_sf(
            [
                "api",
                "request",
                "rest",
                endpoint,
                "-o",
                ORG_ALIAS,
                "-X",
                "POST",
                "-b",
                f"@{tmp_path}",
            ]
        )
    finally:
        tmp_path.unlink(missing_ok=True)

    record_id = extract_created_id(result)
    if not record_id:
        # Surface Salesforce error bodies when present
        raise RuntimeError(
            f"No Id returned creating {sobject}: {json.dumps(result)[:1000]}"
        )
    return record_id


def print_plan() -> None:
    accounts = load_json("accounts.json")
    contacts = load_json("contacts.json")
    opportunities = load_json("opportunities.json")
    tasks = load_json("tasks.json")
    ocrs = load_json("opportunity_contact_roles.json")

    print("=== IMPORT PLAN (no writes) ===")
    print(f"Target alias: {ORG_ALIAS}")
    display = run_sf(["org", "display", "-o", ORG_ALIAS])
    result = display.get("result", {})
    print(f"Username: {result.get('username')}")
    print(f"Instance: {result.get('instanceUrl')}")
    print(f"Connected: {result.get('connectedStatus')}")
    print()
    print("Counts to create:")
    print(f"  Accounts: {len(accounts)}")
    print(f"  Contacts: {len(contacts)}")
    print(f"  Opportunities: {len(opportunities)}")
    print(f"  Tasks: {len(tasks)}")
    print(f"  OpportunityContactRoles: {len(ocrs)}")
    meetings = load_json("granola_meetings.json")
    meeting_tasks = [t for t in tasks if t.get("activity_kind") == "Meeting"]
    email_tasks = [t for t in tasks if t.get("activity_kind") == "Email"]
    print(f"  Granola meetings: {len(meetings)} (local fixtures only; not imported)")
    print(f"  Task mix: {len(meeting_tasks)} meeting / {len(email_tasks)} email")
    print()
    print("Accounts:")
    for a in accounts:
        print(
            f"  {a['account_key']}: {a['Name']} | {a['Industry']} | {a['Type']} | "
            f"{a['BillingCity']}, {a['BillingState']} ({a['BillingStateCode']}), "
            f"{a['BillingCountry']} ({a['BillingCountryCode']})"
        )
    print("Contacts:")
    for c in contacts:
        print(
            f"  {c['contact_key']}: {c['FirstName']} {c['LastName']} <{c['Email']}> → {c['account_key']}"
        )
    print("Opportunities:")
    for o in opportunities:
        print(
            f"  {o['opportunity_key']}: {o['Name']} | {o['StageName']} | "
            f"${o['Amount']} | {o['Type']} | {o['LeadSource']} | {o['account_key']}"
        )
    print("Tasks:")
    for t in tasks:
        print(
            f"  {t['task_key']}: {t['Subject']} | kind={t['activity_kind']} "
            f"subtype={t['TaskSubtype']} | {t['ActivityDate']} | "
            f"Who={t['who_contact_key']} What={t['what_record_type']}:{t['what_record_key']}"
        )
    print("Opportunity Contact Roles:")
    for o in ocrs:
        print(
            f"  {o['ocr_key']}: {o['opportunity_key']} / {o['contact_key']} | "
            f"{o['Role']} | primary={o['IsPrimary']}"
        )
    print()
    print("Metadata adjustments already applied in local fixtures:")
    print("  - Account.Type: Prospect / Customer - Direct (not Customer - Prospect)")
    print("  - Opportunity.Type: New Customer / Existing Customer - Upgrade")
    print("  - Opportunity.LeadSource: Web / Partner Referral / Other / Phone Inquiry")
    print("  - Task.Type omitted (field does not exist on discovery-dev Task)")
    print("  - Meeting activities: TaskSubtype=Task (no Meeting subtype in org)")
    print("  - Email activities: TaskSubtype=Email")
    print()
    print("Insertion order: Accounts → Contacts → Opportunities → Tasks → OpportunityContactRoles")
    print("No existing Salesforce records will be updated or deleted.")
    print()
    print("To execute after explicit approval:")
    print("  python3 scripts/load_salesforce_data.py --execute --i-approve-writes")


def sf_task_fields(task: dict[str, Any], mapping: dict[str, dict[str, str]]) -> dict[str, Any]:
    who = mapping["contacts"][task["who_contact_key"]]
    if task["what_record_type"] == "Account":
        what = mapping["accounts"][task["what_record_key"]]
    else:
        what = mapping["opportunities"][task["what_record_key"]]
    return {
        "Subject": task["Subject"],
        "Status": task["Status"],
        "Priority": task["Priority"],
        "ActivityDate": task["ActivityDate"],
        "Description": task["Description"],
        "TaskSubtype": task["TaskSubtype"],
        "WhoId": who,
        "WhatId": what,
    }


def load_or_init_map() -> dict[str, dict[str, str]]:
    mapping = empty_map()
    if not MAP_PATH.exists():
        return mapping
    existing = json.loads(MAP_PATH.read_text())
    for key in mapping:
        mapping[key] = dict(existing.get(key, {}))
    print(
        "Resuming from existing ID map (skipping keys already mapped to avoid duplicates): "
        f"{ {k: list(v.keys()) for k, v in mapping.items()} }"
    )
    return mapping


def require_deps(mapping: dict[str, dict[str, str]], object_key: str, keys: list[str]) -> None:
    missing = [k for k in keys if k not in mapping[object_key]]
    if missing:
        raise RuntimeError(
            f"Cannot continue: missing mapped {object_key} Ids for {missing}. "
            "Fix prior failures before dependent inserts."
        )


def execute_import() -> None:
    """
    Insert records in dependency order. After each successful create, persist the ID map.
    On rerun: skip synthetic keys already present in the map (no duplicate creates).
    On failure: stop the current object phase after reporting; preserve successful mappings.
    """
    mapping = load_or_init_map()

    accounts = load_json("accounts.json")
    contacts = load_json("contacts.json")
    opportunities = load_json("opportunities.json")
    tasks = load_json("tasks.json")
    ocrs = load_json("opportunity_contact_roles.json")

    print("Creating Accounts...")
    for a in accounts:
        key = a["account_key"]
        if key in mapping["accounts"]:
            print(f"  SKIP {key} (already mapped)")
            continue
        fields = {
            "Name": a["Name"],
            "Website": a["Website"],
            "Industry": a["Industry"],
            "Type": a["Type"],
            "Description": a["Description"],
            "BillingCity": a["BillingCity"],
            "BillingCountry": a["BillingCountry"],
            "BillingCountryCode": a["BillingCountryCode"],
            "BillingState": a["BillingState"],
            "BillingStateCode": a["BillingStateCode"],
            "NumberOfEmployees": a["NumberOfEmployees"],
        }
        try:
            sf_id = create_record("Account", fields)
        except Exception as exc:  # noqa: BLE001
            save_map(mapping)
            raise RuntimeError(f"Account {key} failed; map preserved. {exc}") from exc
        mapping["accounts"][key] = sf_id
        save_map(mapping)
        print(f"  {key} → {sf_id}")

    print("Creating Contacts...")
    for c in contacts:
        key = c["contact_key"]
        if key in mapping["contacts"]:
            print(f"  SKIP {key} (already mapped)")
            continue
        require_deps(mapping, "accounts", [c["account_key"]])
        fields = {
            "FirstName": c["FirstName"],
            "LastName": c["LastName"],
            "Title": c["Title"],
            "Email": c["Email"],
            "Phone": c["Phone"],
            "AccountId": mapping["accounts"][c["account_key"]],
        }
        try:
            sf_id = create_record("Contact", fields)
        except Exception as exc:  # noqa: BLE001
            save_map(mapping)
            raise RuntimeError(f"Contact {key} failed; map preserved. {exc}") from exc
        mapping["contacts"][key] = sf_id
        save_map(mapping)
        print(f"  {key} → {sf_id}")

    print("Creating Opportunities...")
    for o in opportunities:
        key = o["opportunity_key"]
        if key in mapping["opportunities"]:
            print(f"  SKIP {key} (already mapped)")
            continue
        require_deps(mapping, "accounts", [o["account_key"]])
        fields = {
            "Name": o["Name"],
            "AccountId": mapping["accounts"][o["account_key"]],
            "StageName": o["StageName"],
            "CloseDate": o["CloseDate"],
            "Amount": o["Amount"],
            "Type": o["Type"],
            "LeadSource": o["LeadSource"],
            "Description": o["Description"],
            "NextStep": o["NextStep"],
        }
        try:
            sf_id = create_record("Opportunity", fields)
        except Exception as exc:  # noqa: BLE001
            save_map(mapping)
            raise RuntimeError(f"Opportunity {key} failed; map preserved. {exc}") from exc
        mapping["opportunities"][key] = sf_id
        save_map(mapping)
        print(f"  {key} → {sf_id}")

    print("Creating Tasks...")
    for t in tasks:
        key = t["task_key"]
        if key in mapping["tasks"]:
            print(f"  SKIP {key} (already mapped)")
            continue
        require_deps(mapping, "contacts", [t["who_contact_key"]])
        if t["what_record_type"] == "Account":
            require_deps(mapping, "accounts", [t["what_record_key"]])
        else:
            require_deps(mapping, "opportunities", [t["what_record_key"]])
        fields = sf_task_fields(t, mapping)
        try:
            try:
                sf_id = create_record("Task", fields)
            except Exception as exc:  # noqa: BLE001
                print(f"  WARN {key} create failed ({exc}); retrying without TaskSubtype")
                fields = dict(fields)
                fields.pop("TaskSubtype", None)
                sf_id = create_record("Task", fields)
        except Exception as exc:  # noqa: BLE001
            save_map(mapping)
            raise RuntimeError(f"Task {key} failed; map preserved. {exc}") from exc
        mapping["tasks"][key] = sf_id
        save_map(mapping)
        print(f"  {key} → {sf_id}")

    print("Creating OpportunityContactRoles...")
    for o in ocrs:
        key = o["ocr_key"]
        if key in mapping["opportunity_contact_roles"]:
            print(f"  SKIP {key} (already mapped)")
            continue
        require_deps(mapping, "opportunities", [o["opportunity_key"]])
        require_deps(mapping, "contacts", [o["contact_key"]])
        fields = {
            "OpportunityId": mapping["opportunities"][o["opportunity_key"]],
            "ContactId": mapping["contacts"][o["contact_key"]],
            "Role": o["Role"],
            "IsPrimary": o["IsPrimary"],
        }
        try:
            sf_id = create_record("OpportunityContactRole", fields)
        except Exception as exc:  # noqa: BLE001
            save_map(mapping)
            raise RuntimeError(f"OCR {key} failed; map preserved. {exc}") from exc
        mapping["opportunity_contact_roles"][key] = sf_id
        save_map(mapping)
        print(f"  {key} → {sf_id}")

    print("Import complete.")
    save_map(mapping)


def verify() -> None:
    if not MAP_PATH.exists():
        print("No local ID map found; run an approved import first.")
        sys.exit(1)
    mapping = json.loads(MAP_PATH.read_text())
    checks = [
        ("Account", list(mapping.get("accounts", {}).values())),
        ("Contact", list(mapping.get("contacts", {}).values())),
        ("Opportunity", list(mapping.get("opportunities", {}).values())),
        ("Task", list(mapping.get("tasks", {}).values())),
        ("OpportunityContactRole", list(mapping.get("opportunity_contact_roles", {}).values())),
    ]
    for sobject, ids in checks:
        if not ids:
            print(f"{sobject}: no mapped Ids")
            continue
        id_list = ",".join(f"'{i}'" for i in ids)
        q = f"SELECT Id FROM {sobject} WHERE Id IN ({id_list})"
        result = run_sf(["data", "query", "-o", ORG_ALIAS, "-q", q])
        total = result.get("result", {}).get("totalSize")
        print(f"{sobject}: mapped={len(ids)} queried={total}")


def self_test() -> int:
    """
    Local / read-only checks: JSON payload safety, resume skips, dependency gates.
    Does not call Salesforce write APIs.
    """
    print("=== LOADER SELF-TEST (no Salesforce writes) ===")
    before = json.loads(MAP_PATH.read_text()) if MAP_PATH.exists() else empty_map()
    mapping = load_or_init_map()

    accounts = load_json("accounts.json")
    contacts = load_json("contacts.json")
    opportunities = load_json("opportunities.json")
    tasks = load_json("tasks.json")
    ocrs = load_json("opportunity_contact_roles.json")

    skip_accounts = [a["account_key"] for a in accounts if a["account_key"] in mapping["accounts"]]
    skip_contacts = [c["contact_key"] for c in contacts if c["contact_key"] in mapping["contacts"]]
    create_opps = [
        o["opportunity_key"]
        for o in opportunities
        if o["opportunity_key"] not in mapping["opportunities"]
    ]
    print(f"Would SKIP Accounts: {skip_accounts}")
    print(f"Would SKIP Contacts: {skip_contacts}")
    print(f"Would CREATE Opportunities (in order): {create_opps}")
    print(
        f"Would CREATE Tasks: {[t['task_key'] for t in tasks if t['task_key'] not in mapping['tasks']]}"
    )
    print(
        "Would CREATE OCRs: "
        f"{[o['ocr_key'] for o in ocrs if o['ocr_key'] not in mapping['opportunity_contact_roles']]}"
    )

    if set(skip_accounts) != {a["account_key"] for a in accounts}:
        print("FAIL: expected all Accounts to be skipped from existing ID map")
        return 1
    if set(skip_contacts) != {c["contact_key"] for c in contacts}:
        print("FAIL: expected all Contacts to be skipped from existing ID map")
        return 1
    if create_opps[:1] != ["OPP-001"]:
        print(f"FAIL: expected resume to start at OPP-001, got {create_opps[:1]}")
        return 1

    # Dependency gate: Tasks that What=Opportunity must not proceed without Opp Ids
    blocked = []
    for t in tasks:
        if t["what_record_type"] == "Opportunity" and t["what_record_key"] not in mapping[
            "opportunities"
        ]:
            blocked.append(t["task_key"])
    print(f"Tasks blocked until Opportunities exist: {blocked}")
    if not blocked:
        print("FAIL: expected Opportunity-related Tasks to be dependency-blocked")
        return 1

    # Build first Opportunity payload and prove apostrophes survive JSON serialization
    o = next(x for x in opportunities if x["opportunity_key"] == "OPP-001")
    require_deps(mapping, "accounts", [o["account_key"]])
    fields = {
        "Name": o["Name"],
        "AccountId": mapping["accounts"][o["account_key"]],
        "StageName": o["StageName"],
        "CloseDate": o["CloseDate"],
        "Amount": o["Amount"],
        "Type": o["Type"],
        "LeadSource": o["LeadSource"],
        "Description": o["Description"],
        "NextStep": o["NextStep"],
    }
    serialized = json.dumps(fields, ensure_ascii=False)
    roundtrip = json.loads(serialized)
    if "Meridian's" not in roundtrip["Description"]:
        print("FAIL: apostrophe lost in Opportunity Description JSON roundtrip")
        return 1
    if "'" in serialized and '\\"' not in serialized.split("Meridian")[0]:
        pass  # apostrophe as JSON character is fine unescaped in JSON strings
    print("OPP-001 payload JSON roundtrip OK (apostrophe preserved)")
    print("OPP-001 AccountId resolved to", fields["AccountId"])
    print("Sample payload (truncated Description):")
    preview = dict(fields)
    preview["Description"] = preview["Description"][:80] + "..."
    print(json.dumps(preview, indent=2, ensure_ascii=False))

    src = Path(__file__).read_text(encoding="utf-8")
    start = src.index("def create_record")
    end = src.index("\ndef ", start + 1)
    create_region = src[start:end]
    if "api request rest" not in (create_record.__doc__ or ""):
        print("FAIL: create_record docstring missing REST guidance")
        return 1
    if not all(tok in create_region for tok in ('"api"', '"request"', '"rest"', "-X", "POST")):
        print("FAIL: create_record does not appear to use api request rest + JSON body")
        return 1
    if '"-v"' in create_region or "'-v'" in create_region:
        print("FAIL: create_record still appears to use -v values")
        return 1
    print("create_record uses sf api request rest + JSON body file")

    after = json.loads(MAP_PATH.read_text()) if MAP_PATH.exists() else empty_map()
    if after != before:
        print("FAIL: self-test mutated ID map")
        return 1
    print("ID map unchanged by self-test")
    print("PASS: loader ready to resume at OPP-001")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Perform Salesforce inserts")
    parser.add_argument(
        "--i-approve-writes",
        action="store_true",
        help="Required together with --execute; confirms explicit human approval",
    )
    parser.add_argument("--verify", action="store_true", help="Verify mapped Ids exist in org")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Local resume/payload checks without Salesforce writes",
    )
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    if args.verify:
        verify()
        return 0

    if args.execute:
        if not args.i_approve_writes:
            print("Refusing to write: pass --i-approve-writes after explicit approval.")
            return 2
        execute_import()
        return 0

    print_plan()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
