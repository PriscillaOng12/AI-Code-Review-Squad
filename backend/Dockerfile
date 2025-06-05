# syntax=docker/dockerfile:1

FROM python:3.11-slim as builder
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install poetry && poetry export --without-hashes -f requirements.txt > requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /app/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]