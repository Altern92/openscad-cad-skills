#!/usr/bin/env bash
# P38 rest (AC-I3): support volume INFO under flagged overhang regions, exit code unchanged by it.
# Hand-computed: mushroom to the plate ~6283 mm^3, mushroom over a pad ~5027 mm^3 (column stops at the
# part below); a plain cube prints no line.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
P="$SCAD_MODELER_SCRIPTS/check_printability.py"
for n in plate part pass; do "$OPENSCAD" --backend=Manifold --render -o $n.stl $n.scad >/dev/null 2>&1; done
vol() { python3 "$P" --stl $1.stl --min-wall 0 2>&1 | sed -n 's/.*SUPPORT VOLUME: about \([0-9]*\) mm.*/\1/p'; }
a=$(vol plate); b=$(vol part)
python3 "$P" --stl plate.stl --min-wall 0 >/dev/null 2>&1; arc=$?
po=$(python3 "$P" --stl pass.stl --min-wall 0 2>&1); prc=$?
rm -f plate.stl part.stl pass.stl
if [ -n "$a" ] && [ -n "$b" ] && [ "$a" -ge 6000 ] && [ "$a" -le 6500 ] && [ "$b" -ge 4800 ] && [ "$b" -le 5250 ] \
   && [ "$arc" -eq 3 ] && [ "$prc" -eq 0 ] && ! grep -q <<< "$po" "SUPPORT VOLUME"; then exit 0; fi
echo "plate=$a (want ~6283, rc $arc==3) part=$b (want ~5027) pass rc=$prc:"; echo "$po"
exit 1
