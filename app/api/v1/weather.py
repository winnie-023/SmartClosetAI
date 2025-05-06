#api/v1/weather.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os
import logging

logging.basicConfig(level=logging.INFO)

router = APIRouter()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
if not WEATHER_API_KEY:
     logging.error("WEATHER_API_KEY environment variable not set!")
     WEATHER_API_KEY = "your-fallback-weather-api-key-for-dev"


WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"

class WeatherResponse(BaseModel):
    temperature: float
    description: str
    city: str
    humidity: int
    suggestion: str

def get_outfit_suggestion(temp: float, weather: str) -> str:
    """
    根據溫度和天氣描述生成穿搭建議。
    """
    logging.debug(f"Generating outfit suggestion for temp={temp}°C, weather='{weather}'")
    suggestion = "建議穿著舒適的衣物" # 預設建議

    if "雨" in weather:
        suggestion = "天氣有雨，建議攜帶雨具並穿著防水鞋或外套"
    elif temp < 5:
        suggestion = "天氣嚴寒，請務必穿著厚重的多層保暖衣物，如羽絨服、厚毛衣、手套、帽子和圍巾"
    elif temp < 10:
        suggestion = "天氣非常寒冷，請穿著保暖外套、毛衣和長褲"
    elif temp < 15:
        suggestion = "天氣較冷，建議穿著薄外套、毛衣或衛衣搭配長褲"
    elif temp < 20:
        suggestion = "天氣微涼，適合穿著長袖T恤、襯衫搭配長褲或裙子，可攜帶薄外套"
    elif temp < 25:
        suggestion = "天氣舒適溫暖，適合穿著短袖T恤、襯衫、長褲或裙子"
    elif temp < 30:
        suggestion = "天氣溫暖偏熱，建議穿著輕薄透氣的短袖、短褲或裙子"
    else: 
        suggestion = "天氣炎熱，請穿著非常輕薄透氣的衣物，注意防曬和補充水分"

    return suggestion


@router.get("/current")
async def get_current_weather(city: str):
    """根據城市名稱獲取天氣信息"""
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",  
        "lang": "zh_tw"  
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(WEATHER_API_URL, params=params)
            response.raise_for_status() # 如果狀態碼不是 2xx，會拋出異常
            data = response.json()
        except httpx.RequestError as e:
            logging.error(f"HTTP request failed for weather API: {e}")
            raise HTTPException(status_code=500, detail=f"Error fetching weather data: {e}")
        except httpx.HTTPStatusError as e:
             logging.error(f"Weather API returned error status code {e.response.status_code}: {e.response.text}")
             if e.response.status_code == 401:
                  raise HTTPException(status_code=401, detail="Invalid API key for weather service.")
             elif e.response.status_code == 404:
                  raise HTTPException(status_code=404, detail=f"City '{city}' not found.")
             else:
                  raise HTTPException(status_code=e.response.status_code, detail=f"Weather API error: {e.response.text}")
        except Exception as e:
             logging.error(f"An unexpected error occurred fetching weather: {e}")
             raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


    temperature = data["main"]["temp"]
    description = data["weather"][0]["description"]
    humidity = data["main"]["humidity"]

    suggestion = get_outfit_suggestion(temperature, description)

    logging.info(f"Fetched weather for {city}: Temp={temperature}, Desc='{description}', Suggestion='{suggestion}'")

    return WeatherResponse(
        temperature=temperature,
        description=description,
        city=city,
        humidity=humidity,
        suggestion=suggestion
    )

async def get_current_weather_data(city: str):
    """
    根據城市名稱從 OpenWeatherMap API 獲取原始天氣數據。
    """
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",  
        "lang": "zh_tw"  
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(WEATHER_API_URL, params=params)
            response.raise_for_status() 
            data = response.json()
            logging.debug(f"Successfully fetched weather data for {city}: {data}")
            return data
        except httpx.RequestError as e:
            logging.error(f"HTTP request failed for weather API for city {city}: {e}")
            raise HTTPException(status_code=500, detail=f"Error fetching weather data: {e}")
        except httpx.HTTPStatusError as e:
             logging.error(f"Weather API returned error status code {e.response.status_code} for city {city}: {e.response.text}")
             if e.response.status_code == 401:
                  raise HTTPException(status_code=401, detail="Invalid API key for weather service.")
             elif e.response.status_code == 404:
                  raise HTTPException(status_code=404, detail=f"City '{city}' not found.")
             else:
                  raise HTTPException(status_code=e.response.status_code, detail=f"Weather API error: {e.response.text}")
        except Exception as e:
             logging.error(f"An unexpected error occurred fetching weather for city {city}: {e}")
             raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
