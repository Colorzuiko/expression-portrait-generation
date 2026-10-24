# 肢體語言文字規格 01–60

本清單是可獨立使用的文字動作規格，不依賴任何既存角色圖片、圖格位置或備份目錄。描述手位、手型、接觸、肩線及軀幹；可依角色服裝與使用者要求調整，並記錄實際選擇。

第二階段只處理 new_pose 項目。reuse_default 表示沒有額外肢體語言，直接參照 A；不呼叫生圖、不複製 PNG、不建立同圖別名檔，也不為湊數另加手勢。與 A 動作相同時同樣採 reuse_default。使用者明確要求額外動作時，可在計畫內改為 new_pose 並提供文字提示。

預設 60 項中有 44 項額外肢體、16 項沿用預設，因此完整批次預設是 60 + 44 = 104 張成品 PNG。實際數量以當次計畫及驗收結果計算，不固定要求 120 張。相似 B 姿勢可共用母圖，但不同表情仍各有對應輸出；沒有新增肢體的項目不額外輸出。

頭頸角度、朝向與構圖固定，眼球視線可變。碰臉動作由手配合固定臉位，軀幹幅度維持自然頸肩連接。16 在 A 中使用直立頭角的凝視近似版，不另建立 B。21 的空白牌是必要道具。

| No. | 表情 | 第二階段 | 肢體設計 | Body-language prompt |
| --- | --- | --- | --- | --- |
| 01 | 堅定 | reuse_default | 沿用 A，不新增肢體。 | — |
| 02 | 失望 | reuse_default | 沿用 A，不新增肢體。 | — |
| 03 | 輕蔑 | reuse_default | 沿用 A，不新增肢體。 | — |
| 04 | 厭惡 | reuse_default | 沿用 A，不新增肢體。 | — |
| 05 | 微醺 | reuse_default | 沿用 A，不新增肢體。 | — |
| 06 | 嫉妒 | new_pose | 雙臂緊抱胸、手收向對側臂膀，肩略向內。 | arms folded tightly across the chest, hands tucked toward opposite arms, shoulders slightly drawn inward |
| 07 | 興奮 | new_pose | 雙小拳抬至肩頰旁，肘較收，肩微抬。 | both small fists lifted near the shoulders and lower cheeks, elbows close, gently raised shoulders |
| 08 | 面無表情 | reuse_default | 沿用 A，不新增肢體。 | — |
| 09 | 扶額 | new_pose | 一掌貼住額頭、遮住一側眼面，另一臂垂下。 | one palm resting across the forehead and one side of the face, other arm hanging at the side |
| 10 | 慌亂害羞 | new_pose | 雙手不對稱抬在臉頰與胸前，掌略朝外、五指張開，肩上抬。 | both open hands unevenly raised near the cheeks and upper chest, palms angled outward, fingers spread, lifted shoulders |
| 11 | 挫怒 | new_pose | 雙拳握在腰肋兩側，雙肘外張，胸肩緊繃。 | both fists clenched beside the waist and lower ribs, elbows opening outward, taut shoulders and chest |
| 12 | 皺眉 | new_pose | 雙臂結實抱胸，肩線較方正，上身挺直。 | arms crossed firmly across the chest, squared shoulders, upright rigid upper torso |
| 13 | 痛苦扭臉 | new_pose | 雙拳收在上腹前，肘貼身，肩向上及向內收。 | both fists close to the upper abdomen, elbows tucked tightly inward, raised contracted shoulders |
| 14 | 內疚 | new_pose | 雙手在胸前交握，雙肘內收，肩略向內。 | both hands clasped at chest center, elbows close to the torso, shoulders drawn inward |
| 15 | 疲憊 | new_pose | 一手扶太陽穴，另一臂沉重垂下，肩線放鬆下沉。 | one hand supporting the temple, other arm hanging heavily, slack lowered shoulders |
| 16 | 庫柏力克凝視 | reuse_default | 沿用 A，不新增肢體。 | — |
| 17 | 害怕 | new_pose | 雙小拳緊收下巴兩旁，肘貼身，肩高聳。 | both small fists tucked beside the chin, elbows tight against the torso, high hunched shoulders |
| 18 | 恐慌 | new_pose | 雙手在臉旁彎指張開，雙肘外展，肩抬高並收縮。 | both hands raised beside the face, separated fingers bent into tense claws, elbows spread, high contracted shoulders |
| 19 | 擔憂 | new_pose | 一手輕貼胸口，另一臂橫於腹前托住該側手肘。 | one hand lightly against the upper chest, opposite forearm across the abdomen supporting that elbow |
| 20 | 嚴肅 | reuse_default | 沿用 A，不新增肢體。 | — |
| 21 | 舉牌 | new_pose | 雙手分握胸前空白矩形牌的左右邊緣，臉部保持可讀。 | both hands gripping side edges of a blank rectangular sign at chest level, face unobstructed |
| 22 | 睏倦 | new_pose | 一手靠嘴前掩呵欠，另一臂自然鬆垂。 | one hand lifted in front of the mouth to cover a yawn, opposite arm hanging loosely |
| 23 | 賭氣 | new_pose | 抱胸且雙肘內收，肩略向內，閉合而退縮。 | arms folded across the chest with inward elbows, shoulders pulled inward, compact withdrawn torso |
| 24 | 驚訝 | new_pose | 雙手抬到肩旁，掌朝外、五指伸展，上胸微後讓。 | both open palms beside the shoulders, fingers spread, bent elbows, upper chest slightly drawing back |
| 25 | 思考 | new_pose | 一手抵下巴，另一前臂支撐該側手肘，肩線放鬆。 | one hand resting under the chin, opposite forearm supporting the raised elbow, relaxed shoulders |
| 26 | 沉思 | new_pose | 一手靠下巴，另一手托前臂，雙肘內收，輪廓安靜。 | one hand at the chin, opposite hand supporting the forearm, elbows tucked inward, compact reflective posture |
| 27 | V 形怒眉 | new_pose | 一拳在胸前，另一拳低壓腰側，雙臂形成不對稱張力。 | one fist near the upper chest, opposite fist low beside the hip, asymmetrical bent arms, firm shoulders |
| 28 | 畏縮皺臉 | new_pose | 一手半張靠臉旁防護，另一拳收胸前，肩線不對稱。 | one partly open hand beside the cheek, opposite fist near the chest, tight asymmetrical shoulders |
| 29 | 狂氣笑 | new_pose | 雙手爪狀彎指放在胸肩前，雙肘打開，上胸微向前送。 | both hands curled into separated claws before the upper chest, elbows open, upper chest subtly projecting forward |
| 30 | 邪惡微笑 | new_pose | 一手靠嘴角與下巴，另一臂橫托肘部，動作收斂。 | one hand near the mouth corner and chin, opposite arm supporting the elbow across the torso, contained posture |
| 31 | 手指撐笑 | new_pose | 雙食指頂住兩側嘴角外的臉頰，其餘手指彎收。 | both index fingertips pressing the cheeks upward beside the mouth corners, remaining fingers curled, elbows bent in front |
| 32 | 強顏歡笑 | new_pose | 雙手低位交疊在下腹前，手臂向下伸，肩略緊。 | hands held together low before the abdomen, arms extending downward, elbows inward, slightly tense shoulders |
| 33 | 露齒大笑 | new_pose | 雙拳在肩旁抬高，肘比興奮姿勢稍外張，胸口展開。 | both fists raised beside the shoulders, elbows slightly open, lifted chest, cheerful open shoulders |
| 34 | 邪惡咧嘴笑 | new_pose | 雙手於胸前指尖相抵，掌間留空，雙肘收緊。 | both sets of fingertips meeting in a steepled shape before the chest, small gap between palms, elbows close |
| 35 | 淡笑 | new_pose | 一手輕放胸口，另一臂垂下，肩線柔和放鬆。 | one hand resting gently on the upper chest, other arm at the side, soft relaxed shoulders |
| 36 | 悲傷微笑 | new_pose | 雙手輕握胸前，肘貼身、肩略垂，避免攥成拳。 | both hands softly clasped before the chest, elbows close, slightly lowered shoulders, gentle finger contact |
| 37 | 誘惑微笑 | new_pose | 一手輕觸下巴或下唇，另一臂托肘，肩線鬆、上身微側。 | one hand lightly touching the chin near the lower lip, opposite arm supporting the elbow, relaxed shoulders, gently angled torso |
| 38 | 忍笑 | new_pose | 一手掩嘴，另一手托住該側前臂或手肘，肩略收。 | one hand covering the mouth, opposite hand supporting the raised forearm or elbow, slightly inward shoulders |
| 39 | 得意臉 | new_pose | 一手叉腰，另一手以拇指指向自己，胸肩展開。 | one hand on the hip with elbow out, opposite thumb pointing toward the chest, lifted open chest and shoulders |
| 40 | 歪嘴笑 | new_pose | 一手托下巴，另一臂橫胸托肘，肩與軀幹較鬆。 | one hand resting at the chin, opposite arm folded beneath the elbow, relaxed shoulders and torso |
| 41 | 自滿 | new_pose | 雙臂鬆抱胸，肩後展、胸稍挺，保持從容。 | arms loosely folded across the chest, relaxed shoulders held back, chest slightly lifted |
| 42 | 迷因咧嘴笑 | new_pose | 胸前雙手指尖相抵或交錯，上胸微前送，肩向內。 | steepled fingertips with slight tip overlap near the upper chest, elbows close, inward shoulders, chest subtly forward |
| 43 | 上尖括號眼微笑 | new_pose | 雙手輕握成小拳在臉頰旁，肘收、肩微抬。 | softly curled small fists beside the cheeks, elbows close, gently lifted shoulders |
| 44 | 失色 | new_pose | 雙肘彎在腹前，雙腕向下鬆垂，手指無力下彎。 | bent elbows with forearms before the abdomen, both wrists drooping downward, limp gently curved fingers |
| 45 | 驚恐 | new_pose | 雙掌朝外作防禦，五指張開、肘彎，肩高且上身後縮。 | both open palms outward defensively, fingers spread, bent elbows, high contracted shoulders, slightly recoiling chest |
| 46 | 尖叫 | new_pose | 雙手抬到耳側，指節彎曲張開，雙肘外張、肩聳。 | both hands beside the head, fingers spread and curved with tension, elbows flared, raised shoulders |
| 47 | 啜泣 | new_pose | 雙手指節或手背靠兩眼下方，肩內縮，呈擦淚手勢。 | both curled hands beneath the eyes, knuckles or backs close to the cheeks, inward hunched shoulders |
| 48 | 開懷大笑 | new_pose | 雙掌在肩旁舒展打開，雙肘外開，胸肩放鬆而開朗。 | both open hands beside the shoulders, comfortably spread fingers, elbows outward, relaxed welcoming chest |
| 49 | 受創呆滯 | new_pose | 雙小拳並收在胸前，雙肘貼身、肩聳，形成僵住的輪廓。 | both small fists held close together at upper chest, elbows pressed inward, rigid raised shoulders |
| 50 | 嚇得發白 | new_pose | 一手覆嘴，另一手貼胸，肩收緊、上胸僵直。 | one hand covering the mouth, opposite hand against the chest, tense inward shoulders, stiff upper torso |
| 51 | 波浪嘴 | new_pose | 雙手於胸前鬆彎手指、指尖互近，掌心保持小間隙。 | both hands close before the chest with loosely curled fingers and nearby fingertips, palms separated, hesitant inward elbows |
| 52 | 貓嘴 | new_pose | 雙手像小貓爪般抬在臉旁，手腕略內彎、雙肘貼身。 | both small curled hands beside the cheeks like playful paws, wrists gently inward, elbows close |
| 53 | 單眼眨眼 | reuse_default | 沿用 A，不新增肢體。 | — |
| 54 | 安靜害羞／靦腆 | reuse_default | 沿用 A，不新增肢體。 | — |
| 55 | 臉紅嘴硬／害羞不悅 | reuse_default | 沿用 A，不新增肢體。 | — |
| 56 | 疑問／困惑 | reuse_default | 沿用 A，不新增肢體。 | — |
| 57 | 方塊眼淡定吐槽笑 | reuse_default | 沿用 A，不新增肢體。 | — |
| 58 | 漫畫式擠眼驚呼 | reuse_default | 沿用 A，不新增肢體。 | — |
| 59 | 螺旋眼暈眩 | reuse_default | 沿用 A，不新增肢體。 | — |
| 60 | 吐舌眨眼 | reuse_default | 沿用 A，不新增肢體。 | — |

## 辨識與驗收

- 閉拳、鬆彎手指、爪狀彎指、開掌及鬆垂手腕分開處理。
- 胸前合手、低位交握、指尖相抵與掌間留空不是同一手型。
- 22 另一臂下垂、38 另一臂托肘、50 另一手貼胸，保留各自結構。
- 07 肘較收、33 肘較開；17 的聳肩緊拳、43 的放鬆小拳與 52 的內彎手腕不能只換臉代替。
- 非對稱動作以角色自身左右手記錄並固定，檢查手指、關節、袖口、手臉遮擋與接觸點。
