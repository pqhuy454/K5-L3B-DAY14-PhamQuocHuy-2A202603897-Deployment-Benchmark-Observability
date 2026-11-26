# Benchmark & Observability Report — Day 14

> Copy file này thành `BENCHMARK_REPORT.md` trong repo của bạn và điền đầy đủ.
> Mọi con số phải lấy từ report JSON / CSV / screenshot thật, không ước lượng.

**Họ tên:** Phạm Quốc Huy
**Ngày chạy:** 2026-11-26
**Môi trường:** Windows 11 + WSL2 Ubuntu (12 CPU logic, ~15,5 GB RAM), Docker Desktop (server 29.9.3), Python 3.11.18

---

## 1. SLO của agent

| SLI | SLO | Lý do chọn ngưỡng này |
|---|---|---|
| p95 latency `/ask` | ≤ 500 ms | Mock LLM mất khoảng 150–220 ms cho request bình thường (p50 ≈ 187–199 ms ở concurrency 1–50), nên 500 ms cho dư địa hơn 2 lần mà vẫn bắt được request chậm bất thường (+1500 ms). Đặt theo p95, không đặt theo trung bình |
| Error rate `/ask` | ≤ 2 % | Mock LLM có 1 % lỗi upstream mặc định (`MOCK_ERROR_RATE`), nên 2 % là ngưỡng chấp nhận được khi có lỗi tạm thời, lệch hơn nghĩa là có sự cố thật. Trùng ngưỡng mặc định của `load_test.py` |
| Accuracy trên golden dataset | ≥ 95 % | Golden dataset có 23 câu, mỗi câu sai làm accuracy giảm ~4,3 điểm, nên 95 % tương đương cho phép sai tối đa 1 câu. Lần chạy cuối đạt 100 % (23/23) và quality gate của bài dùng `--min-accuracy 1.0` kèm không regression |

---

## 2. Benchmark hiệu năng (develop, `load_test.py`)

### 2.1 Concurrency vs latency (agent v2)

Mỗi mức 300 request. Số liệu lấy từ `reports/load_v2_c*.json`.

| Concurrency | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Error rate | SLO |
|---|---|---|---|---|---|---|
| 1 | 4,61 | 189,3 | 218,5 | 1669,5 | 1,67 % | ✅ PASS |
| 10 | 39,14 | 187,1 | 217,8 | 1703,5 | 0,67 % | ✅ PASS |
| 50 | 104,31 | 198,7 | 247,9 | 1710,1 | 0,00 % | ✅ PASS |
| 100 | 77,73 | 315,7 | 2615,0 | 2924,3 | 0,67 % | ❌ FAIL (p95) |

**Nhận xét:** RPS không tăng tuyến tính. Từ concurrency 1 lên 10 RPS tăng 8,5 lần (4,61 → 39,14) vì các request chờ LLM (giả lập bằng sleep, không tốn CPU) chồng lên nhau. Từ 10 lên 50 chỉ tăng 2,7 lần (→ 104,31). Lên 100 thì RPS **giảm** còn 77,73 và p95 vọt lên 2615 ms, avg 870 ms (tăng gấp ~3,4 lần so với 50), vi phạm SLO. Đây là dấu hiệu quá tải: tôi suy luận nguyên nhân là một process uvicorn đơn, request phải xếp hàng chờ nhau; tôi chưa profile để chứng minh. Mỗi mức chỉ chạy 300 request (mức 100 chạy 3,86 s) nên số liệu có nhiễu, và p99 ở mọi mức đều ≈ 1,7 s do khoảng 3 % request bị chậm bất thường (+1500 ms) của `MOCK_SLOW_RATE`.

### 2.2 Tail latency

Concurrency 20, 300 request, số liệu lấy từ `reports/load_v2_slow_*.json`.

| `MOCK_SLOW_RATE` | avg (ms) | p95 (ms) | p99 (ms) |
|---|---|---|---|
| 0 | 188,1 | 213,8 | 222,3 |
| 0.03 (mặc định) | 236,0 | 219,7 | 1687,8 |
| 0.1 | 383,6 | 1696,5 | 1715,3 |

**Nhận xét:** Khi 3 % request chậm, avg chỉ tăng 47,9 ms (+25 %) và p95 gần như không đổi (213,8 → 219,7), nhưng p99 tăng gần 7,6 lần (222,3 → 1687,8). Khi 10 % request chậm (nhiều hơn 5 %), p95 cũng vọt lên 1696,5 ms và SLO p95 vi phạm, trong khi avg mới là 383,6 ms, trông vẫn "chấp nhận được". Vì vậy p99 nhạy nhất với nhóm request chậm nhỏ, còn p95 chỉ lộ ra khi nhóm đó vượt 5 %. SLO không nên đặt theo average vì average trộn lẫn request nhanh và chậm nên che giấu nhóm người dùng bị chậm; percentile cho biết trải nghiệm của nhóm xấu nhất.

---

## 3. Benchmark chất lượng (develop, `eval/run_eval.py`)

Số liệu lấy từ `reports/eval_v1.json`, `eval_v2.json`, `eval_v2_fixed.json`.

| Chỉ số | Agent v1 | Agent v2 | Agent v2 (sau khi sửa KB) |
|---|---|---|---|
| Accuracy | 4,3 % (1/23) | 91,3 % (21/23) | 100 % (23/23) |
| Avg tokens / câu | 56,6 | 109,0 | 113,7 |
| Tổng cost (USD) | 0,000397 | 0,00076 | 0,00079 |
| Cost / câu đúng (USD) | 0,00039735 | 0,00003619 | 0,00003436 |
| Quality gate | FAIL | PASS | PASS |

Quality gate: v1 và v2 chạy với ngưỡng mặc định (accuracy ≥ 80 %, không regression so với baseline); v2 sau khi sửa chạy với `--min-accuracy 1.0` và baseline là `eval_v2.json`, kết quả 0 câu regression, 2 câu được cải thiện.

**Những câu v2 trả lời sai ban đầu và cách bạn sửa:**

| ID | Keyword bị thiếu | Bạn đã sửa gì |
|---|---|---|
| scaling-03 | cpu, memory, custom metrics | Thêm vào `KNOWLEDGE_BASE` (`develop/utils/mock_llm.py`) một tài liệu kích hoạt bởi `hpa`, `kubernetes`, `autoscal`, nội dung nói Kubernetes HPA scale theo CPU, memory hoặc custom metrics |
| security-02 | token, hết hạn, chữ ký | Thêm tài liệu kích hoạt bởi `jwt`, nội dung so sánh API key (cố định, không tự hết hạn) với JWT (token có chữ ký số, có thời điểm hết hạn) |

**Nhận xét về trade-off chất lượng / chi phí / latency giữa v1 và v2:**

v2 dùng retrieval nên prompt dài hơn: token trung bình mỗi câu tăng từ 56,6 lên 109,0 (gấp ~1,9 lần) và tổng cost tăng từ 0,000397 lên 0,00076 USD. Đổi lại accuracy tăng từ 4,3 % lên 91,3 % (lên 100 % sau khi sửa KB). Vì v1 gần như không trả lời đúng câu nào, cost / câu đúng của v1 là 0,00039735 USD, còn v2 là 0,00003619 USD, tức rẻ hơn khoảng 11 lần. So sánh cost / câu đúng hợp lý hơn so sánh cost / câu vì v1 rẻ hơn mỗi câu nhưng hầu như không có câu nào dùng được. Về latency, tôi chỉ chạy load test cho v2 nên chưa có số so sánh v1 và v2 dưới tải. Trong eval, p95 của v1 là 1495,4 ms và của v2 là 218,7 ms, nhưng mẫu chỉ có 23 request (vài request chậm bất thường làm p95 nhảy mạnh, ví dụ p95 của `eval_v2_fixed.json` là 1709,6 ms), nên không dùng eval để kết luận về latency.

**Quality gate trong CI:** `run_eval.py` trả exit code 1 khi accuracy dưới `--min-accuracy` hoặc có câu regression so với `--baseline`, và exit code 0 khi đạt. Bước CI chỉ cần chạy lệnh này; job fail thì PR không merge được khi bật branch protection. Tôi đã chạy thử: với agent v1 và baseline là `eval_v2_fixed.json`, lệnh trả exit code 1, báo 22 câu regression và `Quality gate ❌ FAIL`. Bước GitHub Actions mẫu:
```yaml
- name: Run agent + eval
  working-directory: 06-lab-complete/benchmark-observability/develop
  run: |
    pip install -r requirements.txt
    AGENT_VERSION=v2 MOCK_ERROR_RATE=0 python app.py &
    sleep 3
    python eval/run_eval.py --url http://localhost:8000 --min-accuracy 0.85
```

---

## 4. Observability stack (production)

### 4.1 Screenshot

- [ ] Dashboard Grafana khi đang có tải (thấy rõ Golden Signals)
- [ ] Một trace chậm trong Jaeger (thấy span nào chiếm thời gian)
- [ ] Một trace lỗi trong Jaeger (có event `exception`)
- [ ] Trang Alerts của Prometheus với ít nhất 1 alert đang **firing**

### 4.2 Thí nghiệm "phá hệ thống"

| # | Thay đổi | Alert nào firing | Thời gian từ lúc đổi → firing | Panel nào phản ánh rõ nhất |
|---|---|---|---|---|
| A | `MOCK_ERROR_RATE=0.2` | | | |
| B | `MOCK_SLOW_RATE=0.3` | | | |
| C | `LLM_MODEL=mock-llm-large` | | | |
| D | `docker pause` 1 instance | | | |
| E | `AGENT_VERSION=v1` | | | |

**Thí nghiệm E không làm alert nào firing. Bạn sẽ phát hiện loại sự cố này trong production bằng cách nào?**

...

### 4.3 Debug bằng trace

Chọn 1 trace chậm nhất bạn tìm được:

- `trace_id`: ...
- Tổng thời gian: ... ms
- Span chiếm nhiều thời gian nhất: ... (... ms, ...%)
- Dòng log tương ứng (grep theo `trace_id`):

```json

```

---

## 5. Benchmark scaling (production, Locust headless, 100 users, 2 phút)

| Số instance | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Failures |
|---|---|---|---|---|---|
| 1 | | | | | |
| 3 | | | | | |

**Giải thích kết quả:** Scale có cải thiện p95 không? Nút thắt nằm ở đâu?

...

---

## 6. Kết luận

- 3 điều bạn học được về benchmark & observability:
  1. ...
  2. ...
  3. ...
- Nếu đưa agent này lên production thật, bạn sẽ thêm metric / alert nào nữa?

...
