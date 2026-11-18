# Design constraints: what was not thought of

Things a design missed and a user, a print or a check caught later. Read this list at §0.6,
**before the first geometry**, and answer each line that applies in `calculations.md`.

**Add a line here as soon as something is caught.** The trigger can be a user remark ("there is
nowhere to put the screw head"), a failed print or a FAIL. Add it before the fix, not at the end of
the session. Format: `- **rule** — check: <script/gate or "manual"> — source: <incident id or project, date>`.
If it can become a check, make it one. A line without a check is a reminder; a check is a guarantee.

## Fasteners

- **Every screw head that a part mounted later covers needs a head hole in that part.** Size it as
  head Ø + 0.5 mm, sized from the real head (an M4 pan head is Ø8 × 3.1 mm, so the hole is Ø8.5).
  — check: `fasteners` (head) — source: cnc-valdymo-punktas 2026-11-08, INC-2026-11-08-01
- **No screw, bore or channel crosses another.** Each fastener is a cylinder; two cylinders keep
  ≥ 0.5 mm between them. — check: `fasteners` (crossings) for screws; channels and bores: manual
  — source: INC-2026-08-21-07
- **A straight tool path to the head exists at the moment the screw is driven.** Write down the
  assembly order and which part is already in place. — check: `fasteners` `access_mm` + manual
  order — source: INC-2026-08-22-06
- **A screw into an unthreaded purchased part (DIN rail, sheet metal, extrusion slot) needs a nut
  and a washer.** Model them, and check that the nut and the screw tip clear the neighbours (clips,
  carriers). — check: manual (model the nut as a part, then `collisions`) — source:
  cnc-valdymo-punktas 2026-11-09
- **A hole that must meet a hole in purchased stock uses that stock's real pitch.** A DIN rail has
  slots every 25 mm; anything else is written down as "drill on assembly". — check: manual,
  measured — source: cnc-valdymo-punktas 2026-11-09
- **A joint bore is sized from the mating part, not from the screw that goes through it.**
  — check: `features` `EXPECTED_HOLE` — source: INC-2026-08-22-08
- **On an instanced part, check fastener faces per placed instance.** A post rotated 90° has its
  "outer" face somewhere else. — check: `fasteners` with `instances` — source: cnc-valdymo-punktas
  2026-11-08

- **For every cable leaving the box, ask where it ends before choosing a panel plug.** A cable that runs
  all the way to a far machine gets a cable gland (PG/M), not a connector. Size the gland from the
  cable Ø, and keep the locknut (across corners) clear of rails and its neighbours. — check: manual +
  `assert()` on the nut size — source: cnc-valdymo-punktas 2026-11-13 (GX12/GX16 → PG7/PG9)

- **Before choosing where a new part bolts on, list every hole, screw head and pin already in the
  host face under its footprint.** For each one: reuse it, leave a relief (head Ø + 1 mm), or move the
  part. The new part gets its own fasteners (holes in the part, tapped or nut in the host).
  — check: `fasteners` (head) once declared; manual ray/section per hole — source: Big_CNC Z motor
  mount 2026-11-13, INC-2026-11-13-02
- **A part built outside parts/*.scad (a trimesh/Python script on an imported assembly) still goes
  into fasteners.json and the collision/motion checks.** Otherwise R-22 never sees it. — check:
  `check_fasteners` `mounts` (export to build/positioned/, declare part → host; no screw = FAIL)
  — source: INC-2026-11-13-02

## Joints and retention

- **A hook or clamp mounted in a gap (under glass, behind a panel) needs an insertion path that fits the gap.** Whatever can be slid in through a gap can be lifted out through it, so retention comes from a second part (keeper/jaw bolted on), not from the gap. — check: manual (§0.6 insertion path vs the gap height, `assert()` in params) — source: macbook_pro14_underdesk_holder 2026-11-14 (inverted-U hook could not pass a 13 mm glass gap)
- **A part that slides over or into another needs a locator and a screw.** A locator alone falls
  apart in transport; a screw alone has no alignment. — check: `attachment`, `joint_graph` —
  source: cnc-valdymo-punktas 2026-11-08 (base tenons)
- **Loose plates and shelves are screwed down if the assembly will be carried.** — check: manual
  (an `attachments.json` entry per shelf) — source: cnc-valdymo-punktas 2026-11-08
- **A cut-out must not remove the functional face it serves.** Check the clip pad, the bearing
  shoulder and the seat after every window or slot. — check: probe in `attachments.json` on the
  face + `fit coupon` — source: cnc-valdymo-punktas 2026-11-08 (DIN clip window cut the pad)
- **Neighbouring cut features keep a minimum wall between them**, or they merge into one hole.
  — check: `subfeature_overlap` (fusions.json) — source: INC-2026-08-21-09

- **Every non-purchased part states its material and how it is made (printed / cut from plate / stock profile)
  before its geometry.** Wall thickness, fasteners and supports depend on it; a bracket left as "a box" ends up
  sized for metal and printed. — check: manual (`plan.md` parts table names the route) — source: Big_CNC drag-chain
  brackets 2026-11-18 (user asked whether they were printed)

## Purchased parts

- **Read the datasheet's mounting conditions before choosing a mount**: shielded or non-flush
  sensor and its metal-free zone, allowed shaft radial load, minimum bend radius, clearance and
  service space. Write the numbers in `calculations.md` with the source. — check: manual — source:
  Big_CNC LJ12A3-4 recessed in aluminium 2026-11-13, INC-2026-11-13-03

## Motion

- **Every part added to an assembly with moving axes is swept over the full stroke of every axis
  that moves it or past it, at the moment it is added.** One static pose proves nothing. Re-run the
  sweep whenever a part is added to a moving group. — check: `motion_sweep` / an asserted sweep in
  the build script — source: Big_CNC Z sensor 2026-11-13, INC-2026-11-13-04
- **Moving groups are declared by name, not by a bounding box, and the sweep asserts that every
  newly added part is in the group it should move with.** — check: `motion_sweep` driver `"parts"` + `"static"` (unassigned = FAIL) — source:
  INC-2026-11-13-05
- **A sensor or target that the moving part passes needs a gap the sensor can read and the
  mechanics can keep** (not "1 mm and hope"). Prefer a flush sensor and a target tab. — check:
  sweep min-gap assert + sensing range from the datasheet — source: INC-2026-11-13-04

## Evidence

- **Every hole or feature you claim is shown so the user can see it**: a section or a ray check per
  hole, not only a preview render. OpenSCAD `--preview` of an imported STL hides blind holes.
  — check: ray per hole (open along its axis) + section PNG — source: Big_CNC M6 holes 2026-11-13,
  INC-2026-11-13-06

## Loads

- **A number taken from an earlier revision or from research (belt tension, preload, torque) is
  checked against the limit of the part that carries it** before it goes into the design.
  — check: manual, in `calculations.md` — source: Big_CNC belt tension 2026-11-13, INC-2026-11-13-08

## Printing and fit

- **Print a fit coupon before every long print** (snap clip, tenon, bore). — check: R-14 manual
  — source: INC-2026-08-21-05
- **Every part fits the bed with a margin of ≥ 5 mm per axis.** 250 mm on a 256 mm bed is too
  tight. — check: manual, `EXPECTED_BBOX` vs the printer — source: INC-2026-08-21-06
- **The user's caliper wins over the STL scan.** — check: manual — source: INC-2026-08-22-06

## Propagation

- **Changing a part's outline changes every part that mates with it.** — check:
  `dependencies`, `references/change_propagation.md` — source: INC-2026-08-21-08
- **A cable hole or a gland does not sit under a fan frame, a rail or a clip.** — check: an
  `assert()` in params — source: cnc-valdymo-punktas 2026-11-08 (lid)
- **A part reused from an older design revision gets an inventory of its existing features (keep /
  reuse / plug) before it is changed.** Leftover holes are found by the user otherwise. — check:
  manual list + ray check per plug — source: Big_CNC side plate 2026-11-13, INC-2026-11-13-07
- **Every purchased part on a joint path (rod end, ball cup, pin, spacer) is drawn as a positioned vitamin and
  swept with the part it is screwed to.** A cup left out of the model hid a sealed insert pocket and a binding joint,
  and the corner looked like it floated. — check: nearest-neighbour scan of the assembly (every part touches its
  neighbour) + sweep pair cup vs the part it pivots on; read the connectivity cavity note — source: esp32_rc_modelis
  front_axle_v4 2026-11-18, INC-2026-11-18-01. Now automated: behavior.json + check_behavior.py (gate `behavior`, R-24).
- A mirrored side (left corner, second arm) is posed by its own linkage solution, never by copying the driven side's
  angle: a servo bar turns the two wheels to different angles. — check: behavior.json poses both sides (HOLDS keeps
  every tie-rod cup on its ball at every pose) — source: front_axle_v4 2026-11-18, INC-2026-11-18-03
- A purchased motor/part screwed to a wall sits with its mounting FACE on the wall and its boss/spigot inside the bore;
  a screw into a vitamin (`into: null`) is not bite-checked, so the face position is the only thing that sets the bite.
  — check: behavior.json joint motor <-> wall with max_gap 0.05 — source: rear_axle_v4 2026-11-18, INC-2026-11-18-04
- A heat-set insert hole is NOT the insert's OD: M3 x 5.7 (OD 4.6) needs a 4.0 hole (4.2 in CAD for a printed hole),
  blind depth >= insert length + 1 mm, wall >= 1.6 mm around the OD. Cutting `d=ins_d` (= knurl OD) leaves nothing to grip.
  — check: `strength` gate (check_strength.py, R-25; declare `insert` in fasteners.json) — source: esp32_rc front/rear_axle_v4 2026-11-18, INC-2026-11-18-07
- A ball joint's tilt at full bump/steer must stay within the purchased rod end's swing (RC M3 cups ~±15° ◇, no datasheet value);
  computing the angle (`ub_mis`) is not checking it. — check: `behavior` gate KINEMATICS, joint `angle` {echo, max_deg, source} — source: front_axle_v4 ub_mis 22.8°
