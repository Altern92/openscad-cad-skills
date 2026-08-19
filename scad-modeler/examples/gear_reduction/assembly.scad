// MODE switch: "assembly" for a full preview, "part" + PART="<name>" for a
// single part positioned in assembly space (used by validate_scad.sh's
// mechanics auto-trigger to export STLs for collision/motion checks).
include <layout.scad>
use <parts/pinion.scad>
use <parts/spur.scad>

MODE = is_undef(MODE) ? "assembly" : MODE;
PART = is_undef(PART) ? "" : PART;

if (MODE == "assembly") {
    at("pinion") pinion();
    at("spur") spur();
    echo(str("BOM: pinion x1, spur x1, printed, module ", gear_module,
             ", ratio ", ratio, ":1"));
} else if (MODE == "part") {
    if (PART == "pinion") at("pinion") pinion();
    else if (PART == "spur") at("spur") spur();
}
