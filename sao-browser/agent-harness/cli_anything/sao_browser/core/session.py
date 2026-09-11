from pathlib import Path
"""Session state management for SAO Browser harness."""
import json
import os
from typing import Any, Dict, List, Optional

class Session:
    def __init__(self, transport: str = "mock"):
        self.transport = transport
        self.working_dir = "/"
        self.current_url = ""
        self.page_title = ""
        self.history: List[str] = []
        self.history_index: int = -1
        self.detected_ats: str = "generic"
        self.elements: Dict[str, Dict[str, Any]] = {}
        self.last_audit: Optional[Dict[str, Any]] = None
        self.candidate_profile: Optional[Dict[str, Any]] = None

    def status(self) -> Dict[str, Any]:
        return {
            "transport": self.transport,
            "working_dir": self.working_dir,
            "current_url": self.current_url,
            "page_title": self.page_title,
            "detected_ats": self.detected_ats,
            "element_count": len(self.elements),
            "history_length": len(self.history),
            "has_profile": self.candidate_profile is not None
        }

    def set_elements(self, raw_elements: List[Dict[str, Any]]):
        self.elements.clear()
        for el in raw_elements:
            path = el.get("path") or f"/{el.get('id', '')}"
            self.elements[path] = el

    def load_profile(self, profile_path: str) -> Dict[str, Any]:
        p = Path(profile_path)
        if not p.exists():
            raise FileNotFoundError(f"Candidate profile not found: {profile_path}")
        self.candidate_profile = json.loads(p.read_text(encoding="utf-8"))
        return self.candidate_profile
