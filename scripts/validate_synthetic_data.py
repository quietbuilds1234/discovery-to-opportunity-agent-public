#!/usr/bin/env python3
"""Validate local synthetic CRM and Granola fixtures. No Salesforce writes."""

from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

SF_ID_RE = re.compile(r"^[a-zA-Z0-9]{15}([a-zA-Z0-9]{3})?$")
ISO_DT_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$"
)


class Validator:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def load(self, name: str):
        path = DATA / name
        try:
            with path.open() as f:
                return json.load(f)
        except Exception as exc:  # noqa: BLE001
            self.err(f"{name}: JSON parse failed: {exc}")
            return None


def is_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def looks_like_sf_id(value: str) -> bool:
    if not isinstance(value, str):
        return False
    if value.startswith(("ACC-", "CON-", "OPP-", "TSK-", "OCR-", "MTG-", "gong-", "granola-")):
        return False
    return bool(SF_ID_RE.match(value)) and value.isalnum()


def main() -> int:
    v = Validator()
    accounts = v.load("accounts.json")
    contacts = v.load("contacts.json")
    opportunities = v.load("opportunities.json")
    tasks = v.load("tasks.json")
    ocrs = v.load("opportunity_contact_roles.json")
    meetings = v.load("granola_meetings.json")

    if None in (accounts, contacts, opportunities, tasks, ocrs, meetings):
        print("FAIL: one or more JSON files could not be parsed")
        for e in v.errors:
            print(f"  - {e}")
        return 1

    # Counts
    if len(accounts) != 3:
        v.err(f"Expected 3 accounts, found {len(accounts)}")
    if len(contacts) != 8:
        v.err(f"Expected 8 contacts, found {len(contacts)}")
    if len(opportunities) != 4:
        v.err(f"Expected 4 opportunities, found {len(opportunities)}")
    if len(tasks) != 11:
        v.err(f"Expected 11 tasks, found {len(tasks)}")
    if not (4 <= len(ocrs) <= 6):
        v.err(f"Expected 4–6 OCRs, found {len(ocrs)}")
    if len(meetings) != 5:
        v.err(f"Expected 5 granola meetings, found {len(meetings)}")

    meeting_tasks = [t for t in tasks if t.get("activity_kind") == "Meeting"]
    email_tasks = [t for t in tasks if t.get("activity_kind") == "Email"]
    if len(meeting_tasks) != 5:
        v.err(f"Expected 5 meeting tasks, found {len(meeting_tasks)}")
    if len(email_tasks) != 6:
        v.err(f"Expected 6 email tasks, found {len(email_tasks)}")

    acc_keys = {a.get("account_key") for a in accounts}
    con_keys = {c.get("contact_key") for c in contacts}
    opp_keys = {o.get("opportunity_key") for o in opportunities}
    tsk_keys = {t.get("task_key") for t in tasks}
    ocr_keys = {o.get("ocr_key") for o in ocrs}
    mtg_keys = {m.get("meeting_key") for m in meetings}

    def unique(label: str, keys: set, expected_prefix: str) -> None:
        raw = [
            x
            for x in (
                accounts
                if label == "accounts"
                else contacts
                if label == "contacts"
                else opportunities
                if label == "opportunities"
                else tasks
                if label == "tasks"
                else ocrs
                if label == "ocrs"
                else meetings
            )
        ]
        key_name = {
            "accounts": "account_key",
            "contacts": "contact_key",
            "opportunities": "opportunity_key",
            "tasks": "task_key",
            "ocrs": "ocr_key",
            "meetings": "meeting_key",
        }[label]
        values = [r.get(key_name) for r in raw]
        if len(values) != len(set(values)):
            v.err(f"{label}: duplicate synthetic keys")
        for key in values:
            if not isinstance(key, str) or not key.startswith(expected_prefix):
                v.err(f"{label}: invalid key {key!r}")
            if looks_like_sf_id(key):
                v.err(f"{label}: key {key!r} looks like a Salesforce Id")

    unique("accounts", acc_keys, "ACC-")
    unique("contacts", con_keys, "CON-")
    unique("opportunities", opp_keys, "OPP-")
    unique("tasks", tsk_keys, "TSK-")
    unique("ocrs", ocr_keys, "OCR-")
    unique("meetings", mtg_keys, "MTG-")

    # Account fields
    for a in accounts:
        for field in (
            "account_key",
            "Name",
            "Website",
            "Industry",
            "Type",
            "Description",
            "BillingCity",
            "BillingState",
            "BillingStateCode",
            "BillingCountry",
            "BillingCountryCode",
            "NumberOfEmployees",
        ):
            if field not in a or a[field] in (None, ""):
                v.err(f"{a.get('account_key')}: missing {field}")
        if not isinstance(a.get("NumberOfEmployees"), int):
            v.err(f"{a.get('account_key')}: NumberOfEmployees must be int")
        if a.get("BillingState") and not a.get("BillingCountry") and not a.get("BillingCountryCode"):
            v.err(
                f"{a.get('account_key')}: BillingState set without BillingCountry/BillingCountryCode"
            )

    # Contacts
    for c in contacts:
        for field in (
            "contact_key",
            "FirstName",
            "LastName",
            "Title",
            "Email",
            "Phone",
            "account_key",
        ):
            if field not in c or c[field] in (None, ""):
                v.err(f"{c.get('contact_key')}: missing {field}")
        if c.get("account_key") not in acc_keys:
            v.err(f"{c.get('contact_key')}: unknown account_key {c.get('account_key')}")
        if looks_like_sf_id(str(c.get("account_key"))):
            v.err(f"{c.get('contact_key')}: account_key looks like Salesforce Id")

    # Opportunities
    stages = {o.get("StageName") for o in opportunities}
    if "Closed Won" not in stages:
        v.err("Expected one Closed Won opportunity")
    if "Closed Lost" not in stages:
        v.err("Expected one Closed Lost opportunity")
    open_opps = [o for o in opportunities if o.get("StageName") not in ("Closed Won", "Closed Lost")]
    if len(open_opps) < 2:
        v.err("Expected at least two open opportunities")

    for o in opportunities:
        for field in (
            "opportunity_key",
            "Name",
            "account_key",
            "StageName",
            "CloseDate",
            "Amount",
            "Type",
            "LeadSource",
            "Description",
            "NextStep",
        ):
            if field not in o or o[field] in (None, ""):
                v.err(f"{o.get('opportunity_key')}: missing {field}")
        if o.get("account_key") not in acc_keys:
            v.err(f"{o.get('opportunity_key')}: unknown account_key")
        if not isinstance(o.get("Amount"), (int, float)):
            v.err(f"{o.get('opportunity_key')}: Amount must be numeric")
        if not is_date(str(o.get("CloseDate"))):
            v.err(f"{o.get('opportunity_key')}: invalid CloseDate")

    # Tasks
    gong_ids = []
    for t in tasks:
        for field in (
            "task_key",
            "Subject",
            "Status",
            "Priority",
            "ActivityDate",
            "Description",
            "activity_kind",
            "TaskSubtype",
            "who_contact_key",
            "what_record_type",
            "what_record_key",
            "gong_activity_id",
        ):
            if field not in t or t[field] in (None, ""):
                v.err(f"{t.get('task_key')}: missing {field}")
        if t.get("who_contact_key") not in con_keys:
            v.err(f"{t.get('task_key')}: unknown who_contact_key")
        what_type = t.get("what_record_type")
        what_key = t.get("what_record_key")
        if what_type == "Account":
            if what_key not in acc_keys:
                v.err(f"{t.get('task_key')}: unknown Account what_record_key")
        elif what_type == "Opportunity":
            if what_key not in opp_keys:
                v.err(f"{t.get('task_key')}: unknown Opportunity what_record_key")
        else:
            v.err(f"{t.get('task_key')}: what_record_type must be Account or Opportunity")
        if not is_date(str(t.get("ActivityDate"))):
            v.err(f"{t.get('task_key')}: invalid ActivityDate")
        gong_ids.append(t.get("gong_activity_id"))
        if t.get("activity_kind") == "Meeting" and not t.get("linked_meeting_key"):
            v.err(f"{t.get('task_key')}: meeting task missing linked_meeting_key")
        if "Type" in t:
            v.warn(
                f"{t.get('task_key')}: local field Type present; discovery-dev Task object has no Type field — loader must omit it"
            )

    if len(gong_ids) != len(set(gong_ids)):
        v.err("Duplicate gong_activity_id values")

    # OCR
    for o in ocrs:
        for field in ("ocr_key", "opportunity_key", "contact_key", "Role", "IsPrimary"):
            if field not in o:
                v.err(f"{o.get('ocr_key')}: missing {field}")
        if o.get("opportunity_key") not in opp_keys:
            v.err(f"{o.get('ocr_key')}: unknown opportunity_key")
        if o.get("contact_key") not in con_keys:
            v.err(f"{o.get('ocr_key')}: unknown contact_key")
        if not isinstance(o.get("IsPrimary"), bool):
            v.err(f"{o.get('ocr_key')}: IsPrimary must be boolean")

    # Meetings ↔ tasks 1:1
    meeting_linked_tasks = []
    for m in meetings:
        for field in (
            "meeting_key",
            "meeting_id",
            "title",
            "start_time",
            "end_time",
            "account_key",
            "account_name",
            "attendees",
            "transcript",
            "summary",
            "action_items",
            "linked_task_key",
        ):
            if field not in m or m[field] in (None, ""):
                v.err(f"{m.get('meeting_key')}: missing {field}")
        if m.get("account_key") not in acc_keys:
            v.err(f"{m.get('meeting_key')}: unknown account_key")
        if m.get("linked_task_key") not in tsk_keys:
            v.err(f"{m.get('meeting_key')}: unknown linked_task_key")
        else:
            meeting_linked_tasks.append(m.get("linked_task_key"))
        for ts_field in ("start_time", "end_time"):
            if not ISO_DT_RE.match(str(m.get(ts_field, ""))):
                v.err(f"{m.get('meeting_key')}: {ts_field} must be ISO-8601")
            else:
                try:
                    datetime.fromisoformat(str(m[ts_field]).replace("Z", "+00:00"))
                except ValueError:
                    v.err(f"{m.get('meeting_key')}: invalid {ts_field}")
        if not isinstance(m.get("attendees"), list) or not m.get("attendees"):
            v.err(f"{m.get('meeting_key')}: attendees must be non-empty list")
        if not isinstance(m.get("action_items"), list) or not m.get("action_items"):
            v.err(f"{m.get('meeting_key')}: action_items must be non-empty list")

    if len(meeting_linked_tasks) != len(set(meeting_linked_tasks)):
        v.err("Multiple meetings link to the same task")

    for t in meeting_tasks:
        mk = t.get("linked_meeting_key")
        if mk not in mtg_keys:
            v.err(f"{t.get('task_key')}: linked_meeting_key {mk} not found")
        else:
            meeting = next(m for m in meetings if m["meeting_key"] == mk)
            if meeting.get("linked_task_key") != t.get("task_key"):
                v.err(
                    f"{t.get('task_key')} / {mk}: meeting↔task link is not reciprocal"
                )
            mtg_day = str(meeting.get("start_time", ""))[:10]
            if t.get("ActivityDate") and mtg_day and t["ActivityDate"] != mtg_day:
                v.err(
                    f"{t.get('task_key')} / {mk}: ActivityDate {t['ActivityDate']} != meeting day {mtg_day}"
                )

    # Ensure no synthetic relationship fields look like SF IDs
    for collection, fields in (
        (contacts, ["account_key"]),
        (opportunities, ["account_key"]),
        (tasks, ["who_contact_key", "what_record_key", "linked_meeting_key"]),
        (ocrs, ["opportunity_key", "contact_key"]),
        (meetings, ["account_key", "linked_task_key"]),
    ):
        for row in collection:
            for field in fields:
                val = row.get(field)
                if val and looks_like_sf_id(str(val)):
                    v.err(f"{row}: field {field}={val} looks like Salesforce Id")

    print("Synthetic data validation")
    print(f"  accounts={len(accounts)} contacts={len(contacts)} opportunities={len(opportunities)}")
    print(
        f"  tasks={len(tasks)} (meetings={len(meeting_tasks)}, emails={len(email_tasks)})"
    )
    print(f"  ocrs={len(ocrs)} granola_meetings={len(meetings)}")

    if v.warnings:
        print("\nWarnings:")
        for w in v.warnings:
            print(f"  - {w}")

    if v.errors:
        print("\nFAIL")
        for e in v.errors:
            print(f"  - {e}")
        return 1

    print("\nPASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
