---
name: cli-anything-sao-browser
description: Agent-native filesystem-first browser automation for SAO Browser. Use to navigate pages, inspect DOM elements with ls/cat/grep, type into fields, select dropdowns, and upload files without taking expensive vision screenshots.
---

# CLI-Anything SAO Browser Skill

Use `cli-anything-sao-browser` to operate Nelson's browser deterministically with minimal token usage.

## Basic Usage
```bash
# Open page and inspect
cli-anything-sao-browser --json page open "https://example.com"

# List form inputs
cli-anything-sao-browser --json fs ls /form

# Read field info
cli-anything-sao-browser --json fs cat /form/email

# Type into field
cli-anything-sao-browser --json act type /form/email "nelson@savvops.com"

# Click button
cli-anything-sao-browser --json act click /form/submit_button
```
