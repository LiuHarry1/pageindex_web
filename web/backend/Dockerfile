# Build from the repository root (pageindex lives next to web/, not inside web/backend):
#   docker build -f web/backend/Dockerfile .

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

COPY web/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pageindex/ /app/pageindex/
COPY web/backend/app/ /app/app/

# Persist uploads + index JSON on the host: mount one directory here, e.g.
#   docker run -v /your/path/pageindex-data:/data ...
ENV PAGEINDEX_STORAGE_ROOT=/data
RUN mkdir -p /data/uploads /data/workspace

ENV PYTHONUNBUFFERED=1

EXPOSE 8008

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8008"]
