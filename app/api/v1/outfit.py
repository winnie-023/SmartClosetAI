#api/v1/outfit.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.wardrobe import Wardrobe
from app.models.auth import User
from app.api.v1.auth import get_current_user
from app.core.db import get_db
import random
# 正確導入需要使用的天氣相關函式
from app.api.v1.weather import get_outfit_suggestion, get_current_weather_data # 確保導入了獲取原始天氣數據的函式
import logging

logging.basicConfig(level=logging.INFO)

router = APIRouter()

@router.get("/recommend_with_weather")
async def recommend_outfit_with_weather(city: str = "Taipei", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    根據使用者衣櫃和指定城市的天氣推薦穿搭。
    """
    try:
        # 1. 正確地呼叫異步函式獲取原始天氣數據
        weather_data = await get_current_weather_data(city=city)
        temperature = weather_data["main"]["temp"] # 從原始數據中獲取溫度
        description = weather_data["weather"][0]["description"] # 從原始數據中獲取天氣描述

        # 2. 將溫度和描述傳遞給同步函式獲取穿搭建議字串
        suggestion_text = get_outfit_suggestion(temp=temperature, weather=description)

    except HTTPException as e:
        # 如果獲取天氣數據時發生 HTTPException，直接拋出
        logging.error(f"獲取{city}的天氣數據失敗: {e.detail}")
        raise e
    except Exception as e:
        logging.error(f"獲取{city}的天氣數據時發生未預期的錯誤: {e}")
        # 對於其他異常，返回一個通用的服務器錯誤
        raise HTTPException(status_code=500, detail=f"獲取天氣數據時發生錯誤: {e}")

    wardrobe_items = db.query(Wardrobe).filter(Wardrobe.user_id == current_user.id).all()
    if not wardrobe_items:
        raise HTTPException(status_code=404, detail="您的衣櫃是空的，請先上傳衣服！")

    # --- 更細化的天氣篩選和搭配邏輯 (您可以根據需要擴展) ---
    filtered_items = []

    # 簡單的篩選邏輯範例：根據溫度範圍篩選
    # 這裡可以使用 temperature 和 description 進行更精確的篩選
    if temperature < 10: # 非常寒冷
        filtered_items = [item for item in wardrobe_items if item.category in ["外套", "毛衣", "衛衣"]]
    elif temperature < 18: # 較冷
        filtered_items = [item for item in wardrobe_items if item.category in ["外套", "毛衣", "衛衣", "上衣"]]
    elif temperature > 30: # 炎熱
        filtered_items = [item for item in wardrobe_items if item.category in ["上衣", "下著"] and item.category not in ["外套", "毛衣", "衛衣"]]
    else: # 舒適 (~18-30度)
        filtered_items = [item for item in wardrobe_items if item.category in ["上衣", "下著"]] # 這裡是一個簡化

    # 如果篩選後沒有衣物，回傳整個衣櫃的隨機衣物
    if not filtered_items:
        logging.warning(f"找不到適合的天氣條件 {description} ({temperature}°C) 的衣物。推薦隨機衣物。")
        recommendation = random.sample(wardrobe_items, min(5, len(wardrobe_items))) # 回傳整個衣櫃的隨機衣物，最多5件
    else:
        # 從篩選後的衣物中隨機選擇一部分進行推薦 (這裡可以加入更複雜的搭配邏輯)
        recommendation = random.sample(filtered_items, min(5, len(filtered_items))) # 從篩選結果中隨機選擇，最多5件

    # --- 回傳結果 ---
    result = []
    for item in recommendation:
        result.append({
            "filename": item.filename,
            "category": item.category,
            "color": item.color,       # 確保 Wardrobe 模型有這些欄位
            "material": item.material, # 確保 Wardrobe 模型有這些欄位
            "style": item.style,       # 確保 Wardrobe 模型有這些欄位
            "size": {"width": item.width, "height": item.height} # 確保 Wardrobe 模型有這些欄位
        })

    return {
        "user_id": current_user.id,
        "weather": { # 回傳更詳細的天氣資訊
            "city": city,
            "temperature": temperature,
            "description": description,
            "humidity": weather_data.get("main", {}).get("humidity") # 安全地獲取濕度
        },
        "weather_suggestion": suggestion_text, # 回傳穿搭建議
        "recommendations": result
    }

@router.get("/recommend")
async def recommend_outfit(city: str = None, occasion: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    根據使用者衣櫃、天氣或場合推薦穿搭。
    """
    wardrobe_items = db.query(Wardrobe).filter(Wardrobe.user_id == current_user.id).all()
    if not wardrobe_items:
        raise HTTPException(status_code=404, detail="您的衣櫃是空的，請先上傳衣服！")

    if city:
        try:
            # 獲取天氣數據
            weather_data = await get_current_weather_data(city=city)
            temperature = weather_data["main"]["temp"]
            description = weather_data["weather"][0]["description"]

            # 根據天氣篩選衣物
            if temperature < 10:
                filtered_items = [item for item in wardrobe_items if item.category in ["外套", "毛衣", "衛衣"]]
            elif temperature < 18:
                filtered_items = [item for item in wardrobe_items if item.category in ["外套", "毛衣", "衛衣", "上衣"]]
            elif temperature > 30:
                filtered_items = [item for item in wardrobe_items if item.category in ["上衣", "下著"] and item.category not in ["外套", "毛衣", "衛衣"]]
            else:
                filtered_items = [item for item in wardrobe_items if item.category in ["上衣", "下著"]]

            if not filtered_items:
                filtered_items = wardrobe_items

            suggestion_text = get_outfit_suggestion(temp=temperature, weather=description)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"獲取天氣數據時發生錯誤: {e}")

    elif occasion:
        # 根據場合篩選衣物
        occasion_mapping = {
            "formal": ["西裝", "襯衫", "長褲"],
            "casual": ["T恤", "牛仔褲", "運動鞋"],
            "party": ["洋裝", "高跟鞋", "飾品"],
            "sport": ["運動服", "運動鞋"]
        }
        filtered_items = [item for item in wardrobe_items if item.category in occasion_mapping.get(occasion.lower(), [])]

        if not filtered_items:
            raise HTTPException(status_code=404, detail=f"找不到適合場合 '{occasion}' 的衣物，請檢查您的衣櫃！")

        suggestion_text = f"根據場合 '{occasion}'，建議穿著以下衣物。"

    else:
        raise HTTPException(status_code=400, detail="請提供城市名稱或場合名稱以獲取穿搭建議！")

    # 隨機選擇推薦的衣物
    recommendation = random.sample(filtered_items, min(5, len(filtered_items)))

    result = []
    for item in recommendation:
        result.append({
            "filename": item.filename,
            "category": item.category,
            "color": item.color,
            "material": item.material,
            "style": item.style,
            "size": {"width": item.width, "height": item.height}
        })

    return {
        "user_id": current_user.id,
        "suggestion": suggestion_text,
        "recommendations": result
    }