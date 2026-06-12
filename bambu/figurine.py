"""OpenSCAD generation for stylized, printable figurines."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from textwrap import dedent


@dataclass(frozen=True)
class Figurine:
    name: str
    height_mm: int = 68
    body_shape: str = "average"
    hair: str = "short hair"
    accessories: list[str] = field(default_factory=list)
    jersey_number: str = "10"


@dataclass(frozen=True)
class Scene:
    title: str
    figures: list[Figurine]


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip()).strip("_")
    return cleaned.lower() or "figure"


def generate_scad(scene: Scene) -> str:
    """Generate an OpenSCAD scene for one or more simplified figurines."""

    if not scene.figures:
        raise ValueError("Scene must include at least one figurine.")

    parts = [_header(scene.title), _modules()]
    spacing = 42
    start = -spacing * (len(scene.figures) - 1) / 2
    for index, figure in enumerate(scene.figures):
        x = start + index * spacing
        parts.append(_figure_call(figure, x))
    return "\n\n".join(parts) + "\n"


def _header(title: str) -> str:
    return dedent(
        f"""
        // {title}
        // Brazil-inspired watch-party figurines.
        // Generated for single-material printing; paint jersey panels yellow/green/blue after printing.
        $fn = 48;
        """
    ).strip()


def _modules() -> str:
    return dedent(
        """
        module rounded_body(height=42, width=18, depth=10) {
          hull() {
            translate([0, 0, 4]) sphere(r=width/2);
            translate([0, 0, height]) scale([0.82, 0.55, 1]) sphere(r=width/2);
          }
        }

        module head_with_hair(hair_note="short hair", glasses=false, sunglasses=false) {
          translate([0, 0, 57]) sphere(r=8);
          translate([0, -0.6, 64]) scale([1.05, 0.75, 0.35]) sphere(r=8);
          if (glasses || sunglasses) {
            translate([-3.2, -7.4, 58.5]) cube([4.2, 1.2, 1.2], center=true);
            translate([3.2, -7.4, 58.5]) cube([4.2, 1.2, 1.2], center=true);
            translate([0, -7.4, 58.5]) cube([2.2, 0.9, 0.8], center=true);
          }
        }

        module brazil_jersey(number_text="10") {
          // Raised panels are paint guides: yellow shirt, green trim, blue number.
          translate([0, -8.7, 36]) cube([17, 1.4, 20], center=true);
          translate([0, -9.6, 42]) cube([12, 1.2, 2], center=true);
          translate([0, -9.8, 34]) linear_extrude(height=1.1) text(number_text, size=7, halign="center", valign="center");
        }

        module arms(height=40) {
          translate([-13, 0, 34]) rotate([0, 12, 6]) cylinder(h=26, r=2.6, center=true);
          translate([13, 0, 34]) rotate([0, -12, -6]) cylinder(h=26, r=2.6, center=true);
        }

        module legs() {
          translate([-4.5, 0, 11]) cylinder(h=22, r=3.2, center=true);
          translate([4.5, 0, 11]) cylinder(h=22, r=3.2, center=true);
          translate([-4.5, -3, 0.9]) cube([8, 14, 2], center=true);
          translate([4.5, -3, 0.9]) cube([8, 14, 2], center=true);
        }

        module base(label="figure") {
          translate([0, 0, -1.5]) cylinder(h=3, r=17);
          translate([0, -15.5, 0.2]) linear_extrude(height=0.9) text(label, size=3.5, halign="center", valign="center");
        }

        module figurine(label="figure", scale_factor=1, number_text="10", glasses=false, sunglasses=false) {
          scale([scale_factor, scale_factor, scale_factor]) {
            base(label);
            legs();
            rounded_body();
            brazil_jersey(number_text);
            arms();
            head_with_hair(glasses=glasses, sunglasses=sunglasses);
          }
        }
        """
    ).strip()


def _figure_call(figure: Figurine, x: float) -> str:
    label = slug(figure.name)
    scale_factor = max(0.72, min(1.2, figure.height_mm / 68))
    accessories = {slug(item) for item in figure.accessories}
    glasses = "true" if "glasses" in accessories else "false"
    sunglasses = "true" if "sunglasses" in accessories else "false"
    number_symbol = f"number_{slug(figure.jersey_number)}"
    return dedent(
        f"""
        // {figure.name}: {figure.body_shape}; {figure.hair}; {', '.join(figure.accessories) or 'no accessories'}
        {number_symbol} = "{figure.jersey_number}";
        translate([{x:.1f}, 0, 1.5]) figurine(label="{label}", scale_factor={scale_factor:.3f}, number_text={number_symbol}, glasses={glasses}, sunglasses={sunglasses});
        """
    ).strip()

