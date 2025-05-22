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
from app.services.image_processing import process_image, analyze_clothing_type
from typing import List
from fastapi import UploadFile, File

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

# 建立衣物類型資料夾
CATEGORY_FOLDERS = {
    "上衣": "wardrobe/上衣",
    "下身": "wardrobe/下身",
    "外套": "wardrobe/外套",
    "洋裝": "wardrobe/洋裝",
    "鞋子": "wardrobe/鞋子",
    "包包": "wardrobe/包包",
    "帽子": "wardrobe/帽子",
    "襪子": "wardrobe/襪子",
    "飾品": "wardrobe/飾品",
    "特殊": "wardrobe/特殊",
}

# 建立所有類型資料夾（只做一次）
for folder in CATEGORY_FOLDERS.values():
    Path(folder).mkdir(parents=True, exist_ok=True)

def classify_to_folder(clothing_type_text: str) -> str:
    for keyword, folder in CATEGORY_FOLDERS.items():
        if keyword in clothing_type_text:
            return folder
    return CATEGORY_FOLDERS["特殊"]

@router.post("/")
async def upload_image(files: List[UploadFile] = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="請上傳至少一張圖片")
    results = []
    """
    上傳圖片 → 自動去背 → 分析類型 → 儲存到相對應類型的衣櫥
    """
    # 1. 儲存圖片到本地資料夾
    # 單張圖片流程
    if len(files) == 1:
        file = files[0]
        filename = f"{uuid.uuid4()}{Path(file.filename).suffix}"
        file_location = UPLOAD_FOLDER / filename

        try:
            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            logging.error(f"儲存檔案 {filename} 失敗: {e}")
            if file_location.exists():
                os.remove(file_location)
            raise HTTPException(status_code=400, detail="無效的檔案或無法儲存檔案")

        # 2. 處理圖片（去背）
        try:
            result = process_image(str(file_location))
            processed_image_path = result["processed_image_path"]
        except Exception as e:
            logging.error(f"圖片處理失敗: {e}")
            raise HTTPException(status_code=500, detail="圖片處理失敗")

        # 3. 分析衣物類型
        try:
            clothing_type = analyze_clothing_type(str(file_location))
        except Exception as e:
            logging.error(f"衣物類型分析失敗: {e}")
            raise HTTPException(status_code=500, detail="衣物類型分析失敗")

        # 4. 移動圖片到對應類別資料夾
        category_folder = classify_to_folder(clothing_type)
        final_path = Path(category_folder) / Path(processed_image_path).name
        shutil.move(processed_image_path, final_path)

        # 5. 儲存進資料庫
        db_item = Wardrobe(
            filename=final_path.name,
            category=clothing_type,
            user_id=current_user.id
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)

        results.append({
                "original_filename": file.filename,
                "stored_filename": filename,
                "processed_image_path": str(final_path),
                "clothing_type": clothing_type
            })
    
    else:
        # 多張圖片同時處理
        for file in files:
            filename = f"{uuid.uuid4()}{Path(file.filename).suffix}"
            file_location = UPLOAD_FOLDER / filename

            try:
                with open(file_location, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
            except Exception as e:
                logging.error(f"儲存檔案 {filename} 失敗: {e}")
                if file_location.exists():
                    os.remove(file_location)
                continue  # 跳過這張繼續處理下一張

            try:
                result = process_image(str(file_location))
                processed_image_path = result["processed_image_path"]
            except Exception as e:
                logging.error(f"圖片處理失敗: {e}")
                continue

            try:
                clothing_type = analyze_clothing_type(str(file_location))
            except Exception as e:
                logging.error(f"衣物類型分析失敗: {e}")
                continue

            category_folder = classify_to_folder(clothing_type)
            final_path = Path(category_folder) / Path(processed_image_path).name
            shutil.move(processed_image_path, final_path)

            db_item = Wardrobe(
                filename=final_path.name,
                category=clothing_type,
                user_id=current_user.id
            )
            db.add(db_item)
            db.commit()
            db.refresh(db_item)

            results.append({
                "original_filename": file.filename,
                "stored_filename": filename,
                "processed_image_path": str(final_path),
                "clothing_type": clothing_type
            })

    return {
        "message": f"成功處理 {len(results)} 張圖片",
        "results": results
    }