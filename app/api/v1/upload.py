from fastapi import APIRouter, UploadFile, File
import shutil
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import os
import base64

router = APIRouter()

# 儲存上傳圖片的資料夾
UPLOAD_FOLDER = Path("uploaded_images")

# 載入 .env 環境變數
load_dotenv()

# 建立 OpenAI 客戶端
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    # 1. 儲存圖片到本地資料夾
    file_location = UPLOAD_FOLDER / file.filename

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. 讀取圖片並轉成 base64 編碼
    with open(file_location, "rb") as img_file:
        img_bytes = img_file.read()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")

    # 3. 呼叫 OpenAI gpt-4o Vision API 分析圖片
    response = client.chat.completions.create(
        model="gpt-4o",  # 注意！新版模型
        messages=[
            {
                "role": "system",
                "content": "你是一位服裝分類專家，請依據圖片判斷衣物的類型、顏色、材質與風格。"
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "請告訴我這件衣服的類型、顏色、材質與風格"},
                    {
                        "type": "image",
                        "image": {
                            "base64": img_base64,
                            "mime_type": "image/jpeg"  # 如果是 PNG 改成 image/png
                        }
                    }
                ]
            }
        ],
        max_tokens=100,
    )

    # 4. 取出 Vision 分析結果
    ai_message = response.choices[0].message.content

    # 5. 回傳
    return {
        "message": "檔案上傳並分析完成",
        "filename": file.filename,
        "ai_analysis": ai_message
    }
