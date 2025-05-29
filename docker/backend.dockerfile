# ============= 빌드 스테이지 =============
FROM python:3.12-slim as builder

# 빌드에 필요한 모든 도구 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libpq-dev \
    libgl1-mesa-dev \
    libglib2.0-dev \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgeos-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN pip install poetry==1.8.3

# Poetry 설정
RUN poetry config virtualenvs.create false

WORKDIR /app

# 의존성 파일 복사
COPY ./backend/pyproject.toml ./backend/poetry.lock* ./

# 의존성 설치 (개발 의존성 제외)
RUN poetry install --no-interaction --no-ansi --no-dev --timeout=600

# ============= 런타임 스테이지 =============
FROM python:3.12-slim as runtime

# 런타임에만 필요한 라이브러리들 설치
RUN apt-get update && apt-get install -y \
    libpq5 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /backend

# 빌드 스테이지에서 설치된 Python 패키지들만 복사
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 소스 코드 복사
COPY ./backend /backend

EXPOSE 8000

CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]