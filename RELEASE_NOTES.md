# v0.3.0：原尺寸人物，底部置中補透明畫布

完整人物裁切後不再放大到 720，也不先縮成 690。627×627 保持原始像素大小，放在 720×720 全透明畫布的 (46,93)；新增區域透明，裁切內 RGBA 與半透明邊緣原樣保留。

新增 pad_portrait_canvas.cjs，可處理透明單格或依 --box 裁切原始四格圖；prepare_matted_pose.cjs 改為原尺寸去背後使用相同補畫布方式。原生裁切超過畫布時拒絕自動縮放或截斷人物。QA 區分來源尺寸與畫布尺寸，記錄 scale=[1,1]、resampled=false 及 offset。

保留 A 全套完成後才製作必要 B 的四格流程、16 項沿用不另存，以及 A 臉部局部 ROI 合成規則。三個技能入口一致。

驗證命令：npm run test:matting（去背及補畫布）、python -m unittest discover -s scripts -p "test_*.py" -v、python scripts/make_release.py。可攜套件包含新工具與測試，不含角色素材或原始生圖。
