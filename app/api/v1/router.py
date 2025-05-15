#api/v1/router.py
from fastapi import APIRouter
from .auth import router as auth_router
from .wardrobe import router as wardrobe_router
from .weather import router as weather_router
from .outfit import router as outfit_router
from .upload import router as upload_router
from .detect import router as detect_router
from .fashion_advice import router as fashion_advice_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["認證"])
api_router.include_router(wardrobe_router, prefix="/wardrobe", tags=["衣櫃"])   
api_router.include_router(weather_router, prefix="/weather", tags=["天氣"])
api_router.include_router(outfit_router, prefix="/outfit", tags=["穿搭"])
api_router.include_router(upload_router, prefix="/upload", tags=["上傳"])
api_router.include_router(detect_router, prefix="/detect", tags=["服裝檢測"])
api_router.include_router(fashion_advice_router, prefix="/fashion-advice", tags=["AI穿搭顧問"]) 
