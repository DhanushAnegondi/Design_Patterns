# Day 02 — Incremental Loader. Small Python image that runs the loader against LocalStack S3.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code and dataset are mounted at runtime by docker-compose (see volumes:).
CMD ["python", "code/run.py"]
