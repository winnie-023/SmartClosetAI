# tests/test_outfit.py
from fastapi.testclient import TestClient
from app.main import app  # 引入 FastAPI 應用

client = TestClient(app)

def test_recommend_outfit():
    # 模擬發送 POST 請求來獲取穿搭建議
    response = client.post("/outfit/recommend", json={"city": "Taipei"})
    
    # 檢查返回的狀態碼
    assert response.status_code == 200
    
    # 檢查返回的數據是否包含 'recommendations' 鍵
    data = response.json()
    assert "recommendations" in data
    
    # 檢查建議是否是列表
    assert isinstance(data["recommendations"], list)  # 確保建議是以列表形式返回

def test_recommend_outfit_with_weather():
    # 模擬發送 GET 請求來獲取帶有天氣的穿搭建議
    response = client.get("/recommend_with_weather?city=Taipei")
    
    # 檢查返回的狀態碼
    assert response.status_code == 200
    
    # 檢查返回的數據是否包含 'weather' 和 'recommendations' 鍵
    data = response.json()
    assert "weather" in data
    assert "recommendations" in data
    
    # 檢查建議是否是列表
    assert isinstance(data["recommendations"], list)  # 確保是列表

def test_no_clothes_in_wardrobe():
    # 模擬用戶衣櫃沒有衣物的情況
    response = client.post("/outfit/recommend", json={"city": "Taipei"})
    
    # 檢查返回的狀態碼
    assert response.status_code == 404
    
    # 檢查錯誤消息是否為預期
    data = response.json()
    assert data["detail"] == "你的衣櫃是空的，請先上傳衣服哦！"