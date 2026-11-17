# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Case của nhóm: `seeded_regression` C-002@11

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`. Run ID: `E-seeded_regression-<ngày>-<sha4>`, lấy từ `reports/eval_seeded_regression.json` sau khi chạy `lab9.eval` ở M4. Lỗi này cũng có thật trong baseline: `swarm C-002@55`, cùng chuỗi event 1–4. |
| Triệu chứng | Grader Lab 8 FAIL `status resolved != denied`. Ledger ghi 20.000 (`refund_count 1`), nhãn là 0 (`denied`). Reply #6 "Dạ, LogiX đã hoàn 20.000đ cho đơn O-202." khớp ledger, nên reply không sai; cái sai là khoản hoàn. |
| Bước sai đầu tiên | Event **#3 `model_override`** `{"delay_days": 5}`: số ngày trễ khách viết trong ticket đè lên `delay_days: 2` của DB. |
| Vì sao là bước *đầu tiên* | #1 `handoff` đúng: `facts: {}` không mang dữ kiện nào từ ticket, `allowed_tools` chỉ gồm công cụ chỉ-đọc. #2 `investigator` đúng: đọc DB được đơn O-202 `delay_days: 2`. Sau #3 thì #4 `quote` (20.000, `entitled`, `SHIP-LATE-03`) tính đúng theo luật trễ ≥ 3 ngày, nhưng trên con số 5 đã bị đè; #4 là hệ quả, không phải nguyên nhân. #5 `refund_history` (`refunded_vnd: 0`) không đổi gì. |
| Failure mode | **FM-03** ticket_trust |
| Đối chứng | `fixed C-002@11`: không có `model_override`; #3 `quote` tính trên 2 ngày ra `amount_vnd: 0`, `no_entitlement`; status `denied`, ledger 0, grader Lab 8 PASS. Hai trace chỉ khác nhau đúng một event. |
| Regression test | `tests/test_lab9_trace_case.py::test_c002_ticket_trust_is_caught`: assert trace của `seeded_regression` có `model_override` và ledger ≠ nhãn; trace của `fixed` thì ledger = nhãn. Đã chạy: pass. Trong eval, grader `DbFactKept` (đếm `model_override`) và `RefundAmountCorrect` (ledger 20.000 ≠ 0) đều bắt được trial này. |
| Chưa chắc chắn | Trace cho thấy *có* override nhưng không cho thấy *vì sao* agent tin ticket. Với MockLLM, lý do là luật cài sẵn (`ticket_trust` ở variant, `seed % 5 == 0` ở swarm); với LLM thật thì cần xem prompt và log của model. Nếu agent đè dữ kiện mà không ghi event (`quiet_override`), `DbFactKept` sẽ bỏ sót và chỉ còn `RefundAmountCorrect` bắt được. Trace cũng không ghi lời gọi host hoàn tiền; khoản 20.000 chỉ thấy được qua ledger. |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
