# Phân tích phim: kiểm tra DNA và vì sao phim giữ chân người xem

- Run: `20261019-025904` · nguồn: 1 video dọc 9663.6s (khoảng 161 phút), 81 unit
- Thời điểm phân tích: 2026-10-21T12:00:00Z
- Chỉ làm việc trên văn bản (dna.json, story.md, transcript, unit files). Không xem khung hình.

**Ghi chú về thời gian.** Mốc ASR có chỗ sớm hơn phụ đề Hán cứng 16-18s. Ví dụ ở c09: phụ đề `和我结婚` hiện ở 1038.1, còn ASR ghi "Kết hôn với tôi" ở 1022.1. Vì vậy mốc lấy từ transcript có thể lệch tới khoảng 20s.

**Ghi chú về trích dẫn.** Giữ nguyên văn ASR. Chỉ chuẩn hóa tên riêng (Hoác thành Hoắc, Tân/Tầng thành Tần, "bản đường" thành Vãn Đường). Chỗ ASR nghe nhầm thì ghi cách đọc đúng trong [ngoặc vuông].

---

## A. Kiểm tra DNA (không sửa dna.json)

| ID | Mức | Vấn đề | Bằng chứng | Sửa |
|---|---|---|---|---|
| A1 | high | Số liệu tốc độ nói, speech_pct và khoảng lặng không tin được vì mốc ASR bị trôi, còn mốc từ bị rải đều trong các đoạn gộp. | c09: phụ đề 1038.1 nhưng ASR 1022.1. "Tôi là chủ nhà họ Tần." dài 0.44s (5391.67-5392.11), tức khoảng 13.6 âm tiết/s, không thể có. DNA ghi 158 wpm, "khoảng 200 wpm ở vả mặt", khoảng lặng 1039.3-1040.5. | Không đặt luật nhịp thoại từ transcript này. Dùng giới hạn 5.0 âm tiết/s của vi-dialogue.md. Đặt beat theo mốc phụ đề hoặc thẻ. |
| A2 | high | Câu hỏi về mẹ ruột thật đã có lời đáp, nhưng DNA ghi "độ chắc thấp" và để trong open_questions. | 8859 "Tôi đã chuông [chôn] một người Cô có biết người đó là ai không"; 9193.83 "Mẹ ơi, tuy là con không nhớ rõ hình dáng của mẹ nữa Nhưng kiếp sau..." và "Bác à, bác cứ yên tâm Sau này con sẽ chăm sóc tốt cho Vãn Đường"; 9397 "Chúng ta đều đã mất mẹ". | Đóng câu hỏi ở 9193.8. Mẹ ruột đã chết, gần như chắc là người bị "chôn" (inferred, chứng cứ mạnh). |
| A3 | high | Bỏ sót chuỗi bẫy dội ngược. "Món quà lớn" bị coi là suy luận. Tuyến ly hôn bị gắn nhầm là "không nhất quán". | 469-473 Hoắc: "Cho cậu ta uống ... Khoan đã Ký cái này Rồi hãy cho uống"; 913 video; 951 VO Lục Thịnh: "Nếu ông nội [ông đội] biết mình đã ký tên Chắc chắn sẽ đánh mình chết"; 1773 "Sớm đưa cho tôi bản ly hôn mà Lục Thịnh đã ký". | Thêm sự kiện 470 và 951. Tuyến ly hôn nhất quán: ký 473, Hoắc giữ, giao lại 1773, công bố 1507. |
| A4 | high | Khán giả biết Thư Tú giật dây sớm hơn khoảng 14 phút so với DNA. | 2918-2951 Thư Tú: "Rơi vào tay nó mới tốt ... Tần Thiệu Hùng sẽ căm ghét nó đến chết, ra tay giết người"; 2951 "Tần Thư Tú và Lâm Kiều Kiều. Kiện [Việc] này tạm thời không thể nói cho Vãn Đường biết được". DNA đặt mốc trả lời ở 3763.4. | Ghi hai mốc riêng: khán giả biết ở khoảng 2918, phe đồng minh xác nhận ở 3763. |
| A5 | high | Luật "nam chính giấu chuyện để kéo 2-3 tập hiểu lầm" bị nói quá. | 4653-4656 "Chuyện này tôi đã biết rồi Yên tâm, tôi không yếu đuối đến vậy đâu"; 9039 Lục Du: "Cứ nhìn tôi chạy ngược chạy xuôi". | Sửa luật: người khác có thể giấu, nhưng nữ chính gần như luôn đã biết. Việc giấu không làm cô trông ngốc. |
| A6 | medium | Tuyến Tạ Nhiên sai mốc và thiếu: khán giả biết cậu là con Thư Tú ở 5580 (DNA ghi 6924); cậu làm lộ phòng 8606; có ơn cũ từ hồi tưởng. | 4216-4220 "Số phòng của nó là bao nhiêu 8606"; 5578 "Dừng tay đi Mẹ"; 6898 "Là cậu đã tiết lộ xuất [số] phòng của Vãn Đường ra ngoài"; 6729-6823 hồi tưởng "Tôi có được ngày hôm nay Tất cả là nhờ chị". | Thêm mốc 4220 và 6729. Ghi mô thức "ơn cũ được trả", lặp lại ở 9480 "lúc đó em cứu anh". |
| A7 | medium | Thiếu rào cản vai vế; "đầu độc" thật ra là chất gây nghiện. | 7432 "Vì [Vị] này chính là Tần Thư Tú"; 7556 "Cô Vãn Đường đó là cô của cháu. Cháu cưới cô của mình"; 8155 "chất kê nghiệm [gây nghiện]"; 8718 "không thể cai được". | Thêm vào obstacles. Đổi "đầu độc" thành "cho dùng chất gây nghiện". |
| A8 | medium | Gán người nói đáng ngờ, thiếu nhân vật. | Câu 1655 "nể tình cô ấy là người mà anh thầm yêu nhiều năm" gán cho "PR của Hoắc", trong khi Nguyên Nhã là "nữ hoàng truyền thông của Giang Thành" (3245). Phương Mặc (3133, 4955, 9161) không có id. Unit c52 gán VO của nữ chính cho Kiều Kiều. | Câu 1655 nhiều khả năng của Nguyên Nhã (inferred). Thêm Phương Mặc. Sửa người nói trong c52. |
| A9 | medium | Đoạn recap khoảng 80s không được đánh dấu, lại bị đếm là clue mới. | 6141-6222 phát lại thoại gốc ở 1021/1038, 1575, 3661, 4062, 5642. c52 đếm 6155 clue, 6178 setup, 6191 reveal. | Đánh dấu là recap, loại khỏi phép đếm nhịp. |
| A10 | medium | reveal_rhythm_sec = 23 không có cách tính. | plot_timeline: trung bình 174s, trung vị 115s, lớn nhất 643s. Unit: 201 hook, khoảng 48s một. | Thay bằng ba mức đo ở phần B. |
| A11 | medium | Thông tin sai "con gái của Tần Thư Tú" được cài từ 317.5. Đó là lời báo cáo trong cảnh, không phải giọng ngoài hình. | 317.5 "Tôi điều tra rồi Cô Vãn Đường đó là con gái của Tần Thư Tú". DNA ghi mở bí ẩn ở 2028.9. | Ghi 317.5 là lúc cài thông tin sai. Thông tin này được tin suốt 6547s. |
| A12 | low | Mọi break candidate đều strength 3, nên không xếp hạng được. | 39 mục, trong khi unit có 78 mục strength 3. | Chấm lại. Xem phần D. |
| A13 | low | "Bí mật trước hôn lễ" bị ghi là chưa trả lời. | 9390 "Bí mật Xong rồi cô sẽ biết thôi", rồi 9596 "Em đồng ý". | Đóng ở 9596. |
| A14 | low | ASR ảo giác bị đếm là thoại. | "Hãy subscribe cho kênh Ghiền Mì Gõ..." ở 258.8, 1241.9, 3949, 5941.6. | Loại khỏi số liệu thoại. |
| A15 | low | Ghi sai người trả 600 tỷ. | 5754-5758 phe Lục trả "150 tỷ ... 240 tỷ". 5782 người trả 600 tỷ là Hoắc. | Sửa relationship_map. |
| A16 | low | "Cold open" có thể do người ghép tạo ra. | Thẻ 未完待续 ở 10.54s (c01). | Inferred: đừng chép "tập 10 giây". Chỉ chép chức năng mở giữa xung đột. |
| A17 | low | Người nói cuộc gọi con tin chưa chắc. | 2475 "Muốn gặp Từ Việt Đến số 325 đường Giang Bắc một mình" là câu của kẻ bắt cóc. | Ghi speaker_unsure. |
| A18 | low | ASR nghe nhầm câu của ông cụ Lục nên dễ hiểu ngược. | 8090 "Cố Vãn Đường Đây là cái bẫy mật của ta dăng ra [cái bẫy mà nó giăng ra] Tôi chết không nhắm mắt mà". | Ông nhận ra cô giăng bẫy, không phải ông tự thú. |

---

## B. Giải phẫu giữ chân người xem

### Hook

| Mốc | Những gì có trên hình | Lời thoại | Tác dụng |
|---|---|---|---|
| 0-3s | Một shot duy nhất (cắt đầu tiên ở 4.96s): nữ chính ngồi bất động, mẹ chồng đứng quát | 0.29 "Cố Vãn Đường Thịnh nhà tôi bây giờ đang bị đám phóng viên giải trí Bây giờ [chặn ở] khách sạn rồi Cô mau tìm cách đưa nó ra ngoài đi"; 2.79 "Vậy sao Nhưng mà đám phóng viên đó là do tôi sắp xếp hết á" | Hook chỉ bằng lời: khủng hoảng, rồi người bị đòi nhận chính mình gây ra |
| 3-30s | Shot/phản shot cận mặt; thẻ 未完待续 ở 10.54 | "Bảo sao con trai tôi không thèm động vào cô"; "Bảo con trai bà li hôn với tôi cho sớm đi"; 27.4 "Ơn tình nợ nần sớm đã trả hết rồi" | Có đủ món nợ, cuộc hôn nhân không tình, và ly hôn do cô chủ động |
| 30-62s | ECU vết đỏ trên cổ (38s), bảo vệ lôi mẹ chồng | 31.4 "Y chang con mẹ hồ ly tinh đã chết của cô"; 61.8 "Làm ơn hiểu rõ Là tôi muốn đá con trai bà" | Cài bí ẩn về mẹ, rồi chốt câu đảo vai |

### Nhịp reveal

| Thước đo | Giá trị |
|---|---|
| Sự kiện lớn (56 mục trong plot_timeline) | trung bình 174s, trung vị 115s, lớn nhất 643s (4744.5 đến 5387.4) |
| Theo hồi (trung bình giữa hai sự kiện) | H1 101s · H2 193s · H3 319s · H4 191s · H5 147s |
| Hook trong unit | 201 hook (khoảng 48s một) · 78 hook mạnh (khoảng 124s một) |
| Thẻ mini-tập | khoảng 100 (số của DNA), tức khoảng 97s một tập |

Đoạn dài nhất không có tin mới là **6141-6222**: recap khoảng 80s toàn thoại cũ. Cái giữ người xem ở đây là cảm xúc dồn lại sau khi cô từ chối Tạ Nhiên ("Người mà trong lòng tôi nghĩ đến Vẫn là Hoắc Vân Thâm"). Đoạn này chốt bằng một quyết định mới: "Xem ra tôi thực sự đã rơi vào tay của anh rồi" (6222).

Khoảng 643s giữa hai sự kiện lớn được lấp bằng các cú xoay nhỏ:
- 4838 "bà nội mới"
- 4902 dự án của Hoắc bị dừng
- 5024 "Món quà này Anh có bất ngờ không?"
- 5076 "Muốn thực sự vào nhà họ Hoắc Phải kết hôn trước"
- 5192 "Còn dẫn theo bạn nhảy nữa"

### Kinh tế bí ẩn

| Câu hỏi | Mở | Khán giả biết | Trả lời | Giữ (s) |
|---|---|---|---|---|
| Ai bỏ thuốc | 231.7 | 2918 | 3763.4 | 3532 |
| Kế hoạch ly hôn riêng | 656.2 | | 1773.6 | 1117 |
| Vì sao Hoắc muốn cưới | 1022.1 | | 1655.3 (gốc rễ ở 9480) | 633 |
| Thư Tú có phải mẹ ruột | 317.5 (cài thông tin sai) / 2028.9 | | 6864.8 (đầy đủ 8957) | 4836 |
| Từ Việt ở đâu | 1739.4 | | 3684.8 | 1945 |
| "Món quà lớn" | 633 | | 913.2 | 280 |
| Tạ Nhiên muốn gì | 2110.1 | 5580 | 6924.6 | 4814 |
| Ai gửi kẻ đột nhập 8606 | 4385.6 | | 5580 | 1195 |
| Mẹ ruột thật ở đâu | 6869 | | 9193.8 | 2325 |
| Ông nội Hoắc bị gì | 7665 | | 8155 | 490 |
| "Bí mật" trước cưới | 9393.9 | | 9596 | 202 |
| Hoắc sắp đặt đêm khách sạn? | 9486 | | bỏ ngỏ có chủ ý | |

- Số câu mở cùng lúc: 3 (700s), 3 (1700s), **4 (2200-3000s, đỉnh)**, 3 (4500s), 2 (6000s), 1 (7000s), 3 (7700s), 2 (8500s), 1 (9550s).
- Tỉ lệ mở/trả lời ở tầng lớn: 12:11. Thời gian giữ trung bình 1942s, trung vị 1195s, tối đa 4836s.
- Tầng nhỏ: khoảng 263 câu mở so với 41 câu trả lời ngay trong cùng unit (khoảng 6:1, tức khoảng 3.2 câu mở mỗi 2 phút).
- Luật thấy được: câu lớn vừa đóng thì một câu lớn hơn mở ngay. Ví dụ 6864 "không phải mẹ", rồi 6869 "Mẹ ruột của tôi ở đâu?".

### Đường cảm xúc

| Hồi | Đỉnh | Đáy | Cái kích hoạt |
|---|---|---|---|
| 1 (0-1931) | 61.8 đá chồng; 425 hạ côn đồ; 629 mời nhảy; 1536-1567 bản kê, "bản phô tô"; 1625 người kế vị | 1398-1427 "Quả nhiên cũng chẳng đáng tin" | Bị sỉ nhục công khai, rồi phản đòn bằng giấy tờ |
| 2 (1931-3846) | 2111 Tạ Nhiên; 3460 180 tỷ; 3539 thừa kế; 3661 "Tôi thương em" | 2506-2561 bị đánh; 2711-2775 chuyện cũ; 3571 tối hậu thư | Nguy hiểm thân thể, rồi được cứu hoặc tỏ tình |
| 3 (3846-6718) | 5391 "Tôi là chủ nhà họ Tần"; 5782 600 tỷ; 6588 nắm cổ tay | 5518-5611 "Ai cũng đều muốn tính kế tôi"; 6370-6554 sân thượng; đoạn hài 4452-4598 | Chiếm vị trí quyền lực; lòng tốt |
| 4 (6718-8632) | 7091 "em thích anh"; 8090 bẫy đất; 8355 "là người của tôi" | 6864-7041 không phải mẹ; 8319 Hoắc bị đuổi | Đau vì thân phận, rồi đảo vai cứu người |
| 5 (8632-9663) | 9054-9106 lửa; 9567 tự lập; 9596 cưới | 9193 mộ mẹ | Kẻ thù liều chết; kết đền bù cả tình lẫn độc lập |

Nhạc: inferred. Transcript không có nhạc nền.

### Cliffhanger ở chỗ ngắt tập (39 mục của DNA)

| Nhóm | Số lượng | Ví dụ |
|---|---|---|
| Reveal (cắt giữa câu 6, thân phận, phản diện, bí mật) | 13 | 4780.9 "Là ai đã thu mua Là cung"; 5592 "Dừng tay đi Mẹ" |
| Nguy hiểm (con tin, sống còn 3, tối hậu thư, mất tích) | 10 | 2493 "Đến số 325 đường Giang Bắc một mình"; 3579 "Trước 8 giờ sáng mai" |
| Đảo thế (vả mặt, tuyên bố, bẫy dội ngược) | 10 | 5391 "Tôi là chủ nhà họ Tần. Tôi quyết định." |
| Tình cảm (chọn công khai, nụ hôn, cử chỉ lớn) | 5 | 5787 "Tôi muốn dùng 600 tỷ này đấu giá sợi dây chuyền này tặng cho cô Cố Vãn Đường" |
| Mất mát (bị đuổi) | 1 | 8319 "Thì ông coi như không có đứa cháu như mày" |

---

## C. Công thức viral (10 cơ chế)

| # | Cơ chế | Cách hoạt động | Bằng chứng | Áp dụng cho truyện khác | Rủi ro |
|---|---|---|---|---|---|
| 1 | Nạn nhân hóa ra là tác giả | Bị đòi dọn hậu quả, nhân vật chính lộ ra chính mình dựng tình huống. Khán giả được nhận vào kế hoạch muộn một nhịp. | 2.79 "đám phóng viên đó là do tôi sắp xếp hết á"; 1567 "bản phô tô"; 7343 "Lừa anh đó"; 8090 ông cụ Lục nhận ra bẫy | Mỗi màn đối đầu có sẵn một nước đi đã chuẩn bị 1-2 tập trước. Để kẻ địch nói hết lời rồi mới lật. | Biết hết thì hết căng. Cần những lần thua thật (1398, 2506, 8319). |
| 2 | Bẫy dội ngược | Bẫy của kẻ địch quay lại đánh họ, kèm một lợi ích phụ (chữ ký, bằng chứng). | 469-473 "Ký cái này Rồi hãy cho uống", rồi video 913; 4385 phòng 8606; 3512 "Tôi đương nhiên là lừa anh ta rồi" | Viết bẫy cùng lúc với cách nó dội ngược. Cho khán giả thấy bẫy được giăng trước (289 "May mà có em bày kế hay"). | Lặp thì đoán được. Đổi loại bẫy và đổi người lật bẫy. |
| 3 | Vả mặt bằng sổ sách trước đám đông | Một tài liệu với con số lẻ, có người chứng kiến, cắt sang mặt kẻ thua. | 1536 "368 triệu 254 nàng [nghìn] 361 đồng 5 hào 6 xu"; 3461 "180 tỷ"; 4744 quy tắc cổ phần | 3-5 tập một lần, con số đọc to, có một nhóm chứng kiến. | Đơn điệu nếu không xen tình cảm hoặc lòng tốt. |
| 4 | Thang phản diện leo dần | Kẻ thù mới, gần hơn về máu mủ, bước vào ngay khi kẻ cũ gục. | 1923 cậu; 2918/3763 "mẹ"; 8957 kẻ đánh tráo "Đều phải nằm trong tay tôi" | 3 bậc: kẻ ngoài, kẻ trong họ, kẻ đội lốt người thân. Bậc cuối có mặt từ sớm. | Bậc cuối chỉ có độc thoại giải thích thì nhạt. |
| 5 | Người quyền lực đã chọn cô từ trước | Tình cảm của người yêu có từ trước câu chuyện và hé từng lớp. | 1048 "không chỉ ba lần đâu"; 1655 "thầm yêu nhiều năm"; 7835 công ty ngầm; 9480 "lúc đó em cứu anh" | Chia backstory thành 4-6 mảnh, 10-15 tập thả một mảnh. Mảnh cuối là việc nhân vật chính từng làm cho họ. | Hoàn hảo quá thì mất xung đột. Cho một thói xấu thật. |
| 6 | Callback đổi vai | Câu cũ quay lại với người nói hoặc thế lực đảo ngược. | 1048 và 8415 "phóng viên vây trước cửa nhà mình ... không ngại"; 5083 và 7069 "Người vợ tôi chọn Chỉ có mình em"; 4659 và 5788 "họ Cố" | Lưu 5-8 câu chữ ký ở nửa đầu, cho quay lại một lần ở nửa sau. | Nếu thành recap cả cảnh (6141-6222) thì là đệm. |
| 7 | Cắt giữa câu, trả lời trong 20s | Tập kết ở câu nói dở; tập sau trả lời ngay rồi mở cái mới. | 119.43 "Là anh?" trả lời ở 119.59; 5027 "Nhưng bây giờ" trả lời ở 5047; 6843 "Tần Thư Tú bà ta..." trả lời ở 6864 | Cắt trước danh từ hoặc tên quyết định. | Phần trả lời tầm thường thì khán giả thấy bị lừa. |
| 8 | Không bao giờ là người cuối cùng biết | Người khác giấu, nhưng nữ chính đã biết. Phản diện mới là người bị bỏ lại. | 4656 "Chuyện này tôi đã biết rồi"; 9012 "Định mượn tay người khác để truy cùng giết tận tôi" | Mỗi lần đồng minh giấu chuyện, trong 5-10 tập phải có cảnh cô lộ ra là đã biết. | Cần ít nhất một cú sốc thật (6864) để còn cảm xúc. |
| 9 | Tha kẻ thù đã gục, nhận lại sau | Cứu và tha phản diện phụ; họ trả ơn bằng bằng chứng. | 6610 "Nếu cô thật lòng xin lỗi Thì đừng nghĩ đến chuyện tìm chết nữa"; 8563 "Đây là thứ Lâm Kiều Kiều để lại ... Là bằng chứng" | Tha ở 65-70% mùa phim, nhận lại ở 85-90%. | Tha kẻ ác nặng thì thấy bất công. Họ phải đã bị phạt công khai. |
| 10 | Nháy mắt với thể loại | Nhân vật gọi tên cái sến ngay lúc nó xảy ra. | 1575 "Cái lời thoại sánh xuống [sến súa] này của anh Xem phim ngắn nhiều quá rồi hả?"; 8540 "Thiên Kim thật giả, chị em thật giả" | Khoảng 1 lần mỗi 20 tập, sau câu thề hoặc cú twist lố. | Dùng nhiều thì phá stake. |

---

## D. Chia tập 60-120 giây

Căn cứ: 201 hook (khoảng 48s một), 78 hook mạnh (khoảng 124s một), khoảng 100 thẻ (khoảng 97s một). Kết quả là **98 tập**, trung bình 98.6s (56.5-126.1s). Có 9 tập trên 120s cần cắt bớt (22, 52, 53, 59, 62, 63, 68, 84, 88) và 3 tập dưới 60s (2, 37, 92). Mốc có thể lệch khoảng 20s (ASR).

| Tập | Mốc (s) | Kết bằng | Loại |
|---|---|---|---|
| 1 | 0-61.8 | "Là tôi muốn đá con trai bà" | đảo vai |
| 2 | 61.8-121.3 | "Là anh?" / "Tổng Giám Đốc Hoắc?" | cắt giữa câu |
| 3 | 121.3-210.7 | "gói dịch vụ li hôn" + "Người đàn ông này bị sao vậy?" | điều kiện |
| 4 | 210.7-317.5 | "con gái riêng của nhà họ Tần ... bị đuổi khỏi nhà từ rất sớm" | manh mối thân phận |
| 5 | 317.5-422.9 | "từng người một hay là lên cùng lúc đây" | thách thức |
| 6 | 422.9-542.6 | "Ký cái này Rồi hãy cho uống" + tiệc sinh nhật | bẫy dội ngược |
| 7 | 542.6-631.1 | "làm bằng [bạn] nhảy của tôi không?" | chọn công khai |
| 8 | 631.1-692.4 | "Vậy nếu là 2 tỷ thì sao?" + trốn | áp lực thời gian |
| 9 | 692.4-800.1 | "kế hoạch của cô, thì tôi sẽ nói cho cô" + roi da | giao kèo/đe dọa |
| 10 | 800.1-913.2 | TV phát video | phơi bày |
| 11 | 913.2-1009.7 | phóng viên chất vấn | áp lực dư luận |
| 12 | 1009.7-1126.6 | "Kết hôn với tôi" | đảo vai |
| 13 | 1126.6-1188.6 | hôn cưỡng, ngã | phản ứng |
| 14 | 1188.6-1286 | "Quá nhiên là cao thủ ấn mình Vậy thì" | cắt giữa câu |
| 15 | 1286-1347.5 | số bằng son + "Chụp được rồi" | mối đe dọa |
| 16 | 1347.5-1448.5 | "đừng có trách ông độc ác" | mất mát |
| 17 | 1448.5-1561.4 | bản kê / xé đơn | trả đòn |
| 18 | 1561.4-1645.8 | "đón người kế vị" | thân phận |
| 19 | 1645.8-1746.6 | "người trong tứ đại gia tục [tộc]" | bí ẩn |
| 20 | 1746.6-1846 | "cũng có thấy anh gọi cho tôi đâu" | tình cảm |
| 21 | 1846-1923.2 | lệnh cướp nam chính + kính râm | mối đe dọa |
| 22 | 1923.2-2045.7 | "Tôi chính là mẹ ruột của Cố Vãn Đường mà" | phản bội |
| 23 | 2045.7-2111.9 | "Ai nói không có nam chính?" | vả mặt |
| 24 | 2111.9-2174 | "Có hôn bước [ước] từ nhỏ" | tình địch |
| 25 | 2174-2290 | "Có qua có lại" | nước đi |
| 26 | 2290-2380 | "Đâu có giống Hoắc tổng để có vợ sắp cưới?" | tình địch |
| 27 | 2380-2493.8 | "Đến số 325 ... một mình" | con tin |
| 28 | 2493.8-2561.5 | Hoắc ngược sáng | giải cứu |
| 29 | 2561.5-2646.2 | "Là người của nhà họ Tần" | gợi ý phản diện |
| 30 | 2646.2-2749.2 | khách bị cướp | mất mát |
| 31 | 2749.2-2860 | "Cậu ra ta [tay] độc ác với tôi sao" | đối đầu |
| 32 | 2860-2927.8 | "bà muốn giết cô ta rồi thư kế [thừa kế] tài sản sao" | bí mật tối |
| 33 | 2927.8-3009.4 | ông ngoại phát bệnh | y tế |
| 34 | 3009.4-3105.4 | Hoắc đến đổi nam chính | tình địch |
| 35 | 3105.4-3222.2 | "Liên quan gì tới cô?" | tình cảm |
| 36 | 3222.2-3319.8 | "Vậy tôi gọi cho em trước" | tình cảm |
| 37 | 3319.8-3379.5 | "Cô đừng có mà không biết điều" | mối đe dọa |
| 38 | 3379.5-3460.9 | 180 tỷ | vả mặt |
| 39 | 3460.9-3579.5 | "Trước 8 giờ sáng mai" | tối hậu thư |
| 40 | 3579.5-3661.7 | "Tôi thương em." | tình cảm |
| 41 | 3661.7-3765.5 | "... là Tần Thư Tú" | lộ phản diện |
| 42 | 3765.5-3880.7 | Tuấn Thành dẫn Kiều Kiều đến phim trường | mối đe dọa |
| 43 | 3880.7-3975 | "Cô dám từ chối sao?" | tối hậu thư |
| 44 | 3975-4083 | nụ hôn khi say | tình cảm |
| 45 | 4083-4186.5 | "Tôi đang thông báo cho anh" | tuyên bố |
| 46 | 4186.5-4282.4 | "8606" / "không nhớ gì về tôi hết" | bí mật |
| 47 | 4282.4-4385.6 | kẻ đeo mặt nạ | bẫy dội ngược |
| 48 | 4385.6-4452.7 | "ở cùng một phòng Không được" | hài |
| 49 | 4452.7-4566.8 | "Thật ra tôi..." | cắt giữa câu |
| 50 | 4566.8-4675.4 | "đổi sang họ Cố" | tuyên bố |
| 51 | 4675.4-4780.9 | "Là cung" | cắt giữa câu |
| 52 | 4780.9-4902 | dự án bị dừng | mất mát |
| 53 | 4902-5027.1 | "Tôi rất vui Nhưng bây giờ" | cắt giữa câu |
| 54 | 5027.1-5112.6 | "Em đưa cho Lục Thịnh đi" | xoay kế hoạch |
| 55 | 5112.6-5196.8 | "Còn dẫn theo bạn nhảy nữa" | tình địch |
| 56 | 5196.8-5310.1 | dây chuyền của "dì Thư Tố [Tú]" | mối đe dọa |
| 57 | 5310.1-5391.7 | "Tôi là chủ nhà họ Tần. Tôi quyết định." | tuyên bố |
| 58 | 5391.7-5469.6 | nghe lén | bí mật |
| 59 | 5469.6-5592.2 | "Dừng tay đi Mẹ" | cắt giữa câu |
| 60 | 5592.2-5703.1 | "Chị thực sự muốn đấu giá nó sao" | quyết định |
| 61 | 5703.1-5787.1 | 600 tỷ | cử chỉ lớn |
| 62 | 5787.1-5913.2 | "đã gửi đi giám định rồi" | bí ẩn |
| 63 | 5913.2-6037.4 | ảnh lên báo | bê bối |
| 64 | 6037.4-6141.5 | "Vẫn là Hoắc Vân Thâm" | tình cảm |
| 65 | 6141.5-6261 | recap + "rơi vào tay của anh" + bê bối | mối đe dọa |
| 66 | 6261-6349.4 | "Lâm Kiều Kiều mất tích rồi" | mất tích |
| 67 | 6349.4-6467.8 | kể tội trên sân thượng | đối đầu |
| 68 | 6467.8-6588.8 | nắm cổ tay | sống còn |
| 69 | 6588.8-6706.7 | "Có lẽ chị đã không nhớ nữa rồi" | bí ẩn |
| 70 | 6706.7-6767.4 | hồi tưởng bị bắt nạt | chuyện cũ |
| 71 | 6767.4-6867.9 | "Tần Thư Tú không phải mẹ của em" | cắt giữa câu |
| 72 | 6867.9-6958.9 | "Lục Du ... mẹ ruột của tôi ở đâu?" | thân phận |
| 73 | 6958.9-7070 | "Người vợ mà tôi chọn" | tình cảm |
| 74 | 7070-7166.4 | "Anh không thể ở lại với em sao" | tình cảm |
| 75 | 7166.4-7259.4 | "Cút khỏi nhà họ Tần" | phản diện gục |
| 76 | 7259.4-7372.2 | "Cá lớn cắn cầu [câu]" | bẫy dội ngược |
| 77 | 7372.2-7460.5 | "Vì [Vị] này chính là Tần Thư Tú" | mối đe dọa |
| 78 | 7460.5-7560.6 | "Cháu cưới cô của mình" | rào cản |
| 79 | 7560.6-7670.5 | "đã xét nghiệm máu chưa" | bí ẩn |
| 80 | 7670.5-7785.2 | Tuấn Thành nắm quyền | mất mát |
| 81 | 7785.2-7873.5 | "qua lại với ông của anh" | bí mật |
| 82 | 7873.5-7985.9 | "54.000 tỷ" | bẫy |
| 83 | 7985.9-8092.3 | "Tôi chết không nhắm mắt mà" | phản diện gục |
| 84 | 8092.3-8218.3 | liên hôn trong một tháng | tối hậu thư |
| 85 | 8218.3-8319.1 | bị đuổi khỏi nhà | lưu đày |
| 86 | 8319.1-8421.6 | "Hoắc Vân Thâm là người của tôi" | nữ chính giải cứu |
| 87 | 8421.6-8541 | "thuốc cấm" | reveal |
| 88 | 8541-8663.3 | "Cô ta muốn xử lý bà" | mối đe dọa |
| 89 | 8663.3-8751.5 | "Hoắc gia không phải là nơi bà có thể làm loạn" | vả mặt |
| 90 | 8751.5-8862.7 | "Cô có biết người đó là ai không" | bí mật tối |
| 91 | 8862.7-8961.7 | "phẫu thuật hơn 100 lần" | thân phận |
| 92 | 8961.7-9018.2 | "tay của mình thì vẫn trong sạch" | buộc tội |
| 93 | 9018.2-9106.7 | "xuống địa ngục" | sống còn |
| 94 | 9106.7-9219.2 | mộ mẹ | tang |
| 95 | 9219.2-9338.2 | "âm thầm điều tra tin tức của cô" | reveal tình cảm |
| 96 | 9338.2-9455.3 | Tạ Nhiên ra đi | chia tay |
| 97 | 9455.3-9547.6 | "Chỉ có thể là anh" / "Là ý gì?" | cắt giữa câu |
| 98 | 9547.6-9663.6 | "đối thủ cạnh tranh" + "Em đồng ý" + [Hết phim] | kết |

### Khuôn beat mỗi tập (mẫu 90s, co giãn theo %)

| Beat | Giây (mẫu 90s) | % | Làm gì | Bằng chứng trong nguồn |
|---|---|---|---|---|
| Hook | 0-8 | 0-9% | Trả lời nửa còn lại của cliffhanger cũ, hoặc nhắc lại mối đe dọa | 119.59; 2506 "Tôi đến rồi"; 5047; 6864 |
| Setup | 8-25 | 9-28% | Một thông tin mới qua trợ lý, điện thoại hoặc tít báo | 2746 / 3880 "Sếp, không hay rồi"; 6030 tít báo |
| Turn | 25-50 | 28-56% | Đối thủ ép: sỉ nhục, luật, hạn chót | 3571; 5076; 8211 |
| Reveal | 50-75 | 56-83% | Nước đi đã chuẩn bị, tài liệu, đồng minh, sự thật | 1536; 2111; 3460; 5391 |
| Cliffhanger | 75-90 | 83-100% | Cắt giữa câu, người mới vào, CU phản ứng + thẻ | 4780.9; 1923; 5787 |

### Luật mở và đóng tập
1. Mở: trả lời cliffhanger cũ trong 20 giây đầu, rồi mở ngay một hệ quả mới.
2. Đóng: kết trên câu dở, người mới vào, hạn chót hoặc mặt sững sờ, không kết trên cảnh đã khép. Câu hỏi nhỏ trả lời trong 1-3 tập.
3. Mỗi tập đẩy ít nhất một câu hỏi trong sổ bí ẩn hoặc một bước quan hệ.
4. Cứ 3-5 tập có một màn đảo thế công khai có người chứng kiến.
5. Cứ khoảng 10 tập có một reveal lớn đổi cục diện (1625, 2918/3763, 5391, 6864, 8957).
6. Không để 3 tập liền kết bằng cùng một nhóm cliffhanger.
7. Beat tình cảm đặt ngay sau beat nguy hiểm (3661 sau 3571; 7091 sau 6952).
8. Tối đa 4 câu hỏi lớn mở cùng lúc.
9. Recap tối đa 15-20s, và phải kèm một quyết định mới.

---

## E. Động cơ nhân vật

**Vì sao người xem đứng về phía nữ chính**
- **Vết thương:** bị gia đình bỏ rơi: "Ông cụ Tần ... đuổi cô ấy ra khỏi nhà Hãy còn ra lệnh phong sát toàn ngành ... kể cả mẹ ruột của cô cố, không một ai giúp cô ấy" (2711-2745). Cô quỳ vay tiền nhà Lục (2768) và lấy chồng để trả ơn (1139). Hồi đi học bị sỉ nhục vì tiếng xấu của mẹ (7005).
- **Mong muốn:** thoát hôn nhân giao dịch: "Chẳng qua cũng chỉ là từ một cuộc giao dịch này đổi sang một cuộc giao dịch khác" (1164); "lấy lại tất cả những gì thuộc về tôi" (4774).
- **Hy sinh:**
  - đến một mình cứu con tin (2506)
  - nói thẳng "Tôi đã nói với ông là tôi không cần rồi" (3571)
  - đem bảo vật gia truyền ra đấu giá (5724)
  - liều mình cứu kẻ thù (6610)
  - bỏ Tần thị để tự lập (9567)
- **Điều cần học:** "Bởi vì tôi biết, tôi chỉ có thể dựa vào chính mình" (3638), rồi "Vậy thì cứ thử dựa dẫm vào anh một chút đi" (5642).
- Cô giỏi, tốt với kẻ yếu ("sao có thể để một đám ngốc bắt nạt chứ?" 6766), và biết tự giễu bằng VO ("Mình là tổng đại viên [tổng đài viên] hả?" 3043).

**Áp lực được tạo ra thế nào**

| Loại | Bằng chứng |
|---|---|
| Phản diện theo bậc | nhà chồng (0-1931), rồi cậu Thiệu Hùng và anh họ Tuấn Thành, rồi "mẹ" Thư Tú tức Lục Du (2918-9161) |
| Luật | 4744 luật cổ phần; 5076 "Phải kết hôn trước"; 5331 dây chuyền "bảo vật trấn gia" (ASR: bấu vật trấn nha) chỉ chủ nhân đeo |
| Hạn chót | 3571 "Trước 8 giờ sáng mai"; 4157 "Ba ngày nữa sẽ chính thức bấm máy"; 8211 "trong vòng một tháng" |
| Đòn bẩy | khóa thẻ (33.76), rút vốn (87), con tin (2506), ảnh khách sạn (1367), vai vế "Cháu cưới cô của mình" (7557) |

**Quan hệ leo thang.** Người cho và người nhận đổi vai sau mỗi bước, nên luôn có một món nợ mới:
mua một đêm (119.6), điều kiện (203), kế hoạch đổi kế hoạch (772), cầu hôn (1038), từ chối (1139), thề bảo vệ (1575), ghen (2350), cứu (2561), "Tôi thương em" (3661), hôn (4062), cô tặng đất (5024), 600 tỷ (5782), cô tỏ tình (7091), cô cứu anh (8355), anh lao vào lửa (9054), cưới (9596).

**Dàn phụ dùng để làm gì**

| Ai | Để làm gì | Bằng chứng |
|---|---|---|
| Trợ lý nữ | Kể thông tin qua báo cáo, đồng ca hài | 1678 "Đã quá, sếp ơi"; 4564 rút lui đúng lúc |
| Trợ lý nam (Phương Mặc, chưa có id) | Đối xứng, lo hậu cần cứu hộ | 3133, 4955, 9161 |
| Bạn làm truyền thông | Vũ khí dư luận, kể quá khứ của nam chính, fan cặp đôi | 2289 "Có qua có lại"; 9280-9338 |
| Tình địch trẻ | Chứng minh nữ chính tự chọn; cầu nối tới phản diện | 6090 "Tôi cũng không muốn làm em trai"; 6924 "Thật ra là mẹ tôi" |
| Kẻ thù gương | Bản nghèo của nữ chính, phép thử lòng tốt, sau đó trả bằng bằng chứng | 6490 "Còn tôi thì sao?"; 8563 |
| Thuộc hạ | Con tin, rồi người điều tra | 2506; 3760-3765 |
| Các ông nội | Dùng ơn nghĩa và máu mủ để trói | 835; 3006 "không cần dùng đạo đức để trái [trói] buộc cháu"; 4866 |
| Hôn thê bị ép | Mối đe dọa hôn nhân sắp đặt | 5218; 5404 "Em gái ngoan" |

---

## F. Thoại và VO

**VO và thoại.** Khoảng 5.5% số câu được gắn nhãn VO (68/1241). VO xưng "mình" và dùng cho ba việc:
- nữ chính tự giễu khi bị bất ngờ (119.59, 210, 230, 2556, 3042)
- phản diện lộ toan tính (951, 8001, 8687)
- nam chính điều tra ngầm (5435)

Tít báo cũng được đọc to (6030, 7750). Mọi đối đầu, đàm phán và tỏ tình đều là thoại trực tiếp.

**Độ dài câu.** Câu đối đáp thường 3-12 âm tiết. Bài nói 40-90 âm tiết chỉ có ở ba chỗ: tuyên bố trước báo chí (1481-1542), kẻ thù gục kể tội (6460-6554), phản diện tự thú (8900-8990). Không đo được tốc độ nói (A1).

**Mẫu câu lặp lại**

| Mẫu | Ví dụ |
|---|---|
| Không phải A, mà là B | 61.8 "Là tôi muốn đá con trai bà"; 3661 "Không phải vì hợp tác ... Mà là vì... Tôi thương em."; 5788 "không phải họ Tần, mà là họ Cố" |
| Điều kiện soi gương | 1773 "Muốn tôi Cố Vãn Đường sụp đổ Vậy thì tôi sẽ để cho nhà họ Lục sụp đổ trước" |
| Câu hỏi tu từ làm đòn | 1567 "Bà đang nghĩ cái gì vậy?"; 2351 "Anh là cái gì của tôi?" |
| Châm ngôn về ân nghĩa | 27.4 "Ơn tình nợ nần sớm đã trả hết rồi"; 3164 "Thứ tôi muốn chưa bao giờ là ân tình" |
| Con số làm cú chốt | 1536 "368 triệu 254 nàng [nghìn] 361 đồng 5 hào 6 xu"; 1018 "6 triệu đủ không?" |
| Tuyên bố hai câu cụt | 5391 "Tôi là chủ nhà họ Tần. Tôi quyết định." |

**Câu nguyên văn và tác dụng**

| t | Câu | Tác dụng |
|---|---|---|
| 2.79 | "Vậy sao Nhưng mà đám phóng viên đó là do tôi sắp xếp hết á" | Hook: lật vai nạn nhân |
| 61.8 | "Làm ơn hiểu rõ Là tôi muốn đá con trai bà" | Đổi khung bị bỏ thành chủ động bỏ |
| 1164.9 | "Chẳng qua cũng chỉ là từ một cuộc giao dịch này đổi sang một cuộc giao dịch khác." | Nói thẳng chủ đề |
| 1536.4 | "Tổng cộng 368 triệu 254 nàng [nghìn] 361 đồng 5 hào 6 xu" | Vả mặt có bằng chứng |
| 1575 | "Cái lời thoại sánh xuống [sến súa] này của anh Xem phim ngắn nhiều quá rồi hả?" | Nháy mắt với thể loại |
| 3661.2 | "Mà là vì... Tôi thương em." | Tỏ tình bằng phép loại trừ |
| 5391.7 | "Tôi là chủ nhà họ Tần. Tôi quyết định." | Giành quyền trước đám đông |
| 5787.3 | "Sau này nó không phải họ Tần, mà là họ Cố." | Callback biến món quà thành lời công nhận |
| 8356 | "Hoắc Vân Thâm là người của tôi Nhà họ Hoắc không chú chấp [chứa chấp] anh ấy Thì tôi cần anh ấy" | Đảo vai người cứu |
| 9105.5 | "Vậy thì các người hãy đi cùng với tôi xuống địa ngục đi." | Đẩy stake lên mạng sống ở 94% |

---

## G. Điểm yếu không nên chép

| Vấn đề | Bằng chứng | Không chép, thay bằng |
|---|---|---|
| Recap đệm khoảng 80s | 6141-6222 | Recap tối đa 20s, kèm quyết định mới |
| Hồi 3 võng nhịp | Hồi 3 trung bình 319s mới có một sự kiện lớn (Hồi 1 là 101s); khoảng 643s ở 4744-5387; đoạn hài 4452-4598 | Khoảng 10 tập một reveal lớn; đoạn hài tối đa 1 tập |
| Tiền bạc lộn xộn | 600 tỷ nhưng phụ đề 2亿; 54.000 / 48.000 / "6.000 tỷ" / "Hơn 900 nghìn tỷ" (7340-8779) | Lập bảng tiền tệ trong bible |
| Lỗ hổng về kẻ đánh tráo | "phẫu thuật hơn 100 lần" (8957) nhưng 20 năm không ai nghi, một lần giám định là lộ | Cho lý do không bị thử, cài manh mối từ trước |
| Tuyến bị bỏ rơi | Tạ Nhiên làm lộ phòng (6898) mà không chịu hậu quả; ông nội "đưa đến viện dưỡng lão" (8718); lửa "không làm kinh động tới người khác" (9161) | Lỗi nào cũng có giá; giải quyết cao trào trên màn hình |
| Cứu giây cuối | 2561; 9161 | Cài trước đường tới của người cứu |
| Sáo mòn có rủi ro | hôn cưỡng (1160); bẫy thuốc và quay video (289-396); âm thanh tình dục (710); "kỹ năng trên giường" (4818) | Bỏ; thay bằng xung đột ý chí (nền tảng video có thể từ chối) |
| Phản diện tự thú bằng độc thoại dài | 8859-9044 | Rải động cơ qua 3-4 cảnh trước |
| Nam chính kiểm soát bằng giấu | 3815; 4124; 9507 | Cho nữ chính chất vấn, cho nam chính trả giá |
| Vai vế mâu thuẫn | 317 "con gái riêng"; 5246 "cô chủ nhà họ Tần chính thống"; 7557 "cô của cháu" | Vẽ cây gia phả, kiểm tra theo address_matrix |

---

## Luật hàng đầu cho biên kịch

1. Ba giây đầu: một người đòi nhân vật chính dọn khủng hoảng, nhân vật chính bình thản nhận chính mình gây ra nó.
2. Trong 60 giây đầu phải có câu đảo vai (từ bị bỏ thành chủ động bỏ) và một bí ẩn về gốc gác được cài.
3. Mỗi tập 60-120s chia hook 0-9%, setup 9-28%, turn 28-56%, reveal 56-83%, cliffhanger 83-100%. Tập sau trả lời cliffhanger trong 20 giây đầu.
4. Viết bẫy của phản diện cùng lúc với cách nó dội ngược, kèm thứ nhân vật chính lấy được nhân dịp đó.
5. Cứ 3-5 tập có một màn đảo thế công khai bằng tài liệu hoặc con số lẻ, có người chứng kiến, cắt sang mặt kẻ thua.
6. Phản diện leo ba bậc: kẻ ngoài, kẻ trong họ, kẻ đội lốt người thân. Bậc cuối phải có mặt từ 5% đầu mùa.
7. Tối đa 4 câu hỏi lớn mở cùng lúc. Đóng một câu thì mở ngay một câu lớn hơn. Câu lớn giữ 20-80 phút, câu nhỏ trả lời trong 1-3 tập.
8. Cho khán giả biết trước một nhịp, nhưng nhân vật chính không bao giờ là người cuối cùng biết.
9. Người yêu có tình cảm từ trước câu chuyện, hé từng lớp; mảnh cuối là ơn nhân vật chính từng làm cho họ.
10. Lưu 5-8 câu chữ ký ở nửa đầu, cho chúng quay lại ở nửa sau với người nói hoặc thế lực đảo ngược.
11. Ở khoảng 65-70% mùa phim, tha cho một phản diện đã gục; ở khoảng 85-90% họ trả ơn bằng bằng chứng.
12. Không recap quá 20s, không hôn cưỡng, giữ thang tiền và cây gia phả nhất quán trong bible.
