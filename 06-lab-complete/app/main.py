"""
Production AI Agent — Part 6 Final Project

Kiểm tra:
    python check_production_ready.py
"""
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.auth import verify_api_key
from app.config import settings
from app.cost_guard import check_budget, record_cost
from app.rate_limiter import check_rate_limit
from app.redis_client import redis_healthy
from utils.mock_llm import ask as llm_ask


# Structured logging (tiêu chí 10): mỗi dòng log của app là 1 JSON object
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "lvl": record.levelname,
            "event": record.getMessage(),
        }
        data.update(getattr(record, "extra_fields", {}))
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


_handler = logging.StreamHandler()
_handler.setFormatter(JsonFormatter())
logger = logging.getLogger("agent")
logger.handlers = [_handler]
logger.setLevel(settings.log_level)
logger.propagate = False


def log(event: str, **fields):
    logger.info(event, extra={"extra_fields": fields})


@asynccontextmanager
async def lifespan(app: FastAPI):
    log("startup", environment=settings.environment, port=settings.port)
    yield
    # Graceful shutdown (tiêu chí 11): uvicorn nhận SIGTERM, ngừng nhận kết nối mới,
    # chờ request đang chạy xong rồi mới chạy đoạn này và thoát (exit code 0).
    # Không tự đăng ký handler SIGTERM để tránh chặn việc tắt của uvicorn.
    log("shutdown")


app = FastAPI(title="Production AI Agent", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    user_id: str | None = None


@app.middleware("http")
async def access_log(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
    except Exception:
        # không lộ stack trace cho client; chi tiết nằm trong log
        logger.exception("unhandled_error", extra={"extra_fields": {"path": request.url.path}})
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
    log(
        "request",
        path=request.url.path,
        method=request.method,
        status=response.status_code,
        ms=round((time.time() - start) * 1000, 1),
    )
    return response


@app.get("/health")
def health():
    """Liveness: luôn 200 khi process còn chạy, không phụ thuộc Redis."""
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """Readiness: 200 khi Redis kết nối được, 503 khi không."""
    if not redis_healthy():
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "reason": "redis unavailable"},
        )
    return {"status": "ready"}


@app.post("/ask")
def ask(body: AskRequest, api_key: str = Depends(verify_api_key)):
    check_rate_limit(api_key)
    check_budget()
    answer = llm_ask(body.question)
    cost = record_cost(len(body.question.split()) * 2, len(answer.split()) * 2)
    return {"question": body.question, "answer": answer, "cost_usd": round(cost, 8)}
