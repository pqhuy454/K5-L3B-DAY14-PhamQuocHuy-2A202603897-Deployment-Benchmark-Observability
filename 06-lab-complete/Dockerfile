# Stage 1: builder — cài dependencies
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: runtime — chỉ copy kết quả, user non-root, HEALTHCHECK
FROM python:3.11-slim AS runtime
RUN groupadd -r appuser && useradd -r -g appuser -m appuser
WORKDIR /app
COPY --from=builder /root/.local /home/appuser/.local
COPY app/ ./app/
COPY utils/ ./utils/
RUN chown -R appuser:appuser /app /home/appuser/.local
USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUSERBASE=/home/appuser/.local \
    PYTHONUNBUFFERED=1 \
    PORT=8000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://localhost:%s/health' % os.getenv('PORT','8000'))" || exit 1
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
