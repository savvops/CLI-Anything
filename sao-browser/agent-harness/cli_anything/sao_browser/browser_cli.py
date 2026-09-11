#!/usr/bin/env python3
"""CLI-Anything SAO AI Browser - Agent-Native Filesystem & DOM Interface."""
import sys
import json
import click
from typing import Optional

from cli_anything.sao_browser.core.session import Session
from cli_anything.sao_browser.core import page as page_mod
from cli_anything.sao_browser.core import fs as fs_mod
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

@click.group(invoke_without_command=True)
@click.option("--json", "use_json", is_flag=True, help="Output as JSON")
@click.option("--transport", type=click.Choice(["mock", "local", "spine"]), default="mock", help="Browser transport")
@click.pass_context
def cli(ctx, use_json, transport):
    """CLI-Anything SAO Browser - Filesystem-first browser automation."""
    global _json_output, _session
    _json_output = use_json
    _session = get_session(transport=transport)
    if ctx.invoked_subcommand is None:
        click.echo("SAO Browser REPL mode active. Use --help for command catalog.")

# ── Page Commands ───────────────────────────────────────────────
@cli.group()
def page():
    """Page navigation and lifecycle commands."""
    pass

@page.command("open")
@click.argument("url")
def page_open(url):
    """Open a URL in SAO Browser."""
    sess = get_session()
    result = page_mod.open_page(sess, url)
    output(result, f"Opened {url}")

@page.command("reload")
def page_reload():
    """Reload the current page."""
    sess = get_session()
    result = page_mod.reload_page(sess)
    output(result, "Page reloaded")

@page.command("back")
def page_back():
    """Navigate back."""
    sess = get_session()
    result = page_mod.go_back(sess)
    output(result, "Navigated back")

@page.command("forward")
def page_forward():
    """Navigate forward."""
    sess = get_session()
    result = page_mod.go_forward(sess)
    output(result, "Navigated forward")

@page.command("info")
def page_info():
    """Display current page metadata and detected ATS."""
    sess = get_session()
    result = page_mod.get_page_info(sess)
    output(result)

# ── Filesystem Commands ──────────────────────────────────────────
@cli.group()
def fs():
    """Virtual filesystem commands for DOM Accessibility Tree."""
    pass

@fs.command("ls")
@click.argument("path", default="", required=False)
def fs_ls(path):
    """List DOM elements at virtual path (e.g. / or /form)."""
    sess = get_session()
    result = fs_mod.list_elements(sess, path)
    if _json_output:
        output(result)
    else:
        click.echo(f"Listing {result['cwd']} ({result['count']} entries):")
        click.echo(f"{'TYPE':<12} {'ROLE':<14} {'NAME':<30} {'PATH'}")
        click.echo("─" * 75)
        for e in result["entries"]:
            click.echo(f"{e.get('type', ''):<12} {e.get('role', ''):<14} {str(e.get('name', ''))[:28]:<30} {e.get('path', '')}")

@fs.command("cd")
@click.argument("path")
def fs_cd(path):
    """Change current virtual directory."""
    sess = get_session()
    result = fs_mod.change_directory(sess, path)
    output(result, f"Changed to {sess.working_dir}")

@fs.command("cat")
@click.argument("path", default="", required=False)
def fs_cat(path):
    """Read element details, label, value, and attributes."""
    sess = get_session()
    result = fs_mod.read_element(sess, path)
    output(result)

@fs.command("grep")
@click.argument("pattern")
@click.argument("path", default="", required=False)
def fs_grep(pattern, path):
    """Search for DOM elements matching a pattern."""
    sess = get_session()
    result = fs_mod.grep_elements(sess, pattern, path)
    output(result)

@fs.command("pwd")
def fs_pwd():
    """Print current working virtual directory."""
    sess = get_session()
    click.echo(sess.working_dir)

# ── Action Commands ──────────────────────────────────────────────
@cli.group()
def act():
    """Actions on DOM elements."""
    pass

@act.command("click")
@click.argument("path")
def act_click(path):
    """Click an element."""
    sess = get_session()
    result = act_mod.click(sess, path)
    output(result, f"Clicked {path}")

@act.command("type")
@click.argument("path")
@click.argument("text")
def act_type(path, text):
    """Type text into an input or textarea."""
    sess = get_session()
    result = act_mod.type_text(sess, path, text)
    output(result, f"Typed into {path}")

@act.command("select")
@click.argument("path")
@click.argument("option_value")
def act_select(path, option_value):
    """Select an option in a dropdown."""
    sess = get_session()
    result = act_mod.select_option(sess, path, option_value)
    output(result, f"Selected {option_value} in {path}")

@act.command("check")
@click.argument("path")
@click.option("--unchecked", is_flag=True, help="Uncheck the checkbox/radio")
def act_check(path, unchecked):
    """Check or uncheck a checkbox or radio."""
    sess = get_session()
    result = act_mod.check(sess, path, checked=not unchecked)
    output(result, f"Checked {path}")

@act.command("upload")
@click.argument("path")
@click.argument("file_path")
def act_upload(path, file_path):
    """Upload/attach a file to a file input element."""
    sess = get_session()
    result = act_mod.upload_file(sess, path, file_path)
    output(result, f"Uploaded {file_path} to {path}")

# ── Session Commands ─────────────────────────────────────────────
@cli.group()
def session():
    """Session management commands."""
    pass

@session.command("status")
def session_status():
    """Display session status."""
    sess = get_session()
    output(sess.status())

def main():
    cli()

if __name__ == "__main__":
    main()
