"""Regression checks for pixel-locked portrait differences; no image API calls."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image, ImageChops, ImageDraw

SCRIPT = Path(__file__).with_name("compose_expression_patch.py")
spec = importlib.util.spec_from_file_location("expression_patch", SCRIPT)
patch_tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch_tool)
ARTIFACTS = SCRIPT.parent.parent / "output/test-runs/compose"


class ExpressionPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        cls.root = Path(tempfile.mkdtemp(prefix="pixel-lock-", dir=ARTIFACTS))

    def setUp(self):
        self.folder = self.root / self._testMethodName
        self.folder.mkdir()
        self.base_path = self.folder / "base.png"
        self.mask_path = self.folder / "mask-input.png"
        self.patch_path = self.folder / "patch.png"
        self.out = self.folder / "final.png"
        self.base = Image.new("RGBA", (720, 720), (3, 255, 4, 0))
        ImageDraw.Draw(self.base).rectangle((160, 100, 560, 710), fill=(10, 20, 30, 255))
        self.base.save(self.base_path)
        mask = Image.new("L", (720, 720), 0)
        ImageDraw.Draw(mask).rectangle((254, 204, 265, 215), fill=255)
        mask.putpixel((255, 205), 128)
        mask.save(self.mask_path)
        Image.new("RGBA", (20, 20), (210, 40, 30, 255)).save(self.patch_path)
        self.contract_path = self.folder / "region" / "patch_contract.json"

    def prepare(self, **changes):
        values = dict(base=self.base_path, mask=self.mask_path, box=[250, 200, 270, 220], pose_id="test-pose", alpha_mode="preserve", output_dir=self.contract_path.parent, force=False)
        values.update(changes)
        return patch_tool.prepare(argparse.Namespace(**values))

    def compose(self, **changes):
        values = dict(contract=self.contract_path, patch=self.patch_path, output=self.out, green_output=None, report=None, resize_patch=False, force=False)
        values.update(changes)
        return patch_tool.compose(argparse.Namespace(**values))

    def verify(self, **changes):
        values = dict(contract=self.contract_path, candidate=self.out, report=None, force=False)
        values.update(changes)
        return patch_tool.verify(argparse.Namespace(**values))

    def test_composition_locks_all_rgba_channels_and_base_file(self):
        original = self.base_path.read_bytes()
        self.prepare()
        result = self.compose(green_output=self.folder / "green.png")
        mask = Image.open(self.mask_path)
        out = Image.open(self.out)
        for b, c, m in zip(self.base.get_flattened_data(), out.get_flattened_data(), mask.get_flattened_data()):
            if m == 0:
                self.assertEqual(b, c)
        self.assertEqual(original, self.base_path.read_bytes())
        self.assertEqual(result["outside_mask_changed_pixels"], 0)
        self.assertGreater(result["changed_pixels"], 0)
        self.assertEqual(Image.open(self.folder / "green.png").getpixel((0, 0)), (0, 255, 0))

    def test_feather_is_local_and_preserves_alpha(self):
        self.prepare()
        result = self.compose()
        out = Image.open(self.out)
        self.assertEqual(out.getpixel((255, 205)), (110, 30, 30, 255))
        self.assertEqual(out.getpixel((256, 205)), (210, 40, 30, 255))
        self.assertEqual(out.getpixel((253, 205)), self.base.getpixel((253, 205)))
        self.assertEqual(result["alpha_changed_pixels"], 0)

    def test_hidden_rgb_change_outside_mask_fails_cli(self):
        self.prepare()
        self.compose()
        out = Image.open(self.out)
        out.putpixel((0, 0), (4, 255, 4, 0))
        out.save(self.out)
        run = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPT), "verify", "--contract", str(self.contract_path), "--candidate", str(self.out)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(run.returncode, 1)
        report = json.loads(run.stdout)
        self.assertEqual(report["outside_mask_changed_pixels"], 1)
        self.assertEqual(report["first_outside_change"], [0, 0])

    def test_one_pixel_whole_portrait_shift_fails(self):
        self.prepare()
        self.compose()
        ImageChops.offset(Image.open(self.out), 1, 0).save(self.out)
        self.assertEqual(self.verify()["status"], "failed")

    def test_changed_base_invalidates_contract(self):
        self.prepare()
        changed = self.base.copy()
        changed.putpixel((0, 0), (0, 0, 0, 0))
        changed.save(self.base_path)
        with self.assertRaises(ValueError):
            self.compose()
        self.assertFalse(self.out.exists())

    def test_changed_mask_invalidates_contract(self):
        self.prepare()
        path = self.contract_path.parent / "editable_mask.png"
        mask = Image.open(path)
        mask.putpixel((256, 205), 0)
        mask.save(path)
        with self.assertRaises(ValueError):
            self.compose()

    def test_wrong_patch_dimensions_are_rejected_without_resizing(self):
        self.prepare()
        Image.new("RGB", (40, 40), "red").save(self.patch_path)
        with self.assertRaises(ValueError):
            self.compose()
        self.assertFalse(self.out.exists())

    def test_explicit_same_aspect_patch_resize_is_recorded(self):
        self.prepare()
        Image.new("RGB", (40, 40), "red").save(self.patch_path)
        result = self.compose(resize_patch=True)
        self.assertTrue(result["patch_resized"])
        self.assertEqual(result["patch_original_size"], [40, 40])
        self.assertEqual(result["outside_mask_changed_pixels"], 0)

    def test_nonuniform_patch_stretch_is_rejected(self):
        self.prepare()
        Image.new("RGB", (20, 30), "red").save(self.patch_path)
        with self.assertRaises(ValueError):
            self.compose(resize_patch=True)

    def test_preserve_mode_rejects_transparent_face_patch(self):
        self.prepare()
        Image.new("RGBA", (20, 20), (255, 0, 0, 100)).save(self.patch_path)
        with self.assertRaises(ValueError):
            self.compose()
        self.assertFalse(self.out.exists())

    def test_preserve_mode_rejects_mask_on_transparent_background(self):
        mask = Image.new("L", (720, 720), 0)
        mask.putpixel((5, 5), 255)
        mask.save(self.mask_path)
        with self.assertRaises(ValueError):
            self.prepare(box=[0, 0, 20, 20])

    def test_blend_mode_adds_soft_local_mark_without_green_contamination(self):
        mask = Image.new("L", (720, 720), 0)
        mask.putpixel((5, 5), 255)
        mask.putpixel((6, 5), 128)
        mask.save(self.mask_path)
        self.prepare(box=[0, 0, 20, 20], alpha_mode="blend")
        Image.new("RGBA", (20, 20), (255, 0, 0, 128)).save(self.patch_path)
        report = self.compose()
        out = Image.open(self.out)
        self.assertEqual(out.getpixel((5, 5)), (255, 0, 0, 128))
        self.assertEqual(out.getpixel((6, 5)), (255, 0, 0, 64))
        self.assertEqual(out.getpixel((7, 5)), self.base.getpixel((7, 5)))
        self.assertEqual(report["alpha_changed_pixels"], 2)
        self.assertEqual(report["outside_mask_changed_pixels"], 0)

    def test_empty_mask_is_rejected(self):
        Image.new("L", (720, 720), 0).save(self.mask_path)
        with self.assertRaises(ValueError):
            self.prepare()

    def test_mask_feather_outside_roi_is_rejected(self):
        mask = Image.open(self.mask_path)
        mask.putpixel((249, 205), 1)
        mask.save(self.mask_path)
        with self.assertRaises(ValueError):
            self.prepare()

    def test_force_does_not_allow_overwriting_base(self):
        self.prepare()
        before = hashlib.sha256(self.base_path.read_bytes()).hexdigest()
        with self.assertRaises(ValueError):
            self.compose(output=self.base_path, force=True)
        self.assertEqual(hashlib.sha256(self.base_path.read_bytes()).hexdigest(), before)

    def test_alpha_change_inside_face_mask_is_rejected(self):
        self.prepare()
        self.compose()
        out = Image.open(self.out)
        out.putpixel((256, 205), (210, 40, 30, 128))
        out.save(self.out)
        report = self.verify()
        self.assertEqual(report["outside_mask_changed_pixels"], 0)
        self.assertEqual(report["alpha_changed_pixels"], 1)
        self.assertEqual(report["status"], "failed")

    def test_report_cannot_overwrite_candidate(self):
        self.prepare()
        self.compose()
        with self.assertRaises(ValueError):
            self.verify(report=self.out, force=True)

    def test_existing_deliverable_is_not_overwritten_by_default(self):
        self.prepare()
        self.compose()
        before = self.out.read_bytes()
        with self.assertRaises(ValueError):
            self.compose()
        self.assertEqual(self.out.read_bytes(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
