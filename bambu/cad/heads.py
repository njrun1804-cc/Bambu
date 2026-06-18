"""Print-safe chibi head cues: glasses ridges, hair caps, engraved pupils."""

from __future__ import annotations

from build123d import Box, Circle, Pos, RectangleRounded, Rot, Sphere

from bambu.cad.primitives import ellipsoid, front_extrude


def open_rect_glasses_frame(*, lens_dx: float = 4.0):
    return (
        Pos(-lens_dx, 0) * RectangleRounded(7.0, 5.4, 1.8)
        - Pos(-lens_dx, 0) * RectangleRounded(4.6, 3.0, 1.0)
        + Pos(lens_dx, 0) * RectangleRounded(7.0, 5.4, 1.8)
        - Pos(lens_dx, 0) * RectangleRounded(4.6, 3.0, 1.0)
        + RectangleRounded(2.6, 1.5, 0.6)
    )


def open_round_glasses_frame(*, lens_dx: float = 4.15):
    return (
        Pos(-lens_dx, 0) * Circle(4.8)
        - Pos(-lens_dx, 0) * Circle(3.1)
        + Pos(lens_dx, 0) * Circle(4.8)
        - Pos(lens_dx, 0) * Circle(3.1)
        + RectangleRounded(3.0, 1.5, 0.6)
    )


def add_glasses_ridge(
    adds: list,
    *,
    fx: float,
    eye_z: float,
    face_y: float,
    round_frames: bool = False,
    lens_dx: float | None = None,
):
    frame = open_round_glasses_frame(lens_dx=lens_dx or 4.15) if round_frames else open_rect_glasses_frame(lens_dx=lens_dx or 4.0)
    adds.append(front_extrude(frame, fx, eye_z, face_y - 1.45, 7.2))
    return lens_dx or (4.15 if round_frames else 4.0)


def add_engraved_pupils(
    engraves: list,
    *,
    fx: float,
    eye_z: float,
    face_y: float,
    pupil_dx: float,
):
    for sx in (-1, 1):
        engraves.append(front_extrude(Circle(0.95), fx + sx * pupil_dx, eye_z, face_y - 0.3, 2.2))


def add_brows(adds: list, *, fx: float, brow_z: float, face_y: float, wide: bool = False):
    for sx in (-1, 1):
        w = 4.8 if wide else 4.8
        adds.append(
            front_extrude(
                Rot(Z=sx * 8) * RectangleRounded(w, 1.6, 0.7),
                fx + sx * 4.1,
                brow_z,
                face_y - 1.3,
                6.5,
            )
        )


def add_swept_hair_cap(
    adds: list,
    *,
    fx: float,
    fy: float,
    head_c: float,
    head_r: float,
    clip_tilt: float = -25.0,
):
    cap = Pos(fx, fy + 0.6, head_c + 0.3) * ellipsoid(head_r + 1.3, head_r + 1.6)
    clip = Pos(fx, fy, head_c + 1.0) * Rot(X=clip_tilt) * Pos(0, 0, 22) * Box(46, 46, 44)
    adds.append(cap & clip)


def add_hair_grooves(engraves: list, *, fx: float, fy: float, crown_z: float, offsets: tuple[float, ...] = (-5.4, -1.8, 1.8, 5.4)):
    from build123d import Box

    for gx in offsets:
        engraves.append(Pos(fx + gx, fy + 2.0, crown_z) * Box(1.3, 24.0, 3.0))


def add_jaw_sphere(adds: list, *, fx: float, jaw_y: float, jaw_z: float, jaw_r: float):
    adds.append(Pos(fx, jaw_y, jaw_z) * Sphere(jaw_r))


def add_smile_engrave(
    engraves: list,
    *,
    fx: float,
    smile_z: float,
    face_y: float,
    jaw_front: float,
):
    from build123d import Circle, Pos

    lune = Circle(2.9) - Pos(0, 1.4) * Circle(2.9)
    engraves.append(front_extrude(lune, fx, smile_z, face_y - 2.0, (jaw_front + 1.7) - (face_y - 2.0)))
