"""Castaway Covers logo badge — build123d model.

Single-color white PLA+ embossed badge.
- Base plate: 45 x 28 x 2.0 mm, rounded corners 3 mm
- Raised border: 0.5 mm proud, 1.0 mm wide frame
- Logo scene (palm tree + beach chair): raised 0.5 mm, left-center zone
- 'Castaway' text: raised 0.5 mm, right of scene, upper
- 'Covers' text: raised 0.5 mm, right of scene, lower
- 4 sewing holes: 2.0 mm dia, one per corner at 3.5 mm from edges
- No supports needed — flat base goes directly on plate

Material: white PLA+ (Generic PLA @BBL A1M profile)
Printer:  Bambu Lab A1 mini, textured PEI plate side up
"""

from __future__ import annotations
import math
from build123d import (
    Align,
    Axis,
    Circle,
    Cylinder,
    Ellipse,
    FontStyle,
    Plane,
    Pos,
    Rectangle,
    RectangleRounded,
    Rot,
    Text,
    extrude,
    make_face,
)
import build123d as bd

# ── Parameters ───────────────────────────────────────────────────────────────
W        = 45.0   # badge width  (X) mm
D        = 28.0   # badge depth  (Y) mm
H        = 2.0    # base plate thickness mm
REL      = 0.5    # relief proud height mm
CR       = 3.0    # corner radius mm
BORDER_W = 1.0    # border frame width mm

HOLE_D   = 2.0    # sewing hole diameter mm
HOLE_OFF = 3.5    # sewing hole center from each edge mm

# Scene center (palm tree + chair), left-of-center
SCX = -10.0
SCY =   1.0


# ── Helpers ──────────────────────────────────────────────────────────────────

def rect_raised(w, d, x, y, z_base=H, amount=REL):
      """Raise a solid rectangle by `amount` from z_base."""
      profile = make_face(Rectangle(w, d))
      return Pos(x, y, z_base) * extrude(Plane.XY * profile, amount)


def circle_raised(r, x, y, z_base=H, amount=REL):
      profile = make_face(Circle(r))
      return Pos(x, y, z_base) * extrude(Plane.XY * profile, amount)


def ellipse_raised(rx, ry, x, y, angle=0, z_base=H, amount=REL):
      profile = make_face(Ellipse(rx, ry))
      return Pos(x, y, z_base) * Rot(Z=angle) * extrude(Plane.XY * profile, amount)


# ── Base plate ────────────────────────────────────────────────────────────────
plate = extrude(RectangleRounded(W, D, CR), H)

# ── Raised border frame ───────────────────────────────────────────────────────
outer_profile = RectangleRounded(W,               D,               CR)
inner_profile = RectangleRounded(W - 2*BORDER_W,  D - 2*BORDER_W,  max(CR - BORDER_W, 0.5))
border_profile = make_face([outer_profile, inner_profile])
border = extrude(Plane.XY.offset(H) * border_profile, REL)
plate = plate + border

# ── Sewing holes (through-holes, 2 mm dia) ────────────────────────────────────
for sx, sy in [(1,1),(-1,1),(1,-1),(-1,-1)]:
      hx = sx * (W/2 - HOLE_OFF)
      hy = sy * (D/2 - HOLE_OFF)
      hole = Pos(hx, hy, 0) * Cylinder(
          HOLE_D/2, H + REL + 0.2,
          align=(Align.CENTER, Align.CENTER, Align.MIN)
      )
      plate = plate - hole


# ── Palm tree scene ───────────────────────────────────────────────────────────
# Ground bar
plate = plate + rect_raised(15, 0.9, SCX, SCY - 7.5)

# Trunk — three overlapping rects to approximate gentle lean/curve
plate = plate + rect_raised(1.1, 0.9, SCX - 0.9, SCY - 6.5)   # root flare
plate = plate + rect_raised(1.0, 5.5, SCX - 0.4, SCY - 2.0)   # mid shaft
plate = plate + rect_raised(0.8, 2.5, SCX + 0.1, SCY + 1.8)   # upper lean

# Crown & fronds — 5 ellipses radiating from crown tip
CROWN_X = SCX + 0.5
CROWN_Y = SCY + 3.5

fronds = [
      # (semi-major, semi-minor, angle_deg, tip_offset_x, tip_offset_y)
    (3.2, 0.55, -55,  -2.8,  2.0),
      (3.5, 0.55, -25,  -1.5,  3.2),
      (3.8, 0.55,  10,   1.5,  3.6),
      (3.2, 0.55,  48,   2.8,  2.8),
      (2.8, 0.55,  80,   3.2,  1.2),
]
for smaj, smin, angle, dx, dy in fronds:
      plate = plate + ellipse_raised(smaj, smin, CROWN_X + dx, CROWN_Y + dy, angle)

# Coconuts — 2 small circles near crown base
for cx, cy in [(-0.6, 0.3), (0.7, 0.1)]:
      plate = plate + circle_raised(0.85, CROWN_X + cx, CROWN_Y + cy)

# ── Beach chair / lounge silhouette ──────────────────────────────────────────
# Positioned to the left/below the trunk base, facing right
CHAIR_X = SCX - 3.5
CHAIR_Y = SCY - 5.0

# Left leg post
plate = plate + rect_raised(0.7, 3.2, CHAIR_X - 1.5, CHAIR_Y + 0.4)
# Right leg post (shorter — chair angles up)
plate = plate + rect_raised(0.7, 2.2, CHAIR_X + 1.5, CHAIR_Y + 0.9)
# Seat (horizontal sling connecting posts)
plate = plate + rect_raised(3.5, 0.7, CHAIR_X,       CHAIR_Y + 2.1)
# Back rest (angled upward from right post)
plate = plate + rect_raised(0.7, 2.0, CHAIR_X + 1.5, CHAIR_Y + 2.8)
# Foot rest (small tab at bottom of left post)
plate = plate + rect_raised(1.4, 0.6, CHAIR_X - 1.2, CHAIR_Y - 1.1)


# ── Text: "Castaway" ─────────────────────────────────────────────────────────
castaway_profile = Plane.XY.offset(H) * Text(
      "Castaway",
      font_size=4.5,
      font="Arial",
      font_style=FontStyle.BOLD,
      align=(Align.CENTER, Align.CENTER),
)
plate = plate + Pos(12.0, 5.0, 0) * extrude(castaway_profile, REL)

# ── Text: "Covers" ───────────────────────────────────────────────────────────
covers_profile = Plane.XY.offset(H) * Text(
      "Covers",
      font_size=4.5,
      font="Arial",
      font_style=FontStyle.BOLD,
      align=(Align.CENTER, Align.CENTER),
)
plate = plate + Pos(12.0, -0.5, 0) * extrude(covers_profile, REL)


# ── Export symbol (required by bambu export-build123d) ───────────────────────
model = plate
