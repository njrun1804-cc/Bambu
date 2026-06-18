"""Fusion-safe animal geometry — validate dog in isolation before full scenes."""

from __future__ import annotations

from build123d import Circle, Pos, Sphere

from bambu.cad.primitives import assert_single_solid, capsule_between, front_extrude, multifuse, subtract_engraves


def make_dog_head(
    *,
    cx: float,
    cy: float,
    cz: float,
    head_r: float = 11.0,
    ear_length: float = 9.0,
    face_y: float | None = None,
):
    """Oversized dog head with floppy ears and tri-color mask engrave cues."""

    face_y = face_y if face_y is not None else cy - head_r
    adds = []
    engraves = []

    adds.append(Pos(cx, cy, cz) * Sphere(head_r))
    # Floppy ears: capsules buried into the skull (>=0.3 mm overlap).
    for sx in (-1, 1):
        root = (cx + sx * (head_r - 2.5), cy + 1.5, cz + 1.0)
        tip = (cx + sx * (head_r + 0.5), cy + 2.5, cz - ear_length + 8.0)
        adds.append(capsule_between(root, tip, 3.4))

    # White chest patch zone (raised paint-guide pad on lower face).
    adds.append(front_extrude(Circle(5.5), cx, cz - 4.5, face_y - 1.0, 4.0))

    # Tri-color mask cues: dark patches as shallow engraves (paint zones).
    for sx, dx in ((-1, -3.8), (1, 3.8)):
        engraves.append(front_extrude(Circle(3.2), cx + dx, cz + 2.5, face_y - 0.4, 2.0))
    engraves.append(front_extrude(Circle(2.4), cx, cz + 5.0, face_y - 0.3, 1.8))

    # Nose bump
    adds.append(front_extrude(Circle(1.8), cx, cz - 2.0, face_y - 1.2, 3.5))

    body = multifuse(*adds)
    return subtract_engraves(body, engraves)


def make_dog_lap_pose(
    *,
    cx: float,
    cy: float,
    base_z: float,
    head_r: float = 11.0,
    body_length: float = 16.0,
):
    """Seated lap dog: fused head + compact body blob anchored to base."""

    head_cz = base_z + 14.0
    face_y = cy - head_r
    head = make_dog_head(cx=cx, cy=cy, cz=head_cz, head_r=head_r, face_y=face_y)
    body = Pos(cx, cy + 2.0, base_z + 6.0) * Sphere(9.5)
    tail = capsule_between((cx + 6.0, cy + 6.0, base_z + 7.0), (cx + 9.0, cy + 10.0, base_z + 3.0), 2.8)
    scene = multifuse(head, body, tail)
    return assert_single_solid(scene, label="dog_lap_pose")


def validate_dog_geometry() -> None:
    """Smoke-build dog geometry; raises if not a single solid."""

    make_dog_lap_pose(cx=0.0, cy=0.0, base_z=10.0)
