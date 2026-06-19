"""Render the Blender-first v4 candidate and visual contact sheet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from bambu.blender_v4 import render_v4_candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--outputs-root", type=Path, default=Path("outputs"))
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    report = render_v4_candidate(args.project, outputs_root=args.outputs_root)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2))

    print("Blender v4 review")
    print("-----------------")
    print(f"project: {report['project']}")
    print(f"review dir: {report['review_dir']}")
    print(f"stl: {report['stl']}")
    if report["visual_contact_sheet"]:
        print(f"contact sheet: {report['visual_contact_sheet']['path']}")
    print(report["manual_boundary"])
    return 0 if report["blender"].get("ok") or not report["blender"].get("available") else 1


if __name__ == "__main__":
    raise SystemExit(main())
