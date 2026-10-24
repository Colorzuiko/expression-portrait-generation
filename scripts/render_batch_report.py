#!/usr/bin/env python3
"""Render a local paired portrait report without copying or generating images."""
from pathlib import Path, PureWindowsPath
import argparse
import hashlib
import html
import json
import os
import struct
from urllib.parse import quote

ACCEPTED = {"accepted", "reused"}
LABELS = {"accepted": "已驗收", "reused": "沿用已驗收圖", "pending": "待補",
          "failed": "未通過", "reuse_default": "沿用預設，不另存",
          "waiting_default": "等待預設版", "unplanned": "尚未規劃"}


def safe_file(root, value):
    if not isinstance(value, str) or not value or "://" in value or PureWindowsPath(value).drive:
        raise ValueError("Use a nonempty run-relative file path")
    target = (root / value).resolve()
    target.relative_to(root)
    if not target.is_file():
        raise FileNotFoundError(value)
    return target


def inspect_variant(root, record):
    record = record if isinstance(record, dict) else {}
    status = record.get("status", "pending")
    if status not in ACCEPTED | {"pending", "failed"}:
        status = "failed"
    result = {"status": status, "image": None, "qa": None, "sha256": None, "issues": []}
    for key in ("image", "qa"):
        value = record.get(key)
        if not value:
            if status in ACCEPTED:
                result["issues"].append("缺少 " + key + " 路徑")
            continue
        try:
            target = safe_file(root, value)
            if key == "image":
                data = target.read_bytes()
                if len(data) < 29 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
                    raise ValueError("不是 PNG")
                width, height, depth, color = struct.unpack(">IIBB", data[16:26])
                if (width, height, depth, color) != (720, 720, 8, 6):
                    raise ValueError("需要 720×720 8-bit RGBA PNG")
                result["sha256"] = hashlib.sha256(data).hexdigest()
            else:
                qa = json.loads(target.read_text(encoding="utf-8-sig"))
                if status in ACCEPTED and qa.get("status") not in {"passed", "accepted"}:
                    raise ValueError("QA 尚未通過")
            result[key] = target
        except (OSError, ValueError, TypeError) as exc:
            result["issues"].append(key + ": " + str(exc))
    if status in ACCEPTED and result["issues"]:
        result["status"] = "failed"
    return result


STYLE = """
*{box-sizing:border-box}body{margin:0;background:#f5f3ef;color:#302c32;font:14px/1.6 system-ui,sans-serif}
header,main{max-width:1200px;margin:auto;padding:24px}h1{font-size:26px;margin:0 0 8px}header p{color:#81757b;margin:6px 0}
.stats{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}.stat{background:white;padding:12px 19px;border-radius:9px;min-width:125px}.stat b{display:block;font-size:25px;color:#934c61}.stat span{font-size:11px}
.banner{padding:12px 16px;background:#e8efe8;border-radius:7px}.banner.incomplete{background:#f3e4d9;color:#815a37}
.tools{position:sticky;top:0;z-index:1;background:#f5f3eff5;padding:12px 0;display:flex;gap:13px;align-items:center;flex-wrap:wrap;border-bottom:1px solid #ded6d3}
input,select{font:inherit;padding:6px 9px;border:1px solid #d9cfd0;border-radius:5px;background:white}label{font-size:12px}input[type=range]{max-width:110px;vertical-align:middle;accent-color:#994c65}
article{background:white;margin:20px 0;border:1px solid #e1d9d7;border-radius:10px;overflow:hidden}article>h2{font-size:17px;padding:13px 17px;margin:0;border-bottom:1px solid #eee7e2}article>h2 small{font-size:11px;font-weight:400;color:#98828b;margin-left:12px}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:#e8dfdc}.variant{background:white;min-width:0}.variant h3{display:flex;justify-content:space-between;font-size:12px;padding:11px 15px;margin:0;gap:8px}.status{font-size:10px;color:#8a6b76;font-weight:400}
.image{aspect-ratio:1;overflow:hidden;background-color:#faf9f5;background-image:conic-gradient(#e9e6e1 25%,transparent 0 50%,#e9e6e1 0 75%,transparent 0);background-size:20px 20px}
.image img{width:100%;height:100%;object-fit:contain;transform:scale(var(--zoom,1));transform-origin:50% 33%;display:block}
body[data-background=white] .image{background:#fff}body[data-background=dark] .image{background:#242733}
.placeholder{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:200px;padding:25px;color:#98838b;gap:8px}.placeholder b{font-size:17px;font-weight:500}.placeholder span{font-size:12px;text-align:center;max-width:340px}
.links{padding:9px 15px;font-size:11px;display:flex;gap:18px}.links a{color:#955267}.issues{margin:0;padding:0 20px 12px 34px;color:#9d5c43;font-size:11px}
.notes{padding:0 16px 13px;font-size:12px;color:#8f7d84}details{padding:8px 17px;font-size:11px;color:#8c7981}details p{white-space:pre-wrap;overflow-wrap:anywhere}summary{cursor:pointer}
body[data-view=default] .variant-body{display:none}body[data-view=body_language] article[data-mode=new_pose] .variant-default{display:none}
body[data-view=default] .pair,body[data-view=body_language] article[data-mode=new_pose] .pair{grid-template-columns:1fr}
.empty{padding:25px;color:#8a7a81}footer{padding:18px 0;color:#9b8a91;font-size:11px}
@media(max-width:650px){header,main{padding:15px}h1{font-size:21px}.stats{gap:7px}.stat{padding:8px 12px;min-width:100px}.stat b{font-size:21px}.tools{gap:8px}.variant h3{padding:8px;font-size:10px}.placeholder{min-height:140px;padding:12px}.placeholder b{font-size:13px}.placeholder span{font-size:10px}.links{padding:7px;font-size:10px;gap:8px}}
"""
SCRIPT = """
const search=document.getElementById('search'), incomplete=document.getElementById('incomplete');
function filter(){let n=0;const q=search.value.trim().toLowerCase();document.querySelectorAll('article').forEach(a=>{const show=a.dataset.search.includes(q)&&(!incomplete.checked||a.dataset.complete!=='true');a.hidden=!show;if(show)n++});document.getElementById('empty').hidden=n>0}
search.addEventListener('input',filter);incomplete.addEventListener('change',filter);
document.getElementById('view').addEventListener('change',e=>document.body.dataset.view=e.target.value);
document.getElementById('background').addEventListener('change',e=>document.body.dataset.background=e.target.value);
document.getElementById('zoom').addEventListener('input',e=>document.documentElement.style.setProperty('--zoom',Number(e.target.value)/100));
"""


def build_report(manifest_path, output=None, force=False):
    manifest_path = Path(manifest_path).resolve()
    root = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("entries", []), list):
        raise ValueError("Manifest must be an object with an entries list")
    expected = manifest.get("expected_ids", list(range(1, 61)))
    if not isinstance(expected, list) or not expected or any(type(n) is not int or not 1 <= n <= 60 for n in expected) or len(set(expected)) != len(expected):
        raise ValueError("expected_ids must be unique integers from 1 to 60")
    records = {}
    for record in manifest.get("entries", []):
        if not isinstance(record, dict):
            raise ValueError("Each entry must be an object")
        no = record.get("no")
        if type(no) is not int or no not in expected or no in records:
            raise ValueError("Invalid, unexpected or duplicate expression number")
        records[no] = record
    output = (root / (output or "report/index.html")).resolve()
    output.relative_to(root)
    if output.suffix.lower() not in {".html", ".htm"}:
        raise ValueError("Report output must be an HTML file")
    summary_path = output.with_name("report-summary.json")
    if not force and (output.exists() or summary_path.exists()):
        raise FileExistsError("Report exists; choose a new output or use --force")
    defaults = {no: inspect_variant(root, records.get(no, {}).get("default")) for no in expected}
    default_hashes = {v["sha256"] for v in defaults.values() if v["status"] in ACCEPTED}
    esc = lambda value: html.escape(str(value), quote=True)

    def url(target):
        return quote(os.path.relpath(target, output.parent).replace(os.sep, "/"), safe="/")

    def pane(variant, title, kind):
        status = variant["status"]
        content = '<div class="image"><img loading="lazy" src="' + esc(url(variant["image"])) + '" alt="' + esc(title) + '"></div>' if variant.get("image") else '<div class="placeholder"><b>' + esc(LABELS.get(status, status)) + '</b></div>'
        links = []
        if variant.get("image"):
            links.append('<a download href="' + esc(url(variant["image"])) + '">PNG ↓</a>')
        if variant.get("qa"):
            links.append('<a target="_blank" href="' + esc(url(variant["qa"])) + '">驗收紀錄 ↗</a>')
        issues = '<ul class="issues">' + "".join("<li>" + esc(s) + "</li>" for s in variant["issues"]) + "</ul>" if variant["issues"] else ""
        return '<section class="variant variant-' + kind + '"><h3>' + esc(title) + '<span class="status">' + esc(LABELS.get(status, status)) + '</span></h3>' + content + '<div class="links">' + "".join(links) + "</div>" + issues + "</section>"

    counts = {"expressions": len(expected), "default_accepted": 0, "body_required": 0,
              "body_accepted": 0, "reuse_default": 0, "unplanned": 0, "complete_items": 0}
    accepted_paths, accepted_hashes, cards, items = set(), set(), [], []
    source_paths = {manifest_path}
    for no in expected:
        entry = records.get(no, {})
        a = defaults[no]
        body = entry.get("body_language") or {}
        if not isinstance(body, dict):
            raise ValueError("body_language must be an object")
        mode = body.get("mode", "unplanned")
        a_ok = a["status"] in ACCEPTED
        counts["default_accepted"] += int(a_ok)
        if a_ok:
            accepted_paths.add(a["image"]); accepted_hashes.add(a["sha256"])
        b_ok, b = False, None
        if mode == "reuse_default":
            counts["reuse_default"] += 1
            reason = body.get("reason", "")
            b_ok = isinstance(reason, str) and bool(reason.strip()) and not body.get("image") and a_ok
            status = "reuse_default" if b_ok else "waiting_default"
            detail = reason if isinstance(reason, str) and reason.strip() else "需要記錄沿用原因"
            if body.get("image"):
                detail = "reuse_default 不應填寫 B image，請只參照 A。"; status = "failed"
            body_html = '<section class="variant variant-body"><h3>B · 肢體語言<span class="status">' + esc(LABELS[status]) + '</span></h3><div class="placeholder"><b>↩ 沿用預設版</b><span>' + esc(detail) + '</span><span>沒有額外 PNG 圖檔</span></div></section>'
        elif mode == "new_pose":
            counts["body_required"] += 1
            b = inspect_variant(root, body)
            if b["status"] in ACCEPTED and b["sha256"] in default_hashes:
                b["status"] = "failed"
                b["issues"].append("與 A 圖片內容相同；沒有額外動作時請用 reuse_default，不另存重複檔。")
            b_ok = b["status"] in ACCEPTED
            counts["body_accepted"] += int(b_ok)
            if b_ok:
                accepted_paths.add(b["image"]); accepted_hashes.add(b["sha256"])
            body_html = pane(b, "B · 新增肢體", "body")
        else:
            counts["unplanned"] += 1
            body_html = '<section class="variant variant-body"><h3>B · 肢體語言</h3><div class="placeholder"><b>尚未規劃</b><span>請指定 new_pose 或 reuse_default</span></div></section>'
        complete = a_ok and b_ok
        for variant in (a, b):
            if variant:
                source_paths.update(variant[key] for key in ("image", "qa") if variant.get(key))
        counts["complete_items"] += int(complete)
        zh, en = entry.get("zh", "待補表情"), entry.get("en", "")
        title = f"{no:02d} {zh}"
        notes = entry.get("notes", [])
        if isinstance(notes, str):
            notes = [notes]
        notes_html = '<div class="notes">' + "<br>".join(esc(s) for s in notes) + "</div>" if notes else ""
        prompt = entry.get("body_prompt", "")
        prompt_html = '<details><summary>肢體文字規格</summary><p>' + esc(prompt) + "</p></details>" if prompt else ""
        cards.append('<article data-mode="' + esc(mode) + '" data-complete="' + str(complete).lower() + '" data-search="' + esc(f"{no:02d} {zh} {en}".lower()) + '"><h2>' + esc(title) + '<small>' + esc(en) + '</small></h2><div class="pair">' + pane(a, "A · 預設姿勢", "default") + body_html + "</div>" + notes_html + prompt_html + "</article>")
        items.append({"no": no, "default_status": a["status"], "body_mode": mode,
                      "body_status": b["status"] if b else ("reuse_default" if b_ok else "pending"),
                      "complete": complete, "issues": a["issues"] + (b["issues"] if b else [])})
    counts["referenced_accepted_png_files"] = len(accepted_paths)
    counts["unique_accepted_image_contents"] = len(accepted_hashes)
    counts["planned_png_files"] = len(expected) + counts["body_required"] if not counts["unplanned"] else None
    phase_a_complete = counts["default_accepted"] == len(expected)
    phase_issue = not phase_a_complete and counts["body_accepted"] > 0
    complete = counts["complete_items"] == len(expected) and not phase_issue
    summary = {"status": "complete" if complete else "incomplete", "phase_a_complete": phase_a_complete,
               "phase_order_issue": phase_issue, "counts": counts, "items": items,
               "limits": "Checks report structure, PNG headers and QA status; does not replace image decoding or visual art review."}
    character = esc(manifest.get("character", "角色"))
    banner = "批次完成；沿用項目僅參照 A，不增加重複圖片。" if complete else "批次尚未完成；缺項、失敗或尚未規劃的項目已標示。"
    if phase_issue:
        banner += " A 未全部完成前已有 B 被標記完成，請查核兩階段順序。"
    stats = "".join('<div class="stat"><b>' + str(value) + "</b><span>" + label + "</span></div>" for value, label in [
        (counts["default_accepted"], "A 已驗收"), (counts["body_accepted"], "B 新增已驗收"),
        (counts["reuse_default"], "沿用 A · 不另存"), (len(accepted_paths), "已驗收 PNG 檔"),
        (len(accepted_hashes), "不重複圖片內容")])
    page = '<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + character + ' · 批次立繪報告</title><style>' + STYLE + '</style></head><body data-view="paired" data-background="checker"><header><h1>' + character + ' · 批次立繪報告</h1><p>先完成全部預設表情，再新增需要的肢體動作。沒有額外動作的項目沿用 A，不重複出圖。</p><div class="stats">' + stats + '</div><div class="banner' + ("" if complete else " incomplete") + '">' + esc(banner) + '</div></header><main><div class="tools"><input id="search" type="search" placeholder="搜尋編號或表情" aria-label="搜尋表情"><label><input id="incomplete" type="checkbox">只看未完成</label><label>檢視 <select id="view"><option value="paired">A／B 並排</option><option value="default">預設姿勢 A</option><option value="body_language">肢體版本 B</option></select></label><label>背景 <select id="background"><option value="checker">棋盤格</option><option value="white">白色</option><option value="dark">深色</option></select></label><label>放大 <input id="zoom" type="range" min="100" max="220" value="100" aria-label="圖片放大"></label></div>' + "".join(cards) + '<p id="empty" class="empty" hidden>沒有符合的項目。</p><footer>圖片與驗收紀錄皆使用本機相對連結。數值與檔案檢查不能代替目視驗收。<br><a href="report-summary.json">批次統計 JSON</a></footer></main><script>' + SCRIPT + "</script></body></html>"
    if output in source_paths or summary_path in source_paths:
        raise ValueError("Report must not replace a manifest, image or QA source")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", help="Output path relative to the manifest directory")
    parser.add_argument("--allow-incomplete", action="store_true", help="Allow a clearly marked progress report")
    parser.add_argument("--force", action="store_true", help="Replace this derived HTML and summary only")
    args = parser.parse_args()
    try:
        result = build_report(args.manifest, args.output, args.force)
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(2, str(exc) + "\n")
    print(json.dumps({"status": result["status"], "counts": result["counts"]}, ensure_ascii=False))
    return 0 if result["status"] == "complete" or args.allow_incomplete else 1


if __name__ == "__main__":
    raise SystemExit(main())
