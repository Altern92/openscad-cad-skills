include <../params.scad>
use_param("axle_d", "wheel_hub_bearing_end", "press_fit_MR105_bore5mm");
assert(axle_d <= 5, "axle_d must fit through the MR105 bearing's 5mm ID");
