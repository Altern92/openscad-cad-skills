// Direct reproduction of the real nas_deck_v3 incident (INCIDENTS.md,
// 2026-09-02): a global post_socket_depth exists; a part file re-declares
// it locally, then introduces a NEW, more-specific local variable
// (_deck_socket_depth) for geometry, but the assert still checks the old
// one.
build_volume_max = 300;
module_width = 200;
module_depth = 150;
nas_deck_thickness = 5;
post_socket_d = 4.6;
post_socket_depth = 8.5;
