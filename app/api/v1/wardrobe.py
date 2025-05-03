from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from PIL import Image
from sqlalchemy.orm import Session
import os, uuid
from app.models.wardrobe import Wardrobe
from app.core.db import get_db
from app.models.auth import User
from app.api.v1.auth import get_current_user

router = APIRouter()

Upload_DIR = "uploads"
os.makedirs(Upload_DIR, exist_ok=True)

@router.post("/upload")
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    file_ext = os.path.splitext(file.filename)[-1]
    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(Upload_DIR, filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    try:
        img = Image.open(file_path)
        img.verify()  # 驗證圖片
    except Exception:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="Invalid image file")

    width, height = img.size

    if height > width:
        category = "外套"
    else:
        category = "褲子"

    db_item = Wardrobe(
        filename=filename,
        category=category,
        width=width,
        height=height,
        user_id=current_user.id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return {
        "filename": filename,
        "category": category,
        "size":{ "width": width, "height": height},
        "user_id": current_user.id
    }