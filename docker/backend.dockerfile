# backend.dockerfile
FROM python:3.9-slim

WORKDIR /backend

COPY ./backend /backend
COPY ./backend/requirements.txt /backend

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

CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]
