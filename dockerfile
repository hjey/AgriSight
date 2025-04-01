# FastAPI 및 Alpine.js를 위한 Dockerfile

# 베이스 이미지로 Python을 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 코드 복사
COPY ./app /app

# requirements.txt를 컨테이너로 복사
COPY requirements.txt /app

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0

# 포트 열기
EXPOSE 8000

# FastAPI 애플리케이션 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
