# 兩階段批次流程與 HTML 報告

## 順序與檔案數

先完成所有 A 的局部表情，再產生需要額外肢體的 B。預設 60 個 A、44 個 new_pose B、16 個 reuse_default，共 104 張成品。使用者的子集或動作選擇會改變數量；以 N + 實際新增 B 計算，不固定為 120。

reuse_default 是語意參照，沒有 B PNG、沒有 B image 路徑，也不複製 A 到另一個檔名。HTML 在這一列只顯示 A 圖，B 欄文字說明沿用原因。不為增加產出而臨時發明手勢。真正需要但尚未完成的 B 必須保持 pending／failed，不能改成 reuse_default 來隱藏缺項。

phase_a_complete 須由 A 全部驗收後記錄。只有此後才開始 B 生圖。若 B 使用新姿勢母圖且已帶正確表情，可直接接受；共用 B 姿勢時，採該姿勢自己的臉部局部契約，不能未檢查座標與遮擋就貼上 A 的臉部圖。

## 輸出結構

以角色名稱及新版本建立專案內絕對路徑，保留舊檔。

~~~text
output/expression-portraits/<reference_stem>/<run>/
  default/NN_expression.png
  body_language/NN_expression.png   僅 new_pose 項目
  pose_templates/
  regions/
  raw_bases/
  patches/raw/
  patches/aligned/
  qa/default/
  qa/body_language/
  batch_plan.md
  manifest.json
  manifest.md
  report/index.html
  report/report-summary.json
~~~

來源設定圖、原始生圖與候選不是成品計數；HTML、總覽、遮罩及中間檔也不計入立繪 PNG 數。成品圖包只收 default/ 與實際存在的 body_language/，同一路徑只收一次。

## manifest.json

所有路徑以 manifest 所在目錄為根，使用相對路徑。每個編號只列一次；expected_ids 省略時為 1–60。明確子集須提供 expected_ids。狀態可為 accepted、reused、pending、failed；accepted／reused 都須有實際圖片與可讀的 QA 紀錄，且 QA 的 status 為 passed 或 accepted。

下例只展示 01、06 兩項，兩個 A 都完成後才製作 06 的 B。01 沒有 B 圖檔。

~~~json
{
  "schema_version": 1,
  "character": "MyCharacter",
  "expected_ids": [1, 6],
  "phase_a_complete": true,
  "entries": [
    {
      "no": 1,
      "zh": "堅定",
      "en": "Determined",
      "default": {
        "status": "accepted",
        "pose_id": "default",
        "image": "default/01_determined.png",
        "qa": "qa/default/01_determined.json"
      },
      "body_language": {
        "mode": "reuse_default",
        "reason": "沒有額外肢體動作，沿用預設姿勢。"
      }
    },
    {
      "no": 6,
      "zh": "嫉妒",
      "en": "Envy",
      "body_prompt": "arms folded tightly across the chest, shoulders drawn inward",
      "default": {
        "status": "accepted",
        "pose_id": "default",
        "image": "default/06_envy.png",
        "qa": "qa/default/06_envy.json"
      },
      "body_language": {
        "mode": "new_pose",
        "status": "accepted",
        "pose_id": "crossed_arms",
        "image": "body_language/06_envy.png",
        "qa": "qa/body_language/06_envy.json"
      }
    }
  ]
}
~~~

A 的 QA 記錄固定母圖、遮罩與 outside_mask_changed_pixels／alpha_changed_pixels，並記錄臉部、接縫、透明效果的目視結果。B 的 QA 分開記錄 body_language_match、head_neck_angle_review、facial_expression_match、matting_review；同姿勢局部差分才檢查像素固定，新姿勢母圖寫 not-applicable。

reuse_default 須附非空 reason；不填 image。報告工具會阻擋 accepted 的 new_pose 若圖片路徑或內容與 A 相同，提示改用 reuse_default；工具不自動刪除使用者檔案。

## 產生報告

從技能包根目錄執行：

~~~powershell
python scripts/render_batch_report.py output/expression-portraits/MyCharacter/run_v1/manifest.json --output report/index.html
~~~

--output 相對 manifest 目錄；省略時為 report/index.html。報告附帶 report-summary.json，支援表情搜尋、只看未完成、A／B／並排檢視、背景與放大切換。所有圖片與 QA 以相對連結讀取，不需伺服器或網路套件。

完整報告須 A 全部驗收、所有必要 B 通過、沿用理由完整、PNG 為 720×720 RGBA、圖片與 QA 路徑存在。報告列出已驗收 A／B、沿用項目、預期 PNG、實際參照成品檔與唯一內容數。編號缺漏或未驗收會顯示待補，命令回傳非零；進度報告可加 --allow-incomplete，頁面仍明示未完成。覆寫自己已知的衍生報告時用 --force，不會改動圖片或 QA。

報告工具檢查結構、PNG 標頭、QA 狀態與重複內容，不能代替圖片解碼、透明品質、肢體或美術的目視驗收。記錄執行環境是否完成瀏覽器驗收；無法預覽時據實說明，不繞過瀏覽器安全限制。
