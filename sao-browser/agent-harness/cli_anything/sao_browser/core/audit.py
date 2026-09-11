"""Pre-submission audit and human review gate for Job Applications."""
import re
from typing import Any, Dict, List
from cli_anything.sao_browser.core.session import Session

PROTECTED_COMMAND_WORDS = {"apply", "submit", "send"}

def audit_application(session: Session) -> Dict[str, Any]:
    missing_required = []
    screening_questions = []
    filled_fields = []
    
    salary_relocation_re = re.compile(r"salary|compensation|relocate|notice|commute", re.IGNORECASE)
    
    for path, el in session.elements.items():
        tag = el.get("tag", "").lower()
        role = el.get("role", "").lower()
        if tag not in ["input", "select", "textarea"] and role not in ["textbox", "combobox", "checkbox", "radio", "file"]:
            continue
            
        name = el.get("name") or el.get("label") or ""
        value = str(el.get("value", "")).strip()
        is_required = el.get("required", False)
        
        if is_required and not value:
            missing_required.append({
                "path": path,
                "name": name,
                "role": role
            })
        elif value:
            filled_fields.append({
                "path": path,
                "name": name,
                "value": value[:30] + ("..." if len(value) > 30 else "")
            })
            
        # Detect custom screening questions
        if salary_relocation_re.search(name) or (tag == "textarea" and not value):
            screening_questions.append({
                "path": path,
                "name": name,
                "current_value": value or "(unanswered)",
                "reason": "Salary / Relocation / Prose question requiring operator review"
            })
            
    is_ready = len(missing_required) == 0
    report = {
        "ok": is_ready,
        "ready_for_review": is_ready,
        "filled_count": len(filled_fields),
        "missing_required_count": len(missing_required),
        "screening_count": len(screening_questions),
        "missing_required": missing_required,
        "screening_questions": screening_questions,
        "human_review_gate": "PASSED" if is_ready else "BLOCKED_ON_MISSING_FIELDS",
        "notice": "Autonomous pre-fill complete. Submission halted per SavvOps safety policy. Nelson must review on-screen and click submit."
    }
    session.last_audit = report
    return report

def ready_for_review(session: Session) -> Dict[str, Any]:
    audit = audit_application(session)
    return {
        "status": "AWAITING_HUMAN_SUBMISSION",
        "url": session.current_url,
        "title": session.page_title,
        "audit": audit,
        "instructions": "Open SAO Browser (local Chrome or Spine:6090), verify filled fields, and click Submit."
    }
