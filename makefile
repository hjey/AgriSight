### 기본 명령 ###
up:
	docker-compose up --build

down:
	docker-compose down

restart:
	docker-compose stop backend worker
	docker-compose up --build -d backend worker

logs:
	docker-compose logs -f


### 단독 실행 ###
frontend:
	docker-compose up --build frontend

backend:
	docker-compose up --build backend

summary:
	docker-compose up --build summary_server


### 단독 실행 (백그라운드) ###
frontend-d:
	docker-compose up -d frontend

backend-d:
	docker-compose up -d backend

summary-d:
	docker-compose up -d summary_server


### 개발 모드 ###
dev:
	docker-compose up -d postgres redis summary_server
	docker-compose up backend frontend worker

back-dev:
	docker-compose exec backend uvicorn main:app --reload --host 0.0.0.0 --port 8000


### 운영 모드 ###
prod:
	docker-compose up --build -d

back-prod:
	docker-compose exec backend gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000


### 캐시 없이 실행 (프론트엔드) ###
web-dev-nocache:
	docker-compose stop backend frontend
	docker-compose rm -f backend frontend
	docker-compose up -d postgres redis summary_server
	NEXT_SKIP_CACHE=1 docker-compose up backend frontend worker


### 정리 작업 ###
clean-web:
	docker-compose stop backend frontend
	docker-compose rm -f backend frontend

clean:
	docker-compose rm -sf backend worker
	docker-compose up --build -d backend worker

clean-all:
	docker-compose down --volumes --remove-orphans
	docker volume prune -f


### 워커 ###
worker:
	docker-compose exec worker celery -A worker worker --loglevel=info

