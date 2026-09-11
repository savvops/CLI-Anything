"""Page lifecycle management for SAO Browser harness."""
from typing import Any, Dict
from cli_anything.sao_browser.core.session import Session
from cli_anything.sao_browser.utils.sao_browser_backend import get_backend

def open_page(session: Session, url: str) -> Dict[str, Any]:
    backend = get_backend(session.transport)
    result = backend.open_page(url)
    session.current_url = url
    session.page_title = result.get("title", "")
    session.working_dir = "/"
    session.history.append(url)
    session.history_index = len(session.history) - 1
    session.set_elements(result.get("elements", []))
    session.detected_ats = result.get("detected_ats", "generic")
    return {
        "ok": True,
        "url": session.current_url,
        "title": session.page_title,
        "detected_ats": session.detected_ats,
        "element_count": len(session.elements)
    }

def reload_page(session: Session) -> Dict[str, Any]:
    if not session.current_url:
        return {"error": "No page open", "ok": False}
    return open_page(session, session.current_url)

def go_back(session: Session) -> Dict[str, Any]:
    if session.history_index > 0:
        session.history_index -= 1
        url = session.history[session.history_index]
        return open_page(session, url)
    return {"error": "No previous page in history", "ok": False}

def go_forward(session: Session) -> Dict[str, Any]:
    if session.history_index < len(session.history) - 1:
        session.history_index += 1
        url = session.history[session.history_index]
        return open_page(session, url)
    return {"error": "No forward page in history", "ok": False}

def get_page_info(session: Session) -> Dict[str, Any]:
    return {
        "url": session.current_url,
        "title": session.page_title,
        "detected_ats": session.detected_ats,
        "transport": session.transport,
        "cwd": session.working_dir,
        "element_count": len(session.elements)
    }
