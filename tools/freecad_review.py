"""Run inside FreeCAD console mode to inspect a STEP file."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import FreeCAD as App  # type: ignore
import Part  # type: ignore


BEGIN = "FREECAD_REVIEW_JSON_BEGIN"
END = "FREECAD_REVIEW_JSON_END"


def main() -> int:
    input_step, output_json = _paths_from_args()
    shape = Part.Shape()
    shape.read(str(input_step))
    report = inspect_shape(shape, input_step)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2) + "\n")
    print(BEGIN)
    print(json.dumps(report, sort_keys=True))
    print(END)
    return 0 if report["ok"] else 2


def inspect_shape(shape, input_step: Path) -> dict:
    geometry_check_error = ""
    try:
        shape.check(True)
    except TypeError:
        try:
            shape.check()
        except Exception as error:  # pragma: no cover - FreeCAD-specific path
            geometry_check_error = str(error)
    except Exception as error:  # pragma: no cover - FreeCAD-specific path
        geometry_check_error = str(error)

    vertices, facets = shape.tessellate(0.2)
    bbox = shape.BoundBox
    center = getattr(shape, "CenterOfMass", None) or getattr(shape, "CenterOfGravity", None)
    center_of_mass = [float(center.x), float(center.y), float(center.z)] if center is not None else []
    report = {
        "available": True,
        "freecad_version": App.ConfigGet("ExeVersion"),
        "input_step": str(input_step),
        "shape_type": shape.ShapeType,
        "is_null": bool(shape.isNull()),
        "is_valid": bool(shape.isValid()),
        "is_closed": bool(shape.isClosed()),
        "counts": {
            "solids": len(shape.Solids),
            "shells": len(shape.Shells),
            "faces": len(shape.Faces),
            "edges": len(shape.Edges),
            "wires": len(shape.Wires),
            "vertices": len(shape.Vertexes),
        },
        "bbox_mm": {
            "x": float(bbox.XLength),
            "y": float(bbox.YLength),
            "z": float(bbox.ZLength),
            "xmin": float(bbox.XMin),
            "xmax": float(bbox.XMax),
            "ymin": float(bbox.YMin),
            "ymax": float(bbox.YMax),
            "zmin": float(bbox.ZMin),
            "zmax": float(bbox.ZMax),
        },
        "volume": float(shape.Volume),
        "area": float(shape.Area),
        "center_of_mass": center_of_mass,
        "geometry_check_error": geometry_check_error,
        "tessellation": {
            "vertices": len(vertices),
            "facets": len(facets),
        },
    }
    report["warnings"] = _warnings(report)
    report["ok"] = not report["warnings"]
    return report


def _paths_from_args() -> tuple[Path, Path]:
    if "--pass" in sys.argv:
        index = sys.argv.index("--pass")
        try:
            return Path(sys.argv[index + 1]), Path(sys.argv[index + 2])
        except IndexError as error:
            raise SystemExit("--pass requires input STEP and output JSON") from error
    if os.environ.get("FREECAD_INPUT_STEP") and os.environ.get("FREECAD_OUTPUT_JSON"):
        return Path(os.environ["FREECAD_INPUT_STEP"]), Path(os.environ["FREECAD_OUTPUT_JSON"])
    raise SystemExit("Provide --pass <input.step> <output.json> or FREECAD_INPUT_STEP/FREECAD_OUTPUT_JSON")


def _warnings(report: dict) -> list[str]:
    warnings: list[str] = []
    if report["is_null"]:
        warnings.append("shape is null")
    if not report["is_valid"]:
        warnings.append("shape is not valid")
    if report["counts"]["solids"] == 0:
        warnings.append("no solids found")
    if report["volume"] <= 0:
        warnings.append("volume is not positive")
    if report["bbox_mm"]["x"] <= 0 or report["bbox_mm"]["y"] <= 0 or report["bbox_mm"]["z"] <= 0:
        warnings.append("bounding box has non-positive dimension")
    if report["bbox_mm"]["x"] > 180 or report["bbox_mm"]["y"] > 180 or report["bbox_mm"]["z"] > 180:
        warnings.append("bounding box exceeds A1 mini build volume")
    if report["geometry_check_error"]:
        warnings.append("geometry check error")
    return warnings


raise SystemExit(main())
