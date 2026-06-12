"""World Cup neighbors v2 build123d model.

The design intentionally favors chunky, attached details over fragile likeness.
It is meant to teach the repo's build123d lane and produce a more readable
single-material print than the v001 OpenSCAD figurine.
"""

from __future__ import annotations

from build123d import Align, Axis, Box, BuildPart, BuildSketch, Cylinder, Locations, Text, add, extrude


PARAMS = {
    "base": {"width": 125.0, "depth": 70.0, "height": 4.0},
    "goal": {"width": 106.0, "height": 52.0, "post": 4.0, "rail_y": 25.0},
    "ball": {"radius": 7.0},
    "feature_min": 0.8,
}


class PersonSpec:
    """Small immutable-enough value object.

    Avoid dataclasses here because project models are loaded dynamically by
    `bambu.cad` without registering the module in `sys.modules`.
    """

    def __init__(
        self,
        *,
        name: str,
        x: float,
        y: float,
        leg_height: float,
        torso_height: float,
        torso_width: float,
        torso_depth: float,
        head_width: float,
        head_depth: float,
        head_height: float,
        hair_style: str,
        jersey_number: str,
        glasses: bool = True,
    ) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.leg_height = leg_height
        self.torso_height = torso_height
        self.torso_width = torso_width
        self.torso_depth = torso_depth
        self.head_width = head_width
        self.head_depth = head_depth
        self.head_height = head_height
        self.hair_style = hair_style
        self.jersey_number = jersey_number
        self.glasses = glasses


DAN = PersonSpec(
    name="Dan",
    x=-24.0,
    y=-5.0,
    leg_height=17.0,
    torso_height=23.0,
    torso_width=13.0,
    torso_depth=8.5,
    head_width=14.0,
    head_depth=8.5,
    head_height=15.0,
    hair_style="short",
    jersey_number="10",
)

CARRIE = PersonSpec(
    name="Carrie",
    x=23.0,
    y=-5.0,
    leg_height=14.5,
    torso_height=20.5,
    torso_width=15.5,
    torso_depth=9.0,
    head_width=14.5,
    head_depth=9.0,
    head_height=14.0,
    hair_style="rounded",
    jersey_number="9",
)


def make_base():
    """Create a rounded shared base with raised labels."""

    width = PARAMS["base"]["width"]
    depth = PARAMS["base"]["depth"]
    height = PARAMS["base"]["height"]
    radius = 8.0
    with BuildPart() as base:
        with Locations((0, 0, height / 2)):
            Box(width - 2 * radius, depth, height)
            Box(width, depth - 2 * radius, height)
        with Locations(
            (-width / 2 + radius, -depth / 2 + radius, height / 2),
            (width / 2 - radius, -depth / 2 + radius, height / 2),
            (-width / 2 + radius, depth / 2 - radius, height / 2),
            (width / 2 - radius, depth / 2 - radius, height / 2),
        ):
            Cylinder(radius=radius, height=height)

        top_face = base.faces().sort_by(Axis.Z)[-1]
        with BuildSketch(top_face):
            with Locations((-24, -28)):
                Text("DAN", font_size=7.0, align=Align.CENTER)
            with Locations((23, -28)):
                Text("CARRIE", font_size=6.0, align=Align.CENTER)
            with Locations((0, -19)):
                Text("BRAZIL WATCH PARTY", font_size=5.0, align=Align.CENTER)
        extrude(amount=0.8)

    return base.part


def make_goal_backdrop():
    """Create a sturdy soccer goal whose bars double as scene structure."""

    goal = PARAMS["goal"]
    width = goal["width"]
    height = goal["height"]
    post = goal["post"]
    rail_y = goal["rail_y"]
    z0 = PARAMS["base"]["height"]

    with BuildPart() as backdrop:
        post_radius = post / 2
        with Locations((-width / 2, rail_y, z0 + height / 2), (width / 2, rail_y, z0 + height / 2)):
            Cylinder(radius=post_radius, height=height)
        with Locations((0, rail_y, z0 + height)):
            Box(width + post, post, post)

        # Low-relief net bars: robust enough to print, not a fragile mesh.
        for z in (z0 + 14, z0 + 26, z0 + 38):
            with Locations((0, rail_y + 1.3, z)):
                Box(width - 14, 1.4, 1.2)
        for x in (-36, -18, 0, 18, 36):
            with Locations((x, rail_y + 1.4, z0 + 26)):
                Box(1.2, 1.4, 38)
        for x, rotation in ((-26, 28), (26, -28)):
            with Locations((x, rail_y + 1.8, z0 + 26)):
                Cylinder(radius=0.75, height=45, rotation=(0, 90, rotation))

    return backdrop.part


def make_soccer_ball_relief():
    """Create an attached low-relief ball with paint-friendly panel guides."""

    radius = PARAMS["ball"]["radius"]
    z = PARAMS["base"]["height"] + 1.25
    with BuildPart() as ball:
        with Locations((-52, -22, z)):
            Cylinder(radius=radius, height=2.5)
        with Locations((-52, -22, z + 1.5)):
            Cylinder(radius=2.2, height=0.9)
            Box(radius * 1.55, 0.8, 0.9)
            Box(0.8, radius * 1.55, 0.9)
            Box(radius * 1.35, 0.7, 0.9, rotation=(0, 0, 45))
            Box(radius * 1.35, 0.7, 0.9, rotation=(0, 0, -45))

    return ball.part


def make_person(spec: PersonSpec):
    """Create one stylized person with attached, print-friendly details."""

    z0 = PARAMS["base"]["height"]
    leg_z = z0 + spec.leg_height / 2
    torso_z = z0 + spec.leg_height + spec.torso_height / 2
    shoulder_z = z0 + spec.leg_height + spec.torso_height - 3.0
    head_z = z0 + spec.leg_height + spec.torso_height + spec.head_height / 2 + 1.5
    head_front_y = spec.y - spec.head_depth / 2 - 0.35

    with BuildPart() as person:
        with Locations((spec.x - 3.2, spec.y, leg_z), (spec.x + 3.2, spec.y, leg_z)):
            Cylinder(radius=2.15, height=spec.leg_height)
        with Locations((spec.x, spec.y, z0 + 1.0)):
            Box(spec.torso_width + 4.0, spec.torso_depth + 2.0, 2.0)

        with Locations((spec.x, spec.y, torso_z)):
            Box(spec.torso_width, spec.torso_depth, spec.torso_height)

        # Jersey panel, collar, sleeve bands, and number guides are raised paint guides.
        front_y = spec.y - spec.torso_depth / 2 - 0.35
        with Locations((spec.x, front_y, torso_z + 1.2)):
            Box(spec.torso_width - 3.0, 0.8, spec.torso_height - 5.0)
        with Locations((spec.x, front_y - 0.15, shoulder_z)):
            Box(5.0, 0.8, 1.0)
        for offset_x in (-2.2, 2.2):
            with Locations((spec.x + offset_x, front_y - 0.2, torso_z + 1.0)):
                Box(1.0, 0.8, 7.0)

        arm_z = z0 + spec.leg_height + spec.torso_height / 2 - 1.0
        with Locations((spec.x - spec.torso_width / 2 - 1.8, spec.y, arm_z), (spec.x + spec.torso_width / 2 + 1.8, spec.y, arm_z)):
            Cylinder(radius=1.8, height=spec.torso_height - 3.0)
        with Locations((spec.x - spec.torso_width / 2 - 1.8, front_y + 0.8, z0 + spec.leg_height + 2.0), (spec.x + spec.torso_width / 2 + 1.8, front_y + 0.8, z0 + spec.leg_height + 2.0)):
            Cylinder(radius=2.1, height=2.2)

        with Locations((spec.x, spec.y, z0 + spec.leg_height + spec.torso_height + 0.8)):
            Cylinder(radius=2.5, height=2.2)
        with Locations((spec.x, spec.y, head_z)):
            Box(spec.head_width, spec.head_depth, spec.head_height)

        _add_hair(spec, head_z)
        if spec.glasses:
            _add_glasses(spec, head_front_y, head_z)
        _add_face_cues(spec, head_front_y, head_z)

    return person.part


def _add_hair(spec: PersonSpec, head_z: float) -> None:
    top_z = head_z + spec.head_height / 2 + 1.1
    if spec.hair_style == "rounded":
        with Locations((spec.x, spec.y, top_z)):
            Box(spec.head_width + 2.5, spec.head_depth + 1.5, 2.2)
        with Locations((spec.x - spec.head_width / 2 - 0.8, spec.y, head_z + 1.0), (spec.x + spec.head_width / 2 + 0.8, spec.y, head_z + 1.0)):
            Box(2.2, spec.head_depth + 1.0, spec.head_height - 2.0)
    else:
        with Locations((spec.x, spec.y + 0.2, top_z)):
            Box(spec.head_width + 1.0, spec.head_depth + 0.8, 2.0)
        with Locations((spec.x - 4.0, spec.y - spec.head_depth / 2 - 0.2, head_z + 5.0), (spec.x, spec.y - spec.head_depth / 2 - 0.2, head_z + 5.4), (spec.x + 4.0, spec.y - spec.head_depth / 2 - 0.2, head_z + 5.0)):
            Box(2.0, 0.8, 4.0)


def _add_glasses(spec: PersonSpec, front_y: float, head_z: float) -> None:
    eye_z = head_z + 1.5
    for eye_x in (-3.2, 3.2):
        with Locations((spec.x + eye_x, front_y, eye_z + 1.4), (spec.x + eye_x, front_y, eye_z - 1.4)):
            Box(4.8, 0.8, 0.8)
        with Locations((spec.x + eye_x - 2.0, front_y, eye_z), (spec.x + eye_x + 2.0, front_y, eye_z)):
            Box(0.8, 0.8, 3.4)
    with Locations((spec.x, front_y, eye_z)):
        Box(2.4, 0.8, 0.8)


def _add_face_cues(spec: PersonSpec, front_y: float, head_z: float) -> None:
    with Locations((spec.x, front_y - 0.1, head_z - 1.5)):
        Box(1.2, 0.8, 3.0)
    with Locations((spec.x, front_y - 0.15, head_z - 4.7)):
        Box(5.2, 0.8, 0.8)
    with Locations((spec.x - 5.1, front_y - 0.15, head_z - 2.7), (spec.x + 5.1, front_y - 0.15, head_z - 2.7)):
        Box(1.0, 0.8, 1.0)


def assemble_scene():
    """Assemble the full v2 scene."""

    with BuildPart() as scene:
        add(make_base())
        add(make_goal_backdrop())
        add(make_soccer_ball_relief())
        add(make_person(DAN))
        add(make_person(CARRIE))

    return scene.part


model = assemble_scene()
