"""
Rate limiting (tiêu chí 7).

Yêu cầu:
  • Mỗi API key tối đa RATE_LIMIT_PER_MINUTE request trong 60 giây (sliding window)
  • Vượt giới hạn → HTTP 429, nên kèm header Retry-After
  • State lưu trong Redis để mọi worker / instance dùng chung và vẫn còn sau khi
    restart agent (script chấm sẽ restart agent để kiểm tra)
"""
import hashlib
import time
import uuid

from fastapi import HTTPException

from app.config import settings
from app.redis_client import r

WINDOW_SECONDS = 60


def check_rate_limit(key: str) -> None:
    # băm API key để không lưu key thô trong Redis
    redis_key = "ratelimit:" + hashlib.sha256(key.encode()).hexdigest()[:16]
    now = time.time()
    try:
        r.zremrangebyscore(redis_key, 0, now - WINDOW_SECONDS)
        if r.zcard(redis_key) >= settings.rate_limit_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(WINDOW_SECONDS)},
            )
        r.zadd(redis_key, {f"{now}:{uuid.uuid4().hex[:8]}": now})
        r.expire(redis_key, WINDOW_SECONDS + 5)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Rate limiter unavailable")
