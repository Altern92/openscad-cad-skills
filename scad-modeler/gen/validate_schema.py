#!/usr/bin/env python3
"""Validate requirements.json against gen/schema.json (AC-02).

Usage:
    python3 gen/validate_schema.py tests/fixtures/*.json
    python3 gen/validate_schema.py --self-check

Exit codes:
    0  visi failai validūs
    4  bent vienas netinkamas (ar naudojimo klaida)
    5  ENV_FAIL: nėra jsonschema (žr. pranešimą)

Kodėl re-exec: sisteminis python3 šiame kompiuteryje neturi jsonschema (audito F6).
Jei importas nepavyksta, bandome $SCAD_PYTHON, tada scad-modeler venv, tada
~/.local/share/scad-modeler/venv --- ir persileidžiame su juo. Taip tas pats
failas veikia ir su `python3`, ir su venv.
"""
import json
import os
import sys

SCHEMA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.json")


def _reexec_with_jsonschema() -> bool:
    if os.environ.get("GENKIT_SCHEMA_REEXEC"):
        return False
    candidates = [
        os.environ.get("SCAD_PYTHON", ""),
        os.path.expanduser("~/.local/share/scad-modeler/venv/bin/python"),
    ]
    for py in candidates:
        if py and os.path.isfile(py) and os.access(py, os.X_OK):
            os.environ["GENKIT_SCHEMA_REEXEC"] = "1"
            os.execv(py, [py, os.path.abspath(__file__)] + sys.argv[1:])
    return False


def load_jsonschema():
    try:
        import jsonschema  # noqa: F401
        return jsonschema
    except ImportError:
        _reexec_with_jsonschema()
        print(
            "ENV_FAIL: jsonschema not installed for this interpreter.\n"
            "  Fix: bash ~/Skills-plugins-etc/skills/scad-modeler/scripts/setup_env.sh\n"
            "  or:  pip install jsonschema",
            file=sys.stderr,
        )
        sys.exit(5)


def main(argv: list[str]) -> int:
    jsonschema = load_jsonschema()

    schema = json.load(open(SCHEMA, encoding="utf-8"))
    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)

    paths = [a for a in argv if not a.startswith("-")]
    if "--self-check" in argv or not paths:
        print(f"OK schema {SCHEMA}")
        return 0

    failures = 0
    for path in paths:
        try:
            doc = json.load(open(path, encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"FAIL {path}: negalima perskaityti ({exc})")
            failures += 1
            continue
        errors = sorted(
            validator_cls(schema, format_checker=jsonschema.FormatChecker()).iter_errors(doc),
            key=lambda e: list(e.absolute_path),
        )
        if not errors:
            print(f"OK   {path}")
            continue
        failures += 1
        print(f"FAIL {path}")
        for err in errors:
            loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
            print(f"       {loc}: {err.message}")

    total = len(paths)
    print(f"\n{total - failures}/{total} OK, {failures} failed")
    return 0 if failures == 0 else 4


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
