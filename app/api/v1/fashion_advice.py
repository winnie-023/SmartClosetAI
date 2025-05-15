# api/v1/fashion_advice.py
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from app.services.fashion_advisor import FashionAdvisor
from app.api.v1.auth import get_current_user
from app.models.auth import User
from app.models.wardrobe import Wardrobe
from app.core.db import get_db
from sqlalchemy.orm import Session
import json
import logging
from app.services.fashion_classifier import predict_fashion_class

router = APIRouter()

class WorkOutfitRequest(BaseModel):
    context: str

class DateOutfitRequest(BaseModel):
    activity: str

class SpecialOccasionRequest(BaseModel):
    occasion: str

class WardrobeOutfitRequest(BaseModel):
    wardrobe_items: List[str]
    activity: str

class WeatherBasedRequest(BaseModel):
    activity: str
    temperature: float
    season: str

class RecommendRequest(BaseModel):
    occasion: str
    context: str

@router.post("/work")
async def get_work_outfit_advice(
    request: WorkOutfitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get outfit advice for work scenarios based on user's wardrobe."""
    try:
        # 獲取用戶的衣櫃物品
        wardrobe_items = db.query(Wardrobe).filter(Wardrobe.user_id == current_user.id).all()
        if not wardrobe_items:
            raise HTTPException(status_code=404, detail="您的衣櫃是空的，請先上傳衣服！")

        # 將衣櫃物品轉換為可讀的格式
        wardrobe_info = []
        for item in wardrobe_items:
            wardrobe_info.append({
                "category": item.category,
                "color": item.color,
                "material": item.material,
                "style": item.style
            })

        # 創建 FashionAdvisor 實例
        advisor = FashionAdvisor()
        
        # 使用 GPT-4 根據衣櫃物品和情境給出建議
        advice = await advisor.get_work_outfit_advice(
            context=request.context,
            wardrobe_items=wardrobe_info
        )
        
        return advice
    except Exception as e:
        logging.error(f"獲取穿搭建議時發生錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/date")
async def get_date_outfit_advice(
    request: DateOutfitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get outfit advice for date/social scenarios, and auto-analyze latest uploaded image."""
    try:
        advisor = FashionAdvisor()
        advice = await advisor.get_date_outfit_advice(request.activity)

        # 取得該用戶最新一張上傳的圖片
        latest_item = db.query(Wardrobe).filter(Wardrobe.user_id == current_user.id).order_by(Wardrobe.id.desc()).first()
        analysis = None
        if latest_item:
            import numpy as np
            from PIL import Image
            import os
            img_path = os.path.join("uploaded_images", latest_item.filename)
            if os.path.exists(img_path):
                image = Image.open(img_path).convert('RGB')
                image_np = np.array(image)
                try:
                    category = predict_fashion_class(image_np)
                except Exception as e:
                    category = None
                analysis = {"category": category, "filename": latest_item.filename}

        # 回傳分析結果
        return {**advice, "analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/special-occasion")
async def get_special_occasion_advice(
    request: SpecialOccasionRequest,
    current_user: User = Depends(get_current_user)
):
    """Get outfit advice for special occasions."""
    try:
        advisor = FashionAdvisor()
        advice = await advisor.get_special_occasion_advice(request.occasion)
        return advice
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/weather-based")
async def get_weather_based_advice(
    request: WeatherBasedRequest,
    current_user: User = Depends(get_current_user)
):
    """Get outfit advice based on weather and season."""
    try:
        advisor = FashionAdvisor()
        advice = await advisor.get_weather_based_advice(
            request.activity,
            request.temperature,
            request.season
        )
        return advice
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommend")
async def recommend_fashion_post(request: RecommendRequest):
    """
    根據用戶選擇的場合類型和上下文提供穿搭建議。
    """
    advisor = FashionAdvisor()
    suggestion = await advisor.get_advice(request.occasion, request.context)

    return {"occasion": request.occasion, "context": request.context, "suggestion": suggestion}