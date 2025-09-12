from celery import Celery
import httpx

# Celery 인스턴스 생성
celery = Celery(
    "worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)
celery.autodiscover_tasks(['worker'])

INFERENCE_URL = "http://inference:8000/segment"

def segment_task(image_data: bytes, model_type: str, content_type: str):
    import asyncio

    async def _call():
        form = {"model_type": model_type}
        files = {"image": ("uploaded.png", image_data, content_type)}
        async with httpx.AsyncClient() as client:
            resp = await client.post(INFERENCE_URL, data=form, files=files)
            return resp.json()

    return asyncio.run(_call())