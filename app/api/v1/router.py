from fastapi import APIRouter
from .auth import router as auth_router
from .wardrobe import router as wardrobe_router
from .weather import router as weather_router
from .outfit import router as outfit_router


api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(wardrobe_router, prefix="/wardrobe", tags=["wardrobe"])   
api_router.include_router(weather_router, prefix="/weather", tags=["weather"])
api_router.include_router(outfit_router, prefix="/outfit", tags=["outfit"])
