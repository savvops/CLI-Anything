"""DOM element interaction actions."""
from typing import Any, Dict
from cli_anything.sao_browser.core.session import Session
from cli_anything.sao_browser.core.fs import normalize_path
from cli_anything.sao_browser.utils.sao_browser_backend import get_backend

def click(session: Session, path: str) -> Dict[str, Any]:
    target_path = normalize_path(session.working_dir, path)
    if target_path not in session.elements:
        return {"error": f"Element not found: {target_path}", "ok": False}
    backend = get_backend(session.transport)
    result = backend.click(target_path, session.elements[target_path])
    return {"ok": True, "action": "click", "path": target_path, "details": result}

def type_text(session: Session, path: str, text: str) -> Dict[str, Any]:
    target_path = normalize_path(session.working_dir, path)
    if target_path not in session.elements:
        return {"error": f"Element not found: {target_path}", "ok": False}
    backend = get_backend(session.transport)
    result = backend.type_text(target_path, text, session.elements[target_path])
    session.elements[target_path]["value"] = text
    return {"ok": True, "action": "type", "path": target_path, "value": text, "details": result}

def select_option(session: Session, path: str, option_value: str) -> Dict[str, Any]:
    target_path = normalize_path(session.working_dir, path)
    if target_path not in session.elements:
        return {"error": f"Element not found: {target_path}", "ok": False}
    backend = get_backend(session.transport)
    result = backend.select_option(target_path, option_value, session.elements[target_path])
    session.elements[target_path]["value"] = option_value
    return {"ok": True, "action": "select", "path": target_path, "value": option_value, "details": result}

def check(session: Session, path: str, checked: bool = True) -> Dict[str, Any]:
    target_path = normalize_path(session.working_dir, path)
    if target_path not in session.elements:
        return {"error": f"Element not found: {target_path}", "ok": False}
    backend = get_backend(session.transport)
    result = backend.check(target_path, checked, session.elements[target_path])
    session.elements[target_path]["checked"] = checked
    session.elements[target_path]["value"] = "checked" if checked else ""
    return {"ok": True, "action": "check", "path": target_path, "checked": checked, "details": result}

def upload_file(session: Session, path: str, file_path: str) -> Dict[str, Any]:
    target_path = normalize_path(session.working_dir, path)
    if target_path not in session.elements:
        return {"error": f"Element not found: {target_path}", "ok": False}
    backend = get_backend(session.transport)
    result = backend.upload_file(target_path, file_path, session.elements[target_path])
    session.elements[target_path]["value"] = file_path
    return {"ok": True, "action": "upload", "path": target_path, "file": file_path, "details": result}
