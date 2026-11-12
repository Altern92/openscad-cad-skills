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

## Joints and retention

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
