"""
apply_dx_responses.py
---------------------
Adds standardized FastAPI error responses and Authorization header examples to your existing route files.

Usage:
  python -m backend.scripts.apply_dx_responses --root backend/routes

What it does, per *.py in --root:
- Ensures imports:
    from core.responses import std_error_responses
    from core.openapi import add_auth_example
- Injects `responses=std_error_responses(),` into every @router.get/post/put/patch/delete decorator if not present.
- Ensures a tiny helper that iterates router.routes and calls add_auth_example(...) so OpenAPI shows an Authorization header example.
- Idempotent: safe to re-run; it won't duplicate inserts.

Back up your repo before mass-editing if you're nervous.
"""
from __future__ import annotations
import argparse, pathlib, re, sys

METHODS = ("get","post","put","patch","delete")


def ensure_imports(text: str) -> str:
    lines = text.splitlines()
    have_resp = any("from core.responses import std_error_responses" in l for l in lines)
    have_auth = any("from core.openapi import add_auth_example" in l for l in lines)
    insert_at = 0
    for i,l in enumerate(lines):
        if l.startswith("from ") or l.startswith("import "):
            insert_at = i+1
    to_add = []
    if not have_resp:
        to_add.append("from core.responses import std_error_responses")
    if not have_auth:
        to_add.append("from core.openapi import add_auth_example")
    if to_add:
        lines[insert_at:insert_at] = to_add
    return "\n".join(lines)


def inject_responses(text: str) -> str:
    # Pattern to find @router.<method>( ... )
    # We'll inject 'responses=std_error_responses(),' after the opening parenthesis if not already present.
    def replacer(match: re.Match) -> str:
        header = match.group(0)
        body = match.group(1)
        # If already has responses=std_error_responses or any responses=, skip
        if re.search(r"\\bresponses\\s*=", body):
            return header
        # Insert as first argument (preserve indentation)
        # Find indentation after '('
        m_indent = re.search(r"\\((\\s*)", header)
        indent = (m_indent.group(1) if m_indent else "") + "    "
        injected = "(" + "\\n" + indent + "responses=std_error_responses(),"  # start a new line after '('
        # Replace first '(' only
        return re.sub(r"\\(", injected, header, count=1)

    pattern = re.compile(
        r"@router\\.(?:%s)\\((?:[^\\)]*?\\n)*?.*?\\)" % "|".join(METHODS),
        re.MULTILINE
    )
    # Use sub with a function; but we need access to inside content, so capture.
    # We'll craft pattern differently capturing the inner part.
    pattern = re.compile(r"@router\\.(?:%s)\\((.*?)\\)" % "|".join(METHODS), re.DOTALL)
    def sub_func(m: re.Match) -> str:
        full = m.group(0)
        inner = m.group(1)
        if re.search(r"\\bresponses\\s*=", inner):
            return full  # unchanged
        # Compute indentation level from the line of the decorator
        # Find whitespace before '@router'
        start = m.start()
        # naive: insert just after '(' with a newline and 4 spaces
        return full.replace("(", "(\n    responses=std_error_responses(),", 1)

    return pattern.sub(sub_func, text)


def ensure_auth_helper(text: str) -> str:
    if "def _attach_auth_examples(" in text:
        return text
    helper = 