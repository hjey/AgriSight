from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes import router
from dotenv import load_dotenv
from db import check_postgres_connection

load_dotenv()

app = FastAPI()
app.include_router(router)

app.mount("/videos", StaticFiles(directory="/data"), name="videos")
app.mount("/static", StaticFiles(directory="/backend/static"), name="static")

@app.on_event("startup")
async def startup():
    print("DB Connection Check Start. ")
    check_postgres_connection()