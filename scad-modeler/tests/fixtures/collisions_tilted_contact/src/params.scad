// All dimensions in one place (scad-modeler §2). Frame: see calculations.md.
$fa = 2; $fs = 0.4;

// --- Gridfinity (NopSCADlib printed/gridfinity.scad: pitch 42, width 41.5, z_step 7) ---
gf_units = 3;
gf_w = (gf_units - 1) * 42 + 41.5;  // 125.5 footprint
gf_corner_r = 3.75;                  // NopSCADlib corner_r
base_h = 7;                          // 1 unit, flat top
gf_foot_bottom_half = 41.5 / 2 - (0.8 + 2.15);  // 17.8: foot bottom face half width

// --- Keys ---
key_pitch = 19.05;
key_cols = 6;
key_rows = 5;
mx_cut = 14.0;          // plate cutout (spec 14.0 +/-0.05; tune with the coupon)
mx_lip = 1.5;           // plate thickness where the clips grab
mx_pocket = 15.6;       // underside pocket for the clips
mx_top_housing = 15.6;  // envelope of the switch top above the plate
mx_top_h = 6.6;
mx_body = 14.0;         // bottom housing below the plate top
mx_body_h = 5.0;
mx_pin_h = 3.3;
mx_post_d = 4.0;

// --- Shell ---
tilt = 15;
wall = 3.0;
plate_t = 5.0;
h_front = 16;                         // plate top at the front outer edge, above the base top
slope_len = gf_w / cos(tilt);
key_s0 = (slope_len - key_rows * key_pitch) / 2;   // margin along the slope
inner_half = gf_w / 2 - wall;          // 59.75

// --- M3 joint ---
col_xy = 55;            // corner column / screw position (+/-)
col_d = 9;
insert_d = 4.0;         // PATIKRINTI: insert datasheet hole
insert_len = 5.7;       // PATIKRINTI
insert_hole_depth = 8;
insert_id = 2.5;        // M3 minor diameter (thread inside the insert)
screw_d = 3; screw_len = 8;
screw_head_d = 5.5; screw_head_h = 3.0;
screw_clear_d = 3.4;
cbore_d = 6.0; cbore_h = 3.2;

// --- Locating lip on the base ---
lip_gap = 0.25; lip_t = 1.6; lip_h = 3; lip_half_len = 40;

// --- ESP32 DOIT DevKit V1 (PATIKRINTI all four) ---
esp_l = 51.5; esp_w = 28.5; esp_pcb_t = 1.6;
esp_hdr_below = 8.5;     // header plastic 2.5 + pins 6
esp_row_x = 12.7;        // pin rows at +/-
esp_gap = 0.4;           // cradle clearance per side
esp_back_gap = 0.3;      // board end to the shell's inner back wall
esp_ledge_h = 10;        // board bottom above the base top
esp_y = inner_half - esp_back_gap - esp_l / 2;   // board centre Y
cradle_wall = 2; cradle_bar_half = 9; cradle_bar_len = 4;
usb_cut_w = 13; usb_cut_h = 10;
usb_z = esp_ledge_h + esp_pcb_t + 1.5;   // connector centre above the base top

// --- Relationships the design depends on ---
assert(key_cols * key_pitch <= 2 * inner_half - 2, "keys do not fit between the walls");
assert(key_s0 > 10, "no room along the slope for the corner columns");
// lowest switch pin of the front row, above the base top (shell frame):
_s_front = key_s0 + key_pitch / 2 - mx_body / 2;
_below = mx_body_h + mx_pin_h;
_z_low = h_front + _s_front * sin(tilt) - _below * cos(tilt);
assert(_z_low >= 8, str("wiring room under front row only ", _z_low, " mm"));
// corner column must clear the key area (projected) incl. the switch hanging toward +Y
_y_key_back = -gf_w / 2 + (key_s0 + key_rows * key_pitch) * cos(tilt) + _below * sin(tilt);
assert(col_xy - col_d / 2 > _y_key_back + 1, "corner column hits the back row of switches");
_y_key_front = -gf_w / 2 + key_s0 * cos(tilt);
assert(-col_xy + col_d / 2 < _y_key_front - 1, "corner column hits the front row of switches");
// screw head inside the corner foot bottom face
assert(col_xy + cbore_d / 2 < (gf_w / 2 - 41.5 / 2) + gf_foot_bottom_half, "counterbore leaves the foot");
assert(insert_d > screw_d && insert_id < screw_d, "insert hole must exceed the screw, insert ID below it");
assert(col_d - insert_d >= 4, "column wall around the insert under 2 mm");
_engage = screw_len - (base_h - cbore_h);
assert(_engage <= insert_len && _engage >= 1.2 * screw_d, str("thread engagement ", _engage, " mm outside [3.6, insert_len]"));
assert(esp_w / 2 + esp_gap > esp_row_x + 1.27, "cradle wall would hit the header rows");
assert(cradle_bar_half < esp_row_x - 1.27, "centre bars would hit the header rows");
assert(esp_ledge_h > esp_hdr_below, "header pins would touch the base");
