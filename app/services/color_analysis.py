import cv2
import numpy as np
from sklearn.cluster import KMeans

# 計算圖片主色調的函數
def analyze_dominant_color(image: np.ndarray) -> str:
    """
    輸入一張圖片，返回主色調
    :param image: OpenCV 讀取的圖片（np.ndarray 格式）
    :return: 主色調的顏色名稱
    """
    # 將圖片轉換到 RGB 色彩空間
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # 攤平成一維陣列：每個像素點為一個顏色
    pixels = image_rgb.reshape(-1, 3)

    # 使用 KMeans 來找出圖片中的主要顏色
    kmeans = KMeans(n_clusters=1)
    kmeans.fit(pixels)

    # 得到主色調的 RGB 顏色
    dominant_color_rgb = kmeans.cluster_centers_[0]
    dominant_color_rgb = dominant_color_rgb.round().astype(int)

    # 將 RGB 轉回 HEX 顏色值
    dominant_color_hex = rgb_to_hex(dominant_color_rgb)

    return dominant_color_hex

def rgb_to_hex(rgb: np.ndarray) -> str:
    """
    將 RGB 顏色轉換為 HEX 顏色代碼
    :param rgb: RGB 顏色陣列
    :return: HEX 顏色代碼
    """
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])