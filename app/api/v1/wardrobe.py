#api/v1/wardrobe.py
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from rembg import remove
from PIL import Image
import io
import os 
from app.models.wardrobe import Wardrobe
from app.models.auth import User
from app.api.v1.auth import get_current_user
from app.core.db import get_db
import logging
from app.services import image_analysis
from fastapi.responses import JSONResponse
import shutil

logging.basicConfig(level=logging.INFO)


router = APIRouter()


@router.get("/items")
def get_wardrobe_items(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    獲取當前使用者的所有衣櫃物品。
    """
    wardrobe_items = db.query(Wardrobe).filter(Wardrobe.user_id == current_user.id).all()
    if not wardrobe_items:
        return {"user_id": current_user.id, "items": [], "message": "您的衣櫃是空的"}

    result = []
    for item in wardrobe_items:
        result.append({
            "id": item.id, 
            "filename": item.filename,
            "user_id": item.user_id
        })

    return {"user_id": current_user.id, "items": result}

@router.delete("/items/{item_id}")
def delete_wardrobe_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    刪除使用者衣櫃中的指定物品。
    """
    db_item = db.query(Wardrobe).filter(Wardrobe.id == item_id, Wardrobe.user_id == current_user.id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="找不到指定的衣櫃物品或您沒有權限刪除")

    db.delete(db_item)
    db.commit()

    return {"message": f"衣櫃物品 {item_id} 已從衣櫃中刪除"}



from app.services.background_removal import remove_background_rembg

@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """
    上傳衣服圖片 → 使用 rembg 去背 → 主色分析 → 回傳圖片與主色
    """
    # 儲存原始圖片
    temp_path = f"uploaded_images/{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 使用 rembg 去背
    with open(temp_path, "rb") as f:
        input_bytes = f.read()
        output_bytes = remove(input_bytes)

    # 儲存去背後圖片
    output_image = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
    output_path = temp_path.replace(".jpg", "_rembg.png").replace(".jpeg", "_rembg.png").replace(".png", "_rembg.png")
    output_image.save(output_path)

    # 主色分析
    dominant_colors = image_analysis.extract_dominant_colors(output_path)

    return JSONResponse(content={
        "message": "圖片處理成功（已使用 rembg 去背＋主色分析）",
        "dominant_colors": dominant_colors,
        "image_result_path": f"/{output_path}"
    })