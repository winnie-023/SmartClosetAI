#api/v1/user.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.auth import User 
from app.core.db import get_db

router = APIRouter()
