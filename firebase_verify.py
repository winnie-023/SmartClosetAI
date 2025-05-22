import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, Request

# 初始化 Firebase Admin（只初始化一次）
cred = credentials.Certificate("firebase-admin-key.json")
firebase_admin.initialize_app(cred)

# 驗證 Token 的函數（可加到 Depends 使用）
def verify_firebase_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        # Bearer <token>
        id_token = auth_header.split(" ")[1]
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token  # 可從中取得 uid、email 等資訊
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")
