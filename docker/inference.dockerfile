# inference.dockerfile
FROM python:3.12-slim

WORKDIR /app

# 시스템 라이브러리 설치 (OpenCV, ffmpeg 등 필요시 추가)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 소스 코드 복사
COPY ../inference /app
COPY ../inference/requirements.txt /app/requirements.txt

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

# uvicorn으로 FastAPI 실행
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
