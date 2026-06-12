"""World Cup neighbors v4 build123d model.

Hand-authored against designs/v4/*.yaml (the spec gates) and the ChatGPT v3b
revised design guide. The hard lesson from the v3b attempt: export exactly one
fused solid. Every component overlaps its neighbor by >= 0.3 mm and the scene
is assembled with explicit boolean fuses; engraved cues are real subtractions.

Coordinate frame: Z up, plate at z=0. Viewer (front) looks along +Y, so front
faces point -Y. Figures stand mid-base, goal behind them, ball in front.
"""

from __future__ import annotations

import math

from build123d import (
    Axis,
    Box,
    Circle,
    Cylinder,
    EllipticalCenterArc,
    FontStyle,
    Line,
    Plane,
    Polygon,
    Pos,
    RectangleRounded,
    RegularPolygon,
    Rot,
    Sphere,
    Text,
    extrude,
    fillet,
    make_face,
    revolve,
)

# Numbers cite designs/v4/print_constraints.yaml and people.yaml.
PARAMS = {
    "base": {"x": 125.0, "y": 68.0, "z": 10.0, "corner_r": 10.0, "top_fillet": 2.0},
    "letters": {"size": 9.0, "proud": 1.8},  # base_lettering_proud_mm 1.5-2.0
    "goal": {"post_r": 2.5, "bar": 2.2, "plane_y": 26.0, "half_span": 47.0, "top_z": 50.0},
    "ball": {"r": 8.0, "y": -23.0, "sink": 4.0},
    "dan": {"x": -19.0, "head_w": 19.0, "head_h": 21.0, "torso_w": 17.0, "torso_h": 17.0},
    "carrie": {"x": 19.0, "head_w": 19.5, "head_h": 20.0, "torso_w": 18.5, "torso_h": 15.0},
    "figure_y": -6.0,
}

FONT = "Arial"


def _front(profile, x: float, z: float, y_out: float, depth: float):
    """Extrude a 2D profile from a -Y-facing plane back into the model (+Y).

    y_out is the foremost point of the feature; depth is how far the solid
    runs back, deep enough to stay buried where the host surface curves away.
    """

    plane = Plane(origin=(x, y_out, z), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    return extrude(plane * profile, amount=-depth)


def _capsule(r: float, length: float):
    """Capsule along local +Z from 0 to length: cylinder with sphere caps."""

    return (
        Pos(0, 0, length / 2) * Cylinder(r, length)
        + Sphere(r)
        + Pos(0, 0, length) * Sphere(r)
    )


def _ellipsoid(r_xy: float, r_z: float):
    """Ellipsoid of revolution about Z.

    Build the half profile from an elliptical arc closed by an axis line.
    Trimming a full Ellipse with a boolean leaves a profile that revolves into
    an unorientable STEP export, and non-uniform scale(Sphere) produces BSpline
    pcurves that fail FreeCAD's strict BOP check.
    """

    arc = EllipticalCenterArc((0, 0), r_xy, r_z, start_angle=-90, end_angle=90)
    profile = make_face([arc.edge(), Line(arc @ 1, arc @ 0).edge()])
    return revolve(Plane.XZ * profile, Axis.Z, 360)


def _star(outer_r: float, inner_r: float):
    pts = []
    for i in range(10):
        r = outer_r if i % 2 == 0 else inner_r
        a = math.pi / 2 + i * math.pi / 5
        pts.append((r * math.cos(a), r * math.sin(a)))
    return Polygon(*pts)


def _rounded_block(w: float, d: float, h: float, corner_r: float, top_fillet: float = 0.0):
    block = extrude(RectangleRounded(w, d, corner_r), h)
    if top_fillet:
        top_edges = block.edges().group_by(lambda e: e.center().Z)[-1]
        block = fillet(top_edges, top_fillet)
    return block


def make_base():
    p = PARAMS["base"]
    slab = _rounded_block(p["x"], p["y"], p["z"], p["corner_r"], p["top_fillet"])

    front_y = -p["y"] / 2.0
    proud = PARAMS["letters"]["proud"]
    size = PARAMS["letters"]["size"]
    label_z = p["z"] / 2.0 - 0.4
    text_kw = {"font": FONT, "font_style": FontStyle.BOLD}
    features = [
        _front(Text("DAN", size, **text_kw), -33.0, label_z, front_y - proud, proud + 2.0),
        _front(_star(4.0, 1.6), 0.0, label_z, front_y - proud, proud + 2.0),
        _front(Text("CARRIE", size, **text_kw), 33.0, label_z, front_y - proud, proud + 2.0),
    ]
    return slab + features


def make_goal(base_h: float):
    g = PARAMS["goal"]
    y = g["plane_y"]
    bar = g["bar"]
    top = g["top_z"]
    parts = []
    for x in (-g["half_span"], g["half_span"]):
        parts.append(Pos(x, y, (top + base_h - 1) / 2) * Cylinder(g["post_r"], top - base_h + 1))
    # Crossbar caps the posts.
    parts.append(Pos(0, y, top) * Box(2 * g["half_span"] + 6.0, 5.0, 5.0))
    # Net lattice: vertical bars every 11 mm -> 8.8 mm openings (spec 8-12).
    for x in range(-44, 45, 11):
        parts.append(Pos(float(x), y + 0.6, (top + base_h - 1) / 2) * Box(bar, bar, top - base_h + 1))
    for z in (20.0, 31.5, 43.0):
        parts.append(Pos(0, y + 0.6, z) * Box(2 * g["half_span"], bar, bar))
    return parts


def make_ball(base_h: float):
    """Fused ball with an engraved front pentagon and radial seams.

    The seams never cross each other or the pentagon; crossing engraves
    (e.g. intersecting torus rings) leave self-intersecting faces behind.
    """

    b = PARAMS["ball"]
    cz = base_h + b["r"] - b["sink"]
    center = (0.0, b["y"], cz)
    ball = Pos(*center) * Sphere(b["r"])
    front_y = b["y"] - b["r"]

    grooves = [
        _front(RegularPolygon(3.0, 5) - RegularPolygon(1.9, 5), 0.0, cz, front_y - 0.2, 1.9)
    ]
    # Radial seams, each cut along the local surface normal for uniform depth.
    beta = math.radians(36.0)
    for k in range(5):
        a = math.radians(90 + k * 72)
        u = (math.cos(a), 0.0, math.sin(a))
        n = (math.sin(beta) * u[0], -math.cos(beta), math.sin(beta) * u[2])
        origin = tuple(center[i] + (b["r"] + 0.3) * n[i] for i in range(3))
        plane = Plane(origin=origin, x_dir=(-u[2], 0.0, u[0]), z_dir=n)
        grooves.append(extrude(plane * RectangleRounded(1.2, 2.6, 0.5), amount=-1.6))
    return ball, grooves


def make_person(who: str, base_h: float):
    """One figure, fused into a single part: additions then engraved cues."""

    adds, engraves = _person_parts(who, base_h)
    figure = adds[0] + adds[1:]
    return figure - engraves


def _person_parts(who: str, base_h: float):
    """Return (adds, engraves) solids for one figure."""

    p = PARAMS[who]
    fx, fy = p["x"], PARAMS["figure_y"]
    is_dan = who == "dan"
    outer = -1.0 if is_dan else 1.0  # which side faces away from the other figure

    head_w = p["head_w"]
    head_h = p["head_h"]
    head_r = head_w / 2.0

    leg_r = 3.2 if is_dan else 3.4
    leg_top = base_h + (11.0 if is_dan else 8.5)
    shorts_h = 7.0
    shorts_top = leg_top + shorts_h - 2.0
    torso_w = p["torso_w"]
    torso_d = 12.0 if is_dan else 13.0
    torso_h = p["torso_h"]
    torso_bottom = shorts_top - 2.0
    torso_top = torso_bottom + torso_h
    neck_top = torso_top + 2.5
    head_c = neck_top + head_h / 2.0 - 1.5
    face_y = fy - head_r  # foremost face point

    adds = []
    engraves = []

    # Feet + legs + shorts ---------------------------------------------------
    foot_dx = 4.3
    for dx in (-foot_dx, foot_dx):
        adds.append(Pos(fx + dx, fy - 2.5, base_h - 1.0) * _rounded_block(7.0, 10.0, 3.0, 2.4))
        adds.append(Pos(fx + dx, fy, (leg_top + base_h - 1) / 2) * Cylinder(leg_r, leg_top - base_h + 1))
    adds.append(Pos(fx, fy, leg_top - 1.0) * _rounded_block(torso_w - 1.0, torso_d - 0.5, shorts_h, 3.5))

    # Torso ------------------------------------------------------------------
    adds.append(Pos(fx, fy, torso_bottom) * _rounded_block(torso_w, torso_d, torso_h, 4.0, top_fillet=2.5))
    if not is_dan:
        # Carrie: rounder silhouette - a soft hip band.
        adds.append(Pos(fx, fy, torso_bottom + 2.5) * _rounded_block(torso_w + 2.0, torso_d + 1.0, 5.0, 4.5))

    # Jersey panel + number ----------------------------------------------------
    chest_front = fy - torso_d / 2.0
    panel_c = torso_bottom + torso_h * 0.52
    adds.append(_front(RectangleRounded(11.5, 11.5, 2.5), fx, panel_c, chest_front - 1.2, 3.0))
    number = "10" if is_dan else "9"
    adds.append(
        _front(Text(number, 7.5, font=FONT, font_style=FontStyle.BOLD), fx, panel_c, chest_front - 2.6, 2.0)
    )
    # V-collar cue.
    for sx in (-1, 1):
        adds.append(
            _front(
                Rot(Z=sx * 28) * RectangleRounded(1.6, 5.4, 0.7),
                fx + sx * 2.1,
                torso_top - 2.2,
                chest_front - 1.2,
                3.0,
            )
        )

    # Arms: simple bent cylinders with mitten hands, fused to torso. Keep the
    # shoulder line off the torso top-fillet start plane (torso_top - 2.5) or
    # OCCT leaves a degenerate tangency sliver behind.
    shoulder_z = torso_top - 3.2
    side = torso_w / 2.0 + 0.6
    arm_r = 2.6 if is_dan else 2.7

    def _arm(root_x: float, tilt_deg: float, length: float, downward: bool):
        """Capsule from the shoulder; returns (solids, tip_point)."""

        tilt = math.radians(tilt_deg)
        direction = (math.sin(tilt), 0.0, -math.cos(tilt) if downward else math.cos(tilt))
        root = (root_x, fy, shoulder_z)
        rot = Rot(Y=tilt_deg if not downward else 180.0 - tilt_deg)
        # Local +Z mapped onto `direction` (downward uses the flipped frame).
        solids = [Pos(*root) * rot * _capsule(arm_r, length)]
        tip = tuple(root[i] + direction[i] * length for i in range(3))
        solids.append(Pos(*tip) * Sphere(arm_r + 0.7))  # mitten
        band = tuple(root[i] + direction[i] * 5.0 for i in range(3))
        solids.append(Pos(*band) * rot * Pos(0, 0, 0.0) * Cylinder(arm_r + 0.8, 2.0))
        solids.append(Pos(*root) * Sphere(arm_r + 1.1))  # shoulder cap
        return solids

    # Raised cheering arm on the outer side; hanging arm rests on the hip so
    # the mitten fuses to the shorts instead of ending in a floating dome.
    adds.extend(_arm(fx + outer * side, outer * 35.0, torso_h - 3.0, downward=False))
    adds.extend(_arm(fx - outer * side, -outer * 5.0, torso_h - 2.0, downward=True))

    # Neck + head ----------------------------------------------------------------
    adds.append(Pos(fx, fy, torso_top) * Cylinder(3.7, 6.0))
    adds.append(Pos(fx, fy, head_c) * _ellipsoid(head_r, head_h / 2.0))
    # Jaw and lower-face masses are SPHERES on purpose: an oblate ellipsoid of
    # revolution (r_z < r_xy) exports unorientable STEP geometry from OCCT.
    if is_dan:
        adds.append(Pos(fx, fy + 0.3, head_c - 7.2) * Sphere(6.7))
        # Ears buried well past the head surface; a graze-depth overlap makes
        # OCCT orphan the protruding cap as a separate solid.
        for sx in (-1, 1):
            adds.append(Pos(fx + sx * (head_r - 1.2), fy + 0.5, head_c - 1.4) * Sphere(2.7))
    else:
        # Carrie: soft chubby lower face.
        adds.append(Pos(fx, fy + 0.5, head_c - 6.8) * Sphere(7.3))

    # Hair -------------------------------------------------------------------------
    if is_dan:
        cap = Pos(fx, fy + 0.6, head_c + 0.4) * _ellipsoid(head_r + 1.2, head_r + 1.3)
        clip = Pos(fx, fy, head_c + 1.2) * Rot(X=-12) * Pos(0, 0, 20) * Box(40, 40, 40)
        adds.append(cap & clip)
        # Parallel strand grooves; angled ones converge and pinch off slivers.
        crown = head_c + head_h / 2.0 + 0.6
        for gx in (-5.1, -1.7, 1.7, 5.1):
            engraves.append(Pos(fx + gx, fy + 2.0, crown + 0.9) * Box(1.3, 22.0, 3.0))
    else:
        bob = Pos(fx, fy + 0.8, head_c + 0.2) * _ellipsoid(head_r + 1.7, (head_r + 1.7) * 1.02)
        clip = Pos(fx, fy, head_c - 6.5) * Pos(0, 0, 20) * Box(44, 44, 40)
        bob = bob & clip
        # Open the face window; the bob keeps bangs above the brow.
        bob = bob - Pos(fx, fy - head_r, head_c - 1.5) * Box(15.5, 14.0, 16.0)
        adds.append(bob)
        crown = head_c + head_h / 2.0 + 1.0
        engraves.append(Pos(fx - 2.6, fy + 1.0, crown) * Rot(Z=10) * Box(1.3, 20.0, 3.2))

    # Face: sunglasses ridge + lens pads, brows, nose, cheeks, smile ---------------
    eye_z = head_c + 1.6
    if is_dan:
        # Lens pads overlap the frame band by ~0.2 mm on every side; an exact
        # fit leaves coincident walls that BOP flags as self-intersections.
        frame = RectangleRounded(14.6, 5.6, 2.0) - RectangleRounded(11.8, 3.2, 1.2)
        lens = RectangleRounded(12.2, 3.6, 1.3) - RectangleRounded(1.6, 3.8, 0.6)
        adds.append(_front(frame, fx, eye_z, face_y - 1.45, 7.2))
        adds.append(_front(lens, fx, eye_z, face_y - 0.75, 6.7))
    else:
        ring = (
            Pos(-3.9, 0) * Circle(4.5)
            - Pos(-3.9, 0) * Circle(2.9)
            + Pos(3.9, 0) * Circle(4.5)
            - Pos(3.9, 0) * Circle(2.9)
            + RectangleRounded(3.0, 1.5, 0.6)
        )
        pads = Pos(-3.9, 0) * Circle(3.1) + Pos(3.9, 0) * Circle(3.1)
        adds.append(_front(ring, fx, eye_z, face_y - 1.45, 7.2))
        adds.append(_front(pads, fx, eye_z, face_y - 0.75, 6.7))

    brow_z = eye_z + (3.6 if is_dan else 4.0)
    for sx in (-1, 1):
        adds.append(
            _front(Rot(Z=sx * 8) * RectangleRounded(4.6, 1.6, 0.7), fx + sx * 4.0, brow_z, face_y - 1.3, 6.5)
        )

    nose_z = eye_z - 3.2
    adds.append(Pos(fx, face_y + 0.1, nose_z) * _ellipsoid(1.5, 2.2))

    # Smile: engraved crescent (lune), wide and friendly. Depth tuned to cut
    # ~1.0 mm into the head but stop short of the jaw/lower-face sphere front;
    # cutting past a bulge's foremost point slices an orphan wafer off it.
    smile_z = head_c - head_h * 0.27
    lune = Circle(2.7) - Pos(0, 1.3) * Circle(2.7)
    engraves.append(_front(lune, fx, smile_z, face_y - 2.0, 4.5))

    # Cheek pads kept >=0.6 mm clear of the smile cut. Prism extrusions, not
    # spheres: near-tangent spheres stall the OCCT fuse; a grazing smile cut
    # orphans the pad in the STEP export.
    for sx in (-1, 1):
        adds.append(_front(Circle(1.9), fx + sx * 5.3, smile_z + 1.3, face_y - 0.8, 4.5))

    return adds, engraves


def build_scene():
    base_h = PARAMS["base"]["z"]
    ball, ball_grooves = make_ball(base_h)
    scene = make_base() + (
        make_goal(base_h) + [ball, make_person("dan", base_h), make_person("carrie", base_h)]
    )
    scene = scene - ball_grooves

    solids = scene.solids()
    if len(solids) != 1:
        raise ValueError(f"v4 scene must be one fused solid, got {len(solids)}")
    return scene


model = build_scene()
