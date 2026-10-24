# Changelog

## 0.3.0 — 2026-10-24

- 完整人物原生裁切不縮放，改為底部置中補 720×720 透明畫布；627×627 的 offset 為 (46,93)。
- 新增 pad_portrait_canvas.cjs，記錄裁切、原生尺寸、留白與 resampled=false，保留 RGBA 像素；超尺寸拒絕自動縮放或截斷。
- 去背母圖包裝工具改用相同補畫布規則；A 的局部 ROI 差分方式保留。
- 三個技能入口保留四格兩階段流程並同步規格；新增補畫布測試，CI 與可攜套件納入新工具。

## 0.2.0 — 2026-10-24

- Merge all three skill entrypoints into one two-pass workflow: all fixed-pose facial expressions first, then only needed body-language variants.
- Define all facial and body-language instructions in portable text catalogs, without character-image or archive dependencies.
- Keep the reference head/neck angle fixed; document the upright-head gaze approximation.
- Represent no-extra-motion entries as reuse_default references, with no duplicate PNG. Default catalog: 60 A + 44 B = 104 PNGs.
- Add a dependency-free paired HTML report renderer with actual file/content counts, QA links, incomplete statuses and duplicate-body detection.
- Add report regression tests and include the renderer, workflow reference and SKILL_3RD alias in portable packaging.

## 0.1.0 — 2026-10-23

Initial public release.

- Fixed RGBA pose bases and local expression patch workflow with a 60-entry catalog.
- Deterministic masked compositing, frozen hashes, and exact checks outside editable regions.
- Foreground-preserving Deback chroma matting with no default alpha contraction and guarded despill.
- Original-resolution matting and QA before premultiplied-alpha resizing; visual review required before freezing.
- Portable Node.js and Python tools, regression tests, reproducible release packaging, and MIT licensing.
- Public package focuses on the current local-difference workflow; historical full-body grid tools and character artwork are not included.

- Locked sharp 0.35.5 and Pillow 12.3.0 for the public release; retested the tools with these dependencies.
