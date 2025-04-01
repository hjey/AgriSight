import redis
from fastapi.templating import Jinja2Templates

# Redis 클라이언트 초기화
redis_client = redis.StrictRedis(host='redis', port=6379, db=0)

# Jinja2 템플릿 설정
templates = Jinja2Templates(directory="templates")
