# Day 14 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
Trong `01-localhost-vs-production/develop/app.py`:
1. API key hardcode: `OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"` (dòng 17). Push lên GitHub là lộ key.
2. `DATABASE_URL` có cả mật khẩu hardcode (dòng 18).
3. Config cứng trong code (`DEBUG = True`, `MAX_TOKENS = 500`, dòng 21-22), không đọc từ biến môi trường nên không đổi được giữa dev/staging/prod.
4. Dùng `print()` thay vì logging có cấu trúc (dòng 33, 36, 38), khó parse trong log aggregator.
5. Log ra secret: `print(f"[DEBUG] Using key: {OPENAI_API_KEY}")` (dòng 34). Đã thấy key này xuất hiện trong log khi chạy thật.
6. Không có endpoint `/health` hay `/ready`: gọi `/health` trả 404, platform không biết khi nào cần restart.
7. Port và host cố định: `host="localhost"`, `port=8000` (dòng 51-52). `localhost` không nhận kết nối từ ngoài container; Render/Railway inject `PORT` qua env nên app không nghe đúng cổng.
8. `reload=True` (dòng 53): chế độ debug reload không dùng cho production.
9. Không có xử lý SIGTERM / graceful shutdown: platform tắt container là cắt ngang request đang chạy.

### Exercise 1.2: Chạy bản develop
Chạy trong WSL2 (`python app.py`), gọi `POST /ask?question=Hello`:
```
HTTP/1.1 200 OK
{"answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận."}
```
Gửi JSON body `{"question":"Hello"}` thì trả `422 Unprocessable Content` vì bản develop nhận `question` qua query. `GET /health` trả `404 Not Found`.
Nhận xét: chạy được, nhưng chưa sẵn sàng production (key lộ ra log, không có health check, không có shutdown).

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcode trong code | Env vars qua `config.py` (`Settings`, `os.getenv`) | Đổi giữa môi trường mà không sửa code; không commit secret |
| Secrets | `OPENAI_API_KEY` ghi thẳng, bị in ra log | `AGENT_API_KEY` đọc từ env, không log secret; `validate()` báo lỗi nếu thiếu key ở production | Lộ key trong repo/log là sự cố bảo mật |
| Host / Port | `localhost`, cổng 8000 cố định | `HOST=0.0.0.0`, `PORT` từ env | Container và Render/Railway cần nghe `0.0.0.0` và đúng `PORT` được inject |
| Health check | Không có (404) | `GET /health` (liveness) và `GET /ready` (readiness, 503 khi chưa sẵn sàng) | Platform biết khi nào restart, load balancer biết khi nào route traffic |
| Logging | `print()`, có in cả secret | `logging` ra JSON, chỉ log độ dài câu hỏi/câu trả lời | Dễ parse, tìm kiếm; không rò rỉ dữ liệu nhạy cảm |
| Shutdown | Đột ngột | `lifespan` + handler SIGTERM, hoàn thành request đang chạy rồi mới tắt | Không mất request khi deploy/scale |
| Debug/reload | `reload=True` luôn bật | `reload` chỉ bật khi `DEBUG=true` | Reload tốn tài nguyên và không an toàn ở production |
| CORS | Không cấu hình | `allowed_origins` từ env | Kiểm soát origin được gọi API |
| Request/validation | `question` qua query, không kiểm tra rỗng | JSON body, rỗng thì trả 422 với thông báo rõ | API ổn định, lỗi dễ hiểu |

### Checkpoint 1: tự kiểm tra
Anti-pattern trong `develop/app.py` mà `production/app.py` đã sửa: `host="localhost", port=8000` (dòng 51-52) được thay bằng `host=settings.host, port=settings.port` (dòng 196-197), lấy từ env.

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
Dockerfile: `02-docker/develop/Dockerfile`
1. Base image: `python:3.11` (bản Python đầy đủ, nặng, khoảng 1 GB).
2. Working directory: `/app` (`WORKDIR /app`).
3. Vì sao `COPY requirements.txt` trước: Docker cache theo từng layer. Dependencies ít đổi, code đổi liên tục. Copy requirements và `pip install` trước thì khi chỉ sửa code, các layer cài thư viện được dùng lại từ cache, build nhanh hơn rất nhiều.
4. CMD vs ENTRYPOINT: `CMD` là lệnh mặc định, bị ghi đè dễ dàng bằng đối số của `docker run <image> <lệnh khác>`. `ENTRYPOINT` là chương trình cố định của container; đối số của `docker run` chỉ được nối thêm vào sau nó. Dockerfile này dùng `CMD ["python", "app.py"]`.

### Exercise 2.2: Build và run
```bash
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .
docker run -d --rm --name dev-agent -p 8000:8000 my-agent:develop
curl -i -X POST 'http://localhost:8000/ask?question=What%20is%20Docker%3F'
```
Kết quả: `HTTP/1.1 200 OK`
`{"answer":"Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!"}`
`GET /health` cũng trả `200 OK`.

### Exercise 2.3: Multi-stage build
Dockerfile: `02-docker/production/Dockerfile`
- Stage 1 (`builder`, `python:3.11-slim`): cài `gcc`, `libpq-dev` và chạy `pip install --user -r requirements.txt` để biên dịch/cài dependencies vào `/root/.local`. Stage này không dùng để deploy.
- Stage 2 (`runtime`, `python:3.11-slim`): tạo user non-root `appuser`, chỉ `COPY --from=builder /root/.local` (các package đã cài) và `main.py`, `utils/mock_llm.py`, chạy bằng `uvicorn --workers 2`, có `HEALTHCHECK`.
- Vì sao nhỏ hơn: image cuối không chứa `gcc`, `libpq-dev`, cache apt và các layer build; base là `slim` thay vì bản đầy đủ.

Kích thước đo bằng `docker images my-agent`:
- Develop: 1,67 GB (1.667.780.273 byte)
- Production: 240 MB (239.815.358 byte)
- Difference: nhỏ hơn 85,6% (production < 500 MB)

### Exercise 2.4: Docker Compose stack
Chạy bằng `docker compose -p k5-day14-docker up -d --build` trong `02-docker/production/` (đã tạo `.env.local` trống). 4 service:

```
Client ──► Nginx (80/443) ──► Agent (8000) ──► Redis (6379)
                                  └──────────► Qdrant (6333)
        (tất cả nằm trong network nội bộ "internal")
```
- `nginx` (nginx:alpine): cổng công khai 80/443, reverse proxy + rate limit 10 req/s mỗi IP, chuyển tới `agent:8000`.
- `agent`: build từ `02-docker/production/Dockerfile` (target `runtime`), không mở cổng ra ngoài, chỉ truy cập qua Nginx.
- `redis` (redis:7-alpine): cache/session/rate limit, có healthcheck.
- `qdrant` (qdrant/qdrant:v1.9.0): vector database, có healthcheck.
- Agent `depends_on` Redis và Qdrant ở trạng thái healthy; các service giao tiếp qua network `internal` bằng tên service (`redis`, `qdrant`, `agent`).

Trạng thái sau khi lên: agent, redis, qdrant đều `healthy`, nginx `Up`. Test qua Nginx (cổng 80):
- `GET http://localhost/health` → `200 OK`, `{"status":"ok","uptime_seconds":14.3,"version":"2.0.0",...}`
- `POST http://localhost/ask` với `{"question":"Explain microservices"}` → `200 OK`, `{"answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận."}`

Đã dọn bằng `docker compose -p k5-day14-docker down -v`.

## Part 4: API Security

### Exercise 4.1: API Key authentication
File: `04-api-gateway/develop/app.py`
- API key được kiểm tra ở hàm `verify_api_key` (dòng 39-54), gắn vào `/ask` bằng `Depends(verify_api_key)`. Key đúng đọc từ biến môi trường `AGENT_API_KEY` (dòng 35).
- Sai key: thiếu header → `401`; có header nhưng sai → `403 Invalid API key`.
- Rotate key: đổi giá trị biến môi trường `AGENT_API_KEY` rồi restart/redeploy, không cần sửa code.

Chạy bằng `AGENT_API_KEY=secret-key-123 python app.py` (WSL):
```
# Không có key
HTTP/1.1 401 Unauthorized
{"detail":"Missing API key. Include header: X-API-Key: <your-key>"}

# Sai key
HTTP/1.1 403 Forbidden
{"detail":"Invalid API key."}

# Đúng key
HTTP/1.1 200 OK
{"question":"Hello","answer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic."}
```

### Exercise 4.2: JWT authentication
File: `04-api-gateway/production/auth.py`. Flow: `POST /auth/token` kiểm tra username/password (`authenticate_user`), tạo JWT HS256 chứa `sub`, `role`, `iat`, `exp` (hết hạn sau 60 phút) bằng `create_token`. Các request sau gửi `Authorization: Bearer <token>`; `verify_token` kiểm tra chữ ký và hạn, không cần tra database.
Token lấy bằng tài khoản `student` / `demo123` (token đã che):
```
POST /auth/token → {"access_token":"<REDACTED>","token_type":"bearer","expires_in_minutes":60,...}

# Không có token
HTTP/1.1 401 Unauthorized
{"detail":"Authentication required. Include: Authorization: Bearer <token>"}

# Token sai
HTTP/1.1 403 Forbidden
{"detail":"Invalid token."}
```

### Exercise 4.3: Rate limiting
File: `04-api-gateway/production/rate_limiter.py`
- Thuật toán: Sliding Window. Mỗi user có một `deque` timestamp; mỗi request xóa các timestamp cũ hơn 60 giây rồi đếm số còn lại.
- Giới hạn: user 10 request/phút (`rate_limiter_user`), admin 100 request/phút (`rate_limiter_admin`).
- Bypass cho admin: `app.py` chọn limiter theo `role`; tài khoản `teacher` (role `admin`) dùng limiter 100 request/phút. Không phải bỏ hẳn giới hạn, chỉ nâng giới hạn.
- Hạn chế: state nằm trong RAM của từng process, nên khi chạy nhiều worker/instance mỗi nơi đếm riêng. Production cần Redis (làm ở Part 6).

Gọi `/ask` liên tục 12 lần bằng token `student`:
```
req 1 … req 10: HTTP/1.1 200 OK
req 11: HTTP/1.1 429 Too Many Requests
req 12: HTTP/1.1 429 Too Many Requests
```
Response 429:
```
HTTP/1.1 429 Too Many Requests
x-ratelimit-limit: 10
x-ratelimit-remaining: 0
x-ratelimit-reset: 1795681733
retry-after: 59
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":59}}
```

### Exercise 4.4: Cost guard implementation
File: `04-api-gateway/production/cost_guard.py`. Cách làm:
- Trước khi gọi LLM: `check_budget(user_id)` lấy usage trong ngày của user; nếu chi phí ≥ ngân sách ngày ($1/user) thì trả `402 Payment Required`; nếu tổng toàn hệ thống ≥ $10/ngày thì trả `503`. Ở mức 80% ngân sách thì ghi log cảnh báo.
- Sau khi gọi LLM: `record_usage(...)` cộng input/output token, tính tiền theo bảng giá (`$0.00015`/1K input, `$0.0006`/1K output) rồi cộng vào chi phí user và chi phí toàn cục.
- Reset theo ngày bằng cách so sánh `day` của record với ngày hiện tại.
- Kiểm tra thật: sau 10 request, `GET /me/usage` trả `cost_usd: 0.000184`, `budget_usd: 1.0`, `requests: 10`.
- Bản mẫu lưu trong RAM nên mất khi restart và không dùng chung giữa các instance. Ở Part 6 tôi sẽ lưu trong Redis (`INCRBYFLOAT` trên khóa theo ngày) để chạy nhiều worker.
- Vì sao cần cả rate limit và cost guard: rate limit bảo vệ tốc độ (chống spam trong thời gian ngắn), cost guard bảo vệ tiền (chặn chi tiêu tích lũy dù từng request đều hợp lệ).

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks
File: `05-scaling-reliability/develop/app.py`. Code đã có sẵn hai endpoint, tôi đọc và chạy thử:
- `GET /health` (liveness): luôn trả 200 khi process còn sống, kèm `uptime_seconds`, `version`, và kiểm tra bộ nhớ. Platform gọi định kỳ, non-200 hoặc timeout thì restart container.
- `GET /ready` (readiness): trả 200 khi `_is_ready = True` (sau khi startup xong), trả `503` khi đang khởi động hoặc đang shutdown. Load balancer dùng nó để quyết định có chuyển traffic vào instance không.
- Khác nhau: liveness hỏi "process còn sống không", readiness hỏi "có nhận traffic được không". Instance đang khởi động thì sống nhưng chưa sẵn sàng, nên không được restart mà chỉ tạm không nhận traffic.

Kết quả chạy (WSL):
```
GET /health → HTTP/1.1 200 OK  {"status":"ok","uptime_seconds":3.8,"version":"1.0.0",...,"checks":{"memory":{"status":"ok","used_percent":6.7}}}
GET /ready  → HTTP/1.1 200 OK  {"ready":true,"in_flight_requests":1}
```

### Exercise 5.2: Graceful shutdown
Cơ chế trong `develop/app.py`:
- Middleware `track_requests` đếm `_in_flight_requests`.
- Khi nhận SIGTERM, uvicorn dừng nhận kết nối mới và gọi phần shutdown của `lifespan`: đặt `_is_ready = False`, chờ tối đa 30 giây cho đến khi không còn request đang xử lý, rồi thoát. `uvicorn.run(..., timeout_graceful_shutdown=30)`.
- `handle_sigterm` chỉ ghi log, việc tắt do uvicorn xử lý.

Thử nghiệm: gửi `POST /ask?question=Long%20task` rồi gửi `kill -TERM` ngay sau đó:
```
ask status=200                      ← request đang chạy vẫn hoàn thành
INFO: Shutting down
INFO: "POST /ask?question=Long%20task HTTP/1.1" 200 OK
🔄 Graceful shutdown initiated...
✅ Shutdown complete
Received signal 15 — uvicorn will handle graceful shutdown
process exited
```
Request nhận 200 trước khi process thoát, đúng yêu cầu graceful shutdown.

### Exercise 5.3: Stateless design
File: `05-scaling-reliability/production/app.py`.
- Không giữ conversation history trong biến của process. Hai hàm `save_session` và `load_session` ghi/đọc `session:{id}` trong Redis (`setex`, TTL 1 giờ); `append_to_history` giữ tối đa 20 tin nhắn.
- Vì sao: khi chạy nhiều instance, mỗi instance có RAM riêng. Nếu history nằm trong RAM thì request thứ hai rơi vào instance khác sẽ mất ngữ cảnh. Với Redis, instance nào cũng đọc được cùng một session.
- Lưu ý: code có phương án dự phòng dùng dict trong RAM khi không kết nối được Redis. Khi chạy thật, response báo `"storage": "in-memory"` và mất tính stateless. Trong stack này Redis luôn chạy nên dùng `"redis"`.

### Exercise 5.4: Load balancing
Chạy trong `05-scaling-reliability/production/`:
```bash
touch .env.local
docker compose -p k5-day14-scaling up -d --build --scale agent=3
```
Trạng thái: 3 container `agent-1/2/3` (healthy), `nginx` mở cổng `8080`, `redis` healthy. `nginx.conf` dùng DNS của Docker (`resolver 127.0.0.11`) với upstream `agent:8000` nên chia traffic round-robin; `proxy_next_upstream error timeout http_503` chuyển sang instance khác khi có lỗi.
Gửi 10 request `POST /chat` qua `http://localhost:8080`, đếm `served_by`:
```
3 instance-100e45
3 instance-6057a1
4 instance-7c3aaf
```
Traffic được chia gần đều cho cả 3 instance.

### Exercise 5.5: Test stateless
`python test_stateless.py` (gửi 5 câu hỏi trong cùng một session, không tự tắt instance):
```
Request 1: [instance-7c3aaf]
Request 2: [instance-6057a1]
Request 3: [instance-100e45]
Request 4: [instance-7c3aaf]
Request 5: [instance-6057a1]
Instances used: {'instance-7c3aaf', 'instance-100e45', 'instance-6057a1'}
Total messages: 10   (5 user + 5 assistant)
✅ Session history preserved across all instances via Redis!
```
Giải thích: 5 request do 3 instance khác nhau xử lý, nhưng `GET /chat/{session_id}/history` trả đủ 10 tin nhắn, vì state nằm trong Redis chứ không nằm trong RAM của instance.

Kiểm tra thêm bằng tay: tạo một session, `docker kill` một container agent, rồi gửi 4 request nữa với cùng `session_id`:
```
after kill req 1..4: 200
history count: 10   (2 tin nhắn ban đầu + 4 request × 2)
```
Một instance chết đi nhưng session không mất và Nginx vẫn phục vụ được.

Đã dọn: `docker compose -p k5-day14-scaling down -v`.

## Part 6: Output check_production_ready.py

Chạy trong WSL2 (`os.name = posix`), thư mục `06-lab-complete/`, Docker đầy đủ:
```
📋 Checklist Deliverable
   ✅ Dockerfile (multi-stage, < 500 MB)
   ✅ docker-compose.yml (agent + redis)
   ✅ .dockerignore
   ✅ Health check endpoint (GET /health)
   ✅ Readiness endpoint (GET /ready)
   ✅ API Key authentication
   ✅ Rate limiting
   ✅ Cost guard
   ✅ Config từ environment variables
   ✅ Structured logging
   ✅ Graceful shutdown
   ✅ Public URL ready (Railway / Render config)
----------------------------------------------------------------
  Result: 12/12 tiêu chí đạt · 42/42 checks passed
  🎉 PASS 12/12 — PRODUCTION READY! Deploy nào!
```
Số đo: image 297 MB; build 123 giây; `docker stop` exit code 0 trong 0,7 giây; rate limit trả 429 sau 5 request và vẫn 429 sau khi restart agent.
