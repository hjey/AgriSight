from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes import router

app = FastAPI()
app.include_router(router)

app.mount("/videos", StaticFiles(directory="/data"), name="videos")
app.mount("/static", StaticFiles(directory="/app/static"), name="static")
