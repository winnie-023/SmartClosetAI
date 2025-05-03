from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.wardrobe import Wardrobe
from app.models.auth import User
from app.api.v1.auth import get_current_user
from app.core.db import get_db
import random
from app.api.v1.weather import get_outfit_suggestion  
from app.api.v1.weather import get_weather_with_suggestion

router = APIRouter()

@router.post("/outfit/recommend")
async def recommend_outfit(db: Session = Depends(get_db), 
                           current_user: User = Depends(get_current_user),
                           city: str = "Taipei"):  
    # 獲取天氣數據
    weather = await get_weather_with_suggestion(city=city) 
    
    # 根據天氣數據給出建議
    if weather.temperature < 15:
        # 如果溫度低於15度，推薦外套
        recommended_category = "外套"
    elif weather.temperature >= 15 and weather.temperature < 25:
        # 如果溫度在15度到25度之間，推薦長袖衣物
        recommended_category = "長袖"
    else:
        # 如果溫度超過25度，推薦短袖或輕便衣物
        recommended_category = "短袖"
    
    # 從資料庫中查詢對應的衣物類型
    items = db.query(Wardrobe).filter(Wardrobe.user_id == current_user.id, Wardrobe.category == recommended_category).all()
    
    if not items:
        raise HTTPException(status_code=404, detail="你的衣櫃是空的，請先上傳衣服哦！")

    # 返回穿搭建議
    return {
        "weather": {
            "temperature": weather.temperature,
            "description": weather.description,
            "city": weather.city
        },
        "recommended_outfit": recommended_category,
        "available_items": [{"filename": item.filename, "category": item.category} for item in items]
    }


@router.get("/recommend_with_weather")
async def recommend_outfit_with_weather(city: str = "Taipei", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)): 
    
    # 獲取天氣數據和建議
    weather = await get_weather_with_suggestion(city=city)
    description = weather["description"]

    # 取得該用戶的衣櫃
    wardrobe_items = db.query(Wardrobe).filter(Wardrobe.user_id == current_user.id).all()
    
    if not wardrobe_items:
        raise HTTPException(status_code=404, detail="你的衣櫃是空的，請先上傳衣服哦！")
    
    # 簡單的天氣篩選
    description = weather.get("description", "")
    if "雨" in description:
        filtered_items = [item for item in wardrobe_items if item.category == "外套"]
    elif "熱" in description or "晴" in description:
        filtered_items = [item for item in wardrobe_items if item.category != "外套"]
    else:
        filtered_items = wardrobe_items  # 不篩選

    if not filtered_items:
        # 如果沒找到適合的，回傳整個衣櫃隨機
        filtered_items = wardrobe_items

    recommendation = random.sample(filtered_items, min(3, len(filtered_items)))

    result = []
    for item in recommendation:
        result.append({
            "filename": item.filename,
            "category": item.category,
            "size": {"width": item.width, "height": item.height}
        })
    
    return {
        "user_id": current_user.id,
        "weather": weather["description"],
        "recommendations": result
    }

# @router.get("/recommend")
# def recommend_outfit(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     # 取得該用戶的衣櫃
#     items = db.query(Wardrobe).filter(Wardrobe.user_id == current_user.id).all()
    
#     if not items:
#         raise HTTPException(status_code=404, detail="你的衣櫃是空的，請先上傳衣服哦！")
    
#     # 隨機推薦 1~3 件
#     recommendation = random.sample(wardrobe_items, min(3, len(wardrobe_items)))

#     result = []
#     for item in recommendation:
#         result.append({
#             "filename": item.filename,
#             "category": item.category,
#             "size": {"width": item.width, "height": item.height}
#         })
    
#     return {
#         "user_id": current_user.id,
#         "recommendations": result
#     }
