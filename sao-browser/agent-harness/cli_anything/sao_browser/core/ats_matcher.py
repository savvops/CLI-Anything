"""Pattern matching and autofill engine for ATS forms (Greenhouse, Lever, Workday, Ashby, BambooHR)."""
import re
from typing import Any, Dict, List, Optional, Tuple

FIELD_PATTERNS = {
    "first_name": [r"first[\s_-]?name", r"given[\s_-]?name", r"fname"],
    "last_name": [r"last[\s_-]?name", r"family[\s_-]?name", r"surname", r"lname"],
    "full_name": [r"^(your\s+)?(full\s+)?name$", r"^name$"],
    "email": [r"email", r"e-mail", r"email[\s_-]?address"],
    "phone": [r"phone", r"telephone", r"mobile", r"contact[\s_-]?number"],
    "location": [r"location", r"city", r"address", r"current[\s_-]?city"],
    "linkedin": [r"linkedin", r"linkedin[\s_-]?(url|profile)?"],
    "github": [r"github", r"github[\s_-]?(url|profile)?"],
    "portfolio": [r"portfolio", r"website", r"personal[\s_-]?(website|url)"],
    "resume": [r"resume", r"cv", r"curriculum[\s_-]?vitae"],
    "cover_letter": [r"cover[\s_-]?letter"],
    "work_authorization": [r"authorized\s+to\s+work", r"legally\s+authorized", r"work\s+auth"],
    "sponsorship": [r"sponsorship", r"require\s+visa", r"require\s+sponsorship"],
    "eeo_gender": [r"gender", r"sex"],
    "eeo_race": [r"race", r"ethnicity"],
    "eeo_veteran": [r"veteran", r"military"],
    "eeo_disability": [r"disability", r"handicap"],
    "salary": [r"salary", r"compensation", r"desired[\s_-]?pay", r"expected[\s_-]?rate"]
}

def detect_ats_type(url: str, elements: Dict[str, Any]) -> str:
    url_lower = url.lower()
    if "greenhouse.io" in url_lower or "grnh.se" in url_lower:
        return "greenhouse"
    if "lever.co" in url_lower:
        return "lever"
    if "myworkdayjobs.com" in url_lower or "workday" in url_lower:
        return "workday"
    if "ashbyhq.com" in url_lower or "ashby" in url_lower:
        return "ashby"
    if "bamboohr.com" in url_lower:
        return "bamboohr"
    return "generic"

def classify_field(el: Dict[str, Any]) -> Optional[str]:
    combined_name = " ".join([
        str(el.get("name", "")),
        str(el.get("label", "")),
        str(el.get("placeholder", "")),
        str(el.get("path", ""))
    ]).lower()
    
    # Check resume file inputs first
    if el.get("type") == "file" or el.get("role") == "file":
        if any(re.search(p, combined_name) for p in FIELD_PATTERNS["cover_letter"]):
            return "cover_letter"
        return "resume"
        
    for field_type, patterns in FIELD_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, combined_name):
                return field_type
                
    return None

def match_and_fill(session, profile: Dict[str, Any]) -> Dict[str, Any]:
    matched_actions = []
    unmatched_fields = []
    
    personal = profile.get("personal", {})
    links = profile.get("links", {})
    work_auth = profile.get("work_authorization", {})
    eeo = profile.get("eeo", {})
    documents = profile.get("documents", {})

    value_map = {
        "first_name": personal.get("first_name", ""),
        "last_name": personal.get("last_name", ""),
        "full_name": f"{personal.get('first_name', '')} {personal.get('last_name', '')}".strip(),
        "email": personal.get("email", ""),
        "phone": personal.get("phone", ""),
        "location": personal.get("location", ""),
        "linkedin": links.get("linkedin", ""),
        "github": links.get("github", ""),
        "portfolio": links.get("portfolio", ""),
        "work_authorization": "Yes" if work_auth.get("authorized_to_work", True) else "No",
        "sponsorship": "No" if not work_auth.get("requires_sponsorship", False) else "Yes",
        "eeo_gender": eeo.get("gender", "Decline to self-identify"),
        "eeo_race": eeo.get("race", "Decline to self-identify"),
        "eeo_veteran": eeo.get("veteran_status", "I am not a protected veteran"),
        "eeo_disability": eeo.get("disability_status", "I do not have a disability"),
        "resume": documents.get("resume_pdf_path", ""),
        "cover_letter": documents.get("cover_letter_pdf_path", "")
    }

    for path, el in session.elements.items():
        # Only target inputs, textareas, selects, and file uploaders
        tag = el.get("tag", "").lower()
        role = el.get("role", "").lower()
        el_type = el.get("type", "").lower()
        
        if tag not in ["input", "select", "textarea"] and role not in ["textbox", "combobox", "checkbox", "radio", "file"]:
            continue
            
        field_type = classify_field(el)
        if field_type and field_type in value_map and value_map[field_type]:
            val = value_map[field_type]
            if el_type == "file" or role == "file":
                action = {"action": "upload", "path": path, "field": field_type, "value": val}
            elif tag == "select" or role == "combobox":
                action = {"action": "select", "path": path, "field": field_type, "value": val}
            elif el_type in ["checkbox", "radio"]:
                action = {"action": "check", "path": path, "field": field_type, "value": True}
            else:
                action = {"action": "type", "path": path, "field": field_type, "value": val}
            matched_actions.append(action)
        else:
            if el.get("required") or el.get("name"):
                unmatched_fields.append({
                    "path": path,
                    "name": el.get("name") or el.get("label") or "",
                    "tag": tag,
                    "role": role,
                    "required": el.get("required", False)
                })

    return {
        "matched_count": len(matched_actions),
        "unmatched_count": len(unmatched_fields),
        "actions": matched_actions,
        "unmatched_fields": unmatched_fields
    }
