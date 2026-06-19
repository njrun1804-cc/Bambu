"""Blender generator for the v4 Dan and Carrie watch-party scene."""

from __future__ import annotations

import argparse
import json
from math import radians
from pathlib import Path
import sys

import bpy
from mathutils import Vector


GREEN = (0.04, 0.78, 0.24, 1.0)
DARK_GREEN = (0.02, 0.38, 0.13, 1.0)
LIGHT_GREEN = (0.35, 0.95, 0.48, 1.0)


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--spec-json", type=Path)
    return parser.parse_args(argv)


def material(name: str, color: tuple[float, float, float, float]):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    return mat


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smooth(obj, *, shade: bool = True, bevel: float = 0.0, segments: int = 4):
    if shade:
        try:
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.shade_smooth()
            obj.select_set(False)
        except RuntimeError:
            pass
    if bevel > 0:
        modifier = obj.modifiers.new("soft print bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = segments
        modifier.affect = "EDGES"
        obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    return obj


def add_cube(name: str, loc, scale, mat, *, bevel: float = 0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return smooth(obj, bevel=bevel)


def add_sphere(name: str, loc, scale, mat, *, segments: int = 48):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=24, radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)
    return smooth(obj)


def add_cylinder(name: str, loc, radius: float, depth: float, mat, *, vertices: int = 48, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return smooth(obj, bevel=0.15, segments=3)


def add_curve(name: str, points, mat, *, bevel_depth: float = 0.55):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 16
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 4
    poly = curve.splines.new("POLY")
    poly.points.add(len(points) - 1)
    for point, coord in zip(poly.points, points):
        point.co = (coord[0], coord[1], coord[2], 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def add_text(name: str, text: str, loc, size: float, mat, *, align: str = "CENTER"):
    bpy.ops.object.text_add(location=loc, rotation=(radians(90), 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.body = text
    obj.data.align_x = align
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.35
    obj.data.bevel_depth = 0.03
    obj.data.materials.append(mat)
    return obj


def build_base(mat, accent):
    add_cube("rounded nameplate base", (0, 0, 6), (125, 70, 12), mat, bevel=5.0)
    add_text("dan label", "DAN", (-36, -35.8, 13.1), 8.2, accent)
    add_text("star label", "*", (0, -35.8, 13.1), 8.0, accent)
    add_text("carrie label", "CARRIE", (35, -35.8, 13.1), 7.4, accent)


def build_goal(mat):
    z0 = 12
    y = 23
    add_cylinder("goal left post", (-52, y, z0 + 21), 2.2, 42, mat)
    add_cylinder("goal right post", (52, y, z0 + 21), 2.2, 42, mat)
    add_cube("goal top rail", (0, y, z0 + 42), (108, 4, 4), mat, bevel=1.2)
    add_cube("goal bottom rail", (0, y, z0 + 4), (108, 3, 3), mat, bevel=1.0)
    for x in (-36, -18, 18, 36):
        add_cube(f"net vertical {x}", (x, y + 0.8, z0 + 23), (1.7, 1.8, 32), mat, bevel=0.45)
    for z in (z0 + 13, z0 + 23, z0 + 33):
        add_cube(f"net horizontal {z}", (0, y + 0.9, z), (88, 1.7, 1.7), mat, bevel=0.45)


def build_ball(mat, accent):
    add_sphere("soccer ball body", (0, -20, 19), (7.8, 7.8, 7.8), mat)
    for angle in (0, 60, 120):
        obj = add_curve(
            f"soccer panel {angle}",
            [(-5, -27.8, 19), (0, -28.5, 24), (5, -27.8, 19), (0, -28.5, 14), (-5, -27.8, 19)],
            accent,
            bevel_depth=0.22,
        )
        obj.rotation_euler[2] = radians(angle)


def build_person(person: dict, x: float, y: float, mat, accent):
    is_dan = person["id"] == "dan"
    height = float(person["target_height_mm"])
    head_w = float(person["head"]["width_mm"])
    torso_w = float(person["body"]["torso_width_mm"])
    torso_h = float(person["body"]["torso_height_mm"])
    base_z = 12
    shoe_z = base_z + 2.2
    leg_z = base_z + 9.0
    torso_z = base_z + 22.0
    head_z = base_z + height - 12.0
    face_y = y - 10.9

    add_sphere(f"{person['id']} torso", (x, y, torso_z), (torso_w / 2, 7.2, torso_h / 2), mat)
    add_cylinder(f"{person['id']} neck", (x, y, torso_z + torso_h / 2 + 1.2), 3.0, 3.0, mat)
    for dx in (-4.2, 4.2):
        add_cylinder(f"{person['id']} leg {dx}", (x + dx, y, leg_z), 2.7, 12, mat)
        add_sphere(f"{person['id']} shoe {dx}", (x + dx, y - 3.4, shoe_z), (4.4, 6.2, 2.0), mat)

    arm_side = torso_w / 2 + 2.0
    add_cylinder(f"{person['id']} left arm", (x - arm_side, y - 0.5, torso_z + 1), 2.2, 15.5, mat)
    add_sphere(f"{person['id']} left hand", (x - arm_side, y - 4, torso_z - 7), (2.5, 2.5, 2.5), mat)
    raised_x = x + arm_side
    add_curve(
        f"{person['id']} raised arm",
        [(raised_x, y - 1, torso_z + 5), (raised_x + 1.5, y - 4, torso_z + 14), (raised_x + 2.0, y - 5, torso_z + 22)],
        mat,
        bevel_depth=1.7,
    )
    add_sphere(f"{person['id']} raised hand", (raised_x + 2.0, y - 5, torso_z + 23), (2.7, 2.7, 2.7), mat)

    add_sphere(f"{person['id']} head", (x, y, head_z), (head_w / 2, head_w / 2 * 0.93, head_w / 2), mat)
    add_sphere(f"{person['id']} cheek left", (x - 5.5, face_y - 0.2, head_z - 3), (2.1, 1.2, 2.1), accent)
    add_sphere(f"{person['id']} cheek right", (x + 5.5, face_y - 0.2, head_z - 3), (2.1, 1.2, 2.1), accent)
    add_sphere(f"{person['id']} nose", (x, face_y - 0.8, head_z - 1.2), (1.7, 1.2, 1.7), accent)
    add_curve(
        f"{person['id']} smile",
        [(x - 3.5, face_y - 1.1, head_z - 5.7), (x, face_y - 1.5, head_z - 6.5), (x + 3.5, face_y - 1.1, head_z - 5.7)],
        accent,
        bevel_depth=0.42,
    )
    add_glasses(person["id"], x, face_y - 1.0, head_z + 1.5, accent)
    if is_dan:
        add_dan_hair(x, y, head_z, head_w, accent)
        add_text("dan jersey number", "10", (x, face_y - 0.5, torso_z + 1.2), 6.2, accent)
    else:
        add_carrie_hair(x, y, head_z, head_w, accent)
        add_text("carrie jersey heart", "♥", (x, face_y - 0.5, torso_z + 1.0), 7.0, accent)


def add_glasses(prefix: str, x: float, y: float, z: float, mat):
    for dx in (-4.2, 4.2):
        add_curve(f"{prefix} glasses {dx}", [(x + dx - 3.2, y, z - 2), (x + dx - 3.2, y, z + 2), (x + dx + 3.2, y, z + 2), (x + dx + 3.2, y, z - 2), (x + dx - 3.2, y, z - 2)], mat, bevel_depth=0.55)
        add_sphere(f"{prefix} eye {dx}", (x + dx, y - 0.4, z), (1.2, 0.7, 1.2), mat)
    add_curve(f"{prefix} glasses bridge", [(x - 1.1, y, z), (x + 1.1, y, z)], mat, bevel_depth=0.45)


def add_dan_hair(x: float, y: float, head_z: float, head_w: float, mat):
    add_sphere("dan hair cap", (x, y - 0.6, head_z + 7.5), (head_w / 2 * 0.95, head_w / 2 * 0.72, 4.8), mat)
    for idx, dx in enumerate((-7, -5, -2.5, 0, 2.5, 5, 7)):
        add_curve(
            f"dan swept hair ridge {idx}",
            [(x + dx - 1.5, y - 11.7, head_z + 7.4), (x + dx + 1.0, y - 12.2, head_z + 11.2)],
            mat,
            bevel_depth=0.65,
        )


def add_carrie_hair(x: float, y: float, head_z: float, head_w: float, mat):
    add_sphere("carrie hair cap", (x, y - 0.5, head_z + 4.5), (head_w / 2 * 1.06, head_w / 2 * 0.86, 8.0), mat)
    add_sphere("carrie left bob", (x - 9.2, y - 1.2, head_z - 3.0), (4.2, 4.0, 8.5), mat)
    add_sphere("carrie right bob", (x + 9.2, y - 1.2, head_z - 3.0), (4.2, 4.0, 8.5), mat)
    for idx, dx in enumerate((-6, -3, 0, 3, 6)):
        add_curve(
            f"carrie hair strand {idx}",
            [(x + dx - 3, y - 11.4, head_z + 8.0), (x + dx, y - 12.0, head_z + 3.5), (x + dx + 2.0, y - 11.7, head_z - 3.5)],
            mat,
            bevel_depth=0.36,
        )


def setup_camera_and_lights():
    bpy.ops.object.light_add(type="AREA", location=(0, -120, 120))
    light = bpy.context.object
    light.name = "large softbox"
    light.data.energy = 520
    light.data.size = 5
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.name = "review camera"
    camera.data.type = "ORTHO"
    bpy.context.scene.camera = camera
    bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
    bpy.context.scene.display.shading.light = "STUDIO"
    bpy.context.scene.display.shading.color_type = "MATERIAL"
    bpy.context.scene.render.resolution_x = 1400
    bpy.context.scene.render.resolution_y = 1000
    return camera


def look_at(camera, target):
    direction = Vector(target) - Vector(camera.location)
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def render_view(name: str, camera, output_dir: Path, loc, scale: float, target=(0, 0, 35)):
    camera.location = loc
    camera.data.ortho_scale = scale
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(output_dir / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def export_scene(output_dir: Path):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.wm.stl_export(filepath=str(output_dir / "scene.stl"), export_selected_objects=True)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    clear_scene()
    mat = material("single green PLA", GREEN)
    accent = material("raised relief shadow green", DARK_GREEN)
    build_base(mat, accent)
    build_goal(mat)
    build_ball(mat, accent)
    build_person({"id": "dan", "target_height_mm": 58, "head": {"width_mm": 24}, "body": {"torso_width_mm": 18, "torso_height_mm": 20}}, -20, -8, mat, accent)
    build_person({"id": "carrie", "target_height_mm": 54, "head": {"width_mm": 24}, "body": {"torso_width_mm": 23, "torso_height_mm": 18}}, 20, -8, mat, accent)
    camera = setup_camera_and_lights()
    render_view("front", camera, args.output_dir, (0, -190, 52), 92)
    render_view("front-angle", camera, args.output_dir, (105, -170, 70), 96)
    render_view("top", camera, args.output_dir, (0, 0, 250), 122, target=(0, 0, 0))
    render_view("dan-head", camera, args.output_dir, (-23, -118, 58), 33, target=(-20, -8, 54))
    render_view("carrie-head", camera, args.output_dir, (23, -118, 56), 33, target=(20, -8, 52))
    render_view("low-front", camera, args.output_dir, (0, -175, 28), 92, target=(0, -8, 36))
    export_scene(args.output_dir)


if __name__ == "__main__":
    main()
