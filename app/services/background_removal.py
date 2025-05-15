# app/services/background_removal.py
import numpy as np
from sklearn.cluster import KMeans

def auto_detect_background_color(img, k=3):
    """用 KMeans 找圖片最常出現的主色（背景）"""
    pixels = img.reshape(-1, 3)
    kmeans = KMeans(n_clusters=k, n_init='auto')
    kmeans.fit(pixels)
    counts = np.bincount(kmeans.labels_)
    dominant = kmeans.cluster_centers_[np.argmax(counts)].astype(int)
    return dominant


from rembg import remove
from PIL import Image
import io

def remove_background_rembg(image_path: str, save_path: str = None) -> str:
    with open(image_path, "rb") as f:
        input_bytes = f.read()

    output_bytes = remove(input_bytes)
    output_image = Image.open(io.BytesIO(output_bytes))

    output_path = save_path or image_path.replace(".jpg", "_rembg.png").replace(".png", "_rembg.png")
    output_image.save(output_path)

    return output_path