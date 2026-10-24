# Expression Portrait Generation

把角色設定圖製作成兩階段對話立繪批次：**先完成固定預設姿勢的全部局部表情，再新增需要的肢體語言版本，最後輸出 HTML 報告。**

A portable Codex skill for two-pass 2×2 portrait batches, native-size bottom-centered transparent padding, and deduplicated HTML reports.

## 一次批次包含什麼

- A：全部表情沿用一張預設 RGBA 母圖，局部改眼眉嘴、臉頰與允許的符號。
- B：A 全部通過後，只產生確實有額外手、手臂、肩或軀幹動作的項目。
- A／B 先各自試作四格，逐張驗收後再以 2×2 擴批；失敗格單張補作，不重生已通過項目。
- 完整人物裁切保持原生尺寸，水平置中、底部貼齊，補透明畫布至 720×720；不為填滿畫布放大人物。
- 沒有額外動作時，manifest 記錄 reuse_default，直接參照 A，不生成或複製另一張同圖。
- 肢體規格是獨立文字，不需要特定角色範例、既存圖包、圖格位置或備份目錄。
- 頭頸角度預設固定；碰臉的手配合臉位。第 16 項採直立頭角的凝視近似表現。
- HTML 顯示 A／B、沿用原因、QA、未完成項目與實際圖片數；沿用列只顯示一張 A。

預設 60 個 A、44 個新增 B、16 個沿用，共 **104 張 PNG**。實際成品數依計畫為 N + 額外肢體版數，不固定要求 120 張。人物原始生圖、遮罩、報告與總覽不計入立繪成品數。

## 快速開始

使用可用圖片生成／編輯工具的環境、Node.js 20.9 以上，以及 Python 3.10 以上。取得目前分支的程式碼 ZIP（Code → Download ZIP）或對應版本的技能套件，保留資料夾結構。

~~~powershell
npm ci
python -m pip install -r requirements.txt
~~~

放入自己有權使用的 character.png，再請 Codex 執行：

~~~text
請讀取 SKILL_3RD.md 與 character.png。
先用固定預設姿勢完成全部 01–60 的局部表情差分並驗收；
第二批只製作有額外肢體語言的版本，固定頭頸角度。
沒有額外動作的項目直接參照 A，不再輸出相同 PNG。
最後交付透明圖、QA、實際檔案數與批次 HTML 報告。
~~~

SKILL.md、SKILL_New.md、SKILL_3RD.md 內容相同，任一入口都使用相同兩階段規則。圖片由當前可用的生成工具製作；本套件本身不附角色素材。

## 工作順序

~~~mermaid
flowchart LR
  A[角色設定與文字清單] --> B[接受預設姿勢母圖]
  B --> C[局部差分完成全部 A]
  C --> D[A 全部驗收通過]
  D --> E{是否需要額外動作}
  E -->|需要| F[生成並驗收 B 姿勢]
  E -->|沒有| G[參照 A 不另存]
  F --> H[配對 HTML 與實際統計]
  G --> H
~~~

[臉部清單](references/expression-catalog-60.md) 只含臉部語意。扶額、舉牌與手指撐笑的手勢在第二批加入，不帶進 A。第二批使用 [肢體文字清單](references/body-language-catalog-60.md)，依角色服裝及活動範圍調整。詳細階段門檻與 manifest 格式見 [兩階段流程](references/dual-variant-workflow.md)。

## 固定差分與去背

同一 pose_id 的局部差分須符合：

~~~text
final[mask == 0] == base[mask == 0]
outside_mask_changed_pixels == 0
alpha_changed_pixels == 0       # 一般臉部差分
~~~

A 的整套表情使用同一母圖；B 的新姿勢各自接受並凍結。新 B 母圖不要求與 A 像素相同，跨姿勢的頭頸與外觀一致性需要目視驗收。相容 B 姿勢共用時，採該組自己的臉部遮罩。

完整人物裁切不超過 720×720 時，保留原生 RGBA 像素，僅在外圍補透明畫布。627×627 放在 720×720 的 (46,93)：左 46、右 47、上 93、下 0；不放大或縮成 690。

~~~powershell
node scripts/pad_portrait_canvas.cjs native-crop.png candidate-720.png
~~~

原始四格圖也可用 `--box left top right bottom` 指定既定格位裁切。QA 記錄原生尺寸、crop_box、offset、padding、scale=[1,1]、resampled=false；原生裁切大於 720 時拒絕自動縮放或截斷人物，需調整生成或完整裁切後重新驗收。此規則用於新母圖與 B 完整立繪；A 臉部局部仍依自己的 ROI 對齊，凍結母圖不重新定位。

已取得透明圖時不再去背。需要綠幕去背時，先在原尺寸處理與檢查前景，再以相同方式底部置中補透明畫布：

~~~powershell
node scripts/prepare_matted_pose.cjs raw_chroma/base_01.png candidates/base_01_rgba.png matting-temp/base_01
~~~

候選經白／深底驗收後才凍結；母圖只去背一次。局部合成工具見 [局部差分流程](references/local-expression-diffs.md)，去背參數與限制見 [去背說明](references/image-matting.md)。

## HTML 報告

依實際產物寫 manifest.json 後執行：

~~~powershell
python scripts/render_batch_report.py output/expression-portraits/MyCharacter/run_v1/manifest.json --output report/index.html
~~~

報告使用相對連結，支援搜尋、只看未完成、A／B／並排檢視、背景及放大切換，另存 report-summary.json。reuse_default 沒有 B PNG，也不插入第二張相同圖片。accepted 的 B 若與 A 內容相同會被標記未通過。

缺少必要圖、QA 未通過或 A 未完整驗收，報告明示未完成並回傳非零；進度輸出可加 --allow-incomplete，已知衍生報告需覆寫時加 --force。工具不改動圖片或 QA。完整格式見 [manifest 範例](references/dual-variant-workflow.md)。

~~~text
output/expression-portraits/<reference_stem>/<run>/
  default/               所有 A 表情
  body_language/         僅實際新增的 B
  pose_templates/        各姿勢凍結母圖
  regions/               ROI、遮罩與契約
  raw_bases/             原始姿勢生成圖
  patches/raw/           原始局部生成圖
  patches/aligned/       對齊後局部
  qa/                    固定像素與目視驗收紀錄
  manifest.json
  manifest.md
  batch_plan.md
  report/index.html
  report/report-summary.json
~~~

## 驗證與打包

~~~powershell
npm run test:matting
# 只測補畫布時可執行 npm run test:canvas
python -m unittest discover -s scripts -p "test_*.py" -v
python scripts/make_release.py
~~~

測試使用合成圖片，不呼叫生圖服務。補畫布測試核對 627→720 不重採樣、RGBA 位元完整保留、奇數留白、矩形格、裁切框、超尺寸拒絕、來源保護及去背整合；CI 的 test:matting 一併執行。報告測試檢查沿用不重複出圖、實際檔數、重複 B、缺項、QA、階段順序及檔案保護。打包依明確檔案清單輸出到 dist/，不包含角色圖片、測試產物或安裝依賴。

## 限制與授權

像素檢查證明修改範圍；表情、接縫、手指、頭頸及透明效果仍需目視驗收。報告檢查 PNG 標頭與 QA 狀態，不能代替完整圖片解碼或美術品質檢查。無法完成的項目保持待補，不以沿用掩蓋缺圖。

程式及技能文件採 [MIT](LICENSE)，第三方聲明見 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。角色與生成素材的權利不由此授權授予。版本變更見 [CHANGELOG.md](CHANGELOG.md)。
