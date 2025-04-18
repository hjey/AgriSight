dev:
	docker-compose up --build

prod:
	docker-compose -f docker-compose.yml up --build

down:
	docker-compose down

clean:
	docker compose down --rmi all --volumes --remove-orphans

worker:
	docker-compose exec worker celery -A worker worker --loglevel=info

web-dev:
	docker-compose exec web uvicorn main:app --reload --host 0.0.0.0 --port 8000

web-prod:
	docker-compose exec web gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000

test:
	echo "Makefile is working!"
