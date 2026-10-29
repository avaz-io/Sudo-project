# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337 AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/backend

WORKDIR /app

COPY backend/requirements.txt /tmp/requirements.txt
COPY devops/constraints.txt /tmp/constraints.txt
RUN python -m pip install --no-cache-dir \
        -r /tmp/requirements.txt -c /tmp/constraints.txt \
    && python -m pip check \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app --no-create-home app \
    && mkdir /data \
    && chown app:app /data

COPY backend/app /app/backend/app
USER app

FROM base AS tests
COPY pytest.ini /app/pytest.ini
COPY tests /app/tests
CMD ["python", "-m", "pytest", "tests/", "-v", "-p", "no:cacheprovider"]

FROM base AS runtime
EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=5 \
    CMD python -c "import json, urllib.request; response = urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2); assert json.load(response) == {'status': 'ok'}"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
