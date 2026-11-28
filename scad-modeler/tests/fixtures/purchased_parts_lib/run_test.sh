#!/usr/bin/env bash
# references/purchased_parts.scad: sourced envelopes render at the published size (MG996R 40.7 x 19.7 x 42.9,
# INJORA 80 mm shock 80 -> 62 mm at full 18 mm travel); an unpublished (◇) dimension has no default, so
# leaving it out, passing it half, or over-travelling the shock is an OpenSCAD assert, never a guess.
set -uo pipefail
lib="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)/references/purchased_parts.scad"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
ext() { python3 -c "import trimesh,sys; m=trimesh.load(sys.argv[1]); print(' '.join(f'{v:.2f}' for v in m.extents))" "$1"; }
render() { local o=$1; shift; openscad -q "$@" -o "$t/$o.stl" "$lib" > "$t/$o.log" 2>&1; }
fail=0
ok() { render "$1" "${@:3}" || { echo "$1: render failed: $(tail -3 "$t/$1.log")"; fail=1; return; }
       e=$(ext "$t/$1.stl"); [ "$e" = "$2" ] || { echo "$1: extents $e, want $2"; fail=1; }; }
bad() { if render "$1" "${@:3}"; then echo "$1: rendered, expected an assert"; fail=1; return; fi
        grep -qF "$2" "$t/$1.log" || { echo "$1: missing '$2': $(tail -3 "$t/$1.log")"; fail=1; }; }
ok mg996r "40.70 19.70 42.90" -D 'PART="mg996r"'
ok mg996r_tabs "54.00 19.70 42.90" -D 'PART="mg996r_tabs"'
ok shock_free "4.00 4.00 80.00" -D 'PART="shock"' -D BD=4
ok shock_full "4.00 4.00 62.00" -D 'PART="shock"' -D BD=4 -D T=18
bad mg996r_half_tabs "tab_span, tab_w, tab_t, tab_z are not published" -D 'PART="mg996r_half_tabs"'
bad shock_no_d "body_d (spring OD) is not published" -D 'PART="shock"'
bad shock_over "outside 0..18" -D 'PART="shock"' -D BD=4 -D T=19
bad rod_end "no published dimensions" -D 'PART="rod_end"'
exit $fail
