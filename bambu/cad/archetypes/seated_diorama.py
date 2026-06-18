"""Seated diorama archetype composition helpers."""

from __future__ import annotations

from typing import Any

from build123d import Circle, Cylinder, Pos, Sphere

from bambu.cad.animals import make_dog_lap_pose
from bambu.cad.base import make_nameplate, make_rounded_base
from bambu.cad.furniture import make_patio_chair
from bambu.cad.heads import (
    add_brows,
    add_engraved_pupils,
    add_glasses_ridge,
    add_hair_grooves,
    add_jaw_sphere,
    add_smile_engrave,
    add_swept_hair_cap,
)
from bambu.cad.primitives import (
    assert_single_solid,
    front_extrude,
    multifuse,
    rounded_block,
    subtract_engraves,
)

# Default PARAMS cite best-buds-chair designs/v1/*.yaml envelope.
DEFAULT_PARAMS = {
    "base": {"x": 118.0, "y": 65.0, "z": 10.0, "corner_r": 9.0},
    "nameplate": {"text": "BEST BUDS", "size": 7.5, "proud": 1.6},
    "chair": {"cx": 8.0, "cy": 2.0, "seat_w": 36.0, "seat_d": 30.0},
    "woman": {"cx": 14.0, "cy": 4.0, "head_w": 20.0, "head_h": 21.0, "torso_w": 17.0, "torso_h": 14.0},
    "dog": {"cx": -6.0, "cy": 6.0, "head_r": 10.5},
}


def make_seated_woman(
    *,
    base_z: float,
    cx: float,
    cy: float,
    head_w: float,
    head_h: float,
    torso_w: float,
    torso_h: float,
):
    """Seated woman with glasses ridge, layered hair cap, arm reaching toward dog."""

    adds: list[Any] = []
    engraves: list[Any] = []

    head_r = head_w / 2.0
    seat_z = base_z + 18.0
    torso_bottom = seat_z
    torso_top = torso_bottom + torso_h
    head_c = torso_top + head_h / 2.0 - 2.0
    face_y = cy - head_r

    adds.append(Pos(cx, cy, torso_bottom) * rounded_block(torso_w, 14.0, torso_h, 4.0, top_fillet=2.0))
    adds.append(Pos(cx, cy - 1.0, seat_z - 4.0) * rounded_block(torso_w + 2.0, 16.0, 6.0, 4.0))
    adds.append(Pos(cx, cy, torso_top) * Cylinder(3.8, 4.5))
    head = Sphere(head_r) if head_h <= head_w else Sphere(head_r)
    adds.append(Pos(cx, cy, head_c) * head)

    jaw_y, jaw_z, jaw_r = cy, head_c - 6.5, 6.8
    add_jaw_sphere(adds, fx=cx, jaw_y=jaw_y, jaw_z=jaw_z, jaw_r=jaw_r)
    add_swept_hair_cap(adds, fx=cx, fy=cy, head_c=head_c, head_r=head_r)
    crown = head_c + head_h / 2.0 + 0.5
    add_hair_grooves(engraves, fx=cx, fy=cy, crown_z=crown)

    eye_z = head_c + 1.0
    pupil_dx = add_glasses_ridge(adds, fx=cx, eye_z=eye_z, face_y=face_y, round_frames=False)
    add_engraved_pupils(engraves, fx=cx, eye_z=eye_z, face_y=face_y, pupil_dx=pupil_dx)
    add_brows(adds, fx=cx, brow_z=eye_z + 3.5, face_y=face_y)

    nose_z = eye_z - 3.0
    adds.append(Pos(cx, face_y + 0.1, nose_z) * Sphere(1.4))
    jaw_front = jaw_y - jaw_r
    add_smile_engrave(engraves, fx=cx, smile_z=jaw_z, face_y=face_y, jaw_front=jaw_front)

    for sx in (-1, 1):
        adds.append(front_extrude(Circle(1.8), cx + sx * 5.5, jaw_z + 1.5, face_y - 0.8, 4.0))

    # Arm reaching toward dog (fused capsule).
    from bambu.cad.primitives import capsule_between

    shoulder = (cx - 8.0, cy + 2.0, torso_top - 2.0)
    hand = (cx - 16.0, cy + 4.0, base_z + 2.0)
    adds.append(capsule_between(shoulder, hand, 2.6))
    adds.append(Pos(*hand) * Sphere(3.2))
    adds.append(Pos(cx - 14.0, cy + 3.0, base_z - 0.5) * Sphere(3.5))

    body = multifuse(*adds)
    return subtract_engraves(body, engraves)


def build_seated_diorama(params: dict[str, Any] | None = None):
    """Compose base + chair + seated woman + lap dog into one fused solid."""

    p = {**DEFAULT_PARAMS, **(params or {})}
    base_p = p["base"]
    base_z = base_p["z"]
    base = make_rounded_base(
        width=base_p["x"],
        depth=base_p["y"],
        height=base_z,
        corner_r=base_p["corner_r"],
    )
    front_y = -base_p["y"] / 2.0
    np = p["nameplate"]
    label = make_nameplate(
        np["text"],
        x=0.0,
        z=base_z / 2.0 - 0.5,
        front_y=front_y,
        size=np["size"],
        proud=np["proud"],
    )

    chair_p = p["chair"]
    chair = make_patio_chair(
        cx=chair_p["cx"],
        cy=chair_p["cy"],
        base_z=base_z,
        seat_w=chair_p["seat_w"],
        seat_d=chair_p["seat_d"],
    )

    w = p["woman"]
    woman = make_seated_woman(
        base_z=base_z,
        cx=w["cx"],
        cy=w["cy"],
        head_w=w["head_w"],
        head_h=w["head_h"],
        torso_w=w["torso_w"],
        torso_h=w["torso_h"],
    )

    d = p["dog"]
    dog = make_dog_lap_pose(cx=d["cx"], cy=d["cy"], base_z=base_z, head_r=d["head_r"])

    scene = multifuse(base, label, chair, woman, dog)
    return assert_single_solid(scene, label="seated_diorama")
