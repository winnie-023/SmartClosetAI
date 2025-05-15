# app/services/clothing_detector.py
from ultralytics import YOLO
import numpy as np
import cv2
from pathlib import Path
from sklearn.cluster import KMeans
from collections import Counter
import logging
from app.services.fashion_classifier import predict_fashion_class  # 你需有這個模組
from rembg import remove
from PIL import Image
from app.services.two_stage_classifier import two_stage_classification

# 使用更強大的 YOLOv8 模型
model = YOLO('yolov8l.pt')  # 使用 large 版本

# 定義服裝類型映射
CLOTHING_TYPES = {
    'person': '人物',
    'tie': '領帶',
    'handbag': '手提包',
    'backpack': '背包',
    'shoe': '鞋子',
    'hat': '帽子',
    'glasses': '眼鏡',
    'shirt': '上衣',
    't-shirt': 'T恤',
    'pants': '褲子',
    'dress': '連衣裙',
    'skirt': '裙子',
    'jacket': '外套',
    'sweater': '毛衣',
    'coat': '大衣',
    'suit': '西裝',
    'jeans': '牛仔褲',
    'shorts': '短褲',
    'blouse': '襯衫',
    'hoodie': '帽T',
    'vest': '背心',
    'scarf': '圍巾',
    'gloves': '手套',
    'socks': '襪子',
    'underwear': '內衣',
    'swimsuit': '泳衣',
    'uniform': '制服',
    'costume': '戲服',
    'accessories': '配件'
}

# 定義顏色映射
COLOR_NAMES = {
    (255, 0, 0): '紅色',
    (0, 255, 0): '綠色',
    (0, 0, 255): '藍色',
    (255, 255, 0): '黃色',
    (255, 0, 255): '紫色',
    (0, 255, 255): '青色',
    (255, 255, 255): '白色',
    (0, 0, 0): '黑色',
    (128, 128, 128): '灰色',
    (165, 42, 42): '棕色',
    (255, 192, 203): '粉色',
    (255, 165, 0): '橙色',
    (139, 69, 19): '深棕色',
    (128, 0, 128): '深紫色',
    (0, 128, 0): '深綠色',
    (0, 0, 128): '深藍色',
    (128, 128, 0): '橄欖色',
    (255, 215, 0): '金色',
    (192, 192, 192): '銀色',
    (255, 228, 196): '米色'
}

# 定義材質特徵
MATERIAL_FEATURES = {
    'cotton': '棉質',
    'denim': '牛仔',
    'leather': '皮革',
    'wool': '毛呢',
    'silk': '絲綢',
    'linen': '亞麻',
    'polyester': '聚酯纖維',
    'nylon': '尼龍',
    'knit': '針織',
    'fleece': '刷毛',
    'suede': '麂皮',
    'velvet': '天鵝絨',
    'lace': '蕾絲',
    'fur': '毛皮',
    'satin': '緞面',
    'tweed': '粗花呢',
    'corduroy': '燈芯絨',
    'canvas': '帆布',
    'spandex': '彈性纖維',
    'cashmere': '喀什米爾'
}

# 定義服裝風格
STYLE_CATEGORIES = {
    'casual': '休閒',
    'formal': '正式',
    'sporty': '運動',
    'vintage': '復古',
    'modern': '現代',
    'business': '商務',
    'elegant': '優雅',
    'street': '街頭',
    'bohemian': '波希米亞',
    'minimalist': '極簡',
    'classic': '經典',
    'romantic': '浪漫',
    'punk': '龐克',
    'gothic': '哥德',
    'preppy': '學院',
    'hipster': '文青',
    'luxury': '奢華',
    'ethnic': '民族風'
}

def get_dominant_colors(image, k=3):
    """獲取圖像的主要顏色（根據顏色分布決定返回一個或多個顏色）"""
    # 將圖像轉換為RGB格式
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # 重塑圖像為二維數組
    pixels = image.reshape(-1, 3)
    
    # 使用K-means聚類找出主要顏色
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(pixels)
    
    # 獲取主要顏色
    colors = kmeans.cluster_centers_
    counts = Counter(kmeans.labels_)
    
    # 計算總像素數
    total_pixels = sum(counts.values())
    
    # 按頻率排序顏色
    color_freq = [(colors[i], count/total_pixels) for i, count in counts.most_common()]
    
    # 將顏色映射到最接近的預定義顏色
    dominant_colors = []
    for color, freq in color_freq:
        min_dist = float('inf')
        closest_color = None
        for predefined_color, name in COLOR_NAMES.items():
            dist = np.sqrt(np.sum((color - predefined_color) ** 2))
            if dist < min_dist:
                min_dist = dist
                closest_color = name
        if closest_color and closest_color not in dominant_colors:
            # 如果顏色佔比超過30%，或者這是第一個顏色，則添加
            if freq > 0.3 or not dominant_colors:
                dominant_colors.append(closest_color)
            
    return dominant_colors

def analyze_material(image, clothing_type):
    """分析服裝材質"""
    # 使用圖像紋理特徵來估計材質
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    texture = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # 基於服裝類型和紋理特徵判斷材質
    if clothing_type in ['sweater', 'hoodie']:
        return 'knit'
    elif clothing_type in ['jeans', 'denim']:
        return 'denim'
    elif clothing_type in ['shirt', 'blouse']:
        return 'cotton'
    elif clothing_type in ['dress', 'skirt']:
        if texture < 100:
            return 'silk'
        else:
            return 'cotton'
    elif clothing_type in ['jacket', 'coat']:
        if texture > 800:
            return 'leather'
        else:
            return 'wool'
    else:
        # 基於紋理特徵判斷材質
        if texture < 100:
            return 'cotton'
        elif texture < 300:
            return 'linen'
        elif texture < 500:
            return 'denim'
        elif texture < 800:
            return 'wool'
        elif texture < 1200:
            return 'silk'
        else:
            return 'leather'

def analyze_styles(image, clothing_type, colors):
    """分析服裝風格（根據特徵決定返回一個或多個風格）"""
    styles = set()
    
    # 基於服裝類型的風格判斷
    if clothing_type in ['suit', 'tie', 'dress']:
        styles.add('formal')
        styles.add('elegant')
    elif clothing_type in ['hoodie', 'sweater', 'jeans']:
        styles.add('casual')
        styles.add('street')
    elif clothing_type in ['sportswear', 't-shirt']:
        styles.add('sporty')
        styles.add('casual')
    
    # 基於顏色的風格判斷
    for color in colors:
        if color in ['黑色', '白色', '灰色']:
            styles.add('elegant')
            styles.add('minimalist')
        elif color in ['紅色', '黃色', '藍色']:
            styles.add('sporty')
            styles.add('casual')
        elif color in ['粉色', '紫色', '米色']:
            styles.add('romantic')
            styles.add('elegant')
        elif color in ['金色', '銀色']:
            styles.add('luxury')
            styles.add('elegant')
    
    # 如果只有一個風格，直接返回
    if len(styles) == 1:
        return [STYLE_CATEGORIES[list(styles)[0]]]
    
    # 轉換為中文風格名稱
    return [STYLE_CATEGORIES[style] for style in styles]

def analyze_clothing_yolo(image: np.ndarray):
    try:
        h, w = image.shape[:2]
        logging.info(f"原始圖像大小: {w}x{h}")
        results = model(image, conf=0.15, iou=0.45)
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy()
                class_name = result.names[cls]
                logging.info(f"檢測到: {class_name}, 置信度: {conf:.2f}")

                if class_name == "person":
                    x1, y1, x2, y2 = map(int, xyxy)
                    if x2 <= x1 or y2 <= y1:
                        logging.warning(f"無效的裁剪區域: x1={x1}, y1={y1}, x2={x2}, y2={y2}")
                        continue
                    cropped = image[y1:y2, x1:x2]
                    if cropped.size == 0:
                        logging.warning("裁剪區域為空")
                        continue
                    # 先去背
                    pil_image = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
                    no_bg_pil = remove(pil_image)
                    no_bg_np = np.array(no_bg_pil)
                    # 二階段分類
                    main_category, fine_class = two_stage_classification(no_bg_np)
                    logging.info(f"大類: {main_category}, 細分類: {fine_class}")
                    clothing_type = fine_class
                elif class_name in CLOTHING_TYPES:
                    x1, y1, x2, y2 = map(int, xyxy)
                    if x2 <= x1 or y2 <= y1:
                        logging.warning(f"無效的裁剪區域: x1={x1}, y1={y1}, x2={x2}, y2={y2}")
                        continue
                    cropped = image[y1:y2, x1:x2]
                    if cropped.size == 0:
                        logging.warning("裁剪區域為空")
                        continue
                    pil_image = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
                    no_bg_pil = remove(pil_image)
                    no_bg_np = np.array(no_bg_pil)
                    main_category, fine_class = two_stage_classification(no_bg_np)
                    clothing_type = fine_class
                else:
                    logging.info(f"跳過非服裝類別: {class_name}")
                    continue

                # 用去背後的圖片做分析
                colors = get_dominant_colors(no_bg_np)
                material = analyze_material(no_bg_np, clothing_type)
                styles = analyze_styles(no_bg_np, clothing_type, colors)

                detections.append({
                    "type": clothing_type,
                    "category": main_category,
                    "confidence": round(conf, 2),
                    "colors": colors,
                    "material": MATERIAL_FEATURES.get(material, material),
                    "styles": styles,
                    "location": {
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2
                    }
                })
        detections.sort(key=lambda x: x["confidence"], reverse=True)
        if not detections:
            logging.warning("未檢測到任何服裝或飾品")
            return {
                "status": "warning",
                "message": "未能識別到任何服裝或飾品，請確保圖片清晰且包含單件服裝或飾品",
                "detections": []
            }
        logging.info(f"成功檢測到 {len(detections)} 件服裝或飾品")
        return {
            "status": "success",
            "detections": detections
        }
    except Exception as e:
        logging.error(f"服裝檢測錯誤: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }