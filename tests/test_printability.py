import json
import struct
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile


def write_stl(path: Path, facets: list[tuple[tuple[float, float, float], ...]]) -> None:
    with open(path, "wb") as handle:
        handle.write(b"\0" * 80)
        handle.write(struct.pack("<I", len(facets)))
        for a, b, c in facets:
            handle.write(struct.pack("<3f", 0, 0, 0))
            for vertex in (a, b, c):
                handle.write(struct.pack("<3f", *vertex))
            handle.write(struct.pack("<H", 0))


CONTEXT = {
    "printer": {"nozzle_mm": 0.4},
    "materials": [
        {
            "name": "Bambu PLA Basic",
            "filament_type": "PLA",
            "density_g_cm3": 1.24,
            "owned_spools": [{"color": "green"}],
        }
    ],
}


def write_sliced_3mf(path: Path, *, support_used: str = "false", filament_type: str = "PLA") -> None:
    slice_info = f"""<?xml version="1.0" encoding="UTF-8"?>
<config>
  <plate>
    <metadata key="index" value="1"/>
    <metadata key="nozzle_diameters" value="0.4"/>
    <metadata key="prediction" value="25560"/>
    <metadata key="outside" value="false"/>
    <metadata key="support_used" value="{support_used}"/>
    <filament id="1" type="{filament_type}" color="#00AE42" used_m="18.43" used_g="0.00"/>
  </plate>
</config>
"""
    plate = {"bed_type": "textured_plate", "bbox_all": [55, 27, 123, 152]}
    with ZipFile(path, "w") as archive:
        archive.writestr("Metadata/slice_info.config", slice_info)
        archive.writestr("Metadata/plate_1.json", json.dumps(plate))
        archive.writestr("Metadata/plate_1.gcode", "; gcode\n")


class OverhangAnalysisTests(unittest.TestCase):
    def test_flat_downward_patch_counts_as_bridge_not_steep(self):
        from bambu.printability import analyze_stl_overhangs

        # One horizontal downward-facing triangle floating at z=20.
        facets = [((0, 0, 20), (10, 10, 20), (10, 0, 20))]
        with tempfile.TemporaryDirectory() as tmp:
            stl = Path(tmp) / "bridge.stl"
            write_stl(stl, facets)
            report = analyze_stl_overhangs(stl)

        self.assertTrue(report["ok"])
        self.assertEqual(report["largest_steep_patch_mm2"], 0.0)
        self.assertEqual(report["bridge_area_mm2"], 50.0)

    def test_large_steep_patch_fails_budget(self):
        from bambu.printability import analyze_stl_overhangs

        # A shallow downward-facing ramp (rise 1 over run 2): its underside
        # normal is ~63 degrees past vertical, well into droop territory.
        facets = []
        for i in range(10):
            x0 = i * 2.0
            lo, hi = 20.0 + x0 * 0.5, 20.0 + (x0 + 2.0) * 0.5
            a, b = (x0, 0, lo), (x0 + 2, 0, hi)
            c, d = (x0 + 2, 5, hi), (x0, 5, lo)
            facets.append((a, c, b))
            facets.append((a, d, c))
        with tempfile.TemporaryDirectory() as tmp:
            stl = Path(tmp) / "steep.stl"
            write_stl(stl, facets)
            report = analyze_stl_overhangs(stl, patch_budget_mm2=50.0)

        self.assertFalse(report["ok"])
        self.assertEqual(report["patch_count"], 1)
        self.assertGreater(report["largest_steep_patch_mm2"], 50.0)

    def test_plate_touching_faces_are_exempt(self):
        from bambu.printability import analyze_stl_overhangs

        facets = [((0, 0, 0), (10, 10, 0), (10, 0, 0))]  # base bottom
        with tempfile.TemporaryDirectory() as tmp:
            stl = Path(tmp) / "base.stl"
            write_stl(stl, facets)
            report = analyze_stl_overhangs(stl)

        self.assertTrue(report["ok"])
        self.assertEqual(report["flagged_area_mm2"], 0.0)


class SlicedQcTests(unittest.TestCase):
    def test_clean_sliced_file_passes_with_owned_filament(self):
        from bambu.printability import qc_sliced_3mf

        with tempfile.TemporaryDirectory() as tmp:
            sliced = Path(tmp) / "model.gcode.3mf"
            write_sliced_3mf(sliced)
            report = qc_sliced_3mf(sliced, context=CONTEXT)

        self.assertTrue(report["ok"], report["failures"])
        self.assertEqual(report["facts"]["print_time"], "7h06m")
        self.assertAlmostEqual(report["facts"]["filament_g_estimate"], 55.0, delta=0.5)

    def test_supports_or_unowned_filament_fail(self):
        from bambu.printability import qc_sliced_3mf

        with tempfile.TemporaryDirectory() as tmp:
            supported = Path(tmp) / "supported.gcode.3mf"
            write_sliced_3mf(supported, support_used="true")
            report = qc_sliced_3mf(supported, context=CONTEXT)
            self.assertFalse(report["ok"])
            self.assertFalse(report["checks"]["supportless"])

            abs_file = Path(tmp) / "abs.gcode.3mf"
            write_sliced_3mf(abs_file, filament_type="ABS")
            report = qc_sliced_3mf(abs_file, context=CONTEXT)
            self.assertFalse(report["ok"])
            self.assertFalse(report["checks"]["filament_type_owned"])


if __name__ == "__main__":
    unittest.main()
