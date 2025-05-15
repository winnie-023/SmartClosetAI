from fastapi import APIRouter, UploadFile, File
from app.services.clothing_detector import analyze_clothing_yolo
import logging
import numpy as np
import cv2
import os
from pathlib import Path
from rembg import remove
from PIL import Image
import io

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

# 創建保存圖片的目錄
SAVE_DIR = Path("uploads/clothes")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/")
async def detect_clothing(file: UploadFile = File(...)):
    """
    檢測上傳圖片中的服裝，進行去背、分類並保存
    """
    try:
        # 讀取上傳的圖像
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("圖片解碼失敗")

        # 記錄原始圖像大小
        h, w = image.shape[:2]
        logging.info(f"原始圖像大小: {w}x{h}")
        
        # 分析服裝
        result = analyze_clothing_yolo(image)

        if "error" in result:
            return {
                "status": "error",
                "error": result["error"]
            }
            
        # 獲取檢測結果
        detections = result.get("detections", [])
        
        # 如果沒有檢測到任何服裝
        if not detections:
            return {
                "status": "warning",
                "message": "未能識別到任何服裝或飾品，請確保圖片清晰且包含單件服裝或飾品",
                "filename": file.filename
            }
            
        # 處理每個檢測到的服裝
        saved_images = []
        for idx, detection in enumerate(detections):
            # 獲取服裝位置
            loc = detection["location"]
            x1, y1, x2, y2 = loc["x1"], loc["y1"], loc["x2"], loc["y2"]
            
            # 裁剪服裝區域
            cropped = image[y1:y2, x1:x2]
            
            # 轉換為PIL圖像進行去背
            pil_image = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
            no_bg = remove(pil_image)
            
            # 創建類別目錄
            category_dir = SAVE_DIR / detection["type"]
            category_dir.mkdir(exist_ok=True)
            
            # 生成文件名
            base_name = Path(file.filename).stem
            save_path = category_dir / f"{base_name}_{idx}.png"
            
            # 保存去背後的圖片
            no_bg.save(save_path)
            saved_images.append(str(save_path))
            
            logging.info(f"已保存去背圖片: {save_path}")

        # 返回檢測結果和保存的圖片路徑
        return {
            "status": "success",
            "filename": file.filename,
            "analysis": detections[0] if detections else None,
            "saved_images": saved_images
        }

    except ValueError as ve:
        logging.error(f"圖片解碼錯誤: {ve}")
        return {"status": "error", "error": "圖片解碼失敗"}
    except Exception as e:
        logging.error(f"未知錯誤: {e}")
        return {"status": "error", "error": str(e)}


@router.post("/process-image")
async def process_image(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes))

    # 去背
    image_no_bg = remove_background(image)

    # 分類
    label = predict_clothing(image_no_bg)

    # 回傳分類結果
    return {"filename": file.filename, "predicted_class": label}