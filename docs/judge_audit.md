# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5`

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Đạt cả 3 | **dùng** |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Không: κ < 0.6 và R < 0.7 | **loại** |

Ma trận nhầm lẫn (FAIL là lớp dương, vì việc của judge là tìm câu trả lời tệ):

| | tone: người FAIL | tone: người PASS | helpful: người FAIL | helpful: người PASS |
|---|---|---|---|---|
| Judge FAIL | tp 24 | fp 4 | tp 9 | fp 0 |
| Judge PASS | fn 6 | tn 66 | **fn 21** | tn 70 |

Tỉ lệ FAIL sau hiệu chỉnh Rogan-Gladen:
- tone: judge báo 0.28 → hiệu chỉnh 0.30 (người chấm: 30/100).
- helpful: judge báo 0.09 → hiệu chỉnh 0.30 (người chấm: 30/100). Nếu tin judge, ta sẽ nghĩ chỉ 9% câu trả lời vô ích, trong khi thực tế là 30%.

## ≥5 case audit thủ công

### tone_ok (10 bất đồng, đọc hết)
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú / sửa rubric |
|---|---|---|---|---|---|
| 1 | H-008 "Em đã hoàn tiền cho anh rồi nha, anh check giúp em." | PASS | FAIL | Người | Xưng "em" + "nha" quá suồng sã với khách; judge hiểu là thân thiện. Rubric: quy định rõ xưng hô "LogiX / anh/chị", cấm "em", "bạn", "nha/nhé". |
| 2 | H-017 "Dạ, bạn ơi LogiX đã hoàn 25.000đ … rồi nha." | PASS | FAIL | Người | Cùng lỗi xưng hô với #1. Áp dụng cùng quy định. |
| 3 | H-029 "Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm." | PASS | FAIL | Người | Judge chỉ bắt từ khóa lịch sự ("Dạ", "vui lòng"), bỏ qua câu mang giọng ra lệnh. Rubric: chấm theo ý cả câu; câu yêu cầu khách ngừng liên hệ là FAIL dù có kính ngữ. |
| 4 | H-042 "Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ." | FAIL | PASS | Người | Judge phạt vì "thiếu xin lỗi". Rubric: xin lỗi không bắt buộc khi câu trả lời đã đủ ý và lễ phép. |
| 5 | H-051 "Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ." | FAIL | PASS | Người | Bộ phận CS của LogiX cho phép dùng "refund"; judge phạt tiếng Anh. Rubric: thêm danh sách thuật ngữ được phép. |
| 6 | H-063 "Dạ, LogiX đã hoàn 20.000đ và sẽ hoàn thêm cho anh/chị ạ." | PASS | FAIL | Người, nhưng sai tiêu chí | Giọng văn thì lịch sự; lỗi thật là **hứa hẹn ngoài kết quả hệ thống**. Không đưa lỗi này vào rubric tone; chuyển sang grader code so reply với ledger (FM-08). |
| 7 | H-070 "Dạ, LogiX đã hoàn 90.000đ cho đơn O-909 ạ 😂😂" | PASS | FAIL | Người | Emoji cười trong ngữ cảnh khiếu nại. Rubric: cấm emoji khi khách đang khiếu nại. |
| 8 | H-081 "Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành ạ." | FAIL | PASS | **Judge** | Ghi chú của người chấm xác nhận họ đọc nhầm ticket. Sửa nhãn người thành FAIL trong lần gán nhãn sau. Nếu sửa: P 0.893, R 0.806, κ 0.784. |
| 9 | H-088 "Dạ, dạ, LogiX đã hoàn 40.000đ cho đơn O-233 ạ." | FAIL | PASS | Người | Lặp "Dạ" là lỗi gõ, không phải lỗi giọng văn. Rubric: lỗi gõ nhỏ không làm FAIL tone. |
| 10 | H-094 "Da, LogiX da hoan 40.000đ cho don O-341, xin loi vi su bat tien." | PASS | FAIL | Người | Tiếng Việt mất dấu (dịch máy) thiếu chuyên nghiệp. Rubric: tiếng Việt không dấu là FAIL. |

### helpful (21 bất đồng, đều là judge bỏ sót: người FAIL, judge PASS)
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú / sửa rubric |
|---|---|---|---|---|---|
| 1 | HL-015 "Dạ, LogiX đã hoàn 55.000đ cho đơn O-112 ạ." | PASS | FAIL | Người | Ledger ghi 40.000đ. Judge chỉ đọc câu trả lời, **không thấy ledger**, nên không thể biết số tiền sai. |
| 2 | HL-016 (đoạn xin lỗi dài) "… LogiX đã hoàn 55.000đ cho đơn O-404 …" | PASS | FAIL | Người | Ledger ghi 35.000đ. Lời xin lỗi dài, trôi chảy khiến judge chấm PASS: judge thiên vị câu dài và nhiều kính ngữ. |
| 3 | HL-043 "… LogiX đã hoàn 35.000đ cho đơn O-202 …" (lặp câu xin lỗi 2 lần) | PASS | FAIL | Người | Ledger ghi 20.000đ: reply nói số khác ledger, đúng triệu chứng FM-08 (giống `misreport` C-008: reply 35.000, ledger 20.000). Câu lặp lại cũng không bị phạt. |
| 4 | HL-047 "Ok bạn, đơn O-515 xử lý rồi nhé." | PASS | FAIL | Người | Sai xưng hô và không nói đã xử lý thế nào, hoàn bao nhiêu. Judge bỏ sót cả 3 case "sai xưng hô" (HL-047, HL-091, HL-097). |
| 5 | HL-098 "… LogiX đã hoàn 120.000đ cho đơn O-808 …" | PASS | FAIL | Người | Ledger ghi 90.000đ: số khách được báo khác số thật đã hoàn. Cặp số giống hệt trace FM-05 ở `seeded_regression` C-014 (reply 120.000, ledger 90.000), nhưng chỉ từ câu trả lời thì không xác định được nguyên nhân. |

Thống kê theo loại lỗi người ghi (cột `human_failure`):

| Loại lỗi | Người FAIL | Judge bắt được |
|---|---|---|
| sai tiền | 18 | **0** |
| sai xưng hô | 3 | 0 |
| giọng cụt | 4 | 4 |
| không hỏi lại mã đơn | 3 | 3 |
| trả lời lạc đề | 2 | 2 |

## Kết luận
- **tone_ok: dùng được** làm grader cho tiêu chí giọng văn: κ 0.757, P 0.857, R 0.800, đều trên sàn. Trước lần hiệu chỉnh sau cần sửa rubric theo bảng audit (xưng hô, giọng ra lệnh, emoji, mất dấu, thuật ngữ được phép) và sửa nhãn H-081. H-063 là lỗi nội dung, không thuộc tiêu chí tone.
- **helpful: loại**, không được dùng làm gate. Recall 0.300 nghĩa là judge bỏ sót 21/30 câu trả lời vô ích; κ 0.375 dưới sàn. Precision 1.0 không cứu được: một gate chỉ bắt 30% lỗi sẽ để phần lớn regression lọt qua. Nguyên nhân chính nằm ở ma trận nhầm lẫn: cả **18/18 câu sai tiền** đều bị cho qua, vì judge không có quyền đọc ledger.
- **Hành động:**
  1. Tách phần "đúng số tiền" ra khỏi tiêu chí helpful và chấm bằng code: grader `ReplyAmountMatchesLedger` (FM-08, M3), đúng quy tắc "tiền luôn chấm bằng code".
  2. Rubric helpful mới chỉ xét các phần không liên quan tới tiền: trả lời đúng câu hỏi, hỏi lại mã đơn khi thiếu, xưng hô; đồng thời phạt câu lặp lại, câu xin lỗi dài lấp chỗ trống.
  3. Gán nhãn người mới rồi hiệu chỉnh lại. Ước tính sơ bộ trên 82 câu không liên quan tới tiền: P 1.0, R 0.750, κ 0.837. Con số này chỉ để tham khảo, vì đo trên chính dữ liệu đã dùng để phân tích.
- **Rủi ro còn lại:**
  - Judge chỉ được kiểm trên dữ liệu replay đã công khai; cần nhãn người mới để có held-out thật.
  - Mỗi file chỉ có 100 câu, chỉ một người chấm, và đã phát hiện ít nhất 1 nhãn người sai (H-081).
  - Hiệu chỉnh Rogan-Gladen giả định độ nhạy của judge giống nhau ở mọi loại câu. Với helpful, giả định này sai: độ nhạy bằng 0 ở nhóm sai tiền. Nếu tỉ lệ câu sai tiền thay đổi, con số đã hiệu chỉnh cũng sẽ sai.
