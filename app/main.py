# app/main.py
from fastapi import FastAPI
from app.core.db import engine, Base
from dotenv import load_dotenv
import logging
import os
from app.api.v1.router import api_router

load_dotenv()

app = FastAPI()

# 啟用資料庫初始化
Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)

# 註冊所有 API 路由
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "智慧衣櫃後端啟動成功"}

from fastapi.staticfiles import StaticFiles

# 確保上傳目錄存在
if not os.path.exists("uploaded_images"):
    os.makedirs("uploaded_images")

app.mount("/uploaded_images", StaticFiles(directory="uploaded_images"), name="uploaded_images")
