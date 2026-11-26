# PROJECT_GUIDELINE — Day 14: Deployment, Benchmark & Observability (K5, cá nhân)

> Tổng hợp từ: README, RULES, CHECKPOINTS, SUBMISSION, RUBRIC, CODE_LAB, DAY14_DELIVERY_CHECKLIST, INSTRUCTOR_GUIDE, `06-lab-complete/README.md`, `06-lab-complete/benchmark-observability/README.md` và `BENCHMARK_REPORT_TEMPLATE.md`.
> **Thứ tự ưu tiên khi tài liệu mâu thuẫn:** thông báo Lab Coach > README mục "Lưu ý khi làm bài (K5)" > RUBRIC / CHECKPOINTS / SUBMISSION / RULES > CODE_LAB / DAY14_DELIVERY_CHECKLIST / INSTRUCTOR_GUIDE.

---

## 1. Tổng quan

- Hình thức: **cá nhân**, 4 giờ tại lớp. Deadline **23h59 (GMT+7) ngày lab** (Lab Coach có thể đổi).
- Nộp: **link repo GitHub Public** trên LMS. Chấm **commit cuối trước deadline**.
- Tên repo: `K5-<L3A|L3B>-DAY14-HoVaTen-MSSV-Deployment-Benchmark-Observability`.
- Điểm: tổng thô 120 → `Điểm = thô × 100 / 120` (làm tròn 0,5). Đạt: 70/100 (84/120).
- Mock LLM, không cần API key thật, không cần thẻ tín dụng.

## 2. Bảng điểm (RUBRIC.md là chuẩn của K5)

| Hạng mục | Điểm | Bằng chứng |
| --- | ---: | --- |
| Part 1 — Localhost vs Production | 8 | `MISSION_ANSWERS.md` |
| Part 2 — Docker | 8 | `MISSION_ANSWERS.md`, có số MB đo thật |
| Part 3 — Cloud Deployment | 8 | URL public chạy 4 lệnh tự kiểm CP6 |
| Part 4 — API Security | 8 | output `curl -i` 401 / 200 / 429 |
| Part 5 — Scaling & Reliability | 8 | `MISSION_ANSWERS.md` |
| **Part 6 — Final Project** | **60** | `check_production_ready.py` = `PASS 12/12`, `DEPLOYMENT.md`, ảnh |
| Part 7 — Load test & SLO | 4 | bảng 4 mức concurrency + so sánh `MOCK_SLOW_RATE` |
| Part 7 — Eval & quality gate | 5 | v1 vs v2, v2 = 23/23 không regression, giải thích exit code |
| Part 7 — Observability stack | 4 | ảnh Grafana có tải + trả lời Exercise 7.4 |
| Part 7 — Tracing | 3 | ảnh trace chậm + `trace_id` khớp log JSON |
| Part 7 — Alerts & chaos | 4 | ảnh ≥ 2 alert firing + thời gian firing + phân tích |

**Part 3 (8đ):** deploy nền tảng chính (Railway hoặc Render) = 4; nền tảng còn lại (deploy hoặc so sánh `railway.toml` vs `render.yaml`) = 3; Exercise 3.3 Cloud Run (đọc `cloudbuild.yaml`, `service.yaml`, viết 3–5 dòng pipeline, không cần GCP) = 1.

**Part 6 (60đ), mỗi mục đạt/không:** mục nào script báo ❌ hoặc ⚠️ = 0.

| Nhóm | Mục | Điểm |
| --- | --- | ---: |
| Functional (15) | `POST /ask` đúng 10; input sai trả mã lỗi rõ, không lộ stack trace 5 | 15 |
| Docker & config (10) | multi-stage 4; image < 500 MB 2; compose agent+Redis 2; config từ env 2 | 10 |
| Security (15) | API key 4; rate limit 4; cost guard 4; không hardcode secret 3 | 15 |
| Reliability (10) | `/health` 2; `/ready` (503 khi mất Redis) 2; SIGTERM 3; stateless 3 | 10 |
| Deployment (10) | URL public (ghi trong `DEPLOYMENT.md`) 5; `railway.toml`/`render.yaml` 3; env đặt trên nền tảng 2 | 10 |

- Conversation history **không** tính điểm. Bonus: **không có**.

## 3. Quy tắc cứng (RULES.md)

**Dùng AI:** được dùng, nhưng ghi mục **AI log** cuối `MISSION_ANSWERS.md` (hỏi gì, nhận gì, tự sửa/kiểm tra thế nào). Lab Coach có thể bắt giải thích bất kỳ đoạn code trong `06-lab-complete/app/` hoặc số nào trong `BENCHMARK_REPORT.md`. **Cấm bịa số đo**: mọi số phải từ lệnh đã chạy và file report đã nộp.

**Cấm sửa:**
- `06-lab-complete/check_production_ready.py` (sửa để lấy PASS → Part 6 = 0 điểm).
- `06-lab-complete/benchmark-observability/develop/eval/golden_dataset.jsonl`. Exercise 7.3 chỉ sửa `KNOWLEDGE_BASE` trong `.../develop/utils/mock_llm.py`.

**Secret:** không commit `.env`, `AGENT_API_KEY` thật, token Railway/Render (chỉ `.env.example`). Lỡ commit → −10 điểm, phải revoke + tạo key mới; xóa file không đủ.

**Khác:**
- Không ghi email, số điện thoại. Họ tên + MSSV chỉ ở tên repo và ô Họ tên của `BENCHMARK_REPORT.md`.
- Không force-push, không sửa ngày commit. Commit sau deadline không được chấm.
- Làm xong: `docker compose down -v` (đúng `-p` đã dùng).
- Sao chép: cả hai bài 0 điểm phần liên quan. URL/ảnh/report trùng người khác là dấu hiệu sao chép.

## 4. Lưu ý riêng K5 (README mục "Lưu ý khi làm bài")

1. Làm Part 6 **ngay trong `06-lab-complete/`**; bỏ cây `app/` ở gốc trong checklist.
2. **Windows: chạy Python trong WSL2** (Docker Desktop bật WSL2). Kiểm: `python -c "import os; print(os.name)"` phải ra `posix`. Nếu không, Graceful shutdown luôn ⚠️ → không đạt 12/12.
3. Part 1, 2: app develop nhận `question` qua **query**: `curl -X POST "http://localhost:8000/ask?question=Hello"`. Cùng cổng 8000 → tắt bản cũ trước.
4. Part 2: build **từ gốc repo**: `docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .` và `docker build -f 02-docker/production/Dockerfile -t my-agent:advanced .`
5. Compose Part 2 và Part 5 cần `.env.local`: `touch .env.local` trong `02-docker/production/` và `05-scaling-reliability/production/`.
6. Part 4: develop bật bằng `AGENT_API_KEY=secret-key-123 python app.py`. Production: tắt develop trước; token ở `POST /auth/token`, tài khoản `student` / `demo123` (10 req/phút); thêm `-i` vào curl; **che token** khi dán.
7. Part 5: stack ở cổng **8080**, endpoint **`POST /chat`**. Lệnh: `docker compose -p k5-day14-scaling up -d --build --scale agent=3`, rồi `python test_stateless.py`, xong `docker compose -p k5-day14-scaling down`. Mọi lệnh compose của một bài dùng cùng `-p`.
8. Part 3 deploy **agent Part 6** (`cd 06-lab-complete && railway up`; CLI cài bằng npm). Cần Redis trên cloud, đặt `REDIS_URL`, `/ready` phải 200 trước khi chụp. Render: `render.yaml` phải tự khai báo Redis.
9. "Bảng Hợp đồng" = mục *Script chấm dựa vào những tiêu chí dưới đây* trong `06-lab-complete/README.md`.
10. Exercise 7.3: sửa `KNOWLEDGE_BASE` rồi **tắt/bật lại agent v2** (không tự nạp lại code). Muốn stack Docker Part 7 Bước 2 cũng 100% thì chép phần sửa sang `production/utils/mock_llm.py`.
11. `load_test.py`, `run_eval.py` chỉ ghi JSON khi có `--out`; v2 ở 8002 thì thêm `--url http://localhost:8002`.

## 5. Hợp đồng Part 6 (script chấm dựa vào)

| Hạng mục | Yêu cầu |
| --- | --- |
| Entry | `app/main.py` có `app` (FastAPI); chạy `uvicorn app.main:app --workers 2` |
| `GET /health` | luôn 200 khi process sống, kể cả Redis chết |
| `GET /ready` | 200 khi sẵn sàng; 503 khi Redis không kết nối được |
| `POST /ask` | body JSON `{"question": "..."}` (có thể thêm `user_id`) → 200 |
| API key | header `X-API-Key` khớp `AGENT_API_KEY`; thiếu/sai → **401** (dùng `auto_error=False`, không dùng `Header(...)` vì sẽ ra 422) |
| Rate limit | ≤ `RATE_LIMIT_PER_MINUTE` req / 60s mỗi API key; vượt → **429** (+ `Retry-After`); state trong **Redis** (sliding window, sorted set), sống sót qua restart |
| Cost guard | tổng chi phí ≥ `DAILY_BUDGET_USD` (hoặc `MONTHLY_BUDGET_USD`) → **402**; lưu Redis (`INCRBYFLOAT`) |
| Env | `AGENT_API_KEY`, `REDIS_URL`, `RATE_LIMIT_PER_MINUTE`, `DAILY_BUDGET_USD`/`MONTHLY_BUDGET_USD`, `PORT`, `ENVIRONMENT`; liệt kê đủ trong `.env.example`; `.env` trong `.gitignore` |
| Log | mỗi dòng log của app là 1 JSON object hợp lệ (log uvicorn không tính) |
| Graceful shutdown | SIGTERM khi có request → request vẫn 200, exit code 0; `docker stop` < 10s. Nếu tự đăng ký handler phải gọi lại handler cũ |
| Docker image | multi-stage, base slim, user non-root, `HEALTHCHECK`, < 500 MB, `CMD` theo `${PORT:-8000}`, uvicorn là PID 1, khởi động được khi không có Redis. Nếu dùng `pip install --user`, đặt `ENV PYTHONUSERBASE` |
| Compose | 1 service build từ Dockerfile + 1 service `redis:*`; agent có `REDIS_URL` trỏ Redis + `depends_on` |
| `.dockerignore` | loại `.env`, `__pycache__`, `venv` |
| Deploy config | `railway.toml` (builder `DOCKERFILE`, `healthcheckPath="/health"`) **hoặc** `render.yaml` (`type: web`, `healthCheckPath: /health`, secret dùng `generateValue`/`sync: false`) |

Thứ tự làm gợi ý: `/health` → `config.py` → log JSON → `auth.py` → `redis_client.py` + `/ready` → `rate_limiter.py` → `cost_guard.py` → graceful shutdown → `Dockerfile` + `.dockerignore` → `docker-compose.yml` → `railway.toml`/`render.yaml`.
Luồng `/ask`: `Depends(verify_api_key)` → `check_rate_limit(...)` → `check_budget()` → gọi LLM → `record_cost(...)`.

Lệnh chấm (trong `06-lab-complete/`):
```bash
python check_production_ready.py --static-only   # sớm, sau mỗi bước
python check_production_ready.py --skip-docker   # nhanh
python check_production_ready.py                 # đầy đủ, bắt buộc trước khi nộp
python check_production_ready.py --public-url <URL>
```

## 6. Lộ trình & Checkpoint (CHECKPOINTS.md)

| Giờ | CP | Nội dung | Sản phẩm |
| --- | --- | --- | --- |
| 0:00 | CP0 | Fork, đổi tên repo, kiểm Python 3.11+/Docker | `docker run --rm hello-world` chạy được |
| 0:10 | CP1 | Part 1 (1.1–1.3) | ≥ 5 anti-pattern, kết quả gọi develop, bảng so sánh có cột "vì sao" |
| 0:30 | CP2 | Part 2 (2.1–2.4) | 4 câu 2.1, kết quả container, **MB đo bằng `docker images` + % chênh**, sơ đồ stack 2.4, test qua Nginx |
| 1:00 | CP3 | Part 4 (4.1–4.4) | `curl -i` 401/200/429 (che token), giải thích cost guard |
| 1:25 | CP4 | Part 5 (5.1–5.5) | mục Part 5; chạy `test_stateless.py` và giải thích |
| 1:50 | CP5 | Part 6 | `PASS 12/12`, dán "📋 Checklist Deliverable" vào `MISSION_ANSWERS.md` |
| 2:50 | CP6 | Part 3 (deploy agent Part 6) | `DEPLOYMENT.md`, ảnh, so sánh `railway.toml` vs `render.yaml`, 3–5 dòng Cloud Run |
| 3:15 | CP7 | Part 7 Bước 1 (7.1–7.3) | `reports/*.json`, `BENCHMARK_REPORT.md` bắt đầu điền |
| Sau lab | CP8 | Part 7 Bước 2 (7.4–7.7) | Grafana/Jaeger/alerts, CSV Locust, đóng gói nộp |

Kẹt > 10 phút thì ghi lỗi, gọi Lab Coach, đi tiếp. CP5 nhiều điểm nhất (60/120), đừng để CP1–CP4 lấn giờ.

**4 lệnh tự kiểm CP6** (`BASE` = URL public, `AGENT_API_KEY` = key đặt trên nền tảng): `/health` → 200; `/ready` → 200; `POST /ask` không key → 401; có key → 200 (dùng `curl -sS -o /dev/null -w '%{http_code}\n'`).

**CP7 (trong `06-lab-complete/benchmark-observability/develop/`):**
- Tạo báo cáo một lần, từ gốc repo: `cp -n 06-lab-complete/benchmark-observability/BENCHMARK_REPORT_TEMPLATE.md BENCHMARK_REPORT.md`.
- Agent v1 cổng 8001 (`AGENT_VERSION=v1 PORT=8001 python app.py`), v2 cổng 8002.
- Load test: `for c in 1 10 50 100; do python load_test.py --url http://localhost:8002 --requests 300 --concurrency "$c" --out "reports/load_v2_c${c}.json"; done`.
- So sánh `MOCK_SLOW_RATE` = 0, 0.03, 0.1 (bật lại v2 mỗi lần), `--requests 300 --concurrency 20`, lưu `reports/load_v2_slow_0.json`, `..._0.03.json`, `..._0.1.json`.
- Eval: `eval_v1.json`, `eval_v2.json` (`--baseline reports/eval_v1.json`); sửa KB, restart v2; `python eval/run_eval.py --url http://localhost:8002 --min-accuracy 1.0 --baseline reports/eval_v2.json --out reports/eval_v2_fixed.json` phải in `Quality gate ... ✅ PASS`.
- Job CI: nộp file job hoặc giải thích dùng exit code `run_eval.py` chặn merge.

**CP8 (trong `.../production/`), luôn dùng `-p k5-day14-observability`:**
```bash
docker compose -p k5-day14-observability up -d --build --scale agent=1
docker compose -p k5-day14-observability run --rm locust -f /mnt/locust/locustfile.py --host http://nginx --headless -u 100 -r 10 -t 2m --csv /mnt/results/scale_1
docker compose -p k5-day14-observability up -d --scale agent=3
docker compose -p k5-day14-observability run --rm locust -f /mnt/locust/locustfile.py --host http://nginx --headless -u 100 -r 10 -t 2m --csv /mnt/results/scale_3
```
- Agent qua Nginx: `http://localhost:8080`, header `X-API-Key: day14-lab-key`. Grafana :3000 (admin/admin), Prometheus :9090, Jaeger :16686, Locust :8089.
- Làm ≥ 2 thí nghiệm chaos (A `MOCK_ERROR_RATE=0.2`, B `MOCK_SLOW_RATE=0.3`, C `LLM_MODEL=mock-llm-large`, D `docker pause` 1 instance, E `AGENT_VERSION=v1`); ghi thời gian từ lúc đổi → firing; chụp **một** ảnh trang Alerts thấy ≥ 2 alert cùng firing.
- Test alert: `docker run --rm -v "$PWD/prometheus:/p" --entrypoint promtool prom/prometheus:v3.16.0 test rules /p/alert_rules_test.yml`.
- **Chụp ảnh + chép log (kèm dòng log JSON cùng `trace_id`) TRƯỚC khi** `docker compose -p k5-day14-observability down -v`. Nhớ `docker unpause` và trả `.env` về như cũ sau chaos.

## 7. Cấu trúc nộp (SUBMISSION.md)

```text
<repo>/
├── MISSION_ANSWERS.md      # Part 1–5 + output check_production_ready.py + AI log
├── DEPLOYMENT.md           # URL public, lệnh test, biến môi trường đã đặt
├── BENCHMARK_REPORT.md     # từ BENCHMARK_REPORT_TEMPLATE.md, điền đủ
├── reports/                # load_v2_c1/10/50/100.json, load_v2_slow_0/0.03/0.1.json, eval_v1/v2/v2_fixed.json
├── benchmark-results/      # scale_1_stats.csv, scale_3_stats.csv
├── screenshots/            # dashboard.png running.png test.png
│                           # grafana-dashboard.png jaeger-slow-trace.png jaeger-error-trace.png prometheus-alert-firing.png
└── 06-lab-complete/        # code hết TODO, PASS 12/12
```
Copy bằng chứng ra gốc repo trước khi nộp:
```bash
mkdir -p reports benchmark-results
cp -r 06-lab-complete/benchmark-observability/develop/reports/. reports/
cp -r 06-lab-complete/benchmark-observability/production/benchmark-results/. benchmark-results/
```

### Mẫu nội dung từng file
- **`MISSION_ANSWERS.md`** (mẫu trong DAY14_DELIVERY_CHECKLIST mục 1): `# Day 14 Lab - Mission Answers` → `## Part 1` (Exercise 1.1 anti-patterns; 1.3 bảng `Feature | Develop | Production | Why Important?`) → `## Part 2` (2.1 câu hỏi; 2.3 Develop MB / Production MB / Difference %) → `## Part 3` (URL, screenshot) → `## Part 4` (output test; 4.4 cost guard) → `## Part 5` (ghi chú + kết quả test) → output script chấm → **AI log**.
- **`DEPLOYMENT.md`** (mục 3): `# Deployment Information` → `## Public URL` → `## Platform` → `## Test Commands` (Health Check, API Test có xác thực) → `## Environment Variables Set` (PORT, REDIS_URL, AGENT_API_KEY, LOG_LEVEL; chỉ tên biến, không giá trị) → `## Screenshots` (3 link).
- **`BENCHMARK_REPORT.md`**: giữ nguyên 6 mục của template: 1 SLO; 2 Benchmark hiệu năng (2.1 concurrency, 2.2 tail latency); 3 Benchmark chất lượng (bảng v1/v2/v2-fixed, bảng câu sai, trade-off); 4 Observability (4.1 screenshot, 4.2 chaos A–E + câu E, 4.3 debug bằng trace); 5 Scaling (1 vs 3 instance); 6 Kết luận.

## 8. Kiến thức cần hiểu (để Lab Coach hỏi trả lời được)

- Hardcode secret nguy hiểm vì sao; health vs readiness; graceful shutdown; vì sao `/health` 200 khi Redis chết còn `/ready` 503.
- Multi-stage giảm dung lượng ở đâu; vì sao `COPY requirements.txt` trước `COPY . .`.
- Rate limit bảo vệ tốc độ, cost guard bảo vệ tiền; state trong RAM hỏng khi nhiều instance/worker.
- p95/p99 thay avg (tail latency); SLO theo percentile; cost / câu đúng tốt hơn cost / câu; v1 vs v2 là trade-off chất lượng–chi phí–latency.
- Cardinality (không dùng `user_id`/URL thật làm label); 4 Golden Signals; vì sao `/metrics` bị Nginx chặn; thí nghiệm E không firing alert (cần eval/giám sát chất lượng); 504 ở Nginx không hiện trên metric của agent.
- Đáp án mẫu giảng viên (tham khảo, chấm theo cách đo, không theo giá trị tuyệt đối): v1 ≈ 4%, v2 ≈ 91% → 100% sau sửa; v2 ≈ 2× token/câu nhưng cost/câu đúng rẻ hơn ≈ 10×; `MOCK_SLOW_RATE` 0.03 → p99 ≈ 1.7s.

## 9. Điều kiện trừ điểm / không chấm

| Tình huống | Xử lý |
| --- | --- |
| Commit `.env`/key/token (kể cả lịch sử) | −10, phải revoke |
| Số trong `BENCHMARK_REPORT.md` không khớp JSON/CSV | Mục Part 7 tương ứng = 0 |
| Sai tên repo / sai chỗ file | −5 (không tìm được thì không chấm) |
| Repo private | Không chấm |
| Sửa `check_production_ready.py` | Part 6 = 0 |
| Nộp muộn, sao chép, dùng AI không khai báo | Theo RULES |

## 10. Checklist trước khi nộp

- [ ] Tên repo đúng mẫu, Public, mở bằng cửa sổ ẩn danh không 404.
- [ ] `06-lab-complete/`: `python check_production_ready.py` = `PASS 12/12` (bản đầy đủ, có Docker, trong WSL2).
- [ ] `MISSION_ANSWERS.md` đủ Part 1–5 + output script chấm + AI log.
- [ ] `DEPLOYMENT.md`: `/health`, `/ready` 200; `/ask` không key 401, có key 200.
- [ ] `BENCHMARK_REPORT.md` đủ; `reports/`, `benchmark-results/` và **7 ảnh** trong `screenshots/`.
- [ ] Số trong report khớp JSON/CSV.
- [ ] `git log --all --oneline -- '*.env' '.env'` không in gì; không có secret/email/SĐT.
- [ ] Không sửa `check_production_ready.py` và `golden_dataset.jsonl`.

## 11. Điểm mâu thuẫn giữa các tài liệu (cách xử lý mặc định)

1. **Phân bổ điểm Part 6:** INSTRUCTOR_GUIDE (20/15/20/15/10 + history) ≠ RUBRIC (15/10/15/10/10, không history) → theo **RUBRIC**.
2. **Exercise 3.3:** INSTRUCTOR_GUIDE ghi "optional/bonus", RUBRIC cho 1 điểm bắt buộc viết 3–5 dòng → làm theo **RUBRIC**.
3. **Exercise 4.2 (JWT):** INSTRUCTOR_GUIDE "implement", CHECKPOINTS "không phải tự viết, chỉ lấy token" → theo **CHECKPOINTS**.
4. **Số alert firing:** template nói "≥ 1", RUBRIC/CHECKPOINTS yêu cầu **≥ 2** → làm **≥ 2**.
5. **CODE_LAB** (endpoint `/token`, `admin/secret`, cổng 80, `/ask` ở Part 5, copy ra repo riêng) khác README K5 → theo **README K5**.
6. **Self-Test** trong DAY14_DELIVERY_CHECKLIST gọi `GET /ask` (ra 405) → dùng 4 lệnh ở CP6.
