// The correct version of dimensions_bbox_fail: the declared width parameter
// is the one actually used to build the geometry, so the rendered bbox
// matches "// EXPECTED_BBOX:".

$fa = 2; $fs = 0.3;

// EXPECTED_BBOX: [40, 20, 10]

declared_width = 40;

cube([declared_width, 20, 10]);
