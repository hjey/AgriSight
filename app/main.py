from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes import router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.include_router(router)

app.mount("/videos", StaticFiles(directory="/data"), name="videos")
app.mount("/static", StaticFiles(directory="/app/static"), name="static")
