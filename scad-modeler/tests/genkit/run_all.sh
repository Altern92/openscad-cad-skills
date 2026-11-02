#!/usr/bin/env bash
# tests/run_all.sh — GenKit P2 testai (AC-21…AC-26).
#
#   1) 8 golden fixtures: emit → vartai PASS (0 failed, 0 inconclusive, exit 0)
#   2) 35 mutantai: emit → renderis KRENTA → pranešime yra expected/*.txt tekstas
#
# Biudžetas: < 120 s (AC-26). Rašoma tik į /tmp/genkit_test, kuri pašalinama
# EXIT metu (AC-25).
#
# Aplinka: vartai imami iš $SCAD_GATE, kitu atveju iš kanoninio skill'o kelio.
set -uo pipefail

TESTS="$(cd "$(dirname "$0")" && pwd)"
# Two layouts, one script: the GenKit repo (tests/ next to gen/) and the copy
# inside scad-modeler (scad-modeler/tests/genkit/, gen/ two levels up).
if [ -f "$TESTS/../gen/emit_part.py" ]; then
    ROOT="$(cd "$TESTS/.." && pwd)"
else
    ROOT="$(cd "$TESTS/../.." && pwd)"
fi
# Inside the skill, test against the gates of the same tree (dev or canon).
if [ -z "${SCAD_GATE:-}" ] && [ -f "$ROOT/scripts/validate_scad.sh" ]; then
    SCAD_GATE="$ROOT/scripts/validate_scad.sh"
fi
TMP="$(mktemp -d "${TMPDIR:-/tmp}/genkit_test.XXXXXX")"
GATE="${SCAD_GATE:-$HOME/Skills-plugins-etc/skills/scad-modeler/scripts/validate_scad.sh}"

trap 'rm -rf "$TMP"' EXIT

pass=0; fail=0; failed_names=()

note() { printf '%-24s %s\n' "$1" "$2"; }

if [ ! -x "$GATE" ] && [ ! -f "$GATE" ]; then
    echo "SKIP: scad-modeler vartai nerasti ($GATE) — golden testai praleisti" >&2
    GATE=""
fi

# --- 1. Golden fixtures -----------------------------------------------------
for f in "$TESTS"/fixtures/*.json; do
    name="$(basename "$f" .json)"
    scad="$TMP/$name.scad"
    if ! python3 "$ROOT/gen/emit_part.py" "$f" -o "$scad" >"$TMP/$name.emit" 2>&1; then
        note "FAIL $name" "emit: $(head -1 "$TMP/$name.emit")"
        fail=$((fail + 1)); failed_names+=("$name"); continue
    fi
    if [ -z "$GATE" ]; then
        note "SKIP $name" "vartai neįdiegti"; pass=$((pass + 1)); continue
    fi
    # Vartai `build/` kuria einamajame kataloge — todėl leidžiame iš $TMP,
    # kad projekte neliktų artefaktų (AC-25).
    if ( cd "$TMP" && bash "$GATE" "$scad" ) >"$TMP/$name.gate" 2>&1 \
       && grep -q '^COVERAGE:.* 0 failed, .* 0 inconclusive,' "$TMP/$name.gate"; then
        note "PASS $name" "declarations+dimensions+topology"
        pass=$((pass + 1))
    else
        note "FAIL $name" "$(grep -m1 '^COVERAGE:' "$TMP/$name.gate" || echo 'vartai nepaleido')"
        fail=$((fail + 1)); failed_names+=("$name")
    fi
done

# --- 2. Mutantai ------------------------------------------------------------
shopt -s nullglob
mutants=("$TESTS"/mutants/*)
[ ${#mutants[@]} -eq 0 ] && echo "SKIP: tests/mutants tuščias" >&2
for m in "${mutants[@]}"; do
    base="$(basename "$m")"
    name="${base%%.*}"
    exp="$TESTS/expected/$name.txt"
    if [ ! -f "$exp" ]; then
        note "FAIL $name" "nėra tests/expected/$name.txt"
        fail=$((fail + 1)); failed_names+=("$name"); continue
    fi

    case "$m" in
        *.json)
            scad="$TMP/m_$name.scad"
            if ! python3 "$ROOT/gen/emit_part.py" "$m" -o "$scad" >"$TMP/m_$name.emit" 2>&1; then
                note "FAIL $name" "emit: $(head -1 "$TMP/m_$name.emit")"
                fail=$((fail + 1)); failed_names+=("$name"); continue
            fi
            ;;
        *.scad)
            scad="$m"
            ;;
        *) continue ;;
    esac

    out="$TMP/m_$name.out"
    if openscad -o "$TMP/m_$name.stl" "$scad" >"$out" 2>&1; then
        note "FAIL $name" "renderis PRAĖJO — mutantas neturi praeiti"
        fail=$((fail + 1)); failed_names+=("$name"); continue
    fi
    if grep -qF -- "$(cat "$exp")" "$out"; then
        note "PASS $name" "$(head -c 60 "$exp")…"
        pass=$((pass + 1))
    else
        note "FAIL $name" "laukto pranešimo nėra: $(head -c 70 "$exp")"
        fail=$((fail + 1)); failed_names+=("$name")
    fi
done

# --- 3. Assembly: box + lid (--all, S-6 coplanar) ---------------------------
if [ -n "$GATE" ]; then
    ASM="$TMP/asm"
    mkdir -p "$ASM/parts"
    ok=1
    python3 "$ROOT/gen/emit_part.py" "$TESTS/fixtures/box.json" -o "$ASM/parts/box.scad" >/dev/null 2>&1 || ok=0
    python3 "$ROOT/gen/emit_part.py" "$TESTS/fixtures/lid.json" -o "$ASM/parts/lid.scad" >/dev/null 2>&1 || ok=0
    cat > "$ASM/assembly.scad" <<EOF
// assembly: box + lid (S-6 coplanar scenarijus) — MODE/PART saugomi
include <$ROOT/kit/lib.scad>
include <$ROOT/kit/box.scad>
include <$ROOT/kit/lid.scad>

\$fn = 64;
BOX_H = 40; LIP = 1.8;

module part_box() {
    kit_box(w = 120, d = 80, h = BOX_H, wall = 2.4, floor = 2.4, corner_r = 6);
}
module part_lid() {
    translate([0, 0, BOX_H - LIP])
        kit_lid(w = 120, d = 80, t = 3, lip = LIP, clearance = 0.2, wall = 2.4, corner_r = 6);
}
module full_assembly() { part_box(); part_lid(); }

MODE = is_undef(MODE) ? "assembly" : MODE;
PART = is_undef(PART) ? "" : PART;

if (MODE == "assembly") full_assembly();
else if (MODE == "part") {
    if (PART == "box") part_box();
    else if (PART == "lid") part_lid();
    else assert(false, str("KLAIDA: nežinoma dalis '", PART, "'"));
} else assert(false, str("KLAIDA: nežinomas MODE '", MODE, "'"));
EOF
    printf '%s\n' '{"contacts": [{"pair": ["box", "lid"], "joint_type": "touching", "expected_interference_mm": [0.0, 0.0], "derivation": "dangčio plokštė guli ant dėžutės krašto tame pačiame Z; lizdas įeina į ertmę su 0.2 mm tarpu"}]}' > "$ASM/joints.json"
    if [ "$ok" -eq 1 ] && ( cd "$ASM" && bash "$GATE" --all ) >"$TMP/asm.gate" 2>&1 \
       && grep -q '^COVERAGE:.* 0 failed, .* 0 inconclusive,' "$TMP/asm.gate"; then
        note "PASS asm_box_lid" "$(grep -m1 'CHECK_RESULT collisions=' "$TMP/asm.gate")"
        pass=$((pass + 1))
    else
        note "FAIL asm_box_lid" "$(grep -m1 -E '^COVERAGE:|DECLARED INTERFERENCE|render failed' "$TMP/asm.gate" || echo 'assembly nepaleido')"
        fail=$((fail + 1)); failed_names+=("asm_box_lid")
    fi

    # Sudėtinis generatorius (kind=box_with_lid, P5 #8: 100x60x40 + 4 M4 varžtai)
    BWL="$TMP/bwl"
    mkdir -p "$BWL"
    cat > "$BWL/req.json" <<'EOF'
{
  "version": 1,
  "kind": "box_with_lid",
  "params": {"w": 100, "d": 60, "h": 40, "corner_r": 4, "hole": "M4", "inset": 8},
  "assumptions": ["M4 varžtai kampuose, inset 8 mm, corner_r 4 mm"],
  "source": {"brief": "Dėžutė 100×60×40 su dangčiu ir 4 varžtais kampuose.", "date": "2026-11-02"}
}
EOF
    if python3 "$ROOT/gen/emit_part.py" "$BWL/req.json" -o "$BWL/assembly.scad" >"$BWL/emit.log" 2>&1 \
       && ( cd "$BWL" && bash "$GATE" --all ) >"$BWL/gate.log" 2>&1 \
       && grep -q '^COVERAGE:.* 0 failed, .* 0 inconclusive,' "$BWL/gate.log"; then
        note "PASS asm_box_with_lid" "$(grep -m1 'CHECK_RESULT collisions=' "$BWL/gate.log")"
        pass=$((pass + 1))
    else
        note "FAIL asm_box_with_lid" "$(grep -m1 -E '^COVERAGE:|DECLARED INTERFERENCE|render failed' "$BWL/gate.log" || head -1 "$BWL/emit.log")"
        fail=$((fail + 1)); failed_names+=("asm_box_with_lid")
    fi
fi

# --- 4. Vartų mutantai (renderis PASS, vartai FAIL) --------------------------
# F1 regresija (docs/13): jei kas nors vėl padarys abi bracket_l skyles
# horizontalias, THROUGH_HOLES ir BBOX sutaps ir vartai praeitų — todėl
# tikriname, kad EXPECTED_HOLE deklaracija (ašis Y) tai pagautų.
if [ -n "$GATE" ] && [ -f "$ROOT/kit/bracket_l.scad" ]; then
    KB="$TMP/kit_bug"
    rm -rf "$KB"; cp -R "$ROOT/kit" "$KB"
    python3 - "$KB/bracket_l.scad" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
old = """        // Vertikali lentyna: kiaurymė per Y.
        translate([0, d / 2 - t - 1, hole_vz])
            rotate([-90, 0, 0])
                cylinder(h = t + 2, d = hole_d, $fn = 64);"""
new = """        // BUG REPRO: antra skylė taip pat horizontali.
        translate([0, hole_vz / 2, -1])
            cylinder(h = t + 2, d = hole_d, $fn = 64);"""
if old not in s:
    sys.exit("mutacijos taikinys nerastas")
open(p, "w", encoding="utf-8").write(s.replace(old, new))
PYEOF
    mkdir -p "$TMP/gm"
    if python3 "$ROOT/gen/emit_part.py" "$TESTS/fixtures/bracket_l.json" \
           -o "$TMP/gm/br_bug.scad" --kit-root "$KB" >/dev/null 2>&1 \
       && ( cd "$TMP/gm" && bash "$GATE" br_bug.scad ) >"$TMP/gm/out" 2>&1; then
        note "FAIL gm_br_orientation" "vartai praėjo, nors antra skylė ne Y ašyje"
        fail=$((fail + 1)); failed_names+=("gm_br_orientation")
    elif grep -q '^CHECK_RESULT features=FAIL' "$TMP/gm/out"; then
        note "PASS gm_br_orientation" "features=FAIL (Y ašies skylė nerasta)"
        pass=$((pass + 1))
    else
        note "FAIL gm_br_orientation" "$(grep -m1 -E 'CHECK_RESULT|COVERAGE' "$TMP/gm/out" || echo 'vartai nepaleido')"
        fail=$((fail + 1)); failed_names+=("gm_br_orientation")
    fi
fi

# --- 5. Gate mutant: a 0.1 mm slip must not hide in the bbox tolerance ------
# Audit 2026-11-02 §5 #7: at $fn=64 the derived bound for 120 mm is 0.144 mm.
# The generator now writes `// EXPECTED_BBOX_TOL: 0.01`, so w = 119.9 with the
# declarations kept must give dimensions=FAIL.
if [ -n "$GATE" ]; then
    mkdir -p "$TMP/gt"
    python3 "$ROOT/gen/emit_part.py" "$TESTS/fixtures/plate.json" -o "$TMP/gt/plate.scad" >/dev/null 2>&1
    if ! grep -q '^kit_plate(w = 120,' "$TMP/gt/plate.scad"; then
        note "FAIL gm_bbox_tight" "mutacijos taikinys nerastas (kit_plate(w = 120, ...)"
        fail=$((fail + 1)); failed_names+=("gm_bbox_tight")
    else
        sed -i '' -e 's/^kit_plate(w = 120,/kit_plate(w = 119.9,/' "$TMP/gt/plate.scad" 2>/dev/null \
            || sed -i -e 's/^kit_plate(w = 120,/kit_plate(w = 119.9,/' "$TMP/gt/plate.scad"
        ( cd "$TMP/gt" && bash "$GATE" plate.scad ) >"$TMP/gt/out" 2>&1
        if grep -q '^CHECK_RESULT dimensions=FAIL' "$TMP/gt/out"; then
            note "PASS gm_bbox_tight" "dimensions=FAIL (0.1 mm per 120 mm)"
            pass=$((pass + 1))
        else
            note "FAIL gm_bbox_tight" "$(grep -m1 -E 'CHECK_RESULT dimensions|COVERAGE' "$TMP/gt/out" || echo 'vartai nepaleido')"
            fail=$((fail + 1)); failed_names+=("gm_bbox_tight")
        fi
    fi
fi

echo "----------------------------------------------------------------"
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ] || { printf '  %s\n' "${failed_names[@]}"; exit 1; }
exit 0
