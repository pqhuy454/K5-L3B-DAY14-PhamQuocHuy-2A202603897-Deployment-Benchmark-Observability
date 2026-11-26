# Deployment Information

## Public URL
https://day14-agent-3k1q.onrender.com

## Platform
Render (Web Service, runtime Docker, gói Free, region Singapore) + Render Key Value (Redis, gói Free, cùng region).
Agent là code Part 6 trong `06-lab-complete/` (Root Directory `06-lab-complete`, build bằng `Dockerfile` trong thư mục đó).
Ghi chú: tạo Blueprint từ `06-lab-complete/render.yaml` bị Render chặn vì yêu cầu thông tin thanh toán, nên hai dịch vụ được tạo thủ công trên dashboard với cấu hình tương đương `render.yaml` (health check `/health`, biến môi trường như bên dưới).

## Test Commands

### Health Check
```bash
curl https://day14-agent-3k1q.onrender.com/health
# {"status":"ok"}   (HTTP 200)
curl https://day14-agent-3k1q.onrender.com/ready
# {"status":"ready"}   (HTTP 200, Redis kết nối được)
```

### API Test (không có key → 401)
```bash
curl -X POST https://day14-agent-3k1q.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
# HTTP 401  {"detail":"Invalid or missing API key"}
```

### API Test (with authentication → 200)
```bash
curl -X POST https://day14-agent-3k1q.onrender.com/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
# HTTP 200
```

Kết quả 4 lệnh tự kiểm CP6 (`/health`, `/ready`, `/ask` không key, `/ask` có key): `200`, `200`, `401`, `200`.

## Environment Variables Set
Chỉ ghi tên biến, giá trị đặt trên dashboard Render, không nằm trong code hay repo:
- PORT (Render tự cấp)
- REDIS_URL (Internal URL của Render Key Value)
- AGENT_API_KEY
- ENVIRONMENT
- RATE_LIMIT_PER_MINUTE
- DAILY_BUDGET_USD
- LOG_LEVEL

## Screenshots
- [Deployment dashboard](screenshots/dashboard.png)
- [Service running](screenshots/running.png)
- [Test results](screenshots/test.png)
