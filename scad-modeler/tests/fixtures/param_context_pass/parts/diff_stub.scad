include <../params.scad>
use_param("axle_d", "diff_stub_end", "photo_measured_~5mm");
assert(axle_d > 4, "diff stub too thin");
