"""Agent-safe 3D review workflow for generated CAD artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

from bambu.cad import export_build123d_project
from bambu.projects import sync_project_artifacts


FREECAD_JSON_BEGIN = "FREECAD_REVIEW_JSON_BEGIN"
FREECAD_JSON_END = "FREECAD_REVIEW_JSON_END"
REVIEW_VIEW_ORDER = ("front", "front-angle", "dan-head", "carrie-head", "top", "low-front", "rear-angle")

# Fractional crops for the ChatGPT concept sheet stored under references/ai-concepts.
# They turn the sheet into direct target-vs-current comparisons instead of a tiny moodboard.
DEFAULT_TARGET_CROPS = {
    "front": (0.350, 0.075, 0.530, 0.472),
    "front-angle": (0.530, 0.075, 0.705, 0.472),
    "dan-head": (0.710, 0.075, 0.815, 0.260),
    "carrie-head": (0.710, 0.270, 0.815, 0.472),
    "top": (0.820, 0.075, 0.985, 0.472),
}


@dataclass(frozen=True)
class FreeCADInstall:
    available: bool
    app: Path | None
    binary: Path | None
    env: dict[str, str]
    reason: str = ""

    @property
    def command(self) -> list[str]:
        if self.binary is None:
            return []
        return [str(self.binary), "-c"]


def detect_freecad(candidates: list[Path] | None = None, *, runtime_root: Path = Path(".freecad-runtime")) -> FreeCADInstall:
    """Detect FreeCAD.app and return a console-mode execution environment."""

    env_bin = os.environ.get("FREECAD_BIN")
    if env_bin:
        binary = Path(env_bin)
        if binary.exists():
            return _freecad_install(binary, app=None, runtime_root=runtime_root)
        return FreeCADInstall(False, None, None, {}, f"FREECAD_BIN does not exist: {binary}")

    app_candidates = candidates or [Path("/Applications/FreeCAD.app")]
    for app in app_candidates:
        binary = app / "Contents" / "MacOS" / "FreeCAD"
        if binary.exists():
            return _freecad_install(binary, app=app, runtime_root=runtime_root)

    return FreeCADInstall(False, None, None, {}, "FreeCAD.app not found")


def inspect_step_with_freecad(
    step_path: Path,
    output_json: Path,
    *,
    freecad: FreeCADInstall | None = None,
    script: Path = Path("tools/freecad_review.py"),
) -> dict[str, Any]:
    """Inspect a STEP file using FreeCAD console mode and return its JSON report."""

    install = freecad or detect_freecad()
    if not install.available:
        return {"available": False, "reason": install.reason}
    if not step_path.exists():
        raise FileNotFoundError(step_path)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    command = install.command + [
        str(script.resolve()),
        "--pass",
        str(step_path.resolve()),
        str(output_json.resolve()),
    ]
    completed = subprocess.run(command, check=False, text=True, capture_output=True, env=install.env)
    if output_json.exists():
        parsed = json.loads(output_json.read_text())
        parsed.setdefault("available", True)
        parsed["freecad_returncode"] = completed.returncode
        if completed.stderr:
            parsed["freecad_stderr_tail"] = completed.stderr[-1000:]
        return parsed
    if completed.returncode != 0:
        return {
            "available": True,
            "ok": False,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "warnings": ["freecad launch failed"],
        }
    parsed = parse_freecad_json(completed.stdout + "\n" + completed.stderr)
    parsed.setdefault("available", True)
    parsed["freecad_returncode"] = completed.returncode
    return parsed


def parse_freecad_json(output: str) -> dict[str, Any]:
    """Extract the marked FreeCAD JSON payload from noisy console output."""

    if FREECAD_JSON_BEGIN not in output or FREECAD_JSON_END not in output:
        raise ValueError("FreeCAD review JSON markers not found")
    payload = output.split(FREECAD_JSON_BEGIN, 1)[1].split(FREECAD_JSON_END, 1)[0].strip()
    return json.loads(payload)


def detect_blender() -> str | None:
    """Return a usable Blender executable path if available."""

    return shutil.which("blender") or (
        "/opt/homebrew/bin/blender" if Path("/opt/homebrew/bin/blender").exists() else None
    )


def build_blender_preview_command(*, blender: str, stl: Path, output_dir: Path) -> list[str]:
    """Build a read-only Blender preview command for an STL."""

    script = f"""
import bpy
from mathutils import Vector
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.wm.stl_import(filepath={str(stl)!r})
obj = bpy.context.object
bpy.context.view_layer.update()
coords = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
min_v = Vector((min(v.x for v in coords), min(v.y for v in coords), min(v.z for v in coords)))
max_v = Vector((max(v.x for v in coords), max(v.y for v in coords), max(v.z for v in coords)))
center = (min_v + max_v) / 2
obj.location -= Vector((center.x, center.y, min_v.z))
mat = bpy.data.materials.new('Green PLA preview')
mat.diffuse_color = (0.03, 0.90, 0.25, 1.0)
obj.data.materials.append(mat)
bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.display.shading.light = 'STUDIO'
bpy.context.scene.display.shading.color_type = 'MATERIAL'
bpy.context.scene.render.resolution_x = 1400
bpy.context.scene.render.resolution_y = 1000
bpy.ops.object.camera_add()
cam = bpy.context.object
bpy.context.scene.camera = cam
cam.data.type = 'ORTHO'
def look_at(target):
    direction = Vector(target) - Vector(cam.location)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
def render(name, loc, scale, target=(0, 0, 32)):
    cam.location = loc
    cam.data.ortho_scale = scale
    look_at(target)
    bpy.context.scene.render.filepath = {str(output_dir)!r} + '/' + name + '.png'
    bpy.ops.render.render(write_still=True)
render('front', (0, -220, 48), 138)
render('front-angle', (120, -190, 75), 145)
render('rear-angle', (-120, 190, 75), 145)
render('top', (0, 0, 260), 132, target=(0, 0, 0))
render('dan-head', (-22, -125, 62), 38, target=(-18, -10, 52))
render('carrie-head', (24, -125, 58), 38, target=(19, -10, 49))
render('low-front', (0, -210, 26), 132, target=(0, -8, 36))
"""
    return [blender, "--background", "--python-expr", script]


def build_visual_contact_sheet(
    *,
    target_images: dict[str, Path],
    current_images: dict[str, Path],
    output_path: Path,
    title: str,
) -> dict[str, Any]:
    """Build a simple target-vs-current review sheet from rendered PNGs."""

    from PIL import Image, ImageDraw, ImageFont

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cell_w = 420
    cell_h = 280
    margin = 24
    title_h = 64
    label_h = 28
    rows = max(len(target_images), len(current_images), 1)
    width = margin * 3 + cell_w * 2
    height = title_h + margin + rows * (cell_h + label_h + margin)
    sheet = Image.new("RGB", (width, height), (246, 245, 239))
    draw = ImageDraw.Draw(sheet)
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 26)
        label_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 17)
    except OSError:
        title_font = ImageFont.load_default()
        label_font = ImageFont.load_default()

    draw.text((margin, 20), title, fill=(24, 52, 28), font=title_font)
    draw.text((margin, title_h), "TARGET", fill=(45, 80, 45), font=label_font)
    draw.text((margin * 2 + cell_w, title_h), "CURRENT CAD", fill=(45, 80, 45), font=label_font)

    labels = [name for name in REVIEW_VIEW_ORDER if name in target_images or name in current_images]
    labels.extend(name for name in target_images if name not in labels)
    labels.extend(name for name in current_images if name not in labels)
    rows = max(len(labels), 1)
    height = title_h + margin + rows * (cell_h + label_h + margin)
    sheet = Image.new("RGB", (width, height), (246, 245, 239))
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, 20), title, fill=(24, 52, 28), font=title_font)
    draw.text((margin, title_h), "TARGET", fill=(45, 80, 45), font=label_font)
    draw.text((margin * 2 + cell_w, title_h), "CURRENT CAD", fill=(45, 80, 45), font=label_font)

    for idx, label in enumerate(labels):
        y = title_h + margin + idx * (cell_h + label_h + margin)
        if label in target_images:
            _paste_labeled_image(sheet, draw, (label, target_images[label]), margin, y, cell_w, cell_h, label_font)
        if label in current_images:
            _paste_labeled_image(
                sheet, draw, (label, current_images[label]), margin * 2 + cell_w, y, cell_w, cell_h, label_font
            )

    sheet.save(output_path)
    return {"path": str(output_path), "width": width, "height": height, "rows": rows}


def build_target_review_crops(
    target_image: Path,
    output_dir: Path,
    *,
    crop_regions: dict[str, tuple[float, float, float, float]] | None = None,
) -> dict[str, Path]:
    """Crop a design-sheet target into review views aligned with Blender cameras."""

    from PIL import Image

    output_dir.mkdir(parents=True, exist_ok=True)
    crops = crop_regions or DEFAULT_TARGET_CROPS
    results: dict[str, Path] = {}
    with Image.open(target_image).convert("RGB") as image:
        width, height = image.size
        for name, region in crops.items():
            left, top, right, bottom = region
            box = (
                max(0, round(left * width)),
                max(0, round(top * height)),
                min(width, round(right * width)),
                min(height, round(bottom * height)),
            )
            if box[2] <= box[0] or box[3] <= box[1]:
                continue
            path = output_dir / f"{name}.png"
            image.crop(box).save(path)
            results[name] = path
    return results


def _paste_labeled_image(
    sheet: Any,
    draw: Any,
    item: tuple[str, Path],
    x: int,
    y: int,
    cell_w: int,
    cell_h: int,
    font: Any,
) -> None:
    from PIL import Image

    label, path = item
    with Image.open(path).convert("RGB") as image:
        image.thumbnail((cell_w, cell_h))
        bg = Image.new("RGB", (cell_w, cell_h), (226, 228, 218))
        px = (cell_w - image.width) // 2
        py = (cell_h - image.height) // 2
        bg.paste(image, (px, py))
        sheet.paste(bg, (x, y))
    draw.rectangle((x, y, x + cell_w, y + cell_h), outline=(160, 166, 150), width=1)
    draw.text((x, y + cell_h + 6), label, fill=(35, 45, 35), font=font)


def render_blender_previews(stl: Path, output_dir: Path, *, blender: str | None = None) -> dict[str, Any]:
    """Render preview PNGs through Blender if available."""

    executable = blender or detect_blender()
    if not executable:
        return {"available": False, "reason": "Blender not found", "paths": []}
    output_dir.mkdir(parents=True, exist_ok=True)
    command = build_blender_preview_command(blender=executable, stl=stl, output_dir=output_dir)
    completed = subprocess.run(command, check=False, text=True, capture_output=True)
    paths = sorted(str(path) for path in output_dir.glob("*.png"))
    return {
        "available": True,
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "paths": paths,
        "stderr_tail": completed.stderr[-1000:],
    }


def review_project_3d(
    project_path: Path | str,
    *,
    outputs_root: Path = Path("outputs"),
    render: bool = True,
    source_file: Path | None = None,
    output_slug: str | None = None,
    target_image: Path | None = None,
) -> dict[str, Any]:
    """Export, inspect, render, and summarize a project without printer contact."""

    project = Path(project_path)
    export = export_build123d_project(project, output_dir=outputs_root, source_file=source_file, output_slug=output_slug)
    if source_file is None and output_slug is None:
        artifacts = sync_project_artifacts(project, outputs_root=outputs_root)
    else:
        artifacts = {"artifacts": []}
    step = Path(export["step"])
    stl = Path(export["stl"])
    review_dir = outputs_root / "review" / export["project_slug"]
    freecad_report = inspect_step_with_freecad(step, review_dir / "freecad_review.json")
    blender_report = render_blender_previews(stl, review_dir) if render else {"available": False, "paths": []}
    contact_sheet: dict[str, Any] | None = None
    if target_image is not None and blender_report.get("paths"):
        current_images = {
            Path(path).stem: Path(path)
            for path in blender_report["paths"]
            if Path(path).exists() and Path(path).suffix.lower() == ".png"
        }
        if current_images:
            target_images = build_target_review_crops(target_image, review_dir / "target-crops")
            contact_sheet = build_visual_contact_sheet(
                target_images=target_images or {"target concept sheet": target_image},
                current_images=current_images,
                output_path=review_dir / "visual-contact-sheet.png",
                title=f"{export['project_slug']} target vs current CAD",
            )
    return {
        "project": export["project_slug"],
        "step": str(step),
        "stl": str(stl),
        "bounding_box_mm": export["bounding_box_mm"],
        "fits_a1_mini": export["fits_a1_mini"],
        "freecad": freecad_report,
        "blender": blender_report,
        "visual_contact_sheet": contact_sheet,
        "artifact_count": len(artifacts.get("artifacts", [])),
        "printer_contact": False,
        "manual_boundary": "No printer contact. Review CAD, previews, slicer settings, and supports manually.",
    }


def _freecad_install(binary: Path, *, app: Path | None, runtime_root: Path) -> FreeCADInstall:
    runtime = runtime_root.resolve()
    home = runtime / "home"
    data = runtime / "data"
    temp = runtime / "temp"
    for path in (home, data, temp):
        path.mkdir(parents=True, exist_ok=True)
    resources = binary.parents[1] / "Resources"
    env = {
        "HOME": str(home),
        "PATH": "/usr/bin:/bin:/opt/homebrew/bin",
        "FREECAD_USER_HOME": str(home),
        "FREECAD_USER_DATA": str(data),
        "FREECAD_USER_TEMP": str(temp),
        "PYTHONHOME": str(resources),
        "PYTHONPATH": str(resources),
        "LD_LIBRARY_PATH": str(resources / "lib"),
        "SSL_CERT_FILE": str(resources / "ssl" / "cacert.pem"),
        "GIT_SSL_CAINFO": str(resources / "ssl" / "cacert.pem"),
    }
    return FreeCADInstall(True, app, binary, env)
