"""Offline report tests. Synthetic PNG fixtures stay under the skill's output/."""
from pathlib import Path
import importlib.util
import json
import struct
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("render_batch_report", ROOT / "scripts/render_batch_report.py")
REPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPORT)


def png(color):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    raw = (b"\0" + bytes(color) * 720) * 720
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 720, 720, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


class ReportTests(unittest.TestCase):
    def setUp(self):
        base = ROOT / "output/test-runs/reports"
        base.mkdir(parents=True, exist_ok=True)
        self.run = Path(tempfile.mkdtemp(prefix="report-", dir=base))

    def variant(self, stem, color, qa_status="passed"):
        image = self.run / (stem + ".png")
        qa = self.run / (stem + ".json")
        image.parent.mkdir(parents=True, exist_ok=True)
        image.write_bytes(png(color))
        qa.write_text(json.dumps({"status": qa_status}), encoding="utf-8")
        return {"status": "accepted", "image": image.relative_to(self.run).as_posix(),
                "qa": qa.relative_to(self.run).as_posix()}

    def render(self, entries, expected=None):
        manifest = self.run / "manifest.json"
        manifest.write_text(json.dumps({"schema_version": 1, "character": "Synthetic report fixture",
                                       "expected_ids": expected or [e["no"] for e in entries],
                                       "entries": entries}), encoding="utf-8")
        return REPORT.build_report(manifest)

    def test_no_body_uses_one_image_and_counts_actual_files(self):
        entries = []
        for no in [1, 6, 7]:
            a = self.variant(f"default/{no}", [no, 30, 40, 255])
            body = {"mode": "reuse_default", "reason": "No extra body movement"}
            if no != 1:
                body = {"mode": "new_pose", **self.variant(f"body/{no}", [no, 90, 40, 255])}
            entries.append({"no": no, "zh": str(no), "default": a, "body_language": body})
        result = self.render(entries)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["counts"]["planned_png_files"], 5)
        self.assertEqual(result["counts"]["referenced_accepted_png_files"], 5)
        self.assertEqual(result["counts"]["unique_accepted_image_contents"], 5)
        self.assertEqual(result["counts"]["reuse_default"], 1)
        page = (self.run / "report/index.html").read_text(encoding="utf-8")
        self.assertEqual(page.count("<img "), 5)
        self.assertIn("沒有額外 PNG 圖檔", page)

    def test_duplicate_new_body_is_not_accepted(self):
        a = self.variant("default/1", [20, 30, 40, 255])
        b = self.variant("body/1", [20, 30, 40, 255])
        result = self.render([{"no": 1, "default": a, "body_language": {"mode": "new_pose", **b}}])
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["counts"]["body_accepted"], 0)
        self.assertEqual(result["counts"]["referenced_accepted_png_files"], 1)
        self.assertTrue(any("相同" in issue for issue in result["items"][0]["issues"]))

    def test_missing_required_body_stays_pending_not_reuse(self):
        a = self.variant("default/6", [50, 30, 40, 255])
        result = self.render([{"no": 6, "default": a, "body_language": {"mode": "new_pose", "status": "pending"}}])
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["counts"]["reuse_default"], 0)
        self.assertEqual(result["items"][0]["body_status"], "pending")

    def test_missing_qa_or_reason_cannot_complete(self):
        a = self.variant("default/1", [30, 50, 40, 255], qa_status="failed")
        result = self.render([{"no": 1, "default": a, "body_language": {"mode": "reuse_default"}}])
        self.assertEqual(result["counts"]["default_accepted"], 0)
        self.assertEqual(result["status"], "incomplete")

    def test_phase_order_and_missing_entries_are_reported(self):
        a = self.variant("default/6", [30, 50, 90, 255])
        b = self.variant("body/6", [60, 50, 90, 255])
        result = self.render([{"no": 6, "default": a, "body_language": {"mode": "new_pose", **b}}], [1, 6])
        self.assertTrue(result["phase_order_issue"])
        self.assertEqual(result["counts"]["unplanned"], 1)
        self.assertIsNone(result["counts"]["planned_png_files"])
        self.assertEqual(result["status"], "incomplete")

    def test_paths_and_force_cannot_replace_image(self):
        a = self.variant("default/1", [30, 50, 70, 255])
        entries = [{"no": 1, "default": a, "body_language": {"mode": "reuse_default", "reason": "No extra movement"}}]
        self.render(entries)
        original = (self.run / a["image"]).read_bytes()
        with self.assertRaises(ValueError):
            REPORT.build_report(self.run / "manifest.json", a["image"], force=True)
        self.assertEqual((self.run / a["image"]).read_bytes(), original)
        with self.assertRaises(ValueError):
            REPORT.build_report(self.run / "manifest.json", "../outside.html")
        with self.assertRaises(FileExistsError):
            REPORT.build_report(self.run / "manifest.json")

    def test_catalog_and_skill_entrypoints(self):
        catalog = (ROOT / "references/body-language-catalog-60.md").read_text(encoding="utf-8")
        self.assertEqual(catalog.count("| new_pose |"), 44)
        self.assertEqual(catalog.count("| reuse_default |"), 16)
        self.assertEqual((ROOT / "SKILL.md").read_bytes(), (ROOT / "SKILL_New.md").read_bytes())
        self.assertEqual((ROOT / "SKILL.md").read_bytes(), (ROOT / "SKILL_3RD.md").read_bytes())


if __name__ == "__main__":
    unittest.main()
