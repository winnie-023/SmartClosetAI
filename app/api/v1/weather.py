from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os

router = APIRouter()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "your-weather-api-key")  # 從環境變數中獲取API金鑰
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"

# 定義返回結果格式
class WeatherResponse(BaseModel):
    temperature: float
    description: str
    city: str
    humidity: int
    suggestion: str

# 根據天氣情況提供穿搭建議
def get_outfit_suggestion(temp: float, weather: str) -> str:
    if "雨" in weather:
        return "建議攜帶雨具並穿防水外套"
    elif temp < 15:
        return "天氣寒冷，請穿厚外套"
    elif temp > 30:
        return "天氣炎熱，建議穿短袖短褲"
    else:
        return "天氣舒適，適合輕便穿著"

# 獲取當前天氣
@router.get("/current")
async def get_current_weather(city: str):
    """根據城市名稱獲取天氣信息"""
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",  # 攝氏溫度
        "lang": "zh_tw"  # 中文返回
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(WEATHER_API_URL, params=params)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Weather API error")
    
    data = response.json()
    temperature = data["main"]["temp"]
    description = data["weather"][0]["description"]
    humidity = data["main"]["humidity"]
    
    # 根據天氣和溫度提供穿搭建議
    suggestion = get_outfit_suggestion(temperature, description)

    return WeatherResponse(
        temperature=temperature,
        description=description,
        city=city,
        humidity=humidity,
        suggestion=suggestion
    )