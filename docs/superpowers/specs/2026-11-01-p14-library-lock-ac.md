# P14: library version lock (AC)

Date: 2026-11-01. Tier: bounded (extends env_gate.py and validate_scad.sh). Approved in advance by the
user ("darome viska pagal tavo rekomendacijas ir sprendimus").

## Evidence (measured 2026-11-01)
- 76 real parts on SSD_1TB rendered with BOSL2 2.0.782 and 2.0.750: 73 identical (volume, bbox, chi);
  3 differ, all in `esp32_rc_modelis/.../steering_reduction_gearbox` (output_gear, gearbox_frame, jackshaft).
- Cause: 2.0.782 has no `worm_gear_thickness()`; params.scad line 104 gets `undef` with only a WARNING,
  so a plain `openscad` render returns a wrong STL (output_gear genus 0, set-screw hole an enclosed void).
- validate_scad.sh stops (`--hardwarnings`) but says "an assert() in params.scad failed" -- wrong cause.
- env_gate.py checks a library exists, never which version.

## AC
- AC-1: Given a project `libs.lock` line `BOSL2 2.0.750` and an installed BOSL2 whose version.scad says
  `[2,0,750]`, then `CHECK_RESULT env=PASS`.
- AC-2: Given `libs.lock` says `BOSL2 2.0.750` and the first BOSL2 on the library path is `[2,0,1]`,
  then `env=FAIL`, exit 5, and the message names both versions and the installed path.
- AC-3: Given `NopSCADlib tree:<12 hex>` and the installed tree's hash differs, then `env=FAIL`.
- AC-4: Given no `libs.lock`, then behaviour is unchanged (no version check).
- AC-5: `env_gate.py --project-dir . --write-lock` writes one line per library the project includes
  (BOSL2 by version, others by tree hash); running the gate right after gives PASS (AC-1).
- AC-6: `build/.validation_state.json` gains `"libs":{"BOSL2":"2.0.750",...}` for included libraries.
- AC-7: When the params.scad preflight fails on a WARNING (not an assertion), the output says
  "warning under --hardwarnings" and prints the WARNING line, not "an assert() failed".
- AC-8: Suite green in dev and via ~/.claude/skills; steering_reduction_gearbox gets a `libs.lock`.

## Decisions
- Single library root on the mini: `~/Documents/OpenSCAD/libraries` (OpenSCAD's default),
  BOSL2 git clone detached at 92d697c (= 2.0.750, byte-identical to the iCloud copy the projects were
  built with), NopSCADlib copied from iCloud. The iCloud copy stays: it is another Mac's live library.
- Tree hash = sha256 over sorted relative paths + contents of `*.scad`, first 12 hex.
