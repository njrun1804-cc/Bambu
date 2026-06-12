"""Command-line interface for the Bambu workbench."""

from __future__ import annotations

import argparse
from pathlib import Path
import shlex
import sys

from bambu.figurine import Figurine, Scene, generate_scad
from bambu.preflight import detect_tools, next_steps
from bambu.slicer import SliceRequest, build_slice_plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bambu",
        description="Agent-assisted 3D-print preparation for a Bambu Lab A1 mini.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Check local CAD/slicer tools and print next steps.")
    subparsers.add_parser("next", help="Print beginner-friendly next steps.")

    figurines = subparsers.add_parser(
        "make-figurines",
        help="Generate the default World Cup neighbor figurine OpenSCAD scene.",
    )
    figurines.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/world-cup-neighbors.scad"),
        help="Where to write the generated .scad file.",
    )

    slice_plan = subparsers.add_parser(
        "slice-plan",
        help="Print a dry-run slicer command for an STL or 3MF file.",
    )
    slice_plan.add_argument("model", type=Path, help="Input model path, usually an STL.")
    slice_plan.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/model.gcode.3mf"),
        help="Output .gcode.3mf path.",
    )
    slice_plan.add_argument(
        "--slicer",
        default="bambu-studio",
        choices=["bambu-studio", "orcaslicer", "orca"],
        help="Slicer CLI to plan for.",
    )

    prototype = subparsers.add_parser(
        "prototype-world-cup",
        help="Generate SCAD, export STL, and slice 3MF for the World Cup figurine prototype.",
    )
    prototype.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory for generated prototype files.",
    )
    prototype.add_argument(
        "--slicer",
        default="bambu-studio",
        choices=["bambu-studio", "orcaslicer", "orca"],
        help="Slicer CLI to run.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "doctor":
        return _doctor()
    if args.command == "next":
        return _next()
    if args.command == "make-figurines":
        return _make_figurines(args.output)
    if args.command == "slice-plan":
        return _slice_plan(args.model, args.output, args.slicer)
    if args.command == "prototype-world-cup":
        return _prototype_world_cup(args.output_dir, args.slicer)

    raise AssertionError(f"Unhandled command: {args.command}")


def _doctor() -> int:
    report = detect_tools()
    print("Bambu preflight")
    print("===============")
    labels = {
        "openscad": "OpenSCAD",
        "bambu_studio": "Bambu Studio",
        "orcaslicer": "OrcaSlicer",
        "blender": "Blender",
    }
    for key, status in report.items():
        marker = "ok" if status.available else "missing"
        detail = status.path if status.available else status.hint
        print(f"- {labels[key]}: {marker} - {detail}")
    print()
    _print_next_steps(report)
    return 0


def _prototype_world_cup(output_dir: Path, slicer: str) -> int:
    from bambu.pipeline import build_world_cup_prototype

    result = build_world_cup_prototype(output_dir, slicer=slicer)
    print("Prototype built")
    print("---------------")
    for key in ("scad", "stl", "sliced"):
        print(f"{key}: {result[key]}")
    print()
    print(result["manual_boundary"])
    return 0


def _next() -> int:
    _print_next_steps(detect_tools())
    return 0


def _print_next_steps(report: dict[str, object]) -> None:
    print("Next")
    print("----")
    for index, step in enumerate(next_steps(report), start=1):
        print(f"{index}. {step}")


def _make_figurines(output: Path) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generate_scad(default_world_cup_scene()))
    print(f"Wrote {output}")
    print("Next: open it in OpenSCAD, export STL, then run `bambu slice-plan <model.stl>`.")
    return 0


def _slice_plan(model: Path, output: Path, slicer: str) -> int:
    executable = _detected_slicer_path(slicer)
    plan = build_slice_plan(
        SliceRequest(
            model_path=model,
            output_path=output,
            slicer=slicer,
            executable=executable,
            resolve_paths=True,
        )
    )
    print("Slicer command")
    print("--------------")
    print(" ".join(shlex.quote(part) for part in plan.command))
    print()
    print("Checklist")
    print("---------")
    for item in plan.checklist:
        print(f"- {item}")
    return 0


def _detected_slicer_path(slicer: str) -> str | None:
    key = "orcaslicer" if slicer in {"orca", "orcaslicer"} else "bambu_studio"
    status = detect_tools().get(key)
    if status and status.available:
        return status.path
    return None


def default_world_cup_scene() -> Scene:
    return Scene(
        title="World Cup neighbors",
        figures=[
            Figurine(
                name="tall_neighbor",
                height_mm=72,
                body_shape="slim",
                hair="short gray hair",
                accessories=["glasses"],
                jersey_number="10",
            ),
            Figurine(
                name="smiling_neighbor",
                height_mm=64,
                body_shape="curvy",
                hair="short light hair",
                accessories=["sunglasses"],
                jersey_number="9",
            ),
        ],
    )


if __name__ == "__main__":
    sys.exit(main())
