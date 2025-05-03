from fastapi import FastAPI
from app.api.v1.router import api_router
from app import models
from app.core.db import engine
import app.models.auth
import app.models.user
from api import upload

app = FastAPI(title="Smart Wardrobe API", version="1.0.0")
app = FastAPI()

app.include_router(upload.router)

models.Base.metadata.create_all(bind=engine)   

@app.get("/")
def read_root():
    return {"message": "智慧穿衣後端啟動成功"}