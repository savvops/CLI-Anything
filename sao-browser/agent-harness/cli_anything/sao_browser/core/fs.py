"""Virtual Filesystem navigation over DOM Accessibility Tree."""
import re
from typing import Any, Dict, List, Optional
from cli_anything.sao_browser.core.session import Session

def normalize_path(working_dir: str, path: str) -> str:
    if not path:
        return working_dir
    if path.startswith("/"):
        norm = path
    else:
        norm = f"{working_dir.rstrip('/')}/{path}"
    parts = []
    for segment in norm.split("/"):
        if segment == "" or segment == ".":
            continue
        elif segment == "..":
            if parts:
                parts.pop()
        else:
            parts.append(segment)
    return "/" + "/".join(parts)

def list_elements(session: Session, path: str = "") -> Dict[str, Any]:
    target_dir = normalize_path(session.working_dir, path)
    entries = []
    
    # Collect direct children or matching prefix elements
    seen_containers = set()
    for el_path, el in session.elements.items():
        if el_path == target_dir:
            continue
        if el_path.startswith(target_dir.rstrip("/") + "/") or target_dir == "/":
            rel = el_path[len(target_dir):].lstrip("/")
            parts = rel.split("/")
            if len(parts) > 1:
                container = parts[0]
                if container not in seen_containers:
                    seen_containers.add(container)
                    entries.append({
                        "name": container,
                        "role": "container",
                        "type": "directory",
                        "path": f"{target_dir.rstrip('/')}/{container}"
                    })
            else:
                entries.append({
                    "name": el.get("name") or el.get("label") or parts[0],
                    "role": el.get("role", "element"),
                    "type": el.get("type", "node"),
                    "tag": el.get("tag", ""),
                    "value": el.get("value", ""),
                    "required": el.get("required", False),
                    "path": el_path
                })
                
    return {
        "cwd": target_dir,
        "count": len(entries),
        "entries": sorted(entries, key=lambda x: (x["type"] != "directory", x["name"]))
    }

def change_directory(session: Session, path: str) -> Dict[str, Any]:
    new_dir = normalize_path(session.working_dir, path)
    if new_dir != "/":
        # Verify container exists
        exists = any(p == new_dir or p.startswith(new_dir.rstrip("/") + "/") for p in session.elements.keys())
        if not exists:
            return {"error": f"Directory not found: {new_dir}", "ok": False}
    session.working_dir = new_dir
    return {"ok": True, "cwd": session.working_dir}

def read_element(session: Session, path: str = "") -> Dict[str, Any]:
    target_path = normalize_path(session.working_dir, path)
    if target_path in session.elements:
        return {"ok": True, "element": session.elements[target_path]}
    return {"error": f"Element not found: {target_path}", "ok": False}

def grep_elements(session: Session, pattern: str, path: str = "") -> Dict[str, Any]:
    regex = re.compile(pattern, re.IGNORECASE)
    base_dir = normalize_path(session.working_dir, path)
    matches = []
    
    for el_path, el in session.elements.items():
        if not (el_path.startswith(base_dir.rstrip("/") + "/") or base_dir == "/"):
            continue
        text_to_search = " ".join([
            str(el.get("name", "")),
            str(el.get("label", "")),
            str(el.get("placeholder", "")),
            str(el.get("value", "")),
            str(el.get("tag", "")),
            str(el_path)
        ])
        if regex.search(text_to_search):
            matches.append({
                "path": el_path,
                "role": el.get("role", ""),
                "name": el.get("name") or el.get("label") or "",
                "value": el.get("value", ""),
                "required": el.get("required", False)
            })
            
    return {"pattern": pattern, "count": len(matches), "matches": matches}
