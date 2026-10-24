# 固定基準與局部表情差分

本文件處理同一 pose_id 內的局部差分。兩階段批次先完成全部 A；新手勢母圖只在第二階段 B 建立，順序依 [兩階段流程](dual-variant-workflow.md)。

本流程的目標是讓對話切換只影響已批准的局部區域。它不依賴生圖模型能完全保留整張圖片：最終圖由原始基準與局部圖經確定性遮罩合成。

## 1. 選定與凍結姿勢基準

以 `pose_templates/base_01_rgba.png` 為例：先完成 720×720 構圖、視角、角色外觀與 RGBA 去背，再作為唯讀母圖。接受的主基準另存 `01_determined.png`，可直接複製到 `default/01_determined.png`；其餘表情都回到同一母圖，不串接上一張表情。

有手勢的項目先建立自己的姿勢母圖。手遮臉時，後續表情遮罩須避開手、手指、瀏海和其他定位輪廓。跨姿勢組不要求像素相同，但需要一致的角色外觀與相容的畫布定位。

去背工具只在接受新姿勢基準或必要的局部透明符號時使用。本包已內附 `scripts/image-matting.cjs` 與鎖定的 `sharp` 依賴，依 [半透明遮罩去背](image-matting.md) 安裝與執行；不依賴作者電腦的絕對路徑。使用它時保留原始綠幕與近綠色過渡像素，每個姿勢／局部用獨立的 `matting-temp/` 子資料夾。已有合格 RGBA 時不必再去背；已知由舊版侵蝕流程產生缺口者須從原始綠幕另建母圖版本，不能當成合格基準。去背遮罩與後續的表情可修改遮罩是兩種不同資源。

## 2. 決定 ROI 與遮罩

ROI 是固定裁切框，座標規格為 `[left, top, right, bottom)`；右界與下界不包含在裁切中。讓局部參考包含足夠的臉部定位依據，而可修改遮罩只覆蓋實際會變的眼眉嘴或臉頰。不要用生成結果的 bounding box 自動回推位置。

遮罩檔案要求 **720×720、模式 L 的灰階 PNG**：

- 黑色 `0`：所有 RGBA 通道均鎖定，連透明像素底下的 RGB 也保持。
- 白色 `255`：使用局部圖內容。
- 灰色 `1–254`：接縫羽化；仍算可修改範圍，不能越出 ROI。

優先用分離的眼眉、嘴與臉頰遮罩，保留髮際、耳位、鼻樑及下顎輪廓。遮罩是各姿勢的共享幾何資源，先視覺檢查再擴批；不得每張重新偵測臉或放大遮罩來消除驗證失敗。

預設 `alpha-mode preserve`，遮罩只允許落在基準的完全不透明部分；局部圖在所有可改點也必須不透明。此模式保留整張母圖 alpha。需要透明背景上的汗滴、淚水或符號時另建小範圍 `alpha-mode blend` 契約，使用 RGBA 局部圖，以預乘 alpha 的方式插值；它仍不能更動遮罩外像素。

## 3. 建立固定契約

下面的 ROI 座標僅示範命令格式，必須依實際人物檢查調整，不能當所有角色共用的座標。

```powershell
python .\scripts\compose_expression_patch.py prepare `
  --base .\output\expression-portraits\MyCharacter\pose_templates\base_01_rgba.png `
  --pose-id base_01 `
  --box 250 80 510 340 `
  --mask .\output\expression-portraits\MyCharacter\regions\face-mask-input.png `
  --output-dir .\output\expression-portraits\MyCharacter\regions\base_01\face
```

輸出：

```text
patch_contract.json  基準相對路徑／雜湊、pose_id、ROI、遮罩雜湊、alpha 模式
editable_mask.png    凍結的完整 720×720 遮罩
context.png          依 ROI 原樣裁出的 RGBA 局部參考
mask_context.png     相同 ROI 的灰階局部遮罩
```

這是合成用的白色可改遮罩。若生圖工具原生遮罩的語意是透明可改或黑色可改，必須依該工具的文件轉換一份供生圖使用，不能把它直接當同一種遮罩。合成契約中的 `editable_mask.png` 不變。

## 4. 選擇生成方式

依可用工具選擇：

1. **原生局部／遮罩編輯可用**：提供局部參考及符合該工具規格的遮罩，限制生成範圍。
2. **只有一般圖片生成或提示編輯**：只要求產出相同局部畫幅與定位的表情圖，記為 `prompt-guided-patch`。即使模型仍處理完整參考，最終也只取契約允許的局部。
3. **只能回傳整張編輯圖**：以已知的相同畫布座標擷取局部，丟棄其他生成像素，再貼回原基準；若生成圖已縮放／平移，先修正局部定位或重試，不得直接當最終差分。

先做一張代表性局部（例如 24 驚訝），確認眼眉嘴定位、畫風與接縫，再擴充。失敗時先修正局部參考、遮罩或局部輸出；一般表情的失敗不應觸發重新生成整個身體。

### 局部提示模板

```text
Input 1 is a fixed crop from the accepted pose base, not a new character design.
Preserve the same crop framing, head angle, face scale, nose bridge, ear position,
jawline, hairline, lighting and linework. Change only the allowed facial features.

Expression: {facial_expression_prompt}
Editable features: {eyes_brows_mouth_cheeks_or_marks}
Occluders to preserve: {bangs_hands_accessories_if_present}

Output one local expression patch aligned to the reference crop.
Requested patch size: {roi_width} x {roi_height}.
No new body pose, camera change, crop shift, border, label or extra panel.
```

表情清單中的手部／姿勢文字只用來選擇或建立姿勢基準，不把它們當作 face-patch 的新增動作指令。預設頭頸角度固定，不啟用低頭或轉頭差分；手勢與肩、軀幹提示僅用於第二階段 B。

### 可選 2×2 局部批次

四格只包含相同範圍的局部參考，依左上、右上、左下、右下指定表情。每格的定位依據、比例、尺寸相同，沒有完整身體、標籤或格線。保留原圖與每格裁切；切出後逐張回貼基準驗證。

A 不以整人四格補成 720×720 取代臉部局部合成；A 局部的最終尺寸來自契約，不是每格「補到 720」。B 的完整人物裁切則按[底部置中補透明畫布規則](dual-variant-workflow.md#完整人物的裁切與補畫布)交付，保持原生人物尺寸。

若工具回傳尺寸不同，先檢查構圖及定位。合成腳本預設拒絕尺寸不同的局部；只有確認等比例且對齊時，才傳 `--resize-patch`，它只縮放局部、拒絕不同比例拉伸，並把尺寸轉換記入 QA。非等比例或需要回裁的結果需另外準備對齊版局部，保留原始圖與轉換紀錄。任何情況都不縮放母圖。

## 5. 合成與驗證

```powershell
python .\scripts\compose_expression_patch.py compose `
  --contract .\output\expression-portraits\MyCharacter\regions\base_01\face\patch_contract.json `
  --patch .\output\expression-portraits\MyCharacter\patches\aligned\24_surprised.png `
  --output .\output\expression-portraits\MyCharacter\transparent\24_surprised.png `
  --green-output .\output\expression-portraits\MyCharacter\expressions\24_surprised.png `
  --report .\output\expression-portraits\MyCharacter\qa\24_surprised.json
```

合成以基準的逐像素複本開始，只替換遮罩非零的像素。`preserve` 模式只插值 RGB，alpha 完整沿用基準；`blend` 模式在允許的區域內按預乘 alpha 插值。輸出重新讀檔驗證後記錄雜湊。綠幕版本由已合成 RGBA 與固定 `#00ff00` 派生，不再獨立生成或去背。

可以對任意候選圖另行驗證；若有遮罩外漂移，程式會回傳非零退出碼並指出第一個不一致位置：

```powershell
python .\scripts\compose_expression_patch.py verify `
  --contract .\output\expression-portraits\MyCharacter\regions\base_01\face\patch_contract.json `
  --candidate .\output\expression-portraits\MyCharacter\transparent\24_surprised.png `
  --report .\output\expression-portraits\MyCharacter\qa\24_surprised-recheck.json
```

基準或遮罩檔案雜湊改變時，原契約會失效。確實接受新基準／新遮罩後，建立新的契約及批次計畫；不要覆寫母圖來讓舊結果通過。輸出預設不覆寫，只有有意重做已知產物時才使用 `--force`，輸入檔案即使加 `--force` 也受保護。

## 6. 驗收紀錄

`batch_plan.md` 至少包含 `no, expression, mode, pose_id, base, contract, patch, output`。`manifest.md` 對每項連結到 QA JSON，列出失敗、重試及視覺檢查狀態。

必查：

- `outside_mask_changed_pixels` 為 0；`preserve` 模式 `alpha_changed_pixels` 也為 0。
- 基準／遮罩雜湊、ROI、輸出尺寸與姿勢組正確。
- 表情可辨識、與編號相符，定位依據不變，沒有面部重影或色差接縫。
- 手、髮際、指尖與衣服不漂移；局部符號的 alpha 與邊緣自然。
- 若 `changed_pixels` 為 0，不能僅因像素檢查通過就當作新表情；仍需人工確認是否符合目標。

記錄實際呼叫次數、請求／回傳尺寸、重試，以及工具提供的用量。局部合成保證輸出範圍，無法單憑它證明生圖工具減少了多少運算或費用。
