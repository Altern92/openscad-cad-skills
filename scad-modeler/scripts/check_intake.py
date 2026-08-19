#!/usr/bin/env python3
"""Gate for Stage 0 Intake (references/intake_and_analysis.md): proves the
brief was actually turned into a structured, schema-valid requirement spec
before any geometry gets written, and that the "status discipline" the
skill's own docs call "the single biggest source of wrong designs" was
actually followed -- not just stated as a good intention.

Two things are checked, both mandatory once a manifest file exists at all:

1. Schema validity against the OpenSCADDesignSpec schema in
   intake_and_analysis.md (required top-level keys: goal, envelope,
   interfaces, motion, parameters, dependencies).
2. No `parameters[].status == "unknown"` left in the file. "unknown" means
   intake asked a question it never got an answer to -- the doc is explicit
   that unknown values "must be asked back or measured -- never invented",
   so a manifest that still has one is not finished, not a design that's
   merely missing some estimates. `estimated` is fine (that's a resolved,
   named decision to proceed without a measurement) and is only reported,
   not failed, so it can be carried into params.scad and the §8 report as
   "still estimated" per the workflow.

This is a Stage 0 gate, not part of validate_scad.sh's per-part render loop
-- it runs once, before params.scad/parts/ exist, so it is invoked directly:

Usage:
    python3 check_intake.py --manifest design_manifest.json
    python3 check_intake.py --manifest requirements.json

Exit codes:
    0  pass -- schema valid, no unresolved 'unknown' parameters.
    2  no manifest file found at any of the default/given paths (intake
       hasn't produced its output yet -- not necessarily an error this
       early, but nothing downstream should proceed).
    3  fail -- schema invalid, or an unresolved 'unknown' status remains.
    4  usage/runtime error (missing jsonschema, malformed JSON).
"""
import argparse
import json
import sys

EXIT_OK = 0
EXIT_NO_MANIFEST = 2
EXIT_FAIL = 3
EXIT_USAGE = 4

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema",
          file=sys.stderr)
    sys.exit(EXIT_USAGE)

SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "OpenSCADDesignSpec",
    "type": "object",
    "required": ["goal", "envelope", "interfaces", "motion", "parameters", "dependencies"],
    "properties": {
        "goal": {"type": "string"},
        "envelope": {
            "type": "object",
            "properties": {
                "max_bounds_xyz_mm": {"type": "array", "items": {"type": "number"},
                                      "minItems": 3, "maxItems": 3},
                "is_strict": {"type": "boolean"},
            },
            "required": ["max_bounds_xyz_mm", "is_strict"],
        },
        "parameters": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "value", "unit", "status"],
                "properties": {
                    "name": {"type": "string"},
                    "value": {"type": "number"},
                    "unit": {"type": "string", "enum": ["mm", "deg", "rpm", "N"]},
                    "status": {"type": "string", "enum": ["confirmed", "estimated", "unknown"]},
                    "tolerance_mm": {"type": "number"},
                },
            },
        },
        "interfaces": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["mate_type", "mating_part", "clearance_mm"],
                "properties": {
                    "mate_type": {"type": "string",
                                  "enum": ["bore", "boss", "slot", "fastener_clearance", "thread_insert"]},
                    "mating_part": {"type": "string"},
                    "clearance_mm": {"type": "number"},
                },
            },
        },
        "motion": {
            "type": "object",
            "properties": {
                "has_kinematics": {"type": "boolean"},
                "dof_type": {"type": "string",
                             "enum": ["none", "rotational", "linear", "planar", "gear_mesh"]},
                "range": {"type": "array", "items": {"type": "number"}},
                "continuous": {"type": "boolean"},
            },
            "required": ["has_kinematics"],
        },
        "dependencies": {
            "type": "object",
            "additionalProperties": {"type": "array", "items": {"type": "string"}},
        },
    },
}

DEFAULT_PATHS = ["design_manifest.json", "requirements.json"]


def find_manifest(explicit):
    if explicit:
        return explicit
    import os
    for p in DEFAULT_PATHS:
        if os.path.isfile(p):
            return p
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", default=None,
                         help="path to design_manifest.json/requirements.json "
                              "(default: look for design_manifest.json then "
                              "requirements.json in the current directory)")
    args = parser.parse_args()

    path = find_manifest(args.manifest)
    if path is None:
        print("No design_manifest.json or requirements.json found -- Stage 0 "
              "Intake has not produced its output yet. Nothing downstream "
              "should proceed until it does (references/intake_and_analysis.md).",
              file=sys.stderr)
        return EXIT_NO_MANIFEST

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        print(f"ERROR: cannot read/parse {path}: {e}", file=sys.stderr)
        return EXIT_USAGE

    try:
        jsonschema.validate(instance=data, schema=SCHEMA)
    except jsonschema.ValidationError as e:
        path_str = "/".join(str(p) for p in e.absolute_path) or "(root)"
        print(f"FAIL: {path} does not match the OpenSCADDesignSpec schema.")
        print(f"  at {path_str}: {e.message}")
        print("Fix the manifest -- do not weaken the schema to make an "
              "incomplete spec pass.")
        return EXIT_FAIL

    unknowns = [p.get("name", "?") for p in data.get("parameters", [])
                if p.get("status") == "unknown"]
    estimated = [p.get("name", "?") for p in data.get("parameters", [])
                 if p.get("status") == "estimated"]

    if unknowns:
        print(f"FAIL: {len(unknowns)} parameter(s) still 'unknown': {unknowns}")
        print("Ask the user or measure -- intake_and_analysis.md is explicit: "
              "'unknown' must be asked back or measured, never invented. This "
              "is not the same as 'estimated', which is a resolved decision "
              "to proceed without a measurement and is allowed to pass.")
        return EXIT_FAIL

    print(f"OK: {path} is schema-valid, no unresolved 'unknown' parameters.")
    if estimated:
        print(f"  NOTE: {len(estimated)} parameter(s) still 'estimated', "
              f"carry into params.scad as named variables and into the §8 "
              f"report as still estimated: {estimated}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
