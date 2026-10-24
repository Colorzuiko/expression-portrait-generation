---
name: expression-portrait-generation
description: "Create portrait batches in two passes: complete every expression on one fixed default pose with local patches, add body-language variants only where needed, then export a deduplicated paired HTML report."
---

# Expression Portrait Generation — 兩階段批次立繪

一次任務先完成全部 **A：預設姿勢表情差分**，第二批才製作 **B：有額外肢體語言的立繪**，最後輸出 HTML 報告。沒有額外肢體變化的項目直接參照 A，不再次生成或複製同一張圖。

本技能的肢體語言由獨立文字規格定義，與既存人物圖包脫鉤。只需當次角色設定圖、表情清單與肢體文字；使用者另提供參考時才加入。SKILL.md、SKILL_New.md、SKILL_3RD.md 為相同內容的相容入口。

## 必讀資料

- 當次角色設定圖：外觀、服裝、髮型、比例及畫風的依據。
- [臉部表情 01–60](references/expression-catalog-60.md)：A、B 共用的眼眉嘴與視線語意，不含手、道具或頭頸轉動。
- [肢體語言 01–60](references/body-language-catalog-60.md)：第二批的 new_pose／reuse_default 選擇，以及可獨立使用的文字動作。
- [兩階段流程與報告格式](references/dual-variant-workflow.md)：階段門檻、輸出結構、manifest 與 HTML 命令。
- [局部差分實作](references/local-expression-diffs.md)：ROI、遮罩、合成及固定像素檢查。需要綠幕去背時讀 [去背說明](references/image-matting.md)。

使用目前可用的圖片工具並遵守其技能。只有提示控制時記為 prompt-guided-patch，不宣稱原生 inpainting。直接取得合格透明圖時保留 alpha；綠幕母圖先原尺寸去背與前景 QA，再以預乘 alpha 縮放一次。

## 先寫完整計畫

逐項列出 no、臉部提示、A 基準與契約、B 模式、肢體文字、左右手與接觸、B pose_id、輸出、QA 與沿用理由。預設處理 01–60，也可依使用者明確指定的子集執行。

- A 每項都有一張 PNG，全部沿用同一個接受的預設身體。
- B 只有確實新增手、手臂、肩或軀幹變化時才設 new_pose。
- 沒有額外動作、或動作與 A 相同者設 reuse_default；manifest 用參照表示，不建立 B 圖檔，不為湊數另加動作。
- 成品數是 N + M：N 為 A 表情數，M 為實際額外肢體版數。預設清單 N=60、M=44，共 104 張；依當次計畫變動。

## 第一批 A：完成全部預設姿勢表情

1. 選定或產生單一預設姿勢母圖；預設 720×720 RGBA、朝畫面右方的三分之四站姿、完整頭頂到大腿中段、雙臂自然垂放。使用者指定的構圖優先。
2. 驗收外觀、構圖與白／深底透明效果，接受後凍結母圖 SHA-256、頭頸定位、ROI 與灰階遮罩。01 可直接使用已接受的母圖，不重複生圖。
3. 先試一張局部（例如 24 驚訝），確認表情、定位與接縫，再完成其餘全部表情。每張都從同一 A 母圖合成，不串接上一張結果。
4. A 僅改眼眉嘴、臉頰與明確允許的符號。09 扶額先做閉眼無奈，21 舉牌先做平靜臉，31 撐笑先做勉強拉開嘴角；手掌、牌子與手指留到第二批。不得把名稱中的手勢帶進 A 的提示。
5. 使用 [compose_expression_patch.py](scripts/compose_expression_patch.py) prepare／compose／verify。A 全部項目的遮罩外 RGBA 改動為 0，一般臉部差分 alpha 改動為 0；臉部與去背另做目視驗收。
6. A 中所有要求的項目通過後，記錄 phase_a_complete，再開始 B。A 未完成時可輸出進度報告，但不能跳過缺項宣稱完整批次。

## 第二批 B：只新增需要的肢體版本

1. 逐項讀取已接受的 A 成品，保留相同表情語意與角色外觀。reuse_default 僅記錄參照與理由，不產生圖片。
2. new_pose 依肢體文字生成新姿勢，保留頭頸角度、朝向、大小與構圖。取消低頭、仰頭、偏頭、轉頭及下巴內收差分；眼球視線仍可改動。手碰臉時調整手去配合臉位。
3. 肩線可聳起、內收或放鬆；軀幹可適度前送、後縮、側讓。頸肩連接不自然時降低軀幹幅度。16 是固定頭角的凝視近似表現，在報告註明。
4. 先驗收手型、接觸、袖口、肩與軀幹，再去背／接受並凍結 B 姿勢母圖。可直接使用已帶正確表情的母圖；相容項目共用 B 姿勢時，再做該組自己的局部臉部差分。
5. 不限制 B 姿勢基準數量；也不要求每項都是不同姿勢。共用前核對手位、手型、遮擋及輪廓，不能因同屬抱胸或托腮就自動合併。
6. 每項分開記錄肢體、頭頸、臉部、去背與像素檢查。獨立 B 母圖不要求與 A 像素相同；只有同 pose_id 的局部差分要求遮罩外像素固定。提示生成的跨姿勢頭部一致性須目視檢查，不宣稱逐像素完全相同。
7. 不得把待補、失敗或缺少的 B 用 A 佔位並改標完成。reuse_default 必須是計畫內沒有額外肢體的選擇。

## 固定像素與透明規則

- 各姿勢凍結一張母圖；改表情時回到該母圖，不逐張平移、縮放或重新置中整人。
- 座標為 [left, top, right, bottom)。遮罩 0 鎖定所有 RGBA 通道，255 可改，1–254 是允許的羽化；羽化不越界。
- 保護髮際、鼻樑、下顎與手指遮擋。一般臉部差分沿用母圖 alpha；透明區符號另建小範圍 blend 契約。
- 每張母圖只去背一次；後續差分不再整張去背、二值化、侵蝕或銳化。去背 QA 與白／深底目視驗收獨立執行。
- 2×2 可用於同尺寸的臉部局部；每格仍須回貼基準並驗證。兩套版本按先 A 全套、再 B 的順序執行，不以整人雙格圖代替固定差分。

## 最後輸出 HTML 報告

以 [render_batch_report.py](scripts/render_batch_report.py) 讀取 manifest.json，輸出逐項 A／B 配對報告。包含篩選、背景、局部放大、QA 連結、沿用原因與實際成品數。reuse_default 只顯示一張 A，B 欄顯示「沿用預設，不另存」，不插入第二份相同圖片。

報告區分完成、待補與失敗，統計 A 檔數、新增 B 檔數、沿用項數及實際唯一 PNG 數。完整狀態須 A 全部通過、每個必要 B 通過、所有沿用有理由、成品與 QA 連結存在；HTML 建立成功不等於圖片目視驗收通過。

## 儲存與交付

以技能包根目錄（含 SKILL.md、scripts/、references/）解析工具路徑；本專案以 AGENTS.md 所在目錄解析輸出。所有新產物放在 output/expression-portraits/<reference_stem>/<new_run>/，保留來源與舊版本。原始生圖由工具外部目錄複製到本次 raw_bases/ 或 patches/raw/，確認 SHA-256 相同並記錄專案內位置。

交付 A 的 default/、實際新增 B 的 body_language/、manifest、QA、原始生成紀錄與 HTML 報告；按需要提供總覽及去重後 ZIP。記錄實際呼叫與可取得用量，不以局部／批次排版推算費用節省。
