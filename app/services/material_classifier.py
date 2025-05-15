# app/services/material_classifier.py
import cv2
import numpy as np
from skimage.feature import local_binary_pattern

# 紋理分析：局部二值模式（LBP）來識別材質
def analyze_material(image: np.ndarray) -> str:
    """
    使用局部二值模式（LBP）進行材質分析
    :param image: OpenCV 讀取的圖片（np.ndarray 格式）
    :return: 預測的材質類型
    """
    # 將圖片轉為灰度圖
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 使用 LBP 特徵提取紋理
    radius = 1
    n_points = 8 * radius
    lbp = local_binary_pattern(gray, n_points, radius, method='uniform')

    # 計算 LBP 的直方圖
    hist, _ = np.histogram(lbp.ravel(), bins=np.arange(0, 11), range=(0, 10))
    hist = hist.astype('float')
    hist /= (hist.sum() + 1e-6)  # 進行規範化處理

    # 基於 LBP 特徵直方圖來推測材質（此處簡單模擬）
    material = classify_material(hist)
    return material

def classify_material(hist: np.ndarray) -> str:
    """
    根據 LBP 直方圖來分類材質
    :param hist: LBP 直方圖
    :return: 材質名稱
    """
    # 假設這裡有一個簡單的判斷邏輯來分類材質
    # 這部分可以替換為更精確的分類器（如 SVM，決策樹等）
    if np.argmax(hist) == 0:
        return "Cotton"
    elif np.argmax(hist) == 1:
        return "Silk"
    elif np.argmax(hist) == 2:
        return "Wool"
    else:
        return "Polyester"