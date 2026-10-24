# Deback 半透明遮罩去背

本技能附帶 `scripts/image-matting.cjs`，以原始 Deback 為基礎，已修正會侵蝕前景的預設值並加入 QA；原始 Deback 檔案不覆寫。它以單色背景估算 alpha，輸出同尺寸 RGBA PNG；不是 AI 重新生成圖像，也不會自動改變人物構圖。

## 安裝與位置

分享包須保留以下相對結構。Node.js 與 npm 需預先可用；在**技能資料夾**安裝 package-lock.json 鎖定的 Sharp，原生套件由 npm 依系統取得。ZIP 不含 `node_modules/`。

```text
MyPortrait/
  SKILL.md
  SKILL_New.md
  package.json
  package-lock.json
  scripts/
    image-matting.cjs
    remove_expression_backgrounds.cjs
    prepare_matted_pose.cjs
    pad_portrait_canvas.cjs
    compose_expression_patch.py
    licenses/commander-LICENSE
  references/
  character.png
```

```powershell
npm ci
node scripts/image-matting.cjs --help
```

需要測試安裝時執行 `npm run test:matting`。原生 `sharp` 依賴缺失時先處理安裝問題，不要將去背替換成粗略的綠色閾值刪除。

## 只在新姿勢母圖階段執行

先將已確認構圖的原生單格綠幕保存為 `raw_chroma/base_01.png`，並保留四格原圖與裁切框；此候選流程要求原生格寬高不超過 720。不要先把近綠色邊緣填成純綠，也不要用已經去背再合成綠底的派生圖代替原始輸入。

```powershell
node scripts/prepare_matted_pose.cjs raw_chroma/base_01.png candidates/base_01_rgba.png matting-temp/base_01
```

此命令先在原尺寸去背並檢查前景保存，再以透明像素補成 720×720：原生人物保持大小、水平置中、底部對齊，RGBA 不重採樣。627×627 的 offset 為 [46,93]；不再先縮成 690 或放大到 720。超過畫布的原生格會被拒絕，不能自動裁掉人物。輸出 QA 的 `needs-visual-review` 表示仍須目視，不能直接當成已凍結母圖。

已取得合格原生透明裁切時，不再跑去背，直接使用 `node scripts/pad_portrait_canvas.cjs native-crop.png candidate-720.png`；完整紀錄與裁切命令見[兩階段流程](dual-variant-workflow.md#完整人物的裁切與補畫布)。

一次處理多個新姿勢母圖，可使用附帶的包裝程式；預設從它自己所在的 `scripts/` 尋找去背 CLI，無論工作目錄在哪裡都不回退到作者電腦路徑。

```powershell
node scripts/remove_expression_backgrounds.cjs raw_chroma candidates matting-temp --prepare-poses
```

使用 `--prepare-poses` 才會產生 720×720 候選；省略時為相容模式，只在來源尺寸去背。包裝程式目前固定使用綠幕 `#00ff00`。其他色鍵請直接呼叫 CLI，明確指定 `--chroma-key`。需要使用其他相容 CLI 副本時可加 `--matting-cli path/to/image-matting.cjs`。

工具預設拒絕覆寫；只有有意重做已知產物時才加 `--force`。輸入、輸出與每個姿勢的中間資料夾保持獨立。

## 半透明遮罩的處理

實際程式依序執行：

1. `soft-chroma-key`：參考與邊界連通的色鍵背景，估算柔和 alpha。
2. `concentric-polyhedra`：由背景樣本建模，估算另一張遮罩；只對半透明或明顯受色鍵污染的像素去溢色，保留可信前景原色。
3. `pixel-wise-min`：逐像素取兩張遮罩的較小 alpha。
4. 將遮罩套用到處理後 RGB，輸出 RGBA PNG。

預設 `erodeRadius=0`，不擴張黑色透明區。舊版 `.dilate(1)` 在目前 Sharp 版本會侵蝕白色 alpha 前景，配合逐點取 min 會刪除下顎、手指及細髮絲，已不作預設。不得以侵蝕去隱藏綠邊。

每次另輸出 `<output>.qa.json`；明顯非色鍵前景被清成透明、可信內部透明度受損、可信不透明前景被改色或殘留強色鍵溢色時，CLI 回傳非零退出碼 2，候選不可凍結。這是啟發式檢查，無法代替原圖對照與目視。

每次保留 `concentric-polyhedra.png`、`soft-chroma-key.png`、`pixel-wise-min.png`。中間遮罩的黑、白、灰代表透明、不透明、半透明；不要將其全部閾值化為 0／255。

**去背 alpha 遮罩**決定人物輪廓與半透明邊緣；**表情編輯遮罩**決定哪些臉部像素可修改。二者不得混用。

## 驗收後才凍結

- 原尺寸去背 QA 通過後才補透明畫布，不縮放綠幕 RGB 或已去背 RGBA；原生人物 RGBA 原樣保留，新增像素為全透明。原尺寸中間圖與三張遮罩保留，最終候選為 720×720。
- 在白底與深色底檢查髮絲、半透明過渡、手指、衣物和配件，沒有誤刪、破洞或殘留綠邊。相近於背景的角色顏色要特別檢查。
- 有破洞時對照原始綠幕及三張中間遮罩，修正母圖去背；不能把破洞當成表情差分的一部分。
- 驗收後凍結母圖 RGBA／alpha／雜湊，再建立局部表情契約。後續 60 項只套用局部差分，不逐張重跑去背。
- 「遮罩外變動 0」證明差分範圍固定；不能據此宣稱去背絕對無破圖。

若已凍結的母圖需要修正，另存新的母圖版本，更新契約並重新合成該組；保留既有版本與 QA 以便追溯。
