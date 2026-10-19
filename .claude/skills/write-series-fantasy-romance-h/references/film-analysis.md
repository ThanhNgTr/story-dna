# Phân tích phim: audit DNA + vì sao truyện giữ người xem

Run: `data/analyses/20261012-015632` | Thời điểm: 2026-10-12T03:30:00Z

Lưu ý chung:
- Truyện thật chỉ dài ~1422s (0-1421.93). Đoạn 1424.1-2842.17 là bản lặp, lệch đúng ~1424.0s (148.01 -> 1572.59; 1198.37 -> 2622.31). Mọi % ở đây tính trên 1422s.
- Mốc giây lấy từ ASR có thể lệch tới ~20s (xem A1). Khi có phụ đề burn-in thì ưu tiên phụ đề.
- Câu trích giữ nguyên tiếng Việt; lỗi chính tả ASR đã sửa theo phụ đề hoặc ngữ cảnh khi rõ ràng.

---

## A. Audit DNA

| # | Vấn đề | Bằng chứng | Sửa | Mức |
|---|---|---|---|---|
| A1 | Timestamp ASR bị nén theo cửa sổ ~30s. Câu bị dồn về đầu cửa sổ rồi im ~18-20s. Mọi mốc trong dna.json đều mang sai số này | 16 từ trong 1.36s: "Mà giờ không có ai đón đứa cháu trai lai dòng của mình lúc tan học." (97.07-98.43). Segment 0.07-11.43 chứa trọn pitch ~140 từ, segment sau ở 30.03. phim_c10 ghi `asr_t_sec 1179.63` nhưng `t_sec 1197`. Phụ đề "vươn tay định đẩy nhóc Viêm ra." ở 1332.30, ASR ghi 1325.84 | Coi mốc ASR là ±20s. Đo nhịp bằng phụ đề/shot. Pitch hook kết thúc ~29s, không phải 11.4s | high |
| A2 | `speech_pct 32.3%` và các luật về im lặng là do lỗi nén. Thực tế VO gần như liên tục | 10636 từ / 2842.2s = 224.5 từ/phút, khớp `words_per_min`: tốc độ này tính trên TOÀN bộ thời lượng, đúng nhịp TTS đọc liên tục. Mốc im lặng 1155.86 nằm giữa cửa sổ bị nén 1144.93-1169.03 | VO phủ ~85-95% (suy luận). Im lặng duy nhất có bằng chứng: 1419.84-1424.02 (end card) | high |
| A3 | % tính trên 2842s (có bản lặp) nên mọi vị trí sai gấp đôi. Insight "đánh mặt ở ~50%" sai | acts pct [0,5],[5,17],[17,34],[34,50]; cú đánh mặt 1337-1410 thực ra ở 94-99% truyện | Hồi 1 0-10%, Hồi 2 10-34%, Hồi 3 34-67%, Hồi 4 67-100%. Bỏ "act 5". Đánh mặt ở 90-100% arc | high |
| A4 | Luật "cắt giữa câu VO" dựa trên chỗ ASR cắt cửa sổ, không phải chỗ video cắt | Cùng audio, hai bản lặp cắt khác nhau: "tự biến mình thành bạn đời định mệ" (11.43) vs "Không hiểu sao tôi lại tự biến mình thành" (1434.3). "Mọi thứ thay" (1329.12) vs "Mọi thứ thay đổi hoàn" (2752.98). Thêm "Tôi đ" 99.69, "Tiếng h" 1068.54, "Ch" 2170.61 không phải điểm kịch tính | Bỏ khỏi pattern đã chứng minh. Chỉ dùng nếu phụ đề xác nhận | high |
| A5 | "Cậu bé là ai" bị ghi là mystery (mở 118, trả 1090). Thực ra hook đã nói đáp án nên đây là dramatic irony | VO 0-29s: "tôi lại nhặt trúng em trai cưng của Long Đế". Linh chỉ biết ở 1089.36: "Cậu đón nhầm người rồi." | Ghi là irony: khán giả biết ~25s, nhân vật biết ở 1090. Câu hỏi thật là "khi nào cô biết" | high |
| A6 | Động cơ của Viêm được VO nói thẳng, DNA lại ghi là suy luận ở 797 | "Sự thật là thằng bé hoàn toàn không muốn quay về." (534.35); "Nó muốn anh nó thấy người phụ nữ bị tẩy não đến mức tin rằng bản thân mình vô giá trị." (558.64) | answered_t ≈ 558. Bí ẩn giữ ~90s | medium |
| A7 | "Derik" là dấu vết bản địa hóa (dịch từ truyện tiếng Anh). "Chìa khoá" là backstory, không phải bí ẩn | phim_c15 1770.88: UI "Derik: There lying to yourself crazy."; phim_c14 1565.9 "chạm vào chiếc chìa khóa căn hộ, gã trả lại vào tuần trước." | Xoá hai câu này khỏi mystery_ledger/open_questions | medium |
| A8 | DNA bỏ sót chuỗi setup/payoff: lời nhục ở metro mô tả đúng việc Linh sẽ làm, quán dùng lại, Uy lật ngược | Metro (bản 2, 1484.08): "Hợp để thuê về trông trẻ và nấu ăn". Quán: "Giờ lại xách mông đi giữ trẻ cho mấy đứa nhãi rồng nhà giàu." (1232.62); "Đàn ông có thể thích đồ cô nấu" (1277.9); "dám công khai thừa nhận cô đâu" (1279.66) -> "Ai bảo chẳng ai dám công khai cô ấy sao. Thử nói lại lần nữa xem." (1409-1410) | Thêm vào craft: lời nhục = đức tính của nữ chính nhìn qua mắt khinh bỉ; payoff dùng lại chính câu đó | high |
| A9 | Gán sai người nói: "Đồ ngu xuẩn. Ngươi chán sống rồi à." là Viêm, không phải Khang | ASR "Đồ mua sụn." 1324.18; phim_c12 gán Khang (speaker_unsure); câu VO kế tiếp là "Thế Khang bật ra một tiếng cười lạnh" | Gán cho Viêm: đứa trẻ thách trước | medium |
| A10 | Cao trào 1329-1378 gần như không có lời trong transcript. Thiếu một hallucination trong danh sách loại bỏ | 1348.3/2772.21 "Hãy subscribe cho kênh Ghiền Mì Gõ...". Chỉ còn phụ đề "ĐOÀNG!" 1337.29, "Ly tách vỡ nát." 1354.67, "Cảnh Uy bước vào qua đống đổ nát." 1357.57. 611.41 "Các bạn hãy đăng ký kênh để ủng hộ kênh của mình nhé." chưa bị loại; bản 2 khôi phục "Đây là kẻ sinh ra đã đứng trên muôn người." (2038.11) | Thêm 611.41 vào dropped. Dùng bản lặp để điền lời bị mất | low |
| A11 | Ranh giới bản lặp lệch. Bản 2 dừng sớm | VO bản 2 bắt đầu 1424.16, không phải 1425.93. Bản 2 dừng ở "dám công khai cô ấy sao?" | Bản lặp 1424.1-2842.17. Câu chốt chỉ có ở bản 1 | low |
| A12 | Hook mâu thuẫn với thân truyện | "Nó cướp ly cà cao của tôi, ăn sạch sườn nướng" (1430.36) vs cô tự dúi cacao (235.33), món là "sườn bò om" (291.86) | Pitch là phóng đại hài, không phải sự kiện chính thức | low |
| A13 | `per_unit_ids` dùng part_01..03, còn file thật là phim_c01..c24 | dna.characters[*].per_unit_ids | Map theo unit id thật | low |

---

## B. Retention anatomy

### Hook
| Mốc | Hình | Lời | Chức năng |
|---|---|---|---|
| 0-3s | EWS thành phố mây có rồng -> cầu thang metro "UNDERGROUND" (3 shot, cắt đầu ở 2.0s) | "Ở thành phố này, loài rồng thống trị bầu trời," / "con người phải chật vật sinh tồn bên dưới." | Đặt luật thế giới + thứ bậc trên/dưới trước khi có người |
| 0-30s | Montage ~1.5s/shot: Linh ở metro, cặp đôi khoác tay, cậu bé sừng + cacao, sofa, người đàn ông tóc dài ở cửa ban công (26.7) | "tôi là Linh Khuê một cô gái nghèo bị gã người yêu cũ phũ phàng đá và sỉ nhục ... tôi lại nhặt trúng em trai cưng của Long Đế không hiểu sao tôi lại tự biến mình thành bạn đời định mệnh" | Pitch toàn bộ: luật -> vết thương -> tai nạn -> nhân vật hài -> twist -> lời hứa tình cảm. Tiết lộ twist trước để có irony |

### Nhịp reveal
- 32 sự kiện đổi truyện trong 1410s: **trung bình cách nhau 45.5s**, trung vị 37.9s, **dài nhất 112.9s**. Nếu tính cả các nhịp nhỏ (hook_moments của unit) thì cứ ~20-25s có một nhịp.

| Đoạn dài nhất không có tin mới | Gap | Thứ giữ người xem |
|---|---|---|
| 797-910 | 113s | Câu hỏi hài cài sẵn: "Cô cho thằng bé ăn thứ này sao?" (883.53) + "Rồi cơ thể anh hoàn toàn phản chủ." (890.21) -> khán giả chờ xem anh có ăn không. Tật kéo vạt áo (852.33) giữ vết thương sống |
| 502-590 | 88s | Hạn chót "Nửa tiếng nữa anh ấy sẽ đến đón tôi." (509.81) + VO kể động cơ của Viêm + chờ người tới |
| 419-502 | 82s | Đấu khẩu vui về anh trai; "Đợi anh ấy đến đây rồi xem." (451.17); đuôi vẫy |
| 0-81 | 81s | Pitch rồi chuỗi sỉ nhục ở metro |

### Mystery economy
| Câu hỏi | Loại | Mở | Khán giả biết | Nhân vật biết | Giữ |
|---|---|---|---|---|---|
| Linh biết mình là bạn đời định mệnh khi nào? | irony | ~29 | 770 | chưa | >1393s |
| Linh biết thân phận cậu bé khi nào? | irony | ~25 | ~25 | 1090 | 1065s |
| Người đàn ông ở ban công là ai? | mystery | 26.7 | 704 | - | 677s |
| Viêm bày mưu gì? | mystery | 468.8 | 558 | - | 90s |
| Ai "định giá" Viêm, vì sao không ai đón? | mystery | ~241 | chưa | - | >1180s |
| "Nếu có chuyện gì xảy ra" / hội đồng | promise | 1179 | 1357 (một phần) | - | 178s |
| Uy xử Khang ra sao? | cliff | 1410 | chưa | - | - |

- Số câu mở cùng lúc: 3 (30s) -> 4 (245) -> 5 (470) -> 3 (704) -> 2 (1090) -> 3 (1180) -> 3 (1410).
- Tỷ lệ mở/trả: 7 câu mở, 4 câu được trả ≈ 1.75:1. Các câu đã trả bị giữ trung bình ~500s.
- Mẫu: trả một câu thì mở ngay câu mới. 704 trả "người ban công" thì 770 mở "khế ước". 1090 trả "thân phận" thì mở mối đe dọa "Ngài có thể nghiền nát một người như kiến" (1095.12).

### Đường cảm xúc
| Hồi | Đáy | Đỉnh | Thứ kích hoạt |
|---|---|---|---|
| 1 (0-148) | Nhục ở metro; "Còn bây giờ tôi hoàn toàn vô cảm." (93.55) | Hài khô: "Đời tôi lúc này đâu thể tồi tệ hơn được nữa." (151.2) | Kẻ ác chê ngoại hình; cuộc gọi nhờ vả |
| 2 (148-481) | Voicemail "Cô chưa bao giờ là kiểu phụ nữ thuộc về giới thượng lưu đâu." (367.08) | "Lần này, nó không hất ra nữa." (268.74); "Hắn sai rồi." (392.65) | Đồ nóng; đứa trẻ bênh vực |
| 3 (481-958) | Muốn trốn: "Cứ nói với anh ấy là cô không có ở đây." (bản 2, 2045.35) | Kinh ngạc (sao băng 583), lãng mạn (hào quang 770), hài (ăn sạch sườn 910-956) | Màn xuất hiện hoành tráng; cơ thể phản chủ |
| 4 (958-1422) | Sâu nhất: "Phẩm giá tôi cất công hàn gắn ba tháng qua, vỡ vụn, chỉ trong tích tắc." (1283.4) | Hả hê: kính vỡ 1337, Khang quỳ 1380, ôm công khai 1385, "Thử nói lại lần nữa xem." 1410 | Bị nhục công khai lần 3 -> đứa trẻ nổ -> người quyền lực nhất bảo vệ công khai |

### Cliffhanger (11 điểm ngắt)
| Loại | Số | Ví dụ |
|---|---|---|
| Đe dọa/đối đầu sắp nổ | 3 | 239 cậu bé quay phắt; 1319 "hoàn toàn bùng nổ"; 1410 "Thử nói lại lần nữa xem." |
| Tin xấu/kẻ ác ập vào | 3 | 358 voicemail; 1104 "nghiền nát một người như kiến"; 1205 Khang vào quán |
| Giấu thông tin | 2 | 119 "Cháu trai nào cơ?"; 475 đuôi vẫy, "Tôi không nghe rõ chữ nào" |
| Xuất hiện quyền lực | 2 | 590 sao băng; 718 anh bước vào |
| Hồi hộp hài | 1 | 909 "Anh im lặng một thoáng." |

---

## C. Công thức viral (9 cơ chế)

| # | Cơ chế | Hoạt động thế nào | Bằng chứng | Áp dụng | Rủi ro |
|---|---|---|---|---|---|
| 1 | Pitch lộ twist trong 30s | Khán giả xem để biết "khi nào nhân vật biết", nên mọi cảnh nhân vật chưa biết đều thành hồi hộp | 0-29 "nhặt trúng em trai cưng của Long Đế"; Linh biết ở 1089 | VO 25-30s: luật, vết thương, tai nạn, twist, lời hứa. Để nhân vật tự phát hiện ở ~75% | Hứa mà không trả; pitch mâu thuẫn thân truyện |
| 2 | Thang sỉ nhục 3 bậc, trả bằng chính câu của kẻ ác | Mỗi lần nhục thì người chứng kiến đông hơn. Payoff công khai ngang mức đó và lặp nguyên văn lời kẻ ác | 81 / 362 / 1231-1281 "dám công khai thừa nhận cô đâu" -> 1409 "Ai bảo chẳng ai dám công khai cô ấy sao." | Câu nhục lần 3 phải bác được bằng hành động ("không ai dám X") | Payoff nhỏ hơn nợ; kẻ ác hoạt hình |
| 3 | Phép thử "không hỏi giá" | Nhân vật phụ nói to vết thương; nữ chính đáp bằng vật ấm, không hỏi han; lặp phép thử với nhân vật mạnh hơn | "Cứ hỏi tôi là ai, rồi định giá tôi đáng bao nhiêu." -> "Cô sẽ không hỏi gì cả" -> Uy ăn sạch đĩa 916 | Vết thương nói bằng lời một lần; đáp lại bằng một đồ vật cụ thể | Lòng tốt không tốn gì sẽ thành sến |
| 4 | Bà mai có kế hoạch ngầm và nói hộ tiềm thức | Nhân vật phụ sắp xếp cuộc gặp và nói ra điều cặp chính không dám nói | 502 "Giống y như trong kế hoạch."; 647 "...không đáng để người khác nhìn thấy"; 797 "Anh, anh thích cô ấy."; 1031 "đừng diễn kịch nữa" | Mỗi tập bà mai vạch mặt một người | Cặp chính thành bị động |
| 5 | Miệng chối, cơ thể khai | Lời nói lạnh, dấu hiệu cơ thể nói thật; mỗi lần chối vụng hơn | 800 "trong này hơi nóng"; 884 "Tôi ăn ở dinh thự rồi." -> sạch đĩa; 981 tai đỏ; 1036 ở lại | 1-2 dấu hiệu cơ thể riêng, leo thang thành hành động | Lặp mà không leo thang thì nhàm |
| 6 | Thân phận lộ qua người thứ ba, kèm lời cảnh báo | Một tin vừa trả lời tò mò vừa sinh xung đột: nữ chính tự đẩy anh ra | 1088-1117 "Long Đế của hai cõi... Đừng để ngài ấy nghĩ cậu đang cố tiếp cận huyết mạch hoàng gia để trục lợi." -> 1147 "Không ai cả." | Đặt reveal ngay sau khoảnh khắc yên bình nhất, qua điện thoại, kéo theo một lời nói dối | Hiểu lầm kéo dài gây ức chế (ở đây chỉ ~50s) |
| 7 | Đảo nghĩa một từ khoá | Câu tự hạ được nói 2 lần, nam chính dùng chính từ đó để định nghĩa lại | 449 "hai thế giới hoàn toàn khác biệt" -> 1149 "không cùng một thế giới" -> 1178 "nếu tôi nói chúng ta cùng một thế giới thì chính là như vậy" | Chọn 1 từ khoá gắn với vết thương | Gieo muộn thì câu đáp nghe sáo |
| 8 | Nghi thức xuất hiện của kẻ mạnh | Được gọi -> có hạn chót -> hiệu ứng từ xa -> lộ dần từ chân lên mặt. Cao trào lặp lại nghi thức, nhanh hơn | 502 -> 509 "Nửa tiếng nữa" -> 583 sao băng -> 599-632 từ ủng lên mặt; 1198 "Tôi sẽ có mặt." -> 1357.57 "bước vào qua đống đổ nát" | Hứa có điều kiện ở tập trước cao trào | Phụ thuộc VFX; dùng quá 2 lần thì mất sức nặng |
| 9 | Đang yên ấm thì bị điện thoại cắt ngang | VO tuyên bố bình yên, ngay sau đó kênh tin xấu cố định reo | 339.78 "mọi thứ bỗng chốc trở nên nhẹ nhàng." -> 341.28 voicemail; 1065.0 "Anh hoàn mỹ đến bức ngỡ như không có thực." -> cuộc gọi của Hân Nghi | Chọn một kênh tin xấu cố định | Khán giả đoán trước được, cần đổi người gửi |

---

## D. Chia tập 60-120s

Cơ sở: điểm ngắt mạnh trung bình ~140s một lần; sự kiện đổi truyện ~45s một lần. Cắt 1422s thành 13 tập.

| Tập | Thời gian | Dài | Mở bằng | Đóng bằng |
|---|---|---|---|---|
| 1 | 0-119 | 119 | Pitch 30s | "Cháu trai nào cơ?" |
| 2 | 119-239 | 120 | "Cháu bên nhà chồng mình" | Cậu bé quay phắt |
| 3 | 239-343 | 104 | "Cứ hỏi tôi là ai..." | "Rồi Thế Khang gửi một tin nhắn thoại đến." |
| 4 | 343-475 | 132* | Voicemail phát | Đuôi vẫy, quyết định ngầm (*có thể tách ở 392) |
| 5 | 475-590 | 115 | Cuộc gọi bí mật | Sao băng đáp xuống |
| 6 | 590-704 | 114 | Lộ từ ủng lên mặt | Khoá cửa kêu, anh bước vào |
| 7 | 704-800 | 96 | Mắt vàng khoá vào cô | "Anh, anh thích cô ấy." |
| 8 | 800-910 | 110 | "trong này hơi nóng" | "Anh im lặng một thoáng." |
| 9 | 910-982 | 72 | Anh cắn miếng sườn | Tai đỏ, "Có điều gì đó sai sai." |
| 10 | 982-1097 | 115 | Giằng co có ở lại không | "nghiền nát một người như kiến" |
| 11 | 1097-1207 | 110 | Cảnh báo trục lợi | "Tôi sẽ có mặt." -> Khang bước vào |
| 12 | 1207-1320 | 113 | Khang tiến tới bàn | "hoàn toàn bùng nổ" |
| 13 | 1320-1422 | 102 | Vung tay | "Thử nói lại lần nữa xem." |

### Khung nhịp cho một tập 90s
| Nhịp | Giây | Quy tắc |
|---|---|---|
| Hook | 0-3 | Nối thẳng vào khung cliffhanger tập trước, không recap dài |
| Trả nợ tập trước | 3-15 | Trả một phần, nhưng câu trả lời mở ra câu hỏi mới |
| Setup | 15-40 | VO đặt mục tiêu nhỏ của tập + 1 chi tiết vết thương |
| Turn | 40-65 | Sự kiện đổi truyện #1: phản ứng trái kỳ vọng |
| Reveal | 65-80 | Sự kiện #2: thông tin mới hoặc dấu hiệu cơ thể mới + 1 câu chốt ngắn |
| Cliffhanger | 80-90 | 1 trong 5 loại; cắt TRƯỚC phản ứng |

Co giãn: tập 60s thì setup còn 10s; tập 120s thì thêm 20-25s cảnh ấm/hài giữa turn và reveal.

### Quy tắc mở/đóng tập
1. Mở bằng câu/hình nối tiếp cliffhanger, trả lời trong <15s.
2. Mỗi tập có ít nhất 2 sự kiện đổi truyện.
3. Không 2 tập liền nhau dùng cùng loại cliffhanger.
4. Sau tập đau/nhục, tối đa 1 tập là phải có cảnh ấm hoặc hài.
5. Luôn giữ 2-5 câu hỏi mở; trả một câu thì mở một câu mới trong cùng tập.
6. Tập 1 = pitch + vết thương + tai nạn khởi động.
7. Tập cuối arc = trả nợ công khai bằng đúng câu nhục, cắt trước phán quyết.

---

## E. Động cơ nhân vật

**Vì sao khán giả đứng về phía nữ chính**
- Vết thương: bị đo giá trị bằng ngoại hình/giai cấp: "Bây giờ trông cô như thể đã hoàn toàn bỏ bê bản thân vậy." (365.42).
- Mong muốn: không bị nhìn thấy trong bộ dạng tồi tàn: "Cứ nói với anh ấy là cô không có ở đây." (2045.35).
- Hy sinh: cho đi thứ ít ỏi của mình: "Tôi gắp hai miếng sườn to nhất vào bát nó." (313.09).
- Hài tự giễu giúp cô không đáng thương: "vì dường như vũ trụ có khiếu hài hước quá tồi tệ" (1203.81).
- Irony: khán giả biết bí mật của cô, còn cô thì không -> khán giả muốn che chở cô.

**Áp lực**
- Kẻ ác: là giọng của xã hội, leo thang 3 lần (81, 362, 1231).
- Luật thế giới: "khoảng cách giữa mặt đất dưới chân tôi và bầu trời trên những tầng mây" (1123.27).
- Hạn chót: "Nửa tiếng nữa" (509.81), "sáng mai chúng ta sẽ đi" (1035.41), hội đồng gọi đi (1174.15). Đều là hạn chót chia ly, nên áp lực là tình cảm, không phải hành động.
- Bên trong: mặc cảm khiến cô tự đẩy anh đi: "Thưa Bệ hạ, ngài nên đưa Cảnh Viêm về đi." (1150.11).

**Thang quan hệ**
| Cặp | Các bậc | Quy tắc |
|---|---|---|
| Nữ - đứa trẻ | từ chối 216 -> nhận đồ ấm 266 -> nắm tay 268 -> bênh vực 392 -> chỉ ra vết thương của cô 647 -> lấy thân che chắn 1322 | Mỗi bậc là một lần chạm hoặc một câu nói thật |
| Nữ - nam | nhìn 704 -> hào quang 770 -> ăn đồ cô nấu 910 -> chạm tay 977 -> ở lại 1036 -> bị đẩy ra 1149 -> "cùng một thế giới" 1178 -> ôm công khai 1385 | Nam tiến một nấc, nữ lùi một nấc, cho đến khi cô bị kéo vào |
| Nam - đứa trẻ | được gọi 502 -> bị vạch mặt 797/1031 -> đến khi em gặp nạn 1357 | Đứa trẻ vừa là cầu nối vừa là cò súng |

**Vai phụ dùng để làm gì**: đứa trẻ = tai nạn khởi động + chủ đề + bà mai + cò súng của cao trào. Bạn thân = mở truyện bằng lời nhờ, báo thân phận + cảnh báo, đứng về phía nữ chính ("Thế Khang, ngậm cái miệng thối của anh lại." 1307.11). Người yêu cũ + bạn gái = kho lời nhục, mỗi câu là một setup. Đám đông = thước đo mức công khai.

---

## F. Thoại và VO

- **Tỷ lệ**: ~65-75% số câu là VO (suy luận; mẫu 1198-1330 có ~30 câu VO / ~16 câu thoại). VO dùng cho luật thế giới, miêu tả kẻ mạnh, đọc tâm, tự giễu, chuyển thời gian ("Chiều tối hôm sau," 481.38). Thoại dùng cho va chạm, câu chốt, điện thoại.
- **Độ dài**: thoại 3-12 chữ ("Hắn sai rồi." 3 chữ). Kẻ ác nói dài nhất. Nam chính ít thoại nhất (33 dòng vs Linh 573, tính cả bản lặp): **quyền lực = ít lời**. VO 8-30 chữ.
- **Mẫu lặp lại**: phủ định + phản chứng bằng hành động; liệt kê hành động thay lời khen; chối bằng lý lẽ vụng; câu hỏi tu từ đánh vào vết thương; đảo nghĩa từ khoá; một câu VO ngắn đóng mỗi nhịp; phán quyết bằng mệnh lệnh ngắn.

| Câu (nguyên văn) | Mốc | Người nói | Tác dụng |
|---|---|---|---|
| "Các người đều giống nhau. Cứ hỏi tôi là ai, rồi định giá tôi đáng bao nhiêu." | ~241 | Viêm | Nói to chủ đề qua vết thương |
| "Được rồi. Cô sẽ không hỏi gì cả... Nếu dở quá, cháu cứ chê thoải mái." | ~250 | Linh | Đáp bằng điều ngược lại, giữ thể diện cho đứa trẻ |
| "Đời tôi lúc này đâu thể tồi tệ hơn được nữa." | 151.2 | Linh VO | Tự giễu, rồi cắt sang bước ngoặt |
| "Hắn sai rồi. Cô không giống như hắn nói." | 392.65 | Viêm | Lần đầu có người đứng về phía cô |
| "Sao cô cứ luôn hành động như thể mình không đáng để người khác nhìn thấy vậy?" | 647.43 | Viêm | Gọi tên điểm yếu của nữ chính |
| "Anh không có, chỉ là trong này hơi nóng, anh ngột ngạt vì em cứ bám lấy anh đấy." | 800.23 | Uy | Chối vụng = thú nhận, biến định mệnh thành hài |
| "Hơn nữa, lãng phí thức ăn là không tốt." | 943.25 | Uy | Lý do giả, câu đùa đóng cảnh |
| "Chúng ta thật sự không cùng một thế giới." | 1149.27 | Linh | Nữ chính tự đóng cửa |
| "Ở thành phố này, nếu tôi nói chúng ta cùng một thế giới thì chính là như vậy." | 1178.07 | Uy | Đảo nghĩa bằng quyền lực |
| "Nhưng chẳng người đàn ông nào có danh tiếng, tiền bạc hay quyền lực dám công khai thừa nhận cô đâu." | 1279.66 | Khang | Lời nhục bác được bằng hành động |
| "Thử nói lại lần nữa xem." | 1410.26 | Uy | Phán quyết; bắt kẻ ác tự lặp lại lời mình |

---

## G. Điểm yếu không nên copy

| Điểm yếu | Bằng chứng | Nên làm |
|---|---|---|
| Phát lại toàn bộ truyện để kéo dài video | 0-1421.93 = 1424.1-2842.17 | Tập nào cũng có nội dung mới; recap ≤5s |
| Lộ POV: người kể ngôi thứ nhất biết điều cô không thể biết | 765.68 giải thích khế ước trong khi cô "chẳng hề mảy may hay biết" (794.47); đọc tâm Viêm 534-561, 1008.39 | Chọn rõ một kiểu kể, hoặc để thông tin đi qua nhân vật khác |
| Kẻ ác không có động cơ, xuất hiện nhờ trùng hợp | voicemail 362.91; "vì dường như vũ trụ có khiếu hài hước quá tồi tệ" (1203.81) | Cho kẻ ác lợi ích riêng và lý do có mặt |
| Nữ chính bị cứu hai lần, không tự hành động | 1306 bạn thân, 1337 đứa trẻ, 1357-1410 nam chính; Linh chỉ sợ (phim_c12 sc04) | Cho cô ít nhất một hành động chủ động trong cao trào |
| Lỗ logic: đứa trẻ quý nhất đứng một mình, nhà không đi tìm | "không có tài xế nào chờ nó" (1608.4); "Giống y như trong kế hoạch." (502.05) | Đưa ra một lý do và gắn nó vào bí ẩn |
| Lời hứa của pitch không được trả | "bạn đời định mệnh" (~29s); sau 1008 không nhắc lại | Nữ chính phải tự biết bí mật lớn ở ~75% mùa |
| Sáo: chê ngoại hình, nhục giai cấp kiểu mẫu | 852.33 "vòng eo hơi tròn"; 1326.3 "con bảo mẫu mạt hạng" | Giữ cơ chế, nhưng đổi sang vết thương riêng của nhân vật |
| VO kể lại điều hình đã cho thấy | 828.08, 977.15; ~224 từ/phút liên tục | VO chỉ nói điều hình không nói được |
| Nhịp chùng ở cảnh ăn sườn | 797-910 không có sự kiện lớn | Nén còn ~60s hoặc chèn thông tin mới |
| Pitch nói sai sự thật | 1430.36 "cướp ly cà cao... sườn nướng" vs 235.33, 291.86 | Pitch có thể hài nhưng phải khớp sự kiện |

---

## Quy tắc hàng đầu cho người viết

1. Mở tập 1 bằng pitch 25-30s nói luôn twist danh tính. Dùng dramatic irony thay cho việc giấu bí mật.
2. Cho nữ chính một vết thương cụ thể và để kẻ ác nói nó thành lời. Kẻ ác hạ nhục 3 lần, người chứng kiến đông dần.
3. Lần nhục thứ 3 là một lời khẳng định "không ai dám X". Payoff là làm X trước đúng đám đông đó và nhắc nguyên văn câu ấy.
4. Một nhân vật phụ nói to chủ đề qua vết thương của họ. Nữ chính đáp bằng một vật ấm cụ thể, không bằng lời.
5. Bà mai có mục tiêu riêng, sắp xếp các cuộc gặp, mỗi tập vạch mặt một người bằng một câu ngắn.
6. Nam chính càng quyền lực càng ít lời. Cảm xúc lộ qua 1-2 dấu hiệu cơ thể, và dấu hiệu leo thang thành hành động.
7. Kẻ mạnh xuất hiện theo nghi thức: được gọi -> hạn chót -> hiệu ứng từ xa -> lộ từ chân lên mặt. Cao trào lặp lại nghi thức, nhanh gấp đôi.
8. Cứ 30-45s một sự kiện đổi truyện. Mỗi tập ≥2 sự kiện, kết bằng 1 trong 5 loại cliffhanger, không lặp loại liền nhau.
9. Cảnh ấm kết bằng VO tuyên bố bình yên, rồi kênh tin xấu cố định cắt ngang.
10. Lộ thân phận qua người thứ ba kèm lời cảnh báo, ngay sau khoảnh khắc yên bình nhất, kéo theo một lời nói dối của nữ chính.
11. Gieo một từ khoá vết thương: nữ chính nói 2 lần, nam chính đảo nghĩa ở lần 3.
12. Đặt cú đảo quyền lực công khai ở 90-100% arc. Nữ chính phải có ít nhất một hành động chủ động trong cao trào.
