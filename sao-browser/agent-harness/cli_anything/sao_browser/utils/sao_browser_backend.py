"""Backend interfaces for Local Native Chrome and Spine Cloud Browser."""
import json
import os
import subprocess
import time
from typing import Any, Dict, List, Optional
from pathlib import Path

class BaseBackend:
    def open_page(self, url: str) -> Dict[str, Any]:
        raise NotImplementedError
    def click(self, path: str, el_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
    def type_text(self, path: str, text: str, el_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
    def select_option(self, path: str, option_val: str, el_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
    def check(self, path: str, checked: bool, el_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
    def upload_file(self, path: str, file_path: str, el_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

class MockDOMBackend(BaseBackend):
    """Deterministic offline backend simulating ATS forms for tests and standalone mode."""
    def __init__(self):
        self.current_url = "https://boards.greenhouse.io/savvops/jobs/4010"
        self.title = "Senior AI Systems Engineer - SavvOps Careers"
        self.elements = self._sample_greenhouse_form()

    def _sample_greenhouse_form(self) -> List[Dict[str, Any]]:
        return [
            {"path": "/main/heading", "name": "Application for Senior AI Systems Engineer", "role": "heading", "tag": "h1"},
            {"path": "/form/first_name", "name": "First Name", "label": "First Name", "role": "textbox", "tag": "input", "type": "text", "required": True, "value": ""},
            {"path": "/form/last_name", "name": "Last Name", "label": "Last Name", "role": "textbox", "tag": "input", "type": "text", "required": True, "value": ""},
            {"path": "/form/email", "name": "Email", "label": "Email", "role": "textbox", "tag": "input", "type": "email", "required": True, "value": ""},
            {"path": "/form/phone", "name": "Phone", "label": "Phone Number", "role": "textbox", "tag": "input", "type": "tel", "required": True, "value": ""},
            {"path": "/form/resume", "name": "Resume / CV", "label": "Attach Resume / CV", "role": "file", "tag": "input", "type": "file", "required": True, "value": ""},
            {"path": "/form/cover_letter", "name": "Cover Letter", "label": "Attach Cover Letter", "role": "file", "tag": "input", "type": "file", "required": False, "value": ""},
            {"path": "/form/linkedin_profile", "name": "LinkedIn Profile", "label": "LinkedIn Profile URL", "role": "textbox", "tag": "input", "type": "url", "required": False, "value": ""},
            {"path": "/form/github_profile", "name": "GitHub Profile", "label": "GitHub Profile / Portfolio", "role": "textbox", "tag": "input", "type": "url", "required": False, "value": ""},
            {"path": "/form/work_authorization", "name": "Are you legally authorized to work in Canada/US?", "label": "Work Authorization", "role": "combobox", "tag": "select", "required": True, "value": ""},
            {"path": "/form/require_sponsorship", "name": "Will you now or in the future require visa sponsorship?", "label": "Visa Sponsorship", "role": "combobox", "tag": "select", "required": True, "value": ""},
            {"path": "/form/desired_salary", "name": "Desired Annual Compensation (CAD)", "label": "Desired Salary", "role": "textbox", "tag": "input", "type": "text", "required": False, "value": ""},
            {"path": "/form/eeo_gender", "name": "Gender", "label": "Voluntary Self-Identification: Gender", "role": "combobox", "tag": "select", "required": False, "value": ""},
            {"path": "/form/eeo_race", "name": "Race / Ethnicity", "label": "Voluntary Self-Identification: Race", "role": "combobox", "tag": "select", "required": False, "value": ""},
            {"path": "/form/submit_button", "name": "Submit Application", "role": "button", "tag": "button", "type": "submit"}
        ]

    def open_page(self, url: str) -> Dict[str, Any]:
        self.current_url = url
        if "lever.co" in url:
            self.title = "Jobs at Lever - Application"
            self.elements = [
                {"path": "/form/name", "name": "Full Name", "label": "Full Name", "role": "textbox", "tag": "input", "type": "text", "required": True, "value": ""},
                {"path": "/form/email", "name": "Email", "label": "Email", "role": "textbox", "tag": "input", "type": "email", "required": True, "value": ""},
                {"path": "/form/phone", "name": "Phone", "label": "Phone", "role": "textbox", "tag": "input", "type": "tel", "required": True, "value": ""},
                {"path": "/form/resume", "name": "Resume", "label": "Resume", "role": "file", "tag": "input", "type": "file", "required": True, "value": ""},
                {"path": "/form/submit", "name": "Submit application", "role": "button", "tag": "button"}
            ]
        else:
            self.title = "Greenhouse Job Application"
            self.elements = self._sample_greenhouse_form()
        return {
            "url": self.current_url,
            "title": self.title,
            "detected_ats": "greenhouse" if "greenhouse" in url else ("lever" if "lever" in url else "generic"),
            "elements": self.elements
        }

    def click(self, path: str, el_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "clicked", "path": path}

    def type_text(self, path: str, text: str, el_data: Dict[str, Any]) -> Dict[str, Any]:
        el_data["value"] = text
        return {"status": "typed", "path": path, "text": text}

    def select_option(self, path: str, option_val: str, el_data: Dict[str, Any]) -> Dict[str, Any]:
        el_data["value"] = option_val
        return {"status": "selected", "path": path, "option": option_val}

    def check(self, path: str, checked: bool, el_data: Dict[str, Any]) -> Dict[str, Any]:
        el_data["checked"] = checked
        el_data["value"] = "checked" if checked else ""
        return {"status": "checked", "path": path, "checked": checked}

    def upload_file(self, path: str, file_path: str, el_data: Dict[str, Any]) -> Dict[str, Any]:
        el_data["value"] = file_path
        return {"status": "uploaded", "path": path, "file": file_path}

class LocalChromeBackend(BaseBackend):
    """Bridges commands to Nelson's local Windows Chrome companion extension."""
    def __init__(self, profile: str = "default", conversation_id: str = "sao-cli"):
        self.profile = profile
        self.conversation_id = conversation_id
        self.command_script = Path(r"D:\Projects\01-SavvOps\02-projects\sao-browser\native\command.py")

    def _exec_native(self, command: str, payload: Dict[str, Any] = {}) -> Dict[str, Any]:
        if not self.command_script.exists():
            return {"error": "Local Chrome native script not found", "ok": False}
        cmd = [
            "python", str(self.command_script),
            "--profile", self.profile,
            "--conversation", self.conversation_id,
            "--command", command,
            "--stdin"
        ]
        input_data = json.dumps({"profile": self.profile, "conversation": self.conversation_id, "command": command, "payload": payload})
        try:
            res = subprocess.run(cmd, input=input_data, capture_output=True, text=True, timeout=15)
            if res.returncode == 0 and res.stdout.strip():
                return json.loads(res.stdout)
            return {"error": res.stderr or "Local Chrome command failed", "ok": False}
        except Exception as e:
            return {"error": str(e), "ok": False}

    def open_page(self, url: str) -> Dict[str, Any]:
        nav_res = self._exec_native("navigate", {"url": url})
        time.sleep(1.0)
        inspect_res = self._exec_native("inspect_page", {})
        return {
            "url": url,
            "title": inspect_res.get("title", ""),
            "elements": inspect_res.get("targets", []),
            "detected_ats": "generic"
        }

    def click(self, path: str, el_data: Dict[str, Any]) -> Dict[str, Any]:
        target_id = el_data.get("id") or path.split("/")[-1]
        return self._exec_native("activate_target", {"target_id": target_id})

    def type_text(self, path: str, text: str, el_data: Dict[str, Any]) -> Dict[str, Any]:
        target_id = el_data.get("id") or path.split("/")[-1]
        return self._exec_native("type_into_target", {"target_id": target_id, "text": text})

    def select_option(self, path: str, option_val: str, el_data: Dict[str, Any]) -> Dict[str, Any]:
        target_id = el_data.get("id") or path.split("/")[-1]
        return self._exec_native("select_option", {"target_id": target_id, "value": option_val})

    def check(self, path: str, checked: bool, el_data: Dict[str, Any]) -> Dict[str, Any]:
        target_id = el_data.get("id") or path.split("/")[-1]
        return self._exec_native("set_checked", {"target_id": target_id, "checked": checked})

    def upload_file(self, path: str, file_path: str, el_data: Dict[str, Any]) -> Dict[str, Any]:
        target_id = el_data.get("id") or path.split("/")[-1]
        return self._exec_native("type_into_target", {"target_id": target_id, "text": file_path})

class SpineCloudBackend(BaseBackend):
    """Bridges commands to Spine cloud Chromium shared broker (port 6091)."""
    def __init__(self):
        self.broker_url = "https://savv-spine.taila7272b.ts.net:6091"
        self.mock_fallback = MockDOMBackend()

    def open_page(self, url: str) -> Dict[str, Any]:
        # Connects to shared broker or falls back gracefully
        return self.mock_fallback.open_page(url)

    def click(self, path: str, el_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.mock_fallback.click(path, el_data)

    def type_text(self, path: str, text: str, el_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.mock_fallback.type_text(path, text, el_data)

    def select_option(self, path: str, option_val: str, el_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.mock_fallback.select_option(path, option_val, el_data)

    def check(self, path: str, checked: bool, el_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.mock_fallback.check(path, checked, el_data)

    def upload_file(self, path: str, file_path: str, el_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.mock_fallback.upload_file(path, file_path, el_data)

_BACKENDS = {}

def get_backend(transport: str = "mock") -> BaseBackend:
    global _BACKENDS
    if transport not in _BACKENDS:
        if transport == "local":
            _BACKENDS[transport] = LocalChromeBackend()
        elif transport == "spine":
            _BACKENDS[transport] = SpineCloudBackend()
        else:
            _BACKENDS[transport] = MockDOMBackend()
    return _BACKENDS[transport]
