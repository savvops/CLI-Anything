"""Unit and integration tests for SAO Browser & Job Application harness."""
import json
import pytest
from click.testing import CliRunner

from cli_anything.sao_browser.core.session import Session
from cli_anything.sao_browser.core import page as page_mod
from cli_anything.sao_browser.core import fs as fs_mod
from cli_anything.sao_browser.core import actions as act_mod
from cli_anything.sao_browser.core import ats_matcher as matcher
from cli_anything.sao_browser.core import audit as audit_mod
from cli_anything.sao_browser.browser_cli import cli as browser_cli
from cli_anything.sao_browser.job_apply_cli import cli as job_apply_cli

@pytest.fixture
def session():
    sess = Session(transport="mock")
    page_mod.open_page(sess, "https://boards.greenhouse.io/savvops/jobs/4010")
    return sess

@pytest.fixture
def profile():
    return {
        "personal": {
            "first_name": "Nelson",
            "last_name": "Tsavnande",
            "email": "nelson@savvops.com",
            "phone": "+1-204-555-0199",
            "location": "Winnipeg, MB"
        },
        "links": {
            "linkedin": "https://linkedin.com/in/savvops",
            "github": "https://github.com/savvops"
        },
        "work_authorization": {
            "authorized_to_work": True,
            "requires_sponsorship": False
        },
        "documents": {
            "resume_pdf_path": "D:/resumes/nelson_resume.pdf"
        },
        "eeo": {
            "gender": "Decline to self-identify",
            "race": "Decline to self-identify"
        }
    }

def test_fs_navigation(session):
    # Test ls root
    res = fs_mod.list_elements(session, "/")
    assert res["count"] > 0
    assert any(e["name"] == "form" for e in res["entries"])

    # Test cd /form
    cd_res = fs_mod.change_directory(session, "/form")
    assert cd_res["ok"] is True
    assert session.working_dir == "/form"

    # Test ls inside /form
    form_res = fs_mod.list_elements(session, "")
    assert form_res["count"] > 0
    names = [e["name"] for e in form_res["entries"]]
    assert "First Name" in names
    assert "Email" in names

    # Test grep
    grep_res = fs_mod.grep_elements(session, "resume")
    assert grep_res["count"] >= 1
    assert any("resume" in m["path"] for m in grep_res["matches"])

def test_actions(session):
    # Test typing into first_name
    type_res = act_mod.type_text(session, "/form/first_name", "Nelson")
    assert type_res["ok"] is True
    assert session.elements["/form/first_name"]["value"] == "Nelson"

    # Test dropdown selection
    select_res = act_mod.select_option(session, "/form/work_authorization", "Yes")
    assert select_res["ok"] is True
    assert session.elements["/form/work_authorization"]["value"] == "Yes"

    # Test upload
    upload_res = act_mod.upload_file(session, "/form/resume", "D:/test/resume.pdf")
    assert upload_res["ok"] is True
    assert session.elements["/form/resume"]["value"] == "D:/test/resume.pdf"

def test_ats_detection(session):
    ats = matcher.detect_ats_type(session.current_url, session.elements)
    assert ats == "greenhouse"

    lever_ats = matcher.detect_ats_type("https://jobs.lever.co/company/job", {})
    assert lever_ats == "lever"

    workday_ats = matcher.detect_ats_type("https://company.myworkdayjobs.com/en-US/careers", {})
    assert workday_ats == "workday"

def test_ats_autofill_and_audit(session, profile):
    # Match and autofill
    plan = matcher.match_and_fill(session, profile)
    assert plan["matched_count"] >= 6
    
    # Audit before filling required fields -> incomplete
    initial_audit = audit_mod.audit_application(session)
    assert initial_audit["ok"] is False
    assert initial_audit["missing_required_count"] > 0

    # Apply all actions
    for act in plan["actions"]:
        if act["action"] == "type":
            act_mod.type_text(session, act["path"], act["value"])
        elif act["action"] == "select":
            act_mod.select_option(session, act["path"], act["value"])
        elif act["action"] == "upload":
            act_mod.upload_file(session, act["path"], act["value"])

    # Audit after autofill
    audit_after = audit_mod.audit_application(session)
    assert audit_after["ok"] is True
    assert audit_after["missing_required_count"] == 0
    assert audit_after["human_review_gate"] == "PASSED"

    # Human review gate handshake
    handshake = audit_mod.ready_for_review(session)
    assert handshake["status"] == "AWAITING_HUMAN_SUBMISSION"
    assert "Nelson must review" in handshake["audit"]["notice"]

def test_cli_runner():
    runner = CliRunner()
    
    # Test page info via JSON
    res = runner.invoke(browser_cli, ["--json", "page", "open", "https://boards.greenhouse.io/savvops/jobs/4010"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["ok"] is True
    assert data["detected_ats"] == "greenhouse"

    # Test fs ls via JSON
    res_ls = runner.invoke(browser_cli, ["--json", "fs", "ls", "/form"])
    assert res_ls.exit_code == 0
    ls_data = json.loads(res_ls.output)
    assert ls_data["count"] > 0

    # Test job-apply scan
    res_scan = runner.invoke(job_apply_cli, ["--json", "scan"])
    assert res_scan.exit_code == 0
    scan_data = json.loads(res_scan.output)
    assert scan_data["detected_ats"] == "greenhouse"
