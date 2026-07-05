"""OpenSCAD generation for stylized, printable figurines."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from textwrap import dedent


@dataclass(frozen=True)
class Figurine:
    name: str
    height_mm: int = 68
    body_shape: str = "average"
    hair: str = "short hair"
    accessories: list[str] = field(default_factory=list)
    jersey_number: str = "10"
    profile: str = "generic"


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
    parts.append('shared_watch_party_base(label="BRAZIL WATCH PARTY");')
    spacing = 52
    start = -spacing * (len(scene.figures) - 1) / 2
    for index, figure in enumerate(scene.figures):
        x = start + index * spacing
        parts.append(_figure_call(figure, x))
        parts.append(_name_label_call(figure, x))
    return "\n\n".join(parts) + "\n"


def _header(title: str) -> str:
    return dedent(
        f"""
        // {title}
        // Brazil-inspired watch-party figurines.
        // A1 mini display-safe: 180x180x180 build volume, 0.4mm nozzle, PLA Basic, Textured PEI Plate.
        // Generated for single-material printing; paint jersey panels yellow/green/blue after printing.
        // minimum raised detail target: 0.8mm
        $fn = 64;
        """
    ).strip()


def _modules() -> str:
    return dedent(
        """
        module rounded_capsule(height=42, width=18, depth=10) {
          hull() {
            translate([0, 0, 4]) scale([1, depth/width, 0.58]) sphere(r=width/2);
            translate([0, 0, height]) scale([0.78, depth/width, 0.9]) sphere(r=width/2);
          }
        }

        module rounded_plate(width=112, depth=58, height=4, radius=12) {
          hull() {
            translate([-width/2+radius, -depth/2+radius, 0]) cylinder(h=height, r=radius);
            translate([ width/2-radius, -depth/2+radius, 0]) cylinder(h=height, r=radius);
            translate([-width/2+radius,  depth/2-radius, 0]) cylinder(h=height, r=radius);
            translate([ width/2-radius,  depth/2-radius, 0]) cylinder(h=height, r=radius);
          }
        }

        module shared_watch_party_base(label="BRAZIL WATCH PARTY") {
          // Wide, low shared base improves first-layer adhesion on the Textured PEI Plate.
          rounded_plate(width=118, depth=62, height=4, radius=14);
          // Soccer cues are supportless raised base details, not fragile free-standing parts.
          shallow_goal_net();
          soccer_ball();
          translate([0, -28.8, 4.05]) cube([102, 2.4, 1.2], center=true);
          translate([0, -25.2, 3.92])
            linear_extrude(height=0.9) text(label, size=4.4, halign="center", valign="center");
          translate([-40, 20, 3.92]) cylinder(h=1.1, r=5.5);
          translate([40, 20, 3.92]) cylinder(h=1.1, r=5.5);
        }

        module shallow_goal_net() {
          // A top-surface goal/net motif gives soccer context without tall posts or mesh.
          translate([0, 23.5, 4.12]) cube([84, 1.25, 1.05], center=true);
          translate([-42, 19.6, 4.12]) cube([1.35, 7.8, 1.05], center=true);
          translate([42, 19.6, 4.12]) cube([1.35, 7.8, 1.05], center=true);
          for (x=[-30,-18,-6,6,18,30]) {
            translate([x, 20.9, 4.14]) cube([1.0, 5.6, 0.95], center=true);
          }
          for (x=[-24,0,24]) {
            translate([x, 21.1, 4.16]) rotate([0, 0, 32]) cube([1.0, 13.0, 0.9], center=true);
            translate([x, 21.1, 4.16]) rotate([0, 0, -32]) cube([1.0, 13.0, 0.9], center=true);
          }
        }

        module soccer_ball() {
          translate([-50.5, -5.5, 3.92]) {
            cylinder(h=1.45, r=6.4);
            translate([0, 0, 1.38]) cylinder(h=0.75, r=2.1, $fn=5);
            for (angle=[0,60,120,180,240,300]) {
              rotate([0, 0, angle]) translate([3.55, 0, 1.36]) cube([4.8, 0.9, 0.76], center=true);
            }
          }
        }

        module base_name_label(label="DAN", x=0) {
          translate([x, -15.2, 3.92])
            linear_extrude(height=0.95) text(label, size=5.0, halign="center", valign="center");
        }

        module head_shape(head_radius=7.8) {
          translate([0, 0, 58]) scale([0.92, 0.82, 1.08]) sphere(r=head_radius);
          translate([0, -6.8, 57.4]) scale([0.50, 0.18, 0.32]) sphere(r=head_radius);
          translate([-2.8, -6.35, 56]) sphere(r=0.95);
          translate([2.8, -6.35, 56]) sphere(r=0.95);
          translate([0, -6.5, 53.8]) rotate([90, 0, 0]) cylinder(h=1.1, r=1.35);
        }

        module eyewear(glasses=false, sunglasses=false) {
          if (glasses || sunglasses) {
            lens_h = sunglasses ? 2.2 : 1.4;
            translate([-3.2, -6.65, 58.1]) cube([4.5, 1.4, lens_h], center=true);
            translate([3.2, -6.65, 58.1]) cube([4.5, 1.4, lens_h], center=true);
            translate([0, -6.65, 58.1]) cube([2.1, 1.2, 0.8], center=true);
            translate([-6.4, -5.95, 58]) rotate([0, 0, 17]) cube([3.3, 1.0, 0.8], center=true);
            translate([6.4, -5.95, 58]) rotate([0, 0, -17]) cube([3.3, 1.0, 0.8], center=true);
          }
        }

        module short_salt_pepper_hair() {
          translate([0, 0, 64.2]) scale([1.02, 0.84, 0.38]) sphere(r=7.6);
          for (x=[-4.8,-2.4,0,2.4,4.8]) {
            translate([x, -5.6, 62.7]) rotate([18, 0, x*2]) cylinder(h=3.2, r=0.9, center=true);
          }
        }

        module swept_light_hair_with_clip() {
          translate([0, 0.2, 63.2]) scale([1.18, 0.92, 0.48]) sphere(r=7.8);
          translate([-5.6, -3.2, 61.0]) rotate([0, 22, -20]) cylinder(h=8.5, r=1.15, center=true);
          translate([5.4, -2.0, 61.2]) rotate([0, -18, 20]) cylinder(h=7.0, r=1.1, center=true);
          translate([7.1, -4.9, 60.8]) cube([4.0, 1.2, 1.8], center=true);
        }

        module jersey_paint_guides(number_text="10", body_width=18, body_depth=11) {
          // Raised guides are thick enough to paint and to survive a 0.4mm nozzle.
          front_y = -body_depth/2 - 0.08;
          text_y = -body_depth/2 + 0.20;
          translate([0, front_y, 37]) cube([body_width*0.88, 1.4, 20], center=true);
          translate([0, front_y-0.08, 47.4]) cube([body_width*0.72, 1.3, 2.2], center=true);
          translate([-body_width*0.31, front_y-0.08, 38.3]) cube([1.6, 1.3, 15.5], center=true);
          translate([ body_width*0.31, front_y-0.08, 38.3]) cube([1.6, 1.3, 15.5], center=true);
          translate([0, text_y, 35.2]) rotate([90, 0, 0])
            linear_extrude(height=1.0) text(number_text, size=8.2, halign="center", valign="center");
        }

        module supportless_pose(body_width=18, body_depth=11, arm_style="relaxed") {
          // Arms stay close to the body to avoid long unsupported overhangs.
          translate([-body_width*0.63, -0.7, 35]) rotate([0, 10, 6]) cylinder(h=27, r=2.45, center=true);
          translate([ body_width*0.63, -0.7, 35]) rotate([0, -10, -6]) cylinder(h=27, r=2.45, center=true);
          translate([-body_width*0.64, -4.0, 23.2]) sphere(r=2.6);
          translate([ body_width*0.64, -4.0, 23.2]) sphere(r=2.6);
        }

        module crossbody_bag(body_width=20, body_depth=12) {
          front_y = -body_depth/2 - 0.05;
          translate([-4, front_y, 39.5]) rotate([0, 0, -26]) cube([2.1, 1.4, 27], center=true);
          translate([8.5, front_y-0.2, 27.5]) scale([0.86, 0.30, 1.08]) sphere(r=5.2);
          translate([8.5, front_y-0.4, 27.5]) cube([5.8, 1.2, 5.8], center=true);
        }

        module legs_and_shoes(body_width=18, stance=1) {
          translate([-body_width*0.22, 0, 14]) rotate([0, 0, 2*stance]) cylinder(h=24, r=3.2, center=true);
          translate([ body_width*0.22, 0, 14]) rotate([0, 0, -2*stance]) cylinder(h=24, r=3.2, center=true);
          translate([-body_width*0.22, -4, 2.3]) cube([8.8, 15, 3.3], center=true);
          translate([ body_width*0.22, -4, 2.3]) cube([8.8, 15, 3.3], center=true);
        }

        module figure_core(body_width=18, body_depth=11, height=68, number_text="10") {
          legs_and_shoes(body_width=body_width);
          translate([0, 0, 25]) rounded_capsule(height=27, width=body_width, depth=body_depth);
          jersey_paint_guides(number_text=number_text, body_width=body_width, body_depth=body_depth);
          supportless_pose(body_width=body_width, body_depth=body_depth);
          head_shape(head_radius=7.7);
        }

        module person_specific_features(profile="generic", body_width=18, body_depth=11, glasses=false, sunglasses=false) {
          if (profile == "tall_neighbor") {
            short_salt_pepper_hair();
            eyewear(glasses=true, sunglasses=false);
            translate([10.9, -4.6, 26.6]) cylinder(h=1.5, r=2.0, center=true);
          } else if (profile == "smiling_neighbor") {
            swept_light_hair_with_clip();
            eyewear(glasses=false, sunglasses=true);
            crossbody_bag(body_width=body_width, body_depth=body_depth);
          } else {
            eyewear(glasses=glasses, sunglasses=sunglasses);
          }
        }

        module figurine(label="figure", scale_factor=1, number_text="10", glasses=false, sunglasses=false, profile="generic", body_width=18, body_depth=11) {
          scale([scale_factor, scale_factor, scale_factor]) {
            figure_core(body_width=body_width, body_depth=body_depth, number_text=number_text);
            person_specific_features(profile=profile, body_width=body_width, body_depth=body_depth, glasses=glasses, sunglasses=sunglasses);
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
    profile_slug = slug(figure.profile)
    profile = (
        profile_slug
        if profile_slug != "generic"
        else label
        if label in {"tall_neighbor", "smiling_neighbor"}
        else "generic"
    )
    body_width = (
        16.5 if figure.body_shape == "slim" else 21.0 if figure.body_shape == "curvy" else 18.0
    )
    body_depth = (
        10.5 if figure.body_shape == "slim" else 12.4 if figure.body_shape == "curvy" else 11.0
    )
    number_symbol = f"number_{slug(figure.jersey_number)}"
    base_contact_z = 3.9 - 0.65 * scale_factor
    return dedent(
        f"""
        // {figure.name}: {figure.body_shape}; {figure.hair}; {", ".join(figure.accessories) or "no accessories"}
        {number_symbol} = "{figure.jersey_number}";
        translate([{x:.1f}, 0, {base_contact_z:.3f}]) figurine(label="{label}", scale_factor={scale_factor:.3f}, number_text={number_symbol}, glasses={glasses}, sunglasses={sunglasses}, profile="{profile}", body_width={body_width:.1f}, body_depth={body_depth:.1f});
        """
    ).strip()


def _name_label_call(figure: Figurine, x: float) -> str:
    label = re.sub(r"[^A-Za-z0-9 +&-]", "", figure.name).strip().upper() or "FRIEND"
    return f'base_name_label(label="{label}", x={x:.1f});'
