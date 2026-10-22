---
name: expression-portrait-generation
description: Create 60-entry game dialogue portrait sets from a character reference using fixed RGBA pose bases, bundled soft-alpha chroma-key matting, local expression patches, and pixel-exact checks outside edit masks.
---

# Expression Portrait Generation — Fixed-Composition Differences

把人物設定圖製作成可切換的對話立繪差分。預設採 **固定姿勢基準＋局部表情圖＋遮罩合成**；同一個姿勢組的遮罩外 RGBA 像素必須完全一致。不能只靠「只改臉」提示或四格整人重畫來宣稱達成局部差分。

`SKILL.md` 與 `SKILL_New.md` 是相同內容的兩個入口。使用者可把技能、設定圖與附帶資料放進工作資料夾，在 Codex 明確指定讀取本檔。

## 輸入與參考

- 人物設定圖：角色外觀、服裝、髮型、比例與畫風的唯一來源。
- 表情清單：預設使用 [完整 01–60 清單](references/expression-catalog-60.md)，保留全部編號及中英文提示；使用者指定子集時只處理子集。
- 實作時讀取 [局部差分流程](references/local-expression-diffs.md)：包含座標、遮罩、提示、合成與驗證命令。
- 綠幕母圖去背使用本包附帶的 [image-matting.cjs](scripts/image-matting.cjs)；執行前讀取 [半透明遮罩去背](references/image-matting.md)，安裝鎖定依賴並檢查邊緣。
- 只有需要手勢時，才讀 [01–52 肢體提示](references/expression-prompts.md) 的 `Half-Body Hand And Body Language Prompts`。完整 60 項混合情緒、眼型、嘴型及手勢，不代表 60 種互斥情緒。

生圖使用目前環境可用的圖片工具；需要時搭配已安裝的 image-generation 或 illustration-generation 技能。先確認工具是否支援裁切圖、實際遮罩與局部尺寸。只有提示控制時，記錄為 `prompt-guided-patch`；不要宣稱使用了工具未提供的原生 inpainting，也不要自行切換服務／模型。

## 固定構圖契約

1. 每個姿勢只接受一張 **720×720 RGBA 基準**，放在 `pose_templates/<pose_id>_rgba.png`；後續所有差分都直接從該基準合成，避免逐張累積編輯。
2. 凍結基準檔案雜湊、`pose_id`、局部裁切座標與灰階遮罩。固定座標使用 `[left, top, right, bottom)`；不依每張圖的前景範圍重新置中、縮放或裁切整個人物。
3. 遮罩 `0` 鎖定、`255` 可改、`1–254` 為允許修改的羽化區。所有羽化也必須在允許範圍內；遮罩本身不能為了掩蓋漂移而擴大到全身。
4. 一般表情只開放眼眉、嘴、臉頰與必要表情符號。鎖住髮際、耳位、下顎、鼻樑等定位依據；手遮臉時把手指與手掌排除在可改遮罩之外。
5. 最終合成必須符合 `final[M == 0] == base[M == 0]`，逐像素檢查全部 RGBA 通道。正常臉部差分也須保留整張基準的 alpha。
6. **基準只去背一次**。後續局部差分直接沿用其 RGBA；不要對每張完整立繪重跑去背、色彩正規化或銳化。汗滴／淚水等若須延伸到透明區，另建明確的局部 `blend` 契約，只處理該局部。

同姿勢的固定構圖可由確定性的合成與檢查保證；表情是否正確、臉部是否對齊仍須視覺檢查。

## 預設產製流程

1. 讀取設定圖與表情清單；檢查可用的生圖、Pillow 與必要去背工具。
2. 產生或選用 `01_determined` 母圖草稿：單一站立人物、45 度朝畫面右方、頭頂到至少大腿中段，保留完整髮頂與配件。保留生圖原尺寸；此時尚未凍結或先縮成 720×720。
3. 綠幕母圖先在**原尺寸**用本包 `scripts/image-matting.cjs` 去背，通過前景保存 QA 後才以預乘 alpha 縮放 RGBA 一次。可用 `scripts/prepare_matted_pose.cjs` 連續執行這兩步，產生 720×720 候選圖。此版本預設不侵蝕 alpha，去溢色須保留可信前景原色。檢查白／深色背景的髮絲、下顎、手指、衣服與孔洞，記錄目視通過後才複製到 pose_templates 並建立固定契約。CLI 執行成功、尺寸正確或與舊輸出一致，都不能代替此驗收。若工具直接產生合格 RGBA，可直接採用。
4. 寫 `batch_plan.md`：每項列出編號、`pose_id`、模式、基準、契約、局部座標、遮罩、提示與輸出路徑。01 直接重用接受的基準，不必再生成一次。
5. 用 `compose_expression_patch.py prepare` 固定局部契約；先試一張局部表情，通過對齊、接縫與像素驗證，再擴大批次。
6. 請生圖工具編輯或輸出局部表情圖；將原始回應保存在 `patches/raw/`。如需尺寸轉換，只對局部圖處理並記錄，不能改基準。
7. 用 `compose_expression_patch.py compose` 將局部貼回對應姿勢基準，同時產生驗證 JSON。只交付驗證通過的結果。
8. 建立全圖與臉部總覽，檢查表情、定位、接縫、手指與透明細節；只重做失敗的局部。未通過者列在 `manifest.md`，不能把整張重畫混入合格差分。
9. 寫入完成紀錄、基準與遮罩雜湊、每項 `pose_id`、驗證結果及實際生成紀錄。

## 模式與姿勢分組

- `base`：首次定稿人物構圖、尺寸與 RGBA；定稿後凍結。
- `face-patch`：預設模式。局部表情生成後，確定性地合成到同一基準。
- `pose-template`：扶額、舉牌、托腮等需要新手勢時，建立獨立 `pose_id`，接受／去背一次，再凍結作為該組基準。
- `local-mark`：汗、淚或漫畫符號需要改動透明區時，另外定義小範圍遮罩與 `blend` 契約。

可從主基準、扶額、舉牌、手靠嘴、托腮、手指撐笑等少數姿勢組開始。09、21、22、25、26、31、38、50 要特別檢查手勢需求；相容時重用同一姿勢組，53–60 預設重用主基準。姿勢組彼此可以不同，同組內才適用像素一致檢查。不要為了普通表情重新設計身體；使用者要求純臉部差分時，按其要求省略或調整手勢項目。

## 四格矩陣與算力

- 預設先做單一局部。若工具適合批次，可用 **2×2 臉部／表情局部圖**；四格需沿用相同裁切尺寸、比例與定位依據。
- 每格切出後仍須回貼固定基準、逐張驗證。四張完整立繪的生成矩陣不再是預設差分方法。
- 舊版整身四格裁切結果不能直接通過固定差分驗收；本公開版只附固定母圖與局部合成工具。
- 節省來自重用基準／去背、縮小實際請求範圍與減少重試。裁切提示或 2×2 排版本身不保證降低模型運算／費用；記錄實際請求／回傳尺寸、呼叫次數與可取得的用量，沒有數據時不要宣稱節省比例。

## 輸出位置

全部生成資料與中間檔案放在 `output/expression-portraits/<reference_stem>/`。來源設定圖不覆寫。

```text
01_determined.png                  接受的主基準 RGBA
pose_templates/<pose_id>_rgba.png   各組不可變基準
regions/<pose_id>/face/             契約、完整遮罩、局部參考
patches/raw/                       原始局部生成回應
patches/aligned/                   尺寸與定位確認後的局部 PNG
grids/                            可選的 2×2 局部矩陣
raw_crops/                        可選的原始局部裁切
transparent/NN_expression.png      已合成且驗證通過的 720×720 RGBA
expressions/NN_expression.png      由最終 RGBA 派生的綠幕版本
qa/                               每項像素檢查 JSON
matting-temp/<pose_id>/            僅基準或必要局部去背的中間產物
batch_plan.md
manifest.md
contact_sheet.png
```

`01_determined.png` 在此版本是 RGBA 基準；綠幕只作派生輸出，不當下一輪差分來源。舊版圖包只能選其中一張作新基準，不能整包改標為像素固定差分。

## 驗收

- 每張符合編號表情與設定外觀；53 與 60 各閉合單眼，60 額外有舌尖；57 黑色橫方塊眼、58 `> <` 眼與 O 嘴、59 螺旋眼與方形張嘴。
- 同組輸出均為 720×720 RGBA，`outside_mask_changed_pixels == 0`；一般臉部差分也須 `alpha_changed_pixels == 0`。
- 原始基準與遮罩雜湊不變；沒有整人平移、縮放、重定中心或每張獨立去背。
- 眼眉嘴對齊、膚色／光影接縫自然，手／瀏海遮擋正確，沒有新增手勢或配件漂移。
- 去背品質獨立檢查：前景保存 QA 通過、保留半透明 alpha；不得以整體侵蝕、二值化或填平所有孔洞掩蓋問題。髮絲、下顎、衣服、手指須和原圖對照，無誤刪或殘留色邊。未完成目視驗收不得先凍結母圖；差分的 alpha 一致只能證明沿用同一遮罩，不能證明遮罩正確。
- 每項都能追溯到姿勢基準、局部圖、契約與 QA 紀錄；無操作能力或未完成的項目據實列出。
