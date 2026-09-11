# SAO AI Browser & Job Application Agent Harness

## Purpose
This harness equips AI agents (Pi, Claude Code, Codex, Agy, JobRaven) with high-speed, filesystem-like browser navigation and an autonomous, token-efficient Job Application Engine.

## Architectural Invariants
1. **Virtual Filesystem over DOM**: DOM elements are mapped to virtual paths (`/form/first_name`, `/form/resume`, `/main/header`), allowing agents to use `fs ls`, `fs cat`, and `fs grep` with tiny JSON payloads (<200 tokens) instead of visual computer-use screenshots (2,000+ tokens).
2. **Strict Human Review Gate (`PROTECTED_COMMAND_WORDS = {"apply", "submit", "send"}`)**:
   The harness deterministically handles navigation, ATS field detection, profile autofill, and resume attachment. It strictly halts before form submission, alerting Nelson to review on-screen and click "Submit".
3. **Transport Agnostic**:
   - `mock`: Deterministic offline execution for automated tests and CI.
   - `local`: Bridges to Nelson's local Windows Chrome companion via native host messaging.
   - `spine`: Bridges to Spine Cloud Chromium on `savv-spine:6092` via shared broker on `6091`.

## Command Catalog

### SAO Browser (`cli-anything-sao-browser`)
- `page open <url>`: Open URL and inspect initial DOM structure.
- `page info`: Get URL, title, transport, and element count.
- `fs ls [path]`: List virtual DOM nodes at path (e.g. `/form`).
- `fs cd <path>`: Change working directory in the DOM tree.
- `fs cat <path>`: Read detailed attributes, values, and labels of an element.
- `fs grep <pattern>`: Search for inputs, buttons, or text matching pattern.
- `act type <path> <text>`: Type into a field.
- `act select <path> <option>`: Select dropdown option.
- `act check <path>`: Toggle checkbox or radio.
- `act upload <path> <file_path>`: Attach a file to an input element.
- `session status`: View active session state.

### Job Application Engine (`cli-anything-job-apply`)
- `job-apply scan [url]`: Detect ATS type (Greenhouse, Lever, Workday, Ashby, BambooHR) and catalog form fields.
- `job-apply fill --profile <path>`: Autofill matching candidate profile fields.
- `job-apply upload-resume <pdf_path>`: Attach resume to file upload input.
- `job-apply audit`: Verify all required fields and flag custom screening questions.
- `job-apply ready-for-review`: Formally pause automation and signal Nelson for human verification and submission.
