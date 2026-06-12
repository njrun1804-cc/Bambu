"""World Cup neighbors v4 build123d model.

Hand-authored against designs/v4/*.yaml (the spec gates) and the ChatGPT v3b
sheets; v4.1 retargets the colored rendering: ~49% chibi heads, stubby legs,
arms-down couple pose with Dan's arm around Carrie's back, eyes behind open
glasses, and the ball fused at Dan's foot.

Hard-won OCCT/STEP rules encoded below:
- export exactly one fused solid; compounds of overlapping solids fail review
- every overlap >= 0.3 mm; graze-depth contacts orphan slivers or stall fuses
- ellipsoids must be revolved from arc profiles, and only prolate ones
  (r_z >= r_xy) survive STEP export; oblate masses are spheres instead
- engraves stop short of any bulge's foremost point or they slice off wafers

Coordinate frame: Z up, plate at z=0. Viewer (front) looks along +Y, so front
faces point -Y. Figures stand mid-base, goal behind them, ball front-left.
"""

from __future__ import annotations

import math

from build123d import (
    Axis,
    Box,
    Circle,
    Cylinder,
    Cone,
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
    "goal": {"post_r": 2.5, "bar": 2.2, "plane_y": 26.0, "half_span": 40.0, "top_z": 45.0},
    "ball": {"r": 9.5, "x": -25.5, "y": -16.5, "sink": 4.0},
    "dan": {"x": -11.8, "head_w": 22.0, "head_h": 23.5, "torso_w": 18.0, "torso_h": 13.5},
    "carrie": {"x": 11.8, "head_w": 22.0, "head_h": 22.0, "torso_w": 19.5, "torso_h": 12.0},
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


def _capsule_between(a: tuple, b: tuple, r: float):
    """Capsule between two world points."""

    d = tuple(b[i] - a[i] for i in range(3))
    length = math.sqrt(sum(c * c for c in d))
    polar = math.degrees(math.acos(d[2] / length))
    azimuth = math.degrees(math.atan2(d[1], d[0]))
    return Pos(*a) * Rot(Z=azimuth) * Rot(Y=polar) * _capsule(r, length)


def _ellipsoid(r_xy: float, r_z: float):
    """Prolate ellipsoid of revolution about Z (requires r_z >= r_xy).

    Build the half profile from an elliptical arc closed by an axis line.
    Trimming a full Ellipse with a boolean leaves a profile that revolves into
    an unorientable STEP export; oblate revolves (r_z < r_xy) are unorientable
    too, so squashed masses must be spheres instead.
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
        # Party banner on the base deck, clear of the ball and the figures.
        # 7 mm bold keeps stroke width above the 1.2 mm raised minimum;
        # v001 proved deck text this size prints legibly.
        extrude(
            Plane.XY.offset(p["z"] - 0.5) * Pos(18.0, -18.5) * Text("WORLD CUP 2026", 7.0, **text_kw),
            amount=1.7,
        ),
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
    # Net lattice: vertical bars every 12 mm -> 9.8 mm openings (spec 8-12).
    for x in range(-36, 37, 12):
        parts.append(Pos(float(x), y + 0.6, (top + base_h - 1) / 2) * Box(bar, bar, top - base_h + 1))
    for z in (21.0, 32.0):
        parts.append(Pos(0, y + 0.6, z) * Box(2 * g["half_span"], bar, bar))
    return parts


def make_ball(base_h: float):
    """Ball fused to the base at Dan's foot, with engraved pentagon + seams.

    The seams never cross each other or the pentagon; crossing engraves
    (e.g. intersecting torus rings) leave self-intersecting faces behind.
    """

    b = PARAMS["ball"]
    cz = base_h + b["r"] - b["sink"]
    center = (b["x"], b["y"], cz)
    ball = Pos(*center) * Sphere(b["r"])
    front_y = b["y"] - b["r"]

    grooves = [
        _front(RegularPolygon(3.4, 5) - RegularPolygon(2.2, 5), b["x"], cz, front_y - 0.2, 2.0)
    ]
    # Radial seams, each cut along the local surface normal for uniform depth.
    # Only the upper seams: grooves on the ball's lower half leave hovering
    # roof ledges that the slicer flags as floating regions.
    beta = math.radians(36.0)
    for k in range(5):
        a = math.radians(90 + k * 72)
        if math.sin(a) < -0.3:
            continue
        u = (math.cos(a), 0.0, math.sin(a))
        n = (math.sin(beta) * u[0], -math.cos(beta), math.sin(beta) * u[2])
        origin = tuple(center[i] + (b["r"] + 0.3) * n[i] for i in range(3))
        plane = Plane(origin=origin, x_dir=(-u[2], 0.0, u[0]), z_dir=n)
        grooves.append(extrude(plane * RectangleRounded(1.3, 3.0, 0.5), amount=-1.6))
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

    leg_r = 3.4 if is_dan else 3.5
    leg_top = base_h + (7.5 if is_dan else 6.0)
    shorts_h = 6.5
    torso_w = p["torso_w"]
    torso_d = 13.0 if is_dan else 14.0
    torso_h = p["torso_h"]
    torso_bottom = leg_top + 2.5
    torso_top = torso_bottom + torso_h
    neck_top = torso_top + 2.0
    # Head bottom sits 1.5 mm INTO the torso top: an exact pole-on-plane
    # tangency (head bottom == torso_top) gives BOP self-intersections.
    head_c = neck_top + head_h / 2.0 - 3.5
    face_y = fy - head_r  # foremost face point

    adds = []
    engraves = []

    # Feet + stubby legs + shorts ---------------------------------------------
    foot_dx = 4.5
    for dx in (-foot_dx, foot_dx):
        adds.append(Pos(fx + dx, fy - 2.5, base_h - 1.0) * _rounded_block(7.5, 10.5, 3.0, 2.5))
        adds.append(Pos(fx + dx, fy, (leg_top + base_h - 1) / 2) * Cylinder(leg_r, leg_top - base_h + 1))
    adds.append(Pos(fx, fy, leg_top - 1.0) * _rounded_block(torso_w - 1.0, torso_d - 0.5, shorts_h, 3.5))

    # Torso ----------------------------------------------------------------------
    adds.append(Pos(fx, fy, torso_bottom) * _rounded_block(torso_w, torso_d, torso_h, 4.5, top_fillet=2.5))
    if not is_dan:
        # Carrie: rounder silhouette - a soft hip band.
        adds.append(Pos(fx, fy, torso_bottom + 1.5) * _rounded_block(torso_w + 2.0, torso_d + 1.0, 4.5, 5.0))

    # Jersey panel + number --------------------------------------------------------
    chest_front = fy - torso_d / 2.0
    panel_c = torso_bottom + torso_h * 0.55
    adds.append(_front(RectangleRounded(11.0, 9.5, 2.5), fx, panel_c, chest_front - 1.2, 3.0))
    number = "10" if is_dan else "9"
    adds.append(
        _front(Text(number, 6.8, font=FONT, font_style=FontStyle.BOLD), fx, panel_c, chest_front - 2.6, 2.0)
    )
    # V-collar cue.
    for sx in (-1, 1):
        adds.append(
            _front(
                Rot(Z=sx * 28) * RectangleRounded(1.6, 4.6, 0.7),
                fx + sx * 1.9,
                torso_top - 1.8,
                chest_front - 1.2,
                3.0,
            )
        )

    # Arms: relaxed couple pose, both arms down. The inner arms tilt toward
    # each other so the mittens overlap into joined hands - a deliberate solid
    # fuse that welds the pair together (graze-depth contacts are the enemy).
    # Keep the shoulder line off the torso top-fillet start plane or OCCT
    # leaves a degenerate tangency sliver.
    shoulder_z = torso_top - 3.2
    side = torso_w / 2.0 + 0.6
    arm_r = 2.8 if is_dan else 2.9

    def _hang_arm(root_x: float, tilt_deg: float, length: float):
        tilt = math.radians(tilt_deg)
        direction = (math.sin(tilt), 0.0, -math.cos(tilt))
        root = (root_x, fy, shoulder_z)
        rot = Rot(Y=180.0 - tilt_deg)
        solids = [Pos(*root) * rot * _capsule(arm_r, length)]
        tip = tuple(root[i] + direction[i] * length for i in range(3))
        solids.append(Pos(*tip) * Sphere(arm_r + 0.7))  # mitten
        band = tuple(root[i] + direction[i] * 4.0 for i in range(3))
        solids.append(Pos(*band) * rot * Cylinder(arm_r + 0.8, 2.0))
        solids.append(Pos(*root) * Sphere(arm_r + 1.1))  # shoulder cap
        return solids

    # Outer arms hang straight down hugging the body, with the mittens
    # grounded in the base like the inner ones: a mitten that ends mid-air
    # starts printing as a floating island (caught by the slicer, not by the
    # overhang QC, which measures slope rather than reachability).
    adds.extend(_hang_arm(fx + outer * side, 0.0, shoulder_z - (base_h + 1.8)))
    # Inner arms reach all the way down so the joined-hands blob fuses into
    # the base: no floating mitten underside, and the pair anchors to the
    # base. The 8-degree tilt keeps the dropped mittens clear of the inner
    # legs (a graze there leaves self-intersecting slivers).
    inner_len = shoulder_z - (base_h + 1.8)
    adds.extend(_hang_arm(fx - outer * side, -outer * 8.0, inner_len))

    # Neck + head --------------------------------------------------------------------
    adds.append(Pos(fx, fy, torso_top) * Cylinder(4.2, 5.0))
    # A round head must be a Sphere: _ellipsoid is only STEP-safe when prolate.
    head = Sphere(head_r) if head_h <= head_w else _ellipsoid(head_r, head_h / 2.0)
    adds.append(Pos(fx, fy, head_c) * head)
    # Jaw and lower-face masses are SPHERES on purpose: an oblate ellipsoid of
    # revolution (r_z < r_xy) exports unorientable STEP geometry from OCCT.
    if is_dan:
        # Jaw exactly coaxial with the neck cylinder: a 0.3 mm offset makes
        # their intersection degenerate (near-equal radii, near-equal axes)
        # and BOP flags self-intersecting faces.
        jaw_y, jaw_z, jaw_r = fy, head_c - 7.8, 7.4
        adds.append(Pos(fx, jaw_y, jaw_z) * Sphere(jaw_r))
        # Ears buried well past the head surface; a graze-depth overlap makes
        # OCCT orphan the protruding cap as a separate solid.
        for sx in (-1, 1):
            adds.append(Pos(fx + sx * (head_r - 1.3), fy + 0.5, head_c - 1.6) * Sphere(2.9))
    else:
        # Carrie: soft chubby lower face.
        jaw_y, jaw_z, jaw_r = fy + 0.5, head_c - 7.0, 7.9
        adds.append(Pos(fx, jaw_y, jaw_z) * Sphere(jaw_r))

    # Hair ----------------------------------------------------------------------------
    if is_dan:
        # Steep clip plane: receded at the front, full coverage low in back.
        cap = Pos(fx, fy + 0.6, head_c + 0.3) * _ellipsoid(head_r + 1.3, head_r + 1.6)
        clip = Pos(fx, fy, head_c + 1.0) * Rot(X=-25) * Pos(0, 0, 22) * Box(46, 46, 44)
        adds.append(cap & clip)
        # Parallel strand grooves; angled ones converge and pinch off slivers.
        crown = head_c + head_h / 2.0 + 0.6
        for gx in (-5.4, -1.8, 1.8, 5.4):
            engraves.append(Pos(fx + gx, fy + 2.0, crown + 0.9) * Box(1.3, 24.0, 3.0))
    else:
        bob = Pos(fx, fy + 0.8, head_c + 0.1) * _ellipsoid(head_r + 1.8, head_r + 1.4)
        # Cone bottom at ~40 degrees: the bob tapers to the shoulders and
        # prints supportless, unlike a flat clipped underside. Exactly 45
        # degrees sits on the overhang threshold and flags half its facets.
        taper = Pos(fx, fy + 0.8, head_c - 9.5) * Cone(bottom_radius=4.0, top_radius=26.0, height=26.0)
        bob = bob & taper
        # Rounded face window (cylinder cut) instead of a boxy opening.
        bob = bob - Pos(fx, fy - head_r - 1.0, head_c + 0.8) * Rot(X=90) * Cylinder(8.4, 13.0)
        adds.append(bob)
        # Side hair lobes carry the bob down past the cheeks to the shoulders.
        for sx in (-1, 1):
            adds.append(
                _capsule_between(
                    (fx + sx * (head_r - 1.0), fy + 0.5, head_c - 6.5),
                    (fx + sx * (head_r - 2.2), fy + 0.5, torso_top - 1.0),
                    3.3,
                )
            )
        crown = head_c + head_h / 2.0 + 1.2
        engraves.append(Pos(fx - 2.8, fy + 1.0, crown) * Rot(Z=10) * Box(1.3, 22.0, 3.2))

    # Face: open glasses with engraved pupils, brows, nose, cheeks, smile ------------
    eye_z = head_c + 1.2
    if is_dan:
        frame = (
            Pos(-4.0, 0) * RectangleRounded(7.0, 5.4, 1.8)
            - Pos(-4.0, 0) * RectangleRounded(4.6, 3.0, 1.0)
            + Pos(4.0, 0) * RectangleRounded(7.0, 5.4, 1.8)
            - Pos(4.0, 0) * RectangleRounded(4.6, 3.0, 1.0)
            + RectangleRounded(2.6, 1.5, 0.6)
        )
        adds.append(_front(frame, fx, eye_z, face_y - 1.45, 7.2))
        pupil_dx = 4.0
    else:
        frame = (
            Pos(-4.15, 0) * Circle(4.8)
            - Pos(-4.15, 0) * Circle(3.1)
            + Pos(4.15, 0) * Circle(4.8)
            - Pos(4.15, 0) * Circle(3.1)
            + RectangleRounded(3.0, 1.5, 0.6)
        )
        adds.append(_front(frame, fx, eye_z, face_y - 1.45, 7.2))
        pupil_dx = 4.15

    # Eyes: engraved pupils inside the open frames - the charm of the target.
    for sx in (-1, 1):
        engraves.append(_front(Circle(0.95), fx + sx * pupil_dx, eye_z, face_y - 0.3, 2.2))

    # Brows clear the frame tops and stay below hairline/bangs.
    brow_z = eye_z + (3.7 if is_dan else 5.6)
    for sx in (-1, 1):
        adds.append(
            _front(Rot(Z=sx * 8) * RectangleRounded(4.8, 1.6, 0.7), fx + sx * 4.1, brow_z, face_y - 1.3, 6.5)
        )

    # Nose with a trimmed flat underside: a full ellipsoid tip pokes past the
    # receding face surface, so its first ~1 mm of layers print as floating
    # dots. The trim makes the first nose layer wide enough to reach the face.
    nose_z = eye_z - 3.4
    nose = Pos(fx, face_y + 0.1, nose_z) * _ellipsoid(1.6, 2.3)
    adds.append(nose & Pos(fx, face_y + 0.1, nose_z - 1.4 + 5.0) * Box(10, 10, 10))

    # Smile: engraved crescent (lune) on the jaw sphere's equator, so the cut
    # floor lands 1.0-1.7 mm inside the jaw across the whole lune. A smile cut
    # straddling the jaw/head transition either grazes the head shell at the
    # lune tips or leaves the jaw dome poking through the groove floor.
    smile_z = jaw_z
    jaw_front = jaw_y - jaw_r
    lune = Circle(2.9) - Pos(0, 1.4) * Circle(2.9)
    engraves.append(_front(lune, fx, smile_z, face_y - 2.0, (jaw_front + 1.7) - (face_y - 2.0)))

    # Cheek pads kept >=0.6 mm clear of the smile cut. Prism extrusions, not
    # spheres: near-tangent spheres stall the OCCT fuse; a grazing smile cut
    # orphans the pad in the STEP export.
    for sx in (-1, 1):
        adds.append(_front(Circle(2.0), fx + sx * 5.8, smile_z + 1.8, face_y - 0.8, 4.5))

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
