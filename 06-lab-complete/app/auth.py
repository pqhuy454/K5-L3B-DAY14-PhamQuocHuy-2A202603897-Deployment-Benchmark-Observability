"""
API Key authentication (tiêu chí 6).

Yêu cầu:
  • Client gửi header  X-API-Key: <key>
  • Key phải trùng biến môi trường AGENT_API_KEY
  • Thiếu hoặc sai key → HTTP 401 (không phải 403 hay 422)
"""
import hmac

from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

from app.config import settings

# auto_error=False để tự trả 401 (mặc định FastAPI trả 403 / 422)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str | None = Security(api_key_header)) -> str:
    """Dependency cho FastAPI — dùng trong /ask: Depends(verify_api_key)."""
    # fail-closed: chưa cấu hình AGENT_API_KEY thì từ chối mọi request
    if (
        not api_key
        or not settings.agent_api_key
        or not hmac.compare_digest(api_key, settings.agent_api_key)
    ):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key
