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
     logging.error("OPENAI_API_KEY environment variable not set!")
     openai_client = None 
else:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

@router.post("/")
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured.")
   
    # 1. 儲存圖片到本地資料夾
    file_ext = Path(file.filename).suffix
    filename = f"{uuid.uuid4()}{file_ext}"
    file_location = UPLOAD_FOLDER / filename

    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logging.error(f"Failed to save file {filename}: {e}")
        if file_location.exists():
             os.remove(file_location)
        raise HTTPException(status_code=400, detail="Invalid file or unable to save file")


    # 2. 讀取圖片並轉成 base64 編碼
    try:
        with open(file_location, "rb") as img_file:
            img_bytes = img_file.read()
            img_base64 = base64.b64encode(img_bytes).decode("utf-8")
    except Exception as e:
        logging.error(f"Failed to read file {filename}: {e}")
        if file_location.exists():
            os.remove(file_location)
        raise HTTPException(status_code=400, detail="Invalid file or unable to read file")

    # 3. 呼叫 OpenAI GPT-4 Vision API 分析圖片
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # 確保使用正確的模型
            messages=[
             {
                "role": "system",
                "content": [
                     {"type": "text", "text": "你是一位服裝分類專家，請依據圖片判斷衣物的類型、顏色、材質與風格，並用繁體中文輸出 JSON 格式的結果。JSON 格式應包含 category, color, material, style 這些欄位。"},
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "請分析這件衣服："},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_base64}",
                        }
                    },
                ],
            },
        ],
        max_tokens=400, 
    )
        ai_message = response.choices[0].message.content
        logging.info(f"OpenAI analysis result: {ai_message}")
    except Exception as e:
        logging.error(f"Error calling OpenAI API: {e}")
        if file_location.exists():
            os.remove(file_location)
        raise HTTPException(status_code=500, detail=f"Error analyzing image with AI: {e}")

     # 4. 解析 GPT-4 分析結果 (需要將 AI 回傳的 JSON 字串解析成 Python 字典)

    try:
        ai_analysis_data = json.loads(ai_message)
        category = ai_analysis_data.get("category", "未知")
        color = ai_analysis_data.get("color", "未知")
        material = ai_analysis_data.get("material", "未知")
        style = ai_analysis_data.get("style", "未知")
    except json.JSONDecodeError:
        logging.error(f"Failed to parse JSON from OpenAI response: {ai_message}")
            # 如果解析失敗，可以使用默認值或記錄錯誤信息
        category = "未知"
        color = "未知"
        material = "未知"
        style = "未知"
        ai_analysis_data = {"raw_response": ai_message} # 儲存原始響應以供調試

    except Exception as e:
        logging.error(f"Error calling OpenAI API: {e}")
         # 刪除已保存的檔案
        if file_location.exists():
             os.remove(file_location)
        raise HTTPException(status_code=500, detail=f"Error analyzing image with AI: {e}")

    
      # 5. 將衣物資訊儲存到資料庫
    # 這裡使用 AI 分析得出的 category，而不是根據尺寸判斷
    db_item = Wardrobe(
        filename=filename,
        category=category, # 使用 AI 分析結果
        color=color,       # 儲存顏色
        material=material, # 儲存材質
        style=style,       # 儲存風格
        width=0,           # 如果不需要，可以不儲存尺寸或使用默認值
        height=0,
        user_id=current_user.id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    logging.info(f"Wardrobe item added for user {current_user.id}: {filename}")

    # 6. 回傳結果
    return {
        "message": "檔案上傳並分析完成",
        "filename": filename,
        "category": category,
        "color": color,
        "material": material,
        "style": style,
        "user_id": current_user.id,
        "ai_analysis_data": ai_analysis_data # 回傳解析後的數據或原始響應
    }
