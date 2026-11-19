"""Opt-out / declaration markers shared by the gates and check_limits.py (P26 / AC-13).

One definition, so the lock cannot miss a spelling a gate accepts (Fable audit 2026-11-19:
validate_scad.sh accepted `// PREVIEW_FILE` without a colon, the lock required one).
"""
import re

def marker(name, reason=True):
    """`// NAME: <reason>` (reason=True) or `// NAME` with or without a colon/reason."""
    tail = r"[ \t]*:[ \t]*\S" if reason else r"\b"
    return re.compile(r"^[ \t]*//[ \t]*" + name + tail, re.M)

PREVIEW_RE = marker("PREVIEW_FILE", reason=False)   # bare form is honoured by validate_scad.sh
LIBRARY_RE = marker("LIBRARY_FILE")                  # P26 / AC-5: a module library under parts/, renders nothing
NO_JOINT_RE = marker("NO_JOINT")
NO_RETENTION_RE = marker("NO_RETENTION")


def unparsed(path, name, strict):
    """`// NAME ...` lines the checker's strict regex cannot read (P26 / AC-15, Fable audit e8):
    validate_scad.sh greps loosely and runs the checker, the checker parsed nothing and said
    "skipping" with exit 0, so `// EXPECTED_BBOX: [L, W, H]` counted as a measured, passing size."""
    loose = re.compile(r"^\s*//\s*" + name + r"\b")
    with open(path, encoding="utf-8", errors="replace") as f:
        return [l.strip() for l in f if loose.match(l) and not strict.match(l)]
