#!/usr/bin/env python3
"""
Mocked guards for the Discovery-to-Opportunity Salesforce write workflow.

Does NOT call Salesforce or Claude MCP. Validates Skill documentation invariants
and a small in-memory approval → create → OCR → verify state machine.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skill" / "discovery-to-opportunity"
TESTS_DIR = Path(__file__).resolve().parent
WRITES = (SKILL_DIR / "references" / "salesforce-writes.md").read_text()
SKILL = (SKILL_DIR / "SKILL.md").read_text()
RETRIEVAL = (SKILL_DIR / "references" / "salesforce-retrieval.md").read_text()
MAPPING = (SKILL_DIR / "references" / "salesforce-field-mapping.md").read_text()
DECISION = (SKILL_DIR / "references" / "decision-framework.md").read_text()
EXPECTED_OUTCOMES = json.loads((TESTS_DIR / "expected_outcomes.json").read_text())
MEETINGS = json.loads((SKILL_DIR / "fixtures" / "granola_meetings.json").read_text())
OPPORTUNITIES = json.loads((ROOT / "data" / "opportunities.json").read_text())


def initiative_fingerprint(
    *,
    name: str = "",
    description: str = "",
    summary: str = "",
    transcript: str = "",
) -> Dict[str, str]:
    """
    Derive use case / scope / buying motion for initiative comparison.

    Mirrors Skill decision-framework: match on problem/use case/product decision —
    not Account or Contact overlap alone.
    """
    name_l = name.lower()
    blob = f"{name}\n{description}\n{summary}\n{transcript}".lower()

    # Name-first: seeded AE platform Opp must not collapse into SDR pilot language
    # that also appears in Meridian transcripts distinguishing the two threads.
    if "sales intelligence platform" in name_l or (
        "platform" in name_l and "sdr" not in name_l and "pilot" not in name_l
    ):
        return {
            "use_case": "ae_sales_intelligence_platform",
            "scope": "ae_platform_rollout",
            "buying_motion": "platform_evaluation",
        }
    if "partner lead" in blob or "partner-referral" in blob or "partner-sourced" in blob:
        return {
            "use_case": "partner_lead_enrichment",
            "scope": "partner_referral_program",
            "buying_motion": "partner_marketing_enrichment",
        }
    if "sdr" in blob and (
        "contact" in blob or "outbound" in blob or "pilot" in blob or "research" in blob
    ):
        return {
            "use_case": "sdr_outbound_contact_data",
            "scope": "sdr_pilot",
            "buying_motion": "sales_budget_pilot",
        }
    if "sales intelligence platform" in blob or ("ae team" in blob and "platform" in blob):
        return {
            "use_case": "ae_sales_intelligence_platform",
            "scope": "ae_platform_rollout",
            "buying_motion": "platform_evaluation",
        }
    return {
        "use_case": "unknown",
        "scope": "unknown",
        "buying_motion": "unknown",
    }


def same_initiative(a: Dict[str, str], b: Dict[str, str]) -> bool:
    if a.get("use_case", "unknown") == "unknown":
        return False
    return (
        a.get("use_case") == b.get("use_case")
        and a.get("scope") == b.get("scope")
        and a.get("buying_motion") == b.get("buying_motion")
    )


def classify_meeting_against_open_opps(
    meeting_fp: Dict[str, str],
    open_opps: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Skill-style initiative check before create (EXISTING vs CREATE)."""
    for opp in open_opps:
        opp_fp = opp.get("initiative_fp") or initiative_fingerprint(
            name=str(opp.get("Name", "")),
            description=str(opp.get("Description", "")),
        )
        if same_initiative(meeting_fp, opp_fp):
            return {
                "outcome": "EXISTING OPPORTUNITY",
                "matched_id": opp["Id"],
                "matched_name": opp.get("Name"),
                "match_basis": {
                    "use_case": meeting_fp["use_case"],
                    "scope": meeting_fp["scope"],
                    "buying_motion": meeting_fp["buying_motion"],
                },
            }
    return {
        "outcome": "CREATE",
        "matched_id": None,
        "match_basis": None,
    }

MUTATION_TOOLS = {
    "mcp__Salesforce__createSobjectRecord",
    "mcp__Salesforce__updateSobjectRecord",
    "mcp__Salesforce__updateRelatedRecord",
}
REQUIRED_READ_TOOLS = {
    "mcp__Salesforce__soqlQuery",
    "mcp__Salesforce__getObjectSchema",
    "mcp__Salesforce__find",
    "mcp__Salesforce__getRelatedRecords",
    "mcp__Salesforce__listRecentSobjectRecords",
}


class DocInvariantTests(unittest.TestCase):
    def test_exact_tool_names_documented(self):
        for name in MUTATION_TOOLS | REQUIRED_READ_TOOLS | {"mcp__Salesforce__getUserInfo"}:
            self.assertIn(name, WRITES + RETRIEVAL)

    def test_no_hypothetical_tool_aliases_as_instructions(self):
        # Allowed only in "do not invent" prose
        for bad in ("describe_sobject", "create_record", "update_record"):
            for block in re.findall(r"```(?:json|soql)?\n(.*?)```", WRITES + SKILL, re.S):
                self.assertNotIn(bad, block)

    def test_approval_gate_language(self):
        blob = WRITES + SKILL
        self.assertIn("explicit", blob.lower())
        self.assertRegex(blob, r"(?i)specific preview|exact.*preview|shown.*preview")
        self.assertRegex(blob, r"(?i)looks good")
        self.assertIn("No mutation tool", WRITES)
        self.assertIn("Do not call any create/update MCP tool in this step", SKILL)

    def test_no_delete_instructions(self):
        # Must forbid delete; must not instruct calling a delete tool
        self.assertRegex(WRITES + SKILL, r"(?i)never.*delete|never invoke.*delete")
        self.assertNotRegex(
            WRITES + SKILL,
            r"mcp__Salesforce__delete|deleteSobjectRecord",
        )

    def test_contacts_never_auto_created(self):
        self.assertRegex(WRITES + SKILL, r"(?i)do not.*create new Contacts|Never.*create Contacts|Do not create Contacts")
        self.assertRegex(WRITES, r'sobject-name:\s*"Contact".*forbidden')

    def test_duplicate_opp_and_ocr_checks(self):
        self.assertIn("Re-check duplicate Opportunities", WRITES)
        self.assertRegex(WRITES, r"(?i)skip any `ContactId` already linked|avoid duplicates")

    def test_timeout_no_blind_retry(self):
        self.assertRegex(WRITES + SKILL, r"(?i)blind-retry|do not blind")
        self.assertRegex(WRITES, r"(?i)query Salesforce first|query first")

    def test_no_false_success_without_verify(self):
        self.assertRegex(WRITES, r"(?i)verification reads succeed|Verify.*before claiming")
        self.assertIn("Never claim success from a create tool response alone", WRITES)

    def test_bant_meddpicc_and_handoff_preserved(self):
        self.assertIn("BANT", SKILL)
        self.assertIn("MEDDPICC", SKILL)
        self.assertIn("Handoff_Notes__c", SKILL + MAPPING + WRITES)
        self.assertIn("writes do not replace qualification", WRITES)
        self.assertIn("Executive Summary", SKILL)

    def test_ocr_docs_default_omit_role_and_isprimary(self):
        self.assertIn("Default create body", WRITES)
        self.assertRegex(WRITES, r"(?i)omit.*IsPrimary|Omit by default")
        self.assertRegex(WRITES + MAPPING, r"(?i)not from title|not.*title alone")
        # Default example JSON must not force IsPrimary:true
        default_examples = re.findall(
            r"Default example.*?\n```json\n(.*?)\n```",
            WRITES,
            re.S,
        )
        self.assertTrue(default_examples)
        self.assertNotIn("IsPrimary", default_examples[0])
        self.assertNotIn('"Role"', default_examples[0])

    def test_handoff_rejection_documented(self):
        self.assertIn("Handoff_Notes__c` rejected on create", WRITES)
        self.assertRegex(WRITES, r"(?i)do not silently drop|preserve drafted")

    def test_no_apex_binds_in_soql_fences(self):
        for block in re.findall(r"```soql\n(.*?)```", RETRIEVAL, re.S):
            self.assertFalse(re.search(r":[a-zA-Z]\w*", block), block[:80])


@dataclass
class Preview:
    name: str
    stage: str
    close_date: str
    account_id: str
    handoff: str
    ocr_contact_ids: List[str]
    approved: bool = False
    # ContactId -> Role only when evidence + preview establish it (never from title alone)
    ocr_roles: Dict[str, str] = field(default_factory=dict)
    # ContactId explicitly designated primary on the approved preview; else omit IsPrimary
    ocr_is_primary: Optional[str] = None


def build_ocr_create_body(
    *,
    opportunity_id: str,
    contact_id: str,
    role: Optional[str] = None,
    is_primary: bool = False,
    job_title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    OCR payload builder mirroring salesforce-writes.md.
    job_title is accepted only to prove it is never mapped into Role.
    """
    _ = job_title  # intentionally unused — titles must not imply Role
    body: Dict[str, Any] = {
        "OpportunityId": opportunity_id,
        "ContactId": contact_id,
    }
    if role:
        body["Role"] = role
    if is_primary:
        body["IsPrimary"] = True
    return body


@dataclass
class MockSalesforce:
    """In-memory stand-in; never network."""

    open_opps_by_account: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    opportunities: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    ocrs: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    contacts: Set[str] = field(default_factory=set)
    create_calls: List[Dict[str, Any]] = field(default_factory=list)
    update_calls: List[Dict[str, Any]] = field(default_factory=list)
    query_calls: List[Dict[str, Any]] = field(default_factory=list)
    delete_calls: List[Dict[str, Any]] = field(default_factory=list)
    next_opp_id: int = 1
    fail_opp_create: bool = False
    fail_ocr_for: Set[str] = field(default_factory=set)
    timeout_opp_create: bool = False
    # If timeout "actually" created despite no response
    timeout_actually_created: bool = False
    # Handoff_Notes__c field rejected → entire create fails
    reject_handoff_field_on_create: bool = False
    # Opp create succeeds but Handoff_Notes__c is not persisted
    strip_handoff_on_create: bool = False
    # After create, verification read returns a mismatched handoff value
    corrupt_handoff_on_verify: bool = False

    def _register_open_opp(self, oid: str, body: Dict[str, Any], initiative: str = "sdr") -> None:
        acc = body.get("AccountId")
        if not acc:
            return
        fp = body.get("initiative_fp") or initiative_fingerprint(
            name=str(body.get("Name", "")),
            description=str(body.get("Description", "")),
            summary=str(body.get("Handoff_Notes__c", "")),
        )
        entry = {
            "Id": oid,
            "Name": body.get("Name"),
            "Description": body.get("Description", ""),
            "initiative": initiative,
            "initiative_fp": fp,
        }
        bucket = self.open_opps_by_account.setdefault(acc, [])
        if any(o["Id"] == oid for o in bucket):
            return
        bucket.append(entry)

    def create(self, sobject_name: str, body: Dict[str, Any], *, initiative: str = "sdr") -> Dict[str, Any]:
        self.create_calls.append({"sobject-name": sobject_name, "body": body})
        if sobject_name == "Contact":
            raise AssertionError("Contact create is forbidden")
        if sobject_name == "Opportunity":
            if self.reject_handoff_field_on_create and "Handoff_Notes__c" in body:
                return {
                    "status": "error",
                    "id": None,
                    "message": "INVALID_FIELD_FOR_INSERT_UPDATE: Handoff_Notes__c",
                    "field": "Handoff_Notes__c",
                }
            if self.timeout_opp_create:
                if self.timeout_actually_created:
                    oid = f"006MOCK{self.next_opp_id:03d}"
                    self.next_opp_id += 1
                    stored = dict(body)
                    if self.strip_handoff_on_create:
                        stored.pop("Handoff_Notes__c", None)
                    self.opportunities[oid] = stored
                    self.opportunities[oid]["Id"] = oid
                    self.ocrs.setdefault(oid, [])
                    self._register_open_opp(oid, body, initiative=initiative)
                return {"status": "timeout", "id": None}
            if self.fail_opp_create:
                return {"status": "error", "id": None, "message": "create failed"}
            oid = f"006MOCK{self.next_opp_id:03d}"
            self.next_opp_id += 1
            rec = dict(body)
            if self.strip_handoff_on_create:
                rec.pop("Handoff_Notes__c", None)
            rec["Id"] = oid
            self.opportunities[oid] = rec
            self.ocrs[oid] = []
            self._register_open_opp(oid, body, initiative=initiative)
            return {"status": "ok", "id": oid}
        if sobject_name == "OpportunityContactRole":
            oid = body["OpportunityId"]
            cid = body["ContactId"]
            if cid in self.fail_ocr_for:
                return {"status": "error", "id": None, "message": "ocr failed"}
            if any(r["ContactId"] == cid for r in self.ocrs.get(oid, [])):
                return {"status": "error", "id": None, "message": "duplicate ocr"}
            rid = f"00K{cid[-3:]}"
            self.ocrs.setdefault(oid, []).append({**body, "Id": rid})
            return {"status": "ok", "id": rid}
        raise AssertionError(f"unexpected sobject {sobject_name}")

    def update(self, sobject_name: str, record_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Tracks updateSobjectRecord-equivalent calls; not used on EXISTING auto-path."""
        self.update_calls.append(
            {"sobject-name": sobject_name, "id": record_id, "body": body}
        )
        if sobject_name == "Opportunity" and record_id in self.opportunities:
            self.opportunities[record_id].update(body)
            return {"status": "ok", "id": record_id}
        return {"status": "error", "id": None, "message": "not found"}

    def delete(self, sobject_name: str, record_id: str) -> Dict[str, Any]:
        self.delete_calls.append({"sobject-name": sobject_name, "id": record_id})
        raise AssertionError("Salesforce delete is forbidden in this workflow")

    def find_open_same_initiative(self, account_id: str, initiative: str = "sdr") -> Optional[str]:
        self.query_calls.append(
            {
                "purpose": "duplicate_recheck",
                "account_id": account_id,
                "initiative": initiative,
            }
        )
        for o in self.open_opps_by_account.get(account_id, []):
            if o.get("initiative") == initiative:
                return o["Id"]
        return None

    def query_opps_by_name_account(self, name: str, account_id: str) -> List[str]:
        self.query_calls.append(
            {"purpose": "timeout_recovery", "name": name, "account_id": account_id}
        )
        return [
            oid
            for oid, rec in self.opportunities.items()
            if rec.get("Name") == name and rec.get("AccountId") == account_id
        ]

    def verify_opportunity_handoff(self, opp_id: str, expected_handoff: str) -> Dict[str, Any]:
        """Post-create verification read for Handoff_Notes__c."""
        self.query_calls.append({"purpose": "verify_handoff", "opp_id": opp_id})
        rec = self.opportunities.get(opp_id)
        if not rec:
            return {"found": False, "handoff": None, "matches": False}
        stored = rec.get("Handoff_Notes__c")
        if self.corrupt_handoff_on_verify:
            stored = "<<corrupted verification read>>"
        return {
            "found": True,
            "handoff": stored,
            "matches": stored == expected_handoff,
        }


class WriteWorkflow:
    """Mirrors Skill Step 6 guards for unit testing."""

    def __init__(self, sf: MockSalesforce):
        self.sf = sf
        self.mutations_allowed = False
        self.last_preview: Optional[Preview] = None
        self.create_attempt_count = 0

    def show_preview(self, preview: Preview) -> None:
        self.last_preview = preview
        self.mutations_allowed = False

    def approve(self, phrase: str) -> bool:
        ok = bool(
            re.search(
                r"(?i)\b(yes,?\s*create|approved.*create|create (the )?opportunity|go ahead and create)\b",
                phrase,
            )
        )
        if ok and self.last_preview:
            self.last_preview.approved = True
            self.mutations_allowed = True
        return ok

    def _require_mutation_allowed(self):
        if not self.mutations_allowed or not self.last_preview or not self.last_preview.approved:
            raise RuntimeError("mutation blocked: no explicit approval of current preview")

    def _ocr_body_for_contact(self, opp_id: str, contact_id: str, preview: Preview) -> Dict[str, Any]:
        return build_ocr_create_body(
            opportunity_id=opp_id,
            contact_id=contact_id,
            role=preview.ocr_roles.get(contact_id),
            is_primary=(preview.ocr_is_primary == contact_id),
            job_title=None,
        )

    def execute_create(self, initiative: str = "sdr") -> Dict[str, Any]:
        self._require_mutation_allowed()
        p = self.last_preview
        assert p is not None

        # Pre-create duplicate Opp re-check (re-query after approval, before mutation)
        existing = self.sf.find_open_same_initiative(p.account_id, initiative)
        if existing:
            self.mutations_allowed = False
            matched = next(
                (
                    o
                    for o in self.sf.open_opps_by_account.get(p.account_id, [])
                    if o["Id"] == existing
                ),
                {"Id": existing, "Name": None},
            )
            return {
                "status": "blocked_duplicate_opp",
                "existing_id": existing,
                "matched_name": matched.get("Name"),
                "handoff_saved": False,
                "handoff_claimed_success": False,
                "full_success": False,
                "succeeded": [],
                "failed": [
                    f"Opportunity create blocked — matching open Opp {existing} "
                    f"({matched.get('Name')}) found on post-approval re-query"
                ],
                "rep_message": (
                    f"Stopped before create. Matching Opportunity already exists: "
                    f"{existing} ({matched.get('Name')}). No Opportunity update or "
                    f"Contact Role writes were performed."
                ),
                "create_retries": 0,
                "deleted": False,
            }

        self.create_attempt_count += 1
        result = self.sf.create(
            "Opportunity",
            {
                "Name": p.name,
                "StageName": p.stage,
                "CloseDate": p.close_date,
                "AccountId": p.account_id,
                "Description": "SDR outbound research + Salesforce contact-data pilot",
                "Handoff_Notes__c": p.handoff,
            },
            initiative=initiative,
        )

        if result["status"] == "timeout":
            # Must query first — no blind retry
            found = self.sf.query_opps_by_name_account(p.name, p.account_id)
            if not found:
                return {
                    "status": "timeout_unconfirmed",
                    "verified": False,
                    "handoff_saved": False,
                    "handoff_claimed_success": False,
                    "full_success": False,
                    "succeeded": [],
                    "failed": ["Opportunity create timed out; record not found on re-query"],
                    "rep_message": (
                        "Opportunity create timed out and no matching record was found. "
                        "No blind retry. No delete. Handoff was not confirmed saved."
                    ),
                    "create_retries": 0,
                    "deleted": False,
                }
            opp_id = found[0]
        elif result["status"] != "ok":
            field = result.get("field")
            if field == "Handoff_Notes__c":
                return {
                    "status": "handoff_rejected_on_create",
                    "verified": False,
                    "handoff_saved": False,
                    "handoff_claimed_success": False,
                    "full_success": False,
                    "detail": result,
                    "succeeded": [],
                    "failed": [
                        f"Opportunity create rejected because of Handoff_Notes__c: "
                        f"{result.get('message')}"
                    ],
                    "rep_message": (
                        "Salesforce rejected Handoff_Notes__c on Opportunity create. "
                        "No Opportunity was created. Drafted handoff notes are preserved "
                        "locally for retry only after you re-approve (optionally without "
                        "handoff, then a separate approved update). No delete. No OCR writes."
                    ),
                    "create_retries": 0,
                    "deleted": False,
                    "draft_handoff_preserved": True,
                }
            return {
                "status": "opp_failed",
                "verified": False,
                "handoff_saved": False,
                "handoff_claimed_success": False,
                "full_success": False,
                "detail": result,
                "succeeded": [],
                "failed": [f"Opportunity create failed: {result.get('message')}"],
                "rep_message": (
                    f"Opportunity create failed ({result.get('message')}). "
                    "No OCRs written. Handoff not saved."
                ),
                "create_retries": 0,
                "deleted": False,
            }
        else:
            opp_id = result["id"]

        # Existing OCRs
        already = {r["ContactId"] for r in self.sf.ocrs.get(opp_id, [])}
        ocr_ok: List[str] = []
        ocr_fail: List[str] = []
        for cid in p.ocr_contact_ids:
            if cid not in self.sf.contacts:
                continue  # never auto-create Contact
            if cid in already:
                continue  # duplicate OCR skip
            ocr_res = self.sf.create(
                "OpportunityContactRole",
                self._ocr_body_for_contact(opp_id, cid, p),
            )
            if ocr_res["status"] == "ok":
                ocr_ok.append(cid)
                already.add(cid)
            else:
                ocr_fail.append(cid)

        # Verify Opp + handoff (required before claiming handoff success)
        verified_opp = opp_id in self.sf.opportunities
        handoff_verify = self.sf.verify_opportunity_handoff(opp_id, p.handoff)
        verified_handoff = bool(handoff_verify.get("matches"))
        verified_ocrs = all(
            any(r["ContactId"] == cid for r in self.sf.ocrs.get(opp_id, []))
            for cid in ocr_ok
        )
        full_success = (
            verified_opp
            and verified_handoff
            and verified_ocrs
            and not ocr_fail
            and set(ocr_ok)
            == {c for c in p.ocr_contact_ids if c in self.sf.contacts}
        )

        succeeded = []
        failed = []
        if verified_opp:
            succeeded.append(f"Opportunity created ({opp_id})")
        if verified_handoff:
            succeeded.append("Handoff_Notes__c verified on Opportunity")
        else:
            failed.append(
                "Handoff_Notes__c not confirmed on Opportunity "
                f"(stored={handoff_verify.get('handoff')!r})"
            )
        for cid in ocr_ok:
            succeeded.append(f"OCR created for Contact {cid}")
        for cid in ocr_fail:
            failed.append(f"OCR failed for Contact {cid}")

        if not verified_handoff:
            status = "partial_handoff_unverified"
            rep_message = (
                f"Opportunity {opp_id} was created and preserved. "
                f"Handoff_Notes__c was NOT confirmed saved "
                f"(verification mismatch or missing field). "
                f"OCRs ok={ocr_ok}; failed={ocr_fail}. "
                "Do not claim the handoff was saved. No blind retry. No delete."
            )
        elif full_success:
            status = "full_success"
            rep_message = (
                f"Full success: Opportunity {opp_id}, Handoff_Notes__c verified, "
                f"OCRs {ocr_ok}."
            )
        else:
            status = "partial_or_unverified"
            rep_message = (
                f"Partial success: Opportunity {opp_id} preserved. "
                f"Succeeded: {succeeded}. Failed: {failed}."
            )

        return {
            "status": status,
            "opp_id": opp_id,
            "ocr_ok": ocr_ok,
            "ocr_fail": ocr_fail,
            "verified": verified_opp and verified_handoff,
            "handoff_saved": verified_handoff,
            "handoff_claimed_success": verified_handoff and full_success,
            "full_success": full_success,
            "succeeded": succeeded,
            "failed": failed,
            "rep_message": rep_message,
            "create_retries": 0,
            "deleted": False,
            "draft_handoff_preserved": not verified_handoff,
        }


class MockWorkflowBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.sf = MockSalesforce(contacts={"003AAA", "003BBB"})
        self.wf = WriteWorkflow(self.sf)
        self.preview = Preview(
            name="Meridian Robotics - SDR Pilot",
            stage="Prospecting",
            close_date="2027-01-31",
            account_id="001ACC",
            handoff="=== Executive Summary ===\nTest",
            ocr_contact_ids=["003AAA", "003BBB", "UNRESOLVED"],
        )

    def test_blocks_mutation_before_approval(self):
        self.wf.show_preview(self.preview)
        with self.assertRaises(RuntimeError):
            self.wf.execute_create()
        self.assertEqual(self.sf.create_calls, [])

    def test_rejects_weak_approval_phrases(self):
        self.wf.show_preview(self.preview)
        self.assertFalse(self.wf.approve("looks good"))
        self.assertFalse(self.wf.approve("thanks"))
        with self.assertRaises(RuntimeError):
            self.wf.execute_create()

    def test_happy_path_after_explicit_approval(self):
        self.wf.show_preview(self.preview)
        self.assertTrue(self.wf.approve("Yes, create the Opportunity"))
        out = self.wf.execute_create()
        self.assertTrue(out["full_success"])
        self.assertEqual(out["status"], "full_success")
        self.assertTrue(out["handoff_saved"])
        self.assertTrue(out["handoff_claimed_success"])
        # Contact create never called; unresolved skipped
        self.assertTrue(all(c["sobject-name"] != "Contact" for c in self.sf.create_calls))
        self.assertEqual(set(out["ocr_ok"]), {"003AAA", "003BBB"})
        # Default OCR payloads omit Role / IsPrimary when not on preview
        ocr_bodies = [
            c["body"]
            for c in self.sf.create_calls
            if c["sobject-name"] == "OpportunityContactRole"
        ]
        self.assertTrue(ocr_bodies)
        for body in ocr_bodies:
            self.assertEqual(set(body.keys()), {"OpportunityId", "ContactId"})

    def test_material_preview_change_requires_reapproval(self):
        self.wf.show_preview(self.preview)
        self.wf.approve("approved — create the Opportunity")
        # Material change resets approval via new preview
        changed = Preview(**{**self.preview.__dict__, "name": "Changed Name", "approved": False})
        self.wf.show_preview(changed)
        with self.assertRaises(RuntimeError):
            self.wf.execute_create()

    def test_duplicate_opp_blocks_create(self):
        self.sf.open_opps_by_account["001ACC"] = [
            {"Id": "006EXIST", "Name": "SDR Pilot", "initiative": "sdr"}
        ]
        self.wf.show_preview(self.preview)
        self.wf.approve("yes, create it")
        out = self.wf.execute_create()
        self.assertEqual(out["status"], "blocked_duplicate_opp")
        self.assertEqual(self.sf.create_calls, [])
        self.assertTrue(
            any(q["purpose"] == "duplicate_recheck" for q in self.sf.query_calls)
        )

    def test_opp_failure_skips_ocr(self):
        self.sf.fail_opp_create = True
        self.wf.show_preview(self.preview)
        self.wf.approve("yes, create it")
        out = self.wf.execute_create()
        self.assertEqual(out["status"], "opp_failed")
        self.assertTrue(all(c["sobject-name"] == "Opportunity" for c in self.sf.create_calls))

    def test_partial_ocr_failure_preserves_opp(self):
        self.sf.fail_ocr_for = {"003BBB"}
        self.wf.show_preview(self.preview)
        self.wf.approve("yes, create it")
        out = self.wf.execute_create()
        self.assertIn(out["opp_id"], self.sf.opportunities)
        self.assertEqual(out["ocr_ok"], ["003AAA"])
        self.assertEqual(out["ocr_fail"], ["003BBB"])
        self.assertFalse(out["full_success"])

    def test_duplicate_ocr_skipped(self):
        self.wf.show_preview(self.preview)
        self.wf.approve("yes, create it")
        out1 = self.wf.execute_create()
        # Simulate second OCR pass with same contacts already linked
        already = {r["ContactId"] for r in self.sf.ocrs[out1["opp_id"]]}
        self.assertEqual(already, {"003AAA", "003BBB"})
        # Creating again should no-op duplicates inside execute path via already set
        ocr_calls_before = sum(
            1 for c in self.sf.create_calls if c["sobject-name"] == "OpportunityContactRole"
        )
        # Manual second association attempt through sf with duplicate
        dup = self.sf.create(
            "OpportunityContactRole",
            {"OpportunityId": out1["opp_id"], "ContactId": "003AAA"},
        )
        self.assertEqual(dup["status"], "error")
        ocr_calls_after = sum(
            1 for c in self.sf.create_calls if c["sobject-name"] == "OpportunityContactRole"
        )
        self.assertEqual(ocr_calls_after, ocr_calls_before + 1)  # attempted but errored

    def test_timeout_queries_before_retry_logic(self):
        self.sf.timeout_opp_create = True
        self.sf.timeout_actually_created = False
        self.wf.show_preview(self.preview)
        self.wf.approve("yes, create it")
        out = self.wf.execute_create()
        self.assertEqual(out["status"], "timeout_unconfirmed")
        # Only one create attempt (no blind retry)
        self.assertEqual(
            sum(1 for c in self.sf.create_calls if c["sobject-name"] == "Opportunity"),
            1,
        )

    def test_timeout_recovers_when_record_exists(self):
        self.sf.timeout_opp_create = True
        self.sf.timeout_actually_created = True
        self.wf.show_preview(self.preview)
        self.wf.approve("yes, create it")
        out = self.wf.execute_create()
        self.assertTrue(out["verified"])
        self.assertIn(out["opp_id"], self.sf.opportunities)

    def test_handoff_field_rejected_on_create(self):
        self.sf.reject_handoff_field_on_create = True
        self.wf.show_preview(self.preview)
        self.wf.approve("yes, create it")
        out = self.wf.execute_create()
        self.assertEqual(out["status"], "handoff_rejected_on_create")
        self.assertFalse(out["handoff_saved"])
        self.assertFalse(out["handoff_claimed_success"])
        self.assertFalse(out["full_success"])
        self.assertTrue(out["draft_handoff_preserved"])
        self.assertEqual(self.sf.opportunities, {})
        self.assertEqual(self.wf.create_attempt_count, 1)
        self.assertEqual(out["create_retries"], 0)
        self.assertFalse(out["deleted"])
        self.assertEqual(self.sf.delete_calls, [])
        self.assertTrue(
            all(c["sobject-name"] != "OpportunityContactRole" for c in self.sf.create_calls)
        )
        self.assertIn("Handoff_Notes__c", out["rep_message"])
        self.assertIn("No Opportunity was created", out["rep_message"])

    def test_handoff_verification_mismatch_preserves_opp(self):
        self.sf.strip_handoff_on_create = True
        self.wf.show_preview(self.preview)
        self.wf.approve("yes, create it")
        out = self.wf.execute_create()
        self.assertEqual(out["status"], "partial_handoff_unverified")
        self.assertIn(out["opp_id"], self.sf.opportunities)
        self.assertNotIn("Handoff_Notes__c", self.sf.opportunities[out["opp_id"]])
        self.assertFalse(out["handoff_saved"])
        self.assertFalse(out["handoff_claimed_success"])
        self.assertFalse(out["full_success"])
        self.assertEqual(out["create_retries"], 0)
        self.assertFalse(out["deleted"])
        self.assertEqual(self.sf.delete_calls, [])
        self.assertIn("NOT confirmed saved", out["rep_message"])
        self.assertTrue(any("Handoff_Notes__c" in f for f in out["failed"]))
        self.assertTrue(any(out["opp_id"] in s for s in out["succeeded"]))
        # OCRs may still proceed after Opp Id; Opp must remain
        self.assertEqual(self.wf.create_attempt_count, 1)

    def test_handoff_corrupt_verify_read_does_not_claim_success(self):
        self.sf.corrupt_handoff_on_verify = True
        self.wf.show_preview(self.preview)
        self.wf.approve("yes, create it")
        out = self.wf.execute_create()
        self.assertEqual(out["status"], "partial_handoff_unverified")
        self.assertTrue(
            self.sf.opportunities[out["opp_id"]].get("Handoff_Notes__c") == self.preview.handoff
        )
        self.assertFalse(out["handoff_claimed_success"])
        self.assertIn("Do not claim the handoff was saved", out["rep_message"])

    def test_ocr_omits_role_and_isprimary_without_evidence(self):
        # Titles must never become Role
        body = build_ocr_create_body(
            opportunity_id="006X",
            contact_id="003AAA",
            role=None,
            is_primary=False,
            job_title="VP of Sales",
        )
        self.assertEqual(body, {"OpportunityId": "006X", "ContactId": "003AAA"})
        self.assertNotIn("Role", body)
        self.assertNotIn("IsPrimary", body)

        self.wf.show_preview(self.preview)  # no ocr_roles / ocr_is_primary
        self.wf.approve("yes, create it")
        self.wf.execute_create()
        for c in self.sf.create_calls:
            if c["sobject-name"] == "OpportunityContactRole":
                self.assertNotIn("Role", c["body"])
                self.assertNotIn("IsPrimary", c["body"])

    def test_ocr_includes_role_and_isprimary_only_when_preview_evidenced(self):
        preview = Preview(
            name=self.preview.name,
            stage=self.preview.stage,
            close_date=self.preview.close_date,
            account_id=self.preview.account_id,
            handoff=self.preview.handoff,
            ocr_contact_ids=["003AAA", "003BBB"],
            ocr_roles={"003AAA": "Decision Maker"},  # evidenced + on preview
            ocr_is_primary="003AAA",
        )
        self.wf.show_preview(preview)
        self.wf.approve("yes, create it")
        self.wf.execute_create()
        by_contact = {
            c["body"]["ContactId"]: c["body"]
            for c in self.sf.create_calls
            if c["sobject-name"] == "OpportunityContactRole"
        }
        self.assertEqual(by_contact["003AAA"].get("Role"), "Decision Maker")
        self.assertTrue(by_contact["003AAA"].get("IsPrimary") is True)
        # Second contact: association only — no invented Role/Primary from attendance
        self.assertNotIn("Role", by_contact["003BBB"])
        self.assertNotIn("IsPrimary", by_contact["003BBB"])

    def test_post_approval_duplicate_recheck_blocks_create(self):
        """Approve first; matching Opp appears before create → re-query blocks writes."""
        self.wf.show_preview(self.preview)
        self.assertTrue(self.wf.approve("Yes, create the Opportunity"))
        self.assertTrue(self.wf.mutations_allowed)
        # Matching Opportunity appears after approval, before mutation
        self.sf.open_opps_by_account["001ACC"] = [
            {
                "Id": "006POSTAPPROVE",
                "Name": "Meridian Robotics - SDR Pilot",
                "initiative": "sdr",
                "initiative_fp": initiative_fingerprint(
                    name="Meridian Robotics - SDR Pilot",
                    description="SDR outbound contact-data pilot",
                ),
            }
        ]
        creates_before = list(self.sf.create_calls)
        updates_before = list(self.sf.update_calls)
        out = self.wf.execute_create(initiative="sdr")
        self.assertEqual(out["status"], "blocked_duplicate_opp")
        self.assertEqual(out["existing_id"], "006POSTAPPROVE")
        self.assertEqual(out["matched_name"], "Meridian Robotics - SDR Pilot")
        self.assertTrue(
            any(q["purpose"] == "duplicate_recheck" for q in self.sf.query_calls)
        )
        self.assertEqual(self.sf.create_calls, creates_before)
        self.assertEqual(self.sf.update_calls, updates_before)
        self.assertFalse(
            any(c["sobject-name"] == "Opportunity" for c in self.sf.create_calls)
        )
        self.assertFalse(
            any(c["sobject-name"] == "OpportunityContactRole" for c in self.sf.create_calls)
        )
        self.assertFalse(out["handoff_claimed_success"])
        self.assertIn("006POSTAPPROVE", out["rep_message"])
        self.assertFalse(self.wf.mutations_allowed)


class Scenario05CrmVariantTests(unittest.TestCase):
    """
    SCENARIO-05 crm_state_variants: after MTG-001 creates an SDR/contact-data Opp,
    MTG-005 must classify EXISTING OPPORTUNITY and not create/update automatically.
    """

    ACCOUNT_ID = "001ACC_MERIDIAN"

    def setUp(self):
        self.scenario_05 = next(
            s for s in EXPECTED_OUTCOMES if s["scenario_key"] == "SCENARIO-05"
        )
        self.existing_variant = next(
            v
            for v in self.scenario_05["crm_state_variants"]
            if v["expected_outcome"] == "EXISTING OPPORTUNITY"
        )
        self.mtg_001 = next(m for m in MEETINGS if m["meeting_key"] == "MTG-001")
        self.mtg_005 = next(m for m in MEETINGS if m["meeting_key"] == "MTG-005")
        self.opp_001 = next(
            o for o in OPPORTUNITIES if o["opportunity_key"] == "OPP-001"
        )
        self.sf = MockSalesforce(contacts={"003AAA", "003BBB"})
        self.wf = WriteWorkflow(self.sf)

        # Seeded AE-platform Opp on same Account (and would share Contacts) —
        # must NOT count as same initiative as SDR pilot.
        ae_fp = initiative_fingerprint(
            name=self.opp_001["Name"],
            description=self.opp_001["Description"],
        )
        self.sf.open_opps_by_account[self.ACCOUNT_ID] = [
            {
                "Id": "006OPP001",
                "Name": self.opp_001["Name"],
                "Description": self.opp_001["Description"],
                "initiative": "ae_platform",
                "initiative_fp": ae_fp,
            }
        ]
        self.sf.opportunities["006OPP001"] = {
            "Id": "006OPP001",
            "Name": self.opp_001["Name"],
            "Description": self.opp_001["Description"],
            "AccountId": self.ACCOUNT_ID,
            "StageName": self.opp_001["StageName"],
        }

    def test_expected_outcomes_define_post_mtg001_existing_variant(self):
        self.assertIn("after MTG-001", self.existing_variant["when"])
        self.assertTrue(self.existing_variant["should_flag_duplicate"])
        self.assertFalse(self.existing_variant["opportunity_creation_allowed"])
        self.assertEqual(
            self.scenario_05["referenced_record_keys"]["prior_meeting_key"],
            "MTG-001",
        )
        self.assertEqual(
            self.scenario_05["referenced_record_keys"]["meeting_key"],
            "MTG-005",
        )
        # Skill docs encode the same rule
        self.assertIn("MTG-001 ↔ MTG-005", RETRIEVAL)
        self.assertIn("EXISTING OPPORTUNITY", RETRIEVAL)
        self.assertRegex(DECISION, r"(?i)Shared Account/contacts alone is \*\*not\*\* a duplicate")
        self.assertIn("Do not enter the write path", WRITES)

    def test_mtg001_create_then_mtg005_existing_no_second_write(self):
        # --- 1) MTG-001: same Account has only AE-platform Opp → CREATE SDR Opp ---
        mtg001_fp = initiative_fingerprint(
            name=self.mtg_001["title"],
            summary=self.mtg_001["summary"],
            transcript=self.mtg_001["transcript"],
        )
        pre = classify_meeting_against_open_opps(
            mtg001_fp, self.sf.open_opps_by_account[self.ACCOUNT_ID]
        )
        self.assertEqual(pre["outcome"], "CREATE")
        self.assertIsNone(pre["matched_id"])
        self.assertEqual(mtg001_fp["use_case"], "sdr_outbound_contact_data")
        self.assertNotEqual(
            mtg001_fp["use_case"],
            initiative_fingerprint(
                name=self.opp_001["Name"],
                description=self.opp_001["Description"],
            )["use_case"],
        )

        preview = Preview(
            name="Meridian Robotics - SDR Outbound & Contact Data Pilot",
            stage="Prospecting",
            close_date="2027-01-31",
            account_id=self.ACCOUNT_ID,
            handoff="=== Executive Summary ===\nSDR contact-data pilot from MTG-001",
            ocr_contact_ids=["003AAA", "003BBB"],
        )
        self.wf.show_preview(preview)
        self.assertTrue(self.wf.approve("Yes, create the Opportunity"))
        created = self.wf.execute_create(initiative="sdr")
        self.assertTrue(created["full_success"])
        sdr_opp_id = created["opp_id"]
        self.assertIn(sdr_opp_id, self.sf.opportunities)

        creates_after_mtg001 = list(self.sf.create_calls)
        updates_after_mtg001 = list(self.sf.update_calls)
        self.assertGreaterEqual(
            sum(1 for c in creates_after_mtg001 if c["sobject-name"] == "Opportunity"),
            1,
        )

        # CRM now returns the Opp created from MTG-001 (plus distinct AE platform Opp)
        open_after = self.sf.open_opps_by_account[self.ACCOUNT_ID]
        self.assertTrue(any(o["Id"] == sdr_opp_id for o in open_after))
        self.assertTrue(any(o["Id"] == "006OPP001" for o in open_after))

        # --- 2–4) MTG-005: Salesforce shows SDR Opp → EXISTING OPPORTUNITY ---
        mtg005_fp = initiative_fingerprint(
            name=self.mtg_005["title"],
            summary=self.mtg_005["summary"],
            transcript=self.mtg_005["transcript"],
        )
        self.assertTrue(
            same_initiative(mtg001_fp, mtg005_fp),
            "MTG-005 must share use case / scope / buying motion with MTG-001",
        )
        decision = classify_meeting_against_open_opps(mtg005_fp, open_after)
        self.assertEqual(
            decision["outcome"],
            self.existing_variant["expected_outcome"],
        )
        self.assertEqual(decision["outcome"], "EXISTING OPPORTUNITY")
        self.assertEqual(decision["matched_id"], sdr_opp_id)
        self.assertNotEqual(decision["matched_id"], "006OPP001")
        self.assertEqual(
            decision["match_basis"],
            {
                "use_case": "sdr_outbound_contact_data",
                "scope": "sdr_pilot",
                "buying_motion": "sales_budget_pilot",
            },
        )

        # Account/Contact overlap alone must not select OPP-001
        ae_only = classify_meeting_against_open_opps(
            mtg005_fp,
            [o for o in open_after if o["Id"] == "006OPP001"],
        )
        self.assertEqual(ae_only["outcome"], "CREATE")

        # --- 5) No second Opportunity create; no automatic update ---
        # Skill: do not enter write path for EXISTING OPPORTUNITY
        self.assertFalse(self.existing_variant["opportunity_creation_allowed"])
        # Re-check guard also blocks if someone still tries to create after "approval"
        self.wf.show_preview(preview)
        self.wf.approve("yes, create it")
        blocked = self.wf.execute_create(initiative="sdr")
        self.assertEqual(blocked["status"], "blocked_duplicate_opp")
        self.assertEqual(blocked["existing_id"], sdr_opp_id)

        new_creates = self.sf.create_calls[len(creates_after_mtg001) :]
        new_updates = self.sf.update_calls[len(updates_after_mtg001) :]
        self.assertEqual(
            [c for c in new_creates if c["sobject-name"] == "Opportunity"],
            [],
            "No second Opportunity create after MTG-005 EXISTING classification",
        )
        self.assertEqual(
            new_updates,
            [],
            "No automatic Opportunity update on EXISTING OPPORTUNITY path",
        )
        # Still exactly one SDR Opp record
        sdr_opps = [
            o
            for o in self.sf.open_opps_by_account[self.ACCOUNT_ID]
            if o.get("initiative") == "sdr"
            or (o.get("initiative_fp") or {}).get("use_case") == "sdr_outbound_contact_data"
        ]
        self.assertEqual(len(sdr_opps), 1)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
