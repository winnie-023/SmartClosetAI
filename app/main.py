# app/main.py
from fastapi import FastAPI
from app.api.v1.router import api_router
from app import models
from app.core.db import engine, Base
from dotenv import load_dotenv
import logging, os
from app.models import wardrobe

load_dotenv()

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(api_router, prefix="/api/v1")

logging.basicConfig(level=logging.DEBUG)

@app.get("/")
def read_root():
    return {"message": "智慧穿衣後端啟動成功"}