"""Rounded base slabs and raised nameplate lettering."""

from __future__ import annotations

from build123d import FontStyle, Pos, Text, extrude, Plane

from bambu.cad.primitives import front_extrude, rounded_block


def make_rounded_base(
    *,
    width: float,
    depth: float,
    height: float,
    corner_r: float,
    top_fillet: float = 2.0,
):
    return rounded_block(width, depth, height, corner_r, top_fillet=top_fillet)


def make_nameplate(
    text: str,
    *,
    x: float,
    z: float,
    front_y: float,
    size: float = 8.0,
    proud: float = 1.6,
    font: str = "Arial",
    depth: float | None = None,
):
    depth = depth or proud + 2.0
    return front_extrude(
        Text(text, size, font=font, font_style=FontStyle.BOLD),
        x,
        z,
        front_y - proud,
        depth,
    )


def make_deck_text(
    text: str,
    *,
    x: float,
    y: float,
    base_z: float,
    size: float = 6.5,
    height: float = 1.5,
    font: str = "Arial",
):
    return extrude(
        Plane.XY.offset(base_z - 0.5) * Pos(x, y) * Text(text, size, font=font, font_style=FontStyle.BOLD),
        amount=height,
    )
