# FastAPI 및 Alpine.js를 위한 Dockerfile

FROM python:3.9-slim

WORKDIR /app

# 코드 및 requirements 복사
COPY ./app /app
COPY requirements.txt /app

# 시스템 패키지 설치 + Python 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download en_core_web_sm

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]