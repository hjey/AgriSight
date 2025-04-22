# Dockerfile

FROM python:3.9-slim

WORKDIR /

COPY . .

RUN pip install --no-cache-dir transformers torch fastapi uvicorn

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
