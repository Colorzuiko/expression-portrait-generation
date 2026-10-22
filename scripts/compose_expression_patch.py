#!/usr/bin/env python3
"""Prepare, compose and verify fixed-position portrait expression patches (Pillow)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image

SIZE = (720, 720)
SCHEMA = "expression-patch-v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_png(path: Path, modes: tuple[str, ...]) -> Image.Image:
    with Image.open(path) as source:
        if source.format != "PNG" or source.mode not in modes:
            raise ValueError(f"{path}: expected PNG in {modes}, got {source.format}/{source.mode}")
        return source.copy()


def output_paths(paths: list[Path], inputs: list[Path], force: bool) -> None:
    resolved = [p.resolve() for p in paths]
    if len(set(resolved)) != len(resolved):
        raise ValueError("Output, green output and report paths must be distinct")
    protected = {p.resolve() for p in inputs}
    for path, target in zip(paths, resolved):
        if target in protected:
            raise ValueError(f"Refusing to overwrite an input: {path}")
        if path.exists() and not force:
            raise ValueError(f"Output exists; use --force intentionally: {path}")


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_geometry(base: Image.Image, mask: Image.Image, box: list[int], alpha_mode: str) -> None:
    if base.size != SIZE or mask.size != SIZE:
        raise ValueError("Base and full-canvas mask must both be 720x720")
    if len(box) != 4 or any(type(n) is not int for n in box):
        raise ValueError("Box must contain four integer coordinates: left top right bottom")
    left, top, right, bottom = box
    if not (0 <= left < right <= 720 and 0 <= top < bottom <= 720):
        raise ValueError("Box must be a nonempty rectangle inside the base canvas")
    support = mask.getbbox()
    if support is None:
        raise ValueError("Mask is empty: white/gray pixels must mark the editable region")
    if not (left <= support[0] and top <= support[1] and support[2] <= right and support[3] <= bottom):
        raise ValueError("All nonzero mask pixels, including feathering, must be inside the box")
    if alpha_mode not in ("preserve", "blend"):
        raise ValueError("Unsupported alpha mode")
    if alpha_mode == "preserve":
        for weight, alpha in zip(mask.get_flattened_data(), base.getchannel("A").get_flattened_data()):
            if weight and alpha != 255:
                raise ValueError("Preserve mode requires the edit mask to stay on opaque foreground; use a separate blend contract for marks extending into transparency")


def prepare(args: argparse.Namespace) -> dict:
    base_path = args.base.resolve()
    base = load_png(base_path, ("RGBA",))
    mask = load_png(args.mask, ("L",))
    validate_geometry(base, mask, args.box, args.alpha_mode)
    folder = args.output_dir.resolve()
    contract_path = folder / "patch_contract.json"
    mask_path = folder / "editable_mask.png"
    context = folder / "context.png"
    mask_context = folder / "mask_context.png"
    outputs = [contract_path, mask_path, context, mask_context]
    output_paths(outputs, [base_path, args.mask], args.force)
    folder.mkdir(parents=True, exist_ok=True)
    mask.save(mask_path)
    base.crop(tuple(args.box)).save(context)
    mask.crop(tuple(args.box)).save(mask_context)
    contract = {
        "schema": SCHEMA,
        "pose_id": args.pose_id,
        "base": os.path.relpath(base_path, folder),
        "base_sha256": digest(base_path),
        "base_rgba_sha256": hashlib.sha256(base.tobytes()).hexdigest(),
        "mask": mask_path.name,
        "mask_sha256": digest(mask_path),
        "canvas": list(SIZE),
        "box": args.box,
        "alpha_mode": args.alpha_mode,
        "mask_meaning": "L=0 locked, L=255 editable, 1..254 feather; this is NOT a renderer-specific API mask",
        "patch_size": [args.box[2] - args.box[0], args.box[3] - args.box[1]],
    }
    write_json(contract_path, contract)
    return {"status": "prepared", "contract": str(contract_path), "patch_size": contract["patch_size"]}


def read_contract(path: Path) -> tuple[dict, Image.Image, Image.Image, list[Path]]:
    contract = json.loads(path.read_text(encoding="utf-8"))
    if contract.get("schema") != SCHEMA or contract.get("canvas") != list(SIZE):
        raise ValueError("Unsupported contract schema/canvas")
    base_path = (path.parent / contract["base"]).resolve()
    mask_path = (path.parent / contract["mask"]).resolve()
    if digest(base_path) != contract["base_sha256"]:
        raise ValueError("Base changed after preparation; create a new contract for the accepted base")
    if digest(mask_path) != contract["mask_sha256"]:
        raise ValueError("Mask changed after preparation; create a new contract for the reviewed mask")
    base = load_png(base_path, ("RGBA",))
    mask = load_png(mask_path, ("L",))
    if hashlib.sha256(base.tobytes()).hexdigest() != contract["base_rgba_sha256"]:
        raise ValueError("Base pixel hash mismatch")
    validate_geometry(base, mask, contract["box"], contract["alpha_mode"])
    left, top, right, bottom = contract["box"]
    if contract.get("patch_size") != [right - left, bottom - top]:
        raise ValueError("Contract patch size disagrees with its box")
    return contract, base, mask, [path.resolve(), base_path, mask_path]


def inspect_difference(base: Image.Image, candidate: Image.Image, mask: Image.Image, alpha_mode: str) -> dict:
    if candidate.mode != "RGBA" or candidate.size != SIZE:
        raise ValueError("Final image must be a 720x720 RGBA PNG")
    outside = changed = alpha_changed = 0
    first = None
    for i, (b, c, weight) in enumerate(zip(base.get_flattened_data(), candidate.get_flattened_data(), mask.get_flattened_data())):
        if b != c:
            changed += 1
            if weight == 0:
                outside += 1
                if first is None:
                    first = [i % 720, i // 720]
        if b[3] != c[3]:
            alpha_changed += 1
    passed = outside == 0 and (alpha_mode != "preserve" or alpha_changed == 0)
    return {
        "status": "passed" if passed else "failed",
        "editable_pixels": sum(1 for value in mask.get_flattened_data() if value),
        "locked_pixels": sum(1 for value in mask.get_flattened_data() if not value),
        "changed_pixels": changed,
        "outside_mask_changed_pixels": outside,
        "first_outside_change": first,
        "alpha_changed_pixels": alpha_changed,
        "alpha_mode": alpha_mode,
    }


def blend_pixel(base: tuple, patch: tuple, mask: int, alpha_mode: str) -> tuple:
    if alpha_mode == "preserve":
        if patch[3] != 255:
            raise ValueError("Patch must be opaque wherever the preserve-mode mask is nonzero")
        return tuple((base[c] * (255 - mask) + patch[c] * mask + 127) // 255 for c in range(3)) + (base[3],)
    base_weight = base[3] * (255 - mask)
    patch_weight = patch[3] * mask
    total = base_weight + patch_weight
    if total == 0:
        return (0, 0, 0, 0)
    rgb = tuple((base[c] * base_weight + patch[c] * patch_weight + total // 2) // total for c in range(3))
    return rgb + ((total + 127) // 255,)


def compose(args: argparse.Namespace) -> dict:
    contract, base, mask, protected = read_contract(args.contract)
    patch = load_png(args.patch, ("RGB", "RGBA")).convert("RGBA")
    original_size = patch.size
    expected = tuple(contract["patch_size"])
    if patch.size != expected:
        if not args.resize_patch:
            raise ValueError(f"Patch is {patch.size}, expected {expected}; no automatic scaling. Use --resize-patch only after reviewing local alignment")
        if patch.width * expected[1] != patch.height * expected[0]:
            raise ValueError("Resize requires matching aspect ratios; refusing to stretch/crop the patch")
        patch = patch.resize(expected, Image.Resampling.LANCZOS)
    report_path = args.report or args.output.with_suffix(".qa.json")
    outputs = [args.output, report_path] + ([args.green_output] if args.green_output else [])
    output_paths(outputs, protected + [args.patch], args.force)
    result = base.copy()
    dst = result.load()
    src = patch.load()
    weights = mask.load()
    left, top, right, bottom = contract["box"]
    for y in range(top, bottom):
        for x in range(left, right):
            weight = weights[x, y]
            if weight:
                dst[x, y] = blend_pixel(dst[x, y], src[x - left, y - top], weight, contract["alpha_mode"])
    report = inspect_difference(base, result, mask, contract["alpha_mode"])
    if report["status"] != "passed":
        raise ValueError("Composition failed the outside-mask invariant")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.save(args.output)
    # Verify the saved deliverable, rather than just the in-memory image.
    report = inspect_difference(base, load_png(args.output, ("RGBA",)), mask, contract["alpha_mode"])
    report.update({"pose_id": contract["pose_id"], "contract": str(args.contract.resolve()), "base_sha256": contract["base_sha256"], "mask_sha256": contract["mask_sha256"], "patch_sha256": digest(args.patch), "patch_original_size": list(original_size), "patch_final_size": list(expected), "patch_resized": original_size != expected, "output": str(args.output.resolve()), "output_sha256": digest(args.output)})
    if args.green_output:
        green = Image.new("RGBA", SIZE, (0, 255, 0, 255))
        green.alpha_composite(result)
        args.green_output.parent.mkdir(parents=True, exist_ok=True)
        green.convert("RGB").save(args.green_output)
        report["green_output"] = str(args.green_output.resolve())
    write_json(report_path, report)
    return report


def verify(args: argparse.Namespace) -> dict:
    contract, base, mask, protected = read_contract(args.contract)
    if args.report:
        output_paths([args.report], protected + [args.candidate], args.force)
    report = inspect_difference(base, load_png(args.candidate, ("RGBA",)), mask, contract["alpha_mode"])
    report.update({"pose_id": contract["pose_id"], "candidate": str(args.candidate.resolve()), "candidate_sha256": digest(args.candidate)})
    if args.report:
        write_json(args.report, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare", help="Freeze a base, a white-editable L mask and fixed crop coordinates")
    prep.add_argument("--base", type=Path, required=True)
    prep.add_argument("--mask", type=Path, required=True, help="720x720 grayscale PNG: black locked, white editable")
    prep.add_argument("--box", type=int, nargs=4, required=True, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    prep.add_argument("--pose-id", required=True)
    prep.add_argument("--alpha-mode", choices=["preserve", "blend"], default="preserve")
    prep.add_argument("--output-dir", type=Path, required=True)
    prep.set_defaults(run=prepare)
    comp = commands.add_parser("compose", help="Paste only the masked patch into an immutable RGBA base")
    comp.add_argument("--contract", type=Path, required=True)
    comp.add_argument("--patch", type=Path, required=True)
    comp.add_argument("--output", type=Path, required=True)
    comp.add_argument("--green-output", type=Path)
    comp.add_argument("--resize-patch", action="store_true", help="Explicitly allow same-aspect resizing of the PATCH ONLY")
    comp.add_argument("--report", type=Path)
    comp.set_defaults(run=compose)
    check = commands.add_parser("verify", help="Fail if any RGBA channel outside the edit mask changed")
    check.add_argument("--contract", type=Path, required=True)
    check.add_argument("--candidate", type=Path, required=True)
    check.add_argument("--report", type=Path)
    check.set_defaults(run=verify)
    for command in (prep, comp, check):
        command.add_argument("--force", action="store_true", help="Overwrite generated outputs intentionally; inputs remain protected")
    args = parser.parse_args()
    try:
        report = args.run(args)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("status") != "failed" else 1
    except (ValueError, KeyError, OSError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
