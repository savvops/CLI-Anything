#!/usr/bin/env python3
"""Autonomous Job Application Engine — ATS Scanning, Profile Autofill & Human Review Gate."""
import sys
import json
import click
from pathlib import Path
from typing import Optional

from cli_anything.sao_browser.core.session import Session
from cli_anything.sao_browser.core import page as page_mod
from cli_anything.sao_browser.core import ats_matcher as matcher
from cli_anything.sao_browser.core import audit as audit_mod
from cli_anything.sao_browser.core import actions as act_mod

_session: Optional[Session] = None
_json_output = False

def get_session(transport: str = "mock") -> Session:
    global _session
    if _session is None:
        _session = Session(transport=transport)
    return _session

def output(data, message: str = ""):
    if _json_output:
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        if message:
            click.echo(message)
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, list):
                    click.echo(f"{k}: ({len(v)} items)")
                    for item in v[:10]:
                        click.echo(f"  - {item}")
                else:
                    click.echo(f"{k}: {v}")
        elif isinstance(data, list):
            for item in data[:20]:
                click.echo(f"- {item}")
        else:
            click.echo(str(data))

@click.group()
@click.option("--json", "use_json", is_flag=True, help="Output as JSON")
@click.option("--transport", type=click.Choice(["mock", "local", "spine"]), default="mock", help="Browser transport")
@click.pass_context
def cli(ctx, use_json, transport):
    """Job Application Engine — Autonomous ATS filling with strict human review gate."""
    global _json_output, _session
    _json_output = use_json
    _session = get_session(transport=transport)

@cli.command("scan")
@click.argument("url", required=False)
def scan_job(url):
    """Scan the job posting, detect ATS type, and catalog form fields."""
    sess = get_session()
    if url:
        page_mod.open_page(sess, url)
    if not sess.elements:
        page_mod.open_page(sess, "https://boards.greenhouse.io/savvops/jobs/4010")
    
    detected = matcher.detect_ats_type(sess.current_url, sess.elements)
    sess.detected_ats = detected
    
    fields = []
    for path, el in sess.elements.items():
        tag = el.get("tag", "").lower()
        role = el.get("role", "").lower()
        if tag in ["input", "select", "textarea"] or role in ["textbox", "combobox", "file"]:
            classified = matcher.classify_field(el)
            fields.append({
                "path": path,
                "name": el.get("name") or el.get("label") or "",
                "role": role,
                "type": el.get("type", tag),
                "required": el.get("required", False),
                "matched_field": classified
            })
            
    res = {
        "url": sess.current_url,
        "detected_ats": detected,
        "total_fields": len(fields),
        "required_fields": sum(1 for f in fields if f["required"]),
        "fields": fields
    }
    output(res, f"Scanned ATS form ({detected}): {len(fields)} fields detected.")

@cli.command("fill")
@click.option("--profile", type=click.Path(exists=True), required=True, help="Candidate profile JSON path")
def fill_job(profile):
    """Match form fields against candidate profile and fill inputs deterministically."""
    sess = get_session()
    if not sess.elements:
        page_mod.open_page(sess, "https://boards.greenhouse.io/savvops/jobs/4010")
        
    profile_data = sess.load_profile(profile)
    plan = matcher.match_and_fill(sess, profile_data)
    
    # Execute matched actions
    applied = []
    for act in plan["actions"]:
        action_type = act["action"]
        path = act["path"]
        val = act["value"]
        if action_type == "type":
            act_mod.type_text(sess, path, str(val))
        elif action_type == "select":
            act_mod.select_option(sess, path, str(val))
        elif action_type == "check":
            act_mod.check(sess, path, bool(val))
        elif action_type == "upload":
            act_mod.upload_file(sess, path, str(val))
        applied.append({"action": action_type, "path": path, "field": act["field"]})
        
    res = {
        "ok": True,
        "applied_count": len(applied),
        "applied": applied,
        "unmatched_count": plan["unmatched_count"],
        "unmatched_fields": plan["unmatched_fields"]
    }
    output(res, f"Autofill applied to {len(applied)} fields. {plan['unmatched_count']} unmatched/custom fields remaining.")

@cli.command("upload-resume")
@click.argument("pdf_path", type=click.Path(exists=True))
def upload_resume(pdf_path):
    """Attach a resume PDF to the application file input."""
    sess = get_session()
    resume_target = None
    for path, el in sess.elements.items():
        if matcher.classify_field(el) == "resume" or el.get("type") == "file":
            resume_target = path
            break
            
    if not resume_target:
        res = {"error": "No resume file input field found in active form", "ok": False}
        output(res)
        return
        
    res = act_mod.upload_file(sess, resume_target, pdf_path)
    output(res, f"Attached resume {pdf_path} to {resume_target}")

@cli.command("audit")
def audit_form():
    """Audit form readiness, checking for missing required fields and custom screening prompts."""
    sess = get_session()
    report = audit_mod.audit_application(sess)
    output(report, f"Audit complete: {'READY FOR REVIEW' if report['ok'] else 'INCOMPLETE'}")

@cli.command("ready-for-review")
def review_handshake():
    """Halt automation and signal Nelson to review on-screen and click submit."""
    sess = get_session()
    receipt = audit_mod.ready_for_review(sess)
    output(receipt, "Application filled and verified. Paused on screen for Nelson's review.")

def main():
    cli()

if __name__ == "__main__":
    main()
