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

- [x] Dashboard Grafana khi đang có tải (thấy rõ Golden Signals) — `screenshots/grafana-dashboard.png`
- [x] Một trace chậm trong Jaeger (thấy span nào chiếm thời gian) — `screenshots/jaeger-slow-trace.png`
- [x] Một trace lỗi trong Jaeger (có event `exception`) — `screenshots/jaeger-error-trace.png`
- [x] Trang Alerts của Prometheus với ít nhất 1 alert đang **firing** — `screenshots/prometheus-alert-firing.png` (2 alert cùng firing: `AgentHighErrorRate`, `AgentHighLatencyP95`)

### 4.1b Trả lời Exercise 7.4

Đo lại trên stack 2 agent sau Nginx, tải Locust 30 user trong 90 giây, số liệu lấy từ Prometheus API.

1. **p95 và avg đang là bao nhiêu? Khoảng cách giữa chúng nói lên điều gì?** Với `/ask`: avg 0,229 s, p50 0,178 s, p95 0,293 s, p99 1,804 s. avg (229 ms) cao hơn p50 (178 ms) khoảng 50 ms nên phân phối lệch phải: phần lớn request nhanh, một nhóm nhỏ chậm bất thường kéo trung bình lên. Nhóm đó nằm ở đuôi p99 (1,8 s, gấp ~10 lần p50) chứ chưa đủ lớn để làm p95 tăng mạnh. Vì vậy chỉ nhìn avg hoặc p95 sẽ không thấy; cần theo dõi cả p99.
2. **Panel "Requests/s theo instance": Nginx có chia đều traffic cho 2 instance không?** Có. 40 request qua Nginx: 20 đến mỗi instance (`X-Served-By`). Prometheus đo 8,75 và 8,65 req/s cho hai instance, chênh khoảng 1 %. Nginx chia theo round-robin mặc định và dùng DNS của Docker để tìm hai instance.
3. **Vì sao input tokens/s lớn hơn output tokens/s?** Đo được input 638,4 và output 339,5 tokens/s (gấp ~1,9 lần). Prompt gồm system prompt, tài liệu retrieval (agent v2) và câu hỏi, còn câu trả lời ngắn hơn nhiều, nên mỗi request tiêu nhiều token đầu vào hơn token đầu ra.
4. **`curl http://localhost:8080/metrics` trả về gì? Vì sao?** Trả về `404 Not Found`. `nginx.conf` có khối `location = /metrics { return 404; }`: endpoint này lộ thông tin hệ thống (route, lưu lượng, version, model) nên không public ra ngoài. Prometheus vẫn đọc được vì scrape trực tiếp từng agent trong mạng nội bộ (gọi `agent:8000/metrics`, không qua Nginx).

Lưu ý: đây là lần đo riêng cho Exercise 7.4 (30 user, 90 giây), nên các số p95 và tokens/s hơi khác lần chạy thí nghiệm ở mục 4.2 (tải và độ dài cửa sổ không giống nhau).

### 4.2 Thí nghiệm "phá hệ thống"

Tải nền Locust 30 user, 2 agent sau Nginx. Thời gian đo bằng Prometheus API (`/api/v1/alerts`) từ lúc chạy lệnh đổi cấu hình, đã gồm thời gian tạo lại container (~3 s).

| # | Thay đổi | Alert nào firing | Thời gian từ lúc đổi → firing | Panel nào phản ánh rõ nhất |
|---|---|---|---|---|
| A | `MOCK_ERROR_RATE=0.2` | `AgentHighErrorRate` (pending sau 29 s) | 89 s (error rate đo được 20,4 %) | Error rate (Golden Signals) |
| B | `MOCK_SLOW_RATE=0.3` (giữ A) | `AgentHighLatencyP95` (pending sau 27 s) | 147 s (p95 đo được 1,92 s) | p95/p99 latency |
| C | `LLM_MODEL=mock-llm-large` | Không thực hiện riêng (xem ghi chú) | — | — |
| D | `docker pause` 1 instance | Không thực hiện | — | — |
| E | `AGENT_VERSION=v1` | Không có (`AgentInstanceDown` chỉ `pending` thoáng qua lúc container khởi động lại, rồi tự hết) | — (quan sát 4 phút) | tokens/s (input 1317 → 692, output 700 → 375 mỗi giây), bảng version đổi sang v1 |

Ghi chú:
- Cột "Panel nào phản ánh rõ nhất" cho A và B tôi điền theo thiết kế dashboard (README mục 2.3 và 2.6) và theo câu truy vấn của alert, không phải do đọc lại từ ảnh.
- Thí nghiệm C không đo sạch được: ngay trước thí nghiệm A, `LLMCostBurnRateHigh` đã firing sẵn. Tải 30 user (~18,6 req/s, ~3,3e-5 USD/request) tương đương khoảng 2,2 USD/giờ, đã vượt ngưỡng 2 USD/giờ, cộng thêm tải 100 user của bài scaling còn trong cửa sổ `rate[5m]`. Alert này tự về inactive sau khi container được tạo lại ở thí nghiệm B vì request chậm làm giảm số request/giây.
- Sau khi trả về cấu hình mặc định, hai alert A và B hết firing sau khoảng 54 s.

**Thí nghiệm E không làm alert nào firing. Bạn sẽ phát hiện loại sự cố này trong production bằng cách nào?**

Metric hạ tầng (error rate, latency, instance up) chỉ phản ánh việc agent có chạy và chạy nhanh hay không, không phản ánh câu trả lời có đúng không. Ở thí nghiệm E, v1 vẫn trả 200 nhanh (error rate 1,1 %, p95 0,199 s) nhưng trả lời chung chung cho cả 3 câu hỏi thử (ví dụ "Tôi là AI agent được deploy lên cloud..."), nên chỉ giám sát chất lượng mới bắt được. Cách phát hiện: chạy eval trên golden dataset định kỳ và trước mỗi lần deploy (quality gate, như mục 3), đo thêm eval trên mẫu traffic thật (LLM-as-judge hoặc so khớp từ khóa), theo dõi các tín hiệu gián tiếp trên dashboard như tỉ lệ retrieval hit và tokens/s (đổi từ v2 sang v1 làm tokens/s giảm gần một nửa), và thu phản hồi của người dùng (đánh giá hữu ích/không hữu ích).

### 4.3 Debug bằng trace

Chọn 1 trace chậm nhất bạn tìm được:

- `trace_id`: `ff0f286815895d9a76e7efa955e35a73`
- Tổng thời gian: 1715,7 ms
- Span chiếm nhiều thời gian nhất: `chat mock-llm-small` (1691,7 ms, 98,6 %); các span còn lại: `agent.run` 1713,2 ms (span cha), `agent.retrieve_context` 21,3 ms (1,2 %)
- Dòng log tương ứng (grep theo `trace_id`):

```json
{"ts": "2026-11-26T10:38:22.782862+00:00", "level": "INFO", "service": "observable-agent", "instance": "69a60aa5be18", "event": "llm_call", "trace_id": "ff0f286815895d9a76e7efa955e35a73", "span_id": "4eb1f84528cce3cf", "request_id": "d88ecc6608c1", "model": "mock-llm-small", "agent_version": "v2", "input_tokens": 74, "output_tokens": 37, "cost_usd": 3.3e-05, "llm_ms": 1690.9}
{"ts": "2026-11-26T10:38:22.783551+00:00", "level": "INFO", "service": "observable-agent", "instance": "69a60aa5be18", "event": "http_request", "trace_id": "ff0f286815895d9a76e7efa955e35a73", "span_id": "4eb1f84528cce3cf", "request_id": "d88ecc6608c1", "method": "POST", "route": "/ask", "status": 200, "ms": 1714.8}
```

Nhận xét: request chậm do bước gọi LLM (`llm_ms` 1690,9 ms), không phải do code của agent hay bước retrieval.

Trace lỗi (cho `jaeger-error-trace.png`): `trace_id` `1601c007f9c384a991f322698c7dbc6c`, 116,9 ms, span `chat mock-llm-small` có event `exception` (`utils.mock_llm.LLMError`: "Upstream LLM error: 503 Service Unavailable (mock)"). Dòng log JSON cùng `trace_id`:

```json
{"ts": "2026-11-26T10:38:25.812731+00:00", "level": "INFO", "service": "observable-agent", "instance": "ff9dbdd06a26", "event": "llm_error", "trace_id": "1601c007f9c384a991f322698c7dbc6c", "span_id": "c8264fe6b39f4cbb", "request_id": "504e01a8a8ed", "error": "Upstream LLM error: 503 Service Unavailable (mock)"}
```

---

## 5. Benchmark scaling (production, Locust headless, 100 users, 2 phút)

Số liệu lấy từ hàng `Aggregated` của `benchmark-results/scale_1_stats.csv` và `scale_3_stats.csv`.

| Số instance | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Failures |
|---|---|---|---|---|---|
| 1 | 66,00 | 190 | 220 | 1700 | 75 (0,95 %) |
| 3 | 66,16 | 190 | 220 | 1700 | 85 (1,08 %) |

**Giải thích kết quả:** Scale từ 1 lên 3 instance **không cải thiện** RPS (66,00 → 66,16) và p95 (220 ms ở cả hai). Nút thắt không nằm ở số instance. Mỗi user của Locust nghỉ 0,5–2 giây giữa các lần gọi, nên 100 user chỉ tạo tối đa khoảng 100 / (1,25 s nghỉ trung bình + ~0,2 s xử lý) ≈ 68 request/giây, rất gần mức 66 đo được. Nghĩa là tải đưa vào bị giới hạn bởi thời gian nghỉ của user, một instance đã đủ sức xử lý, thêm instance không làm hệ thống nhanh hơn. Thời gian của mỗi request chủ yếu là bước gọi LLM (~190 ms, cộng đuôi ~1,7 s cho khoảng 3 % request chậm), không đổi theo số instance, và p99 vì thế vẫn ≈ 1700 ms. Số lỗi (~1 %) là lỗi upstream giả lập của `MOCK_ERROR_RATE`, không liên quan đến năng lực hệ thống. Tôi suy luận điều này từ các con số, không đối chiếu thêm panel LLM latency. Muốn thấy lợi ích của scale cần tải lớn hơn (nhiều user hơn hoặc thời gian nghỉ ngắn hơn) đến khi một instance bão hòa, như mức concurrency 100 ở mục 2.1 (một process đơn đã quá tải).

---

## 6. Kết luận

- 3 điều bạn học được về benchmark & observability:
  1. Average che giấu tail latency: ở `MOCK_SLOW_RATE=0.03` avg chỉ tăng 25 % nhưng p99 tăng gần 7,6 lần, nên SLO phải đặt theo p95/p99.
  2. Metric hạ tầng không bắt được lỗi chất lượng: đổi sang v1 không alert nào firing dù câu trả lời kém đi, nên cần eval trên golden dataset và quality gate bên cạnh metrics, traces và alerts.
  3. Kết quả đo phụ thuộc điều kiện thử nghiệm, phải kiểm tra điều kiện trước khi kết luận: scale lên 3 instance không nhanh hơn vì tải bị giới hạn bởi thời gian nghỉ của user, và alert cost đã firing sẵn ở 30 user nên thí nghiệm C không đo sạch được.
- Nếu đưa agent này lên production thật, bạn sẽ thêm metric / alert nào nữa?

Thêm alert chất lượng (eval điểm số trên mẫu traffic thật, tỉ lệ retrieval hit giảm), alert ở tầng Nginx/load balancer cho lỗi 5xx và 504 (vì lỗi này không hiện trên metric của agent), kiểm tra tổng hợp (synthetic probe) từ bên ngoài, alert độ bão hòa (số request đang xử lý `agent_in_flight_requests`), alert p99 bên cạnh p95, và ngân sách chi phí theo ngày thay vì chỉ tốc độ chi tiêu theo giờ. Cũng nên điều chỉnh ngưỡng `LLMCostBurnRateHigh` theo tải bình thường để nó không firing ở trạng thái khỏe mạnh.

Ghi chú môi trường: `production/Dockerfile` của lab thiếu `ENV PYTHONUSERBASE=/home/agent/.local` khiến container agent crash (`No module named 'uvicorn'`); tôi đã thêm đúng dòng này rồi mới chạy stack.
