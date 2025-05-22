#api/v1/auth.py
from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String
from fastapi.security import OAuth2PasswordBearer
from app.core.db import Base, get_db
from app.models.auth import User
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
import os
import logging


logging.basicConfig(level=logging.INFO)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")  # 通常從環境變數獲取

ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

def get_password_hash(password:str):
    hashed = pwd_context.hash(password)
    logging.debug(f"密碼雜湊值: {hashed}")  
    return hashed

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=60)):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    encoded_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logging.debug(f"產生的 Token: {encoded_token}")  # 日誌輸出
    return encoded_token

@router.get("/ping")
def ping():
    return {"message": "pong"}

@router.post("/register")
def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # 檢查使用者名稱是否已經註冊
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="使用者名稱已被註冊")

    # 檢查電子郵件是否已經註冊
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="電子郵件已被註冊")

    # 建立新使用者
    hashed_password = get_password_hash(password)
    new_user = User(username=username, email=email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"msg": "使用者建立成功"}

@router.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        logging.warning(f"找不到使用者: {username}")
        raise HTTPException(status_code=400, detail="無效的認證資訊")
    
    if not verify_password(password, db_user.password):
        logging.warning(f"使用者 {username} 的密碼錯誤")
        raise HTTPException(status_code=400, detail="無效的認證資訊")
    
    token = create_access_token(data={"sub": username})
    logging.info(f"使用者登入成功: {username}")
    return {"access_token": token, "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="無法驗證認證資訊",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        logging.debug(f"收到 token: {token}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        logging.debug(f"解碼後的 token: {payload}")
    except JWTError as e:
        logging.error(f"JWT 解碼失敗: {str(e)}")
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
    
