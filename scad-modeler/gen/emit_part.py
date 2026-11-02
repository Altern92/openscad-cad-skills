#!/usr/bin/env python3
"""gen/emit_part.py — requirements.json -> .scad + deklaracijos (P1 plonas pjūvis).

Naudojimas:
    python3 gen/emit_part.py tests/fixtures/plate_with_holes.json -o out/pwh.scad
    python3 gen/emit_part.py --check tests/fixtures/lid.json
    python3 gen/emit_part.py <json> -o out/x.scad --kit-root /kitas/kit

Exit kodai:
    0  failas sugeneruotas (arba --check praėjo ir nieko nerašė)
    4  blogas įėjimas: schema, trūkstami parametrai, unsupported_kind
    5  ENV_FAIL: nėra jsonschema (žr. pranešimą)

Sutartis su skill'u: sugeneruotas failas turi tik `.scad` kodą ir
`// EXPECTED_*` komentarus (docs/03, AGENTS.md 11). Deklaracijos skaičiuojamos
IŠ TŲ PAČIŲ parametrų, kaip `kit_bbox_<name>()` OpenSCAD'e — dublikatas yra
sąmoningas: Python neturi OpenSCAD vykdyklės, o sutapimą pagauna
`check_dimensions.py` ir `check_topology.py` vartai (AC-29).

Skylų Ø čia NIEKADA nerašomi: generatorius perduoda tik žymėjimą ("M4"),
lentelė gyvena kit/lib.scad (AC-31).
"""
import argparse
import json
import re
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
SCHEMA = os.path.join(HERE, "schema.json")
DEFAULT_KIT = os.path.join(PROJECT, "kit")
# Declared bbox tolerance (mm) -> `// EXPECTED_BBOX_TOL:`; see emit().
BBOX_TOL_MM = 0.01

# --- Registras: ką generatorius moka (P1: 8 moduliai) -----------------------
# "order" — parametrų tvarka išvedime (schema properties tvarka).
# "defaults" — schemos `default` reikšmės (jsonschema jų NETAIKO, todėl
# turime tai daryti patys; kitaip bbox formulei trūktų lip/t/corner_r).
# bbox/through gauna (params, holes) — `holes` yra skylų lentelė, nuskaityta
# IŠ kit/lib.scad (vienintelis šaltinis; generatorius Ø nerašo, AC-31).


def bbox_plate(p, holes):
    return [p["w"], p["d"], p["t"]]


def through_plate(p, holes):
    return 0


def bbox_plate_with_holes(p, holes):
    return [p["w"], p["d"], p["t"]]


def through_plate_with_holes(p, holes):
    return 6 if p.get("pattern") == "corners6" else 4


def bbox_bracket_l(p, holes):
    return [p["w"], p["d"], p["h"]]


def through_bracket_l(p, holes):
    return 2


def bbox_box(p, holes):
    return [p["w"], p["d"], p["h"]]


def through_box(p, holes):
    return 4 if p.get("hole", "") != "" else 0


def bbox_lid(p, holes):
    return [p["w"], p["d"], p["t"] + p["lip"]]


def through_lid(p, holes):
    return 4 if p.get("hole", "") != "" else 0


def bbox_boss(p, holes):
    return [p["d_out"], p["d_out"], p["h"]]


def through_boss(p, holes):
    return 1


def bbox_hole_pattern(p, holes):
    # Plokštė = nx*dx × ny*dy (skylės celių centruose). Žr. kit/hole_pattern.scad
    # pastabą apie 2026-11-01 kontrakto pataisą.
    return [p["nx"] * p["dx"], p["ny"] * p["dy"], p["t"]]


def through_hole_pattern(p, holes):
    return p["nx"] * p["ny"]


def bbox_snap_hook(p, holes):
    return [p["beam_w"], p["beam_t"], p["beam_l"]]


def through_snap_hook(p, holes):
    return 0


KINDS = {
    "plate": {
        "order": ["w", "d", "t", "corner_r", "chamfer"],
        "defaults": {"corner_r": 0, "chamfer": 0},
        "bbox": bbox_plate,
        "through": through_plate,
    },
    "plate_with_holes": {
        "order": ["w", "d", "t", "hole", "inset", "corner_r", "pattern"],
        "defaults": {"corner_r": 0, "pattern": "corners"},
        "bbox": bbox_plate_with_holes,
        "through": through_plate_with_holes,
    },
    "bracket_l": {
        "order": ["w", "d", "h", "t", "hole"],
        "defaults": {},
        "bbox": bbox_bracket_l,
        "through": through_bracket_l,
    },
    "box": {
        "order": ["w", "d", "h", "wall", "floor", "corner_r", "hole", "inset"],
        "defaults": {"wall": 2.4, "floor": 2.4, "corner_r": 0, "hole": "", "inset": 0},
        "bbox": bbox_box,
        "through": through_box,
    },
    "lid": {
        "order": ["w", "d", "t", "lip", "clearance", "wall", "corner_r", "hole", "inset"],
        "defaults": {"t": 3, "lip": 1.8, "clearance": 0.2, "wall": 2.4, "corner_r": 0,
                     "hole": "", "inset": 0},
        "bbox": bbox_lid,
        "through": through_lid,
    },
    "box_with_lid": {
        "order": ["w", "d", "h", "wall", "floor", "corner_r", "lid_t", "lip",
                  "clearance", "hole", "inset"],
        "defaults": {"wall": 2.4, "floor": 2.4, "corner_r": 0, "lid_t": 3,
                     "lip": 1.8, "clearance": 0.2, "hole": "", "inset": 0},
        "composite": True,
    },
    "boss": {
        "order": ["d_out", "d_bore", "h"],
        "defaults": {},
        "bbox": bbox_boss,
        "through": through_boss,
    },
    "hole_pattern": {
        "order": ["nx", "ny", "dx", "dy", "hole", "t"],
        "defaults": {},
        "bbox": bbox_hole_pattern,
        "through": through_hole_pattern,
    },
    "snap_hook": {
        "order": ["beam_l", "beam_w", "beam_t", "hook_h", "undercut"],
        "defaults": {},
        "bbox": bbox_snap_hook,
        "through": through_snap_hook,
    },
}


def load_hole_table(kit_root):
    """Skaito skylų lentelę IŠ kit/lib.scad (vienintelis šaltinis, AC-05/AC-31)."""
    path = os.path.join(kit_root, "lib.scad")
    table = {}
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return table
    for name, mm in re.findall(r'hole\s*==\s*"(M\d)"\s*\?\s*([0-9.]+)', text):
        table[name] = float(mm)
    return table


def hole_d(hole, holes):
    if isinstance(hole, str):
        if hole not in holes:
            raise KeyError(f"skylės žymėjimas {hole!r} nerastas kit/lib.scad lentelėje")
        return holes[hole]
    return float(hole)


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


def fmt_num(x):
    """Stabilus skaičiaus formatas: 80 -> "80", 4.75 -> "4.75", 4.8000 -> "4.8"."""
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, int):
        return str(x)
    if isinstance(x, float):
        r = round(x, 4)
        if r == int(r):
            return str(int(r))
        return f"{r:.4f}".rstrip("0").rstrip(".")
    return str(x)


def fmt_param(v):
    return f'"{v}"' if isinstance(v, str) else fmt_num(v)


def load_schema():
    with open(SCHEMA, encoding="utf-8") as fh:
        return json.load(fh)


def validate(jsonschema, schema, doc, path):
    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    return sorted(
        validator_cls(schema, format_checker=jsonschema.FormatChecker()).iter_errors(doc),
        key=lambda e: list(e.absolute_path),
    )


def missing_required(schema, kind, params):
    kind_def = schema.get("$defs", {}).get(kind, {})
    need = kind_def.get("required", [])
    return [k for k in need if k not in params]


def resolve_params(kind, params):
    spec = KINDS[kind]
    out = {}
    for key in spec["order"]:
        if key in params:
            out[key] = params[key]
        elif key in spec["defaults"]:
            out[key] = spec["defaults"][key]
    return out


def emit(doc, json_path, kit_root):
    kind = doc["kind"]
    spec = KINDS[kind]
    p = resolve_params(kind, doc["params"])
    holes = load_hole_table(kit_root)
    bbox = spec["bbox"](p, holes)
    through = spec["through"](p, holes)

    bbox_txt = ", ".join(fmt_num(v) for v in bbox)
    decls = [
        f"// EXPECTED_BBOX: [{bbox_txt}]",
        # Audit 2026-11-02 §5 #7: the gate's derived bound gives a 180 mm part
        # ~0.22 mm of slack at $fn=64. Every kit extent is a plane or a circle
        # whose vertices land on the axes ($fn=64, 64 % 4 == 0); measured on all
        # 11 fixtures: bbox error 0.00000 mm. The gate only lets this tighten.
        f"// EXPECTED_BBOX_TOL: {fmt_num(BBOX_TOL_MM)}",
        f"// EXPECTED_THROUGH_HOLES: {through}",
    ]
    # boss: docs/03 reikalauja HOLE deklaracijos (matuojama across-flats).
    if kind == "boss":
        decls.append('// EXPECTED_HOLE: [0, 0, 0, "Z", %s]' % fmt_num(p["d_bore"]))
    elif kind == "bracket_l":
        # F1 (auditas docs/13): be šių dviejų eilučių vartai nemato, KURIOJE
        # plokštumoje skylė yra — P5 bug'as (abi skylės horizontaliai) praėjo
        # visus vartus, nes sutapo tik THROUGH_HOLES skaičius.
        hd = hole_d(p["hole"], holes)
        inset = hd / 2 + 2.0  # sutampa su kit/bracket_l.scad wall_min = 2.0
        hole_y = -p["d"] / 2 + inset
        hole_vz = p["h"] - inset
        decls.append('// EXPECTED_HOLE: [0, %s, %s, "Z", %s]' % (
            fmt_num(hole_y), fmt_num(p["t"] / 2), fmt_num(hd)))
        decls.append('// EXPECTED_HOLE: [0, %s, %s, "Y", %s]' % (
            fmt_num(p["d"] / 2 - p["t"] / 2), fmt_num(hole_vz), fmt_num(hd)))
    elif kind == "plate_with_holes":
        hd = hole_d(p["hole"], holes)
        w, d, ins, z = p["w"], p["d"], p["inset"], p["t"] / 2
        pts = [(w / 2 - ins, d / 2 - ins), (-w / 2 + ins, d / 2 - ins),
               (-w / 2 + ins, -d / 2 + ins), (w / 2 - ins, -d / 2 + ins)]
        if p.get("pattern") == "corners6":
            pts += ([(0, d / 2 - ins), (0, -d / 2 + ins)] if w >= d
                    else [(w / 2 - ins, 0), (-w / 2 + ins, 0)])
        for x, y in pts:
            decls.append('// EXPECTED_HOLE: [%s, %s, %s, "Z", %s]' % (
                fmt_num(x), fmt_num(y), fmt_num(z), fmt_num(hd)))
    elif kind == "hole_pattern":
        hd = hole_d(p["hole"], holes)
        nx, ny, dx, dy, z = p["nx"], p["ny"], p["dx"], p["dy"], p["t"] / 2
        w, d = nx * dx, ny * dy
        for i in range(nx):
            for j in range(ny):
                x = -w / 2 + dx / 2 + i * dx
                y = -d / 2 + dy / 2 + j * dy
                decls.append('// EXPECTED_HOLE: [%s, %s, %s, "Z", %s]' % (
                    fmt_num(x), fmt_num(y), fmt_num(z), fmt_num(hd)))
    elif kind == "box" and p.get("hole", "") != "":
        hd = hole_d(p["hole"], holes)
        w, d, ins, z = p["w"], p["d"], p["inset"], p["h"] / 2
        for x, y in [(w / 2 - ins, d / 2 - ins), (-w / 2 + ins, d / 2 - ins),
                     (-w / 2 + ins, -d / 2 + ins), (w / 2 - ins, -d / 2 + ins)]:
            decls.append('// EXPECTED_HOLE: [%s, %s, %s, "Z", %s]' % (
                fmt_num(x), fmt_num(y), fmt_num(z), fmt_num(hd)))
    elif kind == "lid" and p.get("hole", "") != "":
        hd = hole_d(p["hole"], holes)
        w, d, ins, z = p["w"], p["d"], p["inset"], p["lip"] + p["t"] / 2
        for x, y in [(w / 2 - ins, d / 2 - ins), (-w / 2 + ins, d / 2 - ins),
                     (-w / 2 + ins, -d / 2 + ins), (w / 2 - ins, -d / 2 + ins)]:
            decls.append('// EXPECTED_HOLE: [%s, %s, %s, "Z", %s]' % (
                fmt_num(x), fmt_num(y), fmt_num(z), fmt_num(hd)))

    kit = os.path.abspath(kit_root)
    call_items = [
        (k, v) for k, v in p.items()
        if not (kind == "box" and k in ("hole", "inset") and p.get("hole", "") == "" and p.get("inset", 0) == 0)
    ]
    call = ", ".join(f"{k} = {fmt_param(v)}" for k, v in call_items)
    lines = [
        f"// GENERUOTA: gen/emit_part.py iš {json_path}",
        f"// kind: {kind}",
        f"include <{os.path.join(kit, 'lib.scad')}>",
        f"include <{os.path.join(kit, kind + '.scad')}>",
        "",
        *decls,
        "",
        "$fn = 64;",
        f"kit_{kind}({call});",
        "",
    ]
    return "\n".join(lines)


def emit_box_with_lid(doc, json_path, kit_root, out_path=None):
    """Sudėtinis 2 dalių projektas (auditas §5 #2, P5 #8):
    parts/box.scad + parts/lid.scad + assembly.scad + joints.json.
    """
    p = resolve_params("box_with_lid", doc["params"])
    box_params = {k: p[k] for k in ("w", "d", "h", "wall", "floor", "corner_r", "hole", "inset")}
    lid_params = {
        "w": p["w"], "d": p["d"], "t": p["lid_t"], "lip": p["lip"],
        "clearance": p["clearance"], "wall": p["wall"], "corner_r": p["corner_r"],
        "hole": p["hole"], "inset": p["inset"],
    }
    box_scad = emit({"kind": "box", "params": box_params}, json_path, kit_root)
    lid_scad = emit({"kind": "lid", "params": lid_params}, json_path, kit_root)

    kit = os.path.abspath(kit_root)
    box_call = ", ".join(
        f"{k} = {fmt_param(v)}" for k, v in box_params.items()
        if not (k in ("hole", "inset") and box_params["hole"] == "" and box_params["inset"] == 0)
    )
    lid_call = ", ".join(f"{k} = {fmt_param(v)}" for k, v in lid_params.items())
    asm_scad = "\n".join([
        f"// GENERUOTA: gen/emit_part.py iš {json_path}",
        "// kind: box_with_lid (2 dalių surinkimas)",
        f"include <{os.path.join(kit, 'lib.scad')}>",
        f"include <{os.path.join(kit, 'box.scad')}>",
        f"include <{os.path.join(kit, 'lid.scad')}>",
        "",
        "$fn = 64;",
        f"BOX_H = {fmt_num(p['h'])};",
        f"LIP = {fmt_num(p['lip'])};",
        "",
        "module part_box() {",
        f"    kit_box({box_call});",
        "}",
        "module part_lid() {",
        "    translate([0, 0, BOX_H - LIP])",
        f"        kit_lid({lid_call});",
        "}",
        "module full_assembly() { part_box(); part_lid(); }",
        "",
        'MODE = is_undef(MODE) ? "assembly" : MODE;',
        'PART = is_undef(PART) ? "" : PART;',
        "",
        'if (MODE == "assembly") full_assembly();',
        'else if (MODE == "part") {',
        '    if (PART == "box") part_box();',
        '    else if (PART == "lid") part_lid();',
        '    else assert(false, str("KLAIDA: nežinoma dalis \'", PART, "\'"));',
        '} else assert(false, str("KLAIDA: nežinomas MODE \'", MODE, "\'"));',
        "",
    ])
    joints = {
        "contacts": [{
            "pair": ["box", "lid"],
            "joint_type": "touching",
            "expected_interference_mm": [0.0, 0.0],
            "derivation": (
                "dangčio plokštė guli ant dėžutės krašto (ir kampinių statramsčių) "
                f"ties z = {fmt_num(p['h'])} mm; lizdas įeina į ertmę su "
                f"{fmt_num(p['clearance'])} mm tarpu"
            ),
        }]
    }
    if out_path is not None:
        abs_out = os.path.abspath(out_path)
        proj_dir = os.path.dirname(abs_out) if abs_out.endswith(".scad") else abs_out
        parts_dir = os.path.join(proj_dir, "parts")
        os.makedirs(parts_dir, exist_ok=True)
        with open(os.path.join(parts_dir, "box.scad"), "w", encoding="utf-8") as fh:
            fh.write(box_scad)
        with open(os.path.join(parts_dir, "lid.scad"), "w", encoding="utf-8") as fh:
            fh.write(lid_scad)
        asm_path = os.path.join(proj_dir, "assembly.scad")
        with open(asm_path, "w", encoding="utf-8") as fh:
            fh.write(asm_scad)
        if abs_out.endswith(".scad") and abs_out != asm_path:
            with open(abs_out, "w", encoding="utf-8") as fh:
                fh.write(asm_scad)
        with open(os.path.join(proj_dir, "joints.json"), "w", encoding="utf-8") as fh:
            json.dump(joints, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    return asm_scad


def main(argv):
    ap = argparse.ArgumentParser(
        description="requirements.json -> OpenSCAD dalis su deklaracijomis")
    ap.add_argument("json", help="requirements.json failas")
    ap.add_argument("-o", "--output", help="kuria rašyti .scad (privaloma, jei ne --check)")
    ap.add_argument("--kit-root", default=DEFAULT_KIT,
                    help="kit/ katalogas (numatytas: <projektas>/kit)")
    ap.add_argument("--check", action="store_true",
                    help="tik patikrinti įėjimą; nieko nerašyti (AC-33)")
    args = ap.parse_args(argv)

    if not args.check and not args.output:
        ap.error("reikia -o/--output (arba --check)")

    jsonschema = load_jsonschema()
    schema = load_schema()

    try:
        with open(args.json, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"FAIL {args.json}: negalima perskaityti ({exc})", file=sys.stderr)
        return 4

    kind = doc.get("kind")
    if kind == "custom":
        print(
            "unsupported_kind: custom — GenKit generuoja 8 parametrinius modulius ir box_with_lid\n"
            f"  ({args.json})\n"
            "  Ką daryti:\n"
            "   1) krumpliaračiai / vyriai / laisvos formos → BOSL2 (gear, hinges) arba\n"
            "      rankinis .scad su // EXPECTED_* deklaracijomis (docs/03 §custom);\n"
            "   2) dėžutė su dangčiu (ir varžtais) → naudok kind=\"box_with_lid\"; kitiems\n"
            "      sudėtiniams prašymams išskaidyk po vieną (box, lid, plate_with_holes,\n"
            "      bracket_l, boss, hole_pattern, snap_hook);\n"
            "   3) neužpildyti parametrai → įrašyk juos į params (mūsų spartusis kelias\n"
            "      yra sąžininga prielaida `assumptions`, o ne tylus spėjimas).",
            file=sys.stderr)
        return 4
    if kind not in KINDS:
        known = ", ".join(sorted(KINDS))
        print(f"unsupported_kind: {kind} — palaikoma: {known}",
              file=sys.stderr)
        return 4

    errors = validate(jsonschema, schema, doc, args.json)
    if errors:
        miss = missing_required(schema, kind, doc.get("params") or {})
        if miss:
            print(f"missing: {', '.join('params.' + m for m in miss)}", file=sys.stderr)
        for err in errors:
            loc = "/".join(str(x) for x in err.absolute_path) or "<root>"
            print(f"  {loc}: {err.message}", file=sys.stderr)
        return 4

    if KINDS[kind].get("composite"):
        emit_box_with_lid(doc, args.json, args.kit_root,
                          None if args.check else args.output)
        if args.check:
            return 0
        print(f"OK {args.output} (kind={kind}, parts=box+lid)")
        return 0

    text = emit(doc, args.json, args.kit_root)

    if args.check:
        return 0

    out_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(out_dir, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"OK {args.output} (kind={kind})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
