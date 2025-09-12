# 기본 명령어
up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build --no-cache

rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

logs:
	docker-compose logs -f

status:
	docker-compose ps

# 개별 서비스
frontend:
	docker-compose up -d frontend

backend:
	docker-compose up -d backend

inference:
	docker-compose up -d inference

# 개발용 (로그 보면서)
dev:
	docker-compose up

# ONNX 변환
convert-onnx:
	docker exec -it $$(docker-compose ps -q inference) bash -c "cd /app/models && python convert_to_onnx.py"

check-onnx:
	docker exec -it $$(docker-compose ps -q inference) ls -la /app/models/*.onnx

# 완전 정리
clean:
	docker-compose down --volumes --remove-orphans
	docker system prune -f

# 컨테이너 접속
shell-backend:
	docker exec -it $$(docker-compose ps -q backend) bash

shell-inference:
	docker exec -it $$(docker-compose ps -q inference) bash

# 도움말
help:
	@echo "사용 가능한 명령어:"
	@echo "  up          - 모든 서비스 백그라운드 실행"
	@echo "  down        - 모든 서비스 중지"
	@echo "  dev         - 로그 보면서 실행"
	@echo "  logs        - 로그 보기"
	@echo "  convert-onnx - ONNX 변환 실행"
	@echo "  clean       - 완전 정리"