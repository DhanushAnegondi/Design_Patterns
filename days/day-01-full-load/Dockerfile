# Day 01 — Full Loader. A tiny Python image that runs the loader against LocalStack S3.
FROM python:3.11-slim

WORKDIR /app

# Install only what the loader needs. (moto is included so the same image can also run the
# in-process variant, but in Docker we talk to LocalStack via AWS_ENDPOINT_URL.)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code and dataset are mounted at runtime by docker-compose (see volumes:), so we don't COPY them.
CMD ["python", "code/run.py"]
