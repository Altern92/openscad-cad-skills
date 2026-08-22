include <../params.scad>
use_param("axle_d", "wheel_hub_bearing_end", "press_fit_MR105_bore5mm");
// BUG (the real incident): no assert here checking axle_d against the
// MR105 bearing's fixed 5mm ID.
