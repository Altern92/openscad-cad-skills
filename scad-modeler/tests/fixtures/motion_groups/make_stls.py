# Shared by the motion_groups fixtures: a static rail, a 2-part carriage (plate + block) that
# slides +X as one group, a home sensor either in the carriage path or beside it, and an
# optional cable tray nobody assigned. Built with trimesh, not OpenSCAD (P21: parts made in
# Python scripts must be sweepable too).
import sys, trimesh
out, sensor_in_path, tray = sys.argv[1], sys.argv[2] == "in", len(sys.argv) > 3
def box(lo, hi, name):
    b = trimesh.creation.box(extents=[h - l for l, h in zip(lo, hi)])
    b.apply_translation([(l + h) / 2 for l, h in zip(lo, hi)])
    b.export(f"{out}/{name}.stl")
box([0, 0, 0], [200, 20, 10], "rail")
box([0, 0, 11], [30, 20, 15], "carriage_plate")
box([5, 5, 15], [25, 15, 30], "carriage_block")
box([120, 5, 20], [130, 15, 28], "home_sensor") if sensor_in_path else box([120, 5, 30.8], [130, 15, 40], "home_sensor")
if tray:
    box([0, 30, 0], [200, 40, 5], "cable_tray")
