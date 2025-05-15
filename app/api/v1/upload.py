#api/v1/upload.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from app.core.db import get_db 
from app.models.wardrobe import Wardrobe 
from app.models.auth import User 
from app.api.v1.auth import get_current_user 
import os, base64, openai, logging, uuid, shutil, json, re
from app.services.fashion_classifier import predict_fashion_class


logging.basicConfig(level=logging.INFO)

router = APIRouter()

# 儲存上傳圖片的資料夾
UPLOAD_FOLDER = Path("uploaded_images")

# 確保資料夾存在
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# 載入 .env 環境變數
load_dotenv()

# 載入 OpenAI API 金鑰
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
     logging.error("未設定 OPENAI_API_KEY 環境變數！")
     openai_client = None 
else:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

@router.post("/")
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. 儲存圖片到本地資料夾
    file_ext = Path(file.filename).suffix
    filename = f"{uuid.uuid4()}{file_ext}"
    file_location = UPLOAD_FOLDER / filename

    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logging.error(f"儲存檔案 {filename} 失敗: {e}")
        if file_location.exists():
             os.remove(file_location)
        raise HTTPException(status_code=400, detail="無效的檔案或無法儲存檔案")

    # 2. 將衣物資訊儲存到資料庫
    db_item = Wardrobe(
        filename=filename,
        user_id=current_user.id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    logging.info(f"已為使用者 {current_user.id} 新增衣櫃物品: {filename}")

    # 3. 用模型分析圖片類別
    import numpy as np
    from PIL import Image
    image = Image.open(file_location).convert('RGB')
    image_np = np.array(image)
    try:
        category = predict_fashion_class(image_np)
    except Exception as e:
        logging.error(f"圖片分析失敗: {e}")
        category = None

    # 4. 回傳結果
    return {
        "message": "檔案上傳成功",
        "filename": filename,
        "user_id": current_user.id,
        "analysis": {
            "category": category
        }
    }
