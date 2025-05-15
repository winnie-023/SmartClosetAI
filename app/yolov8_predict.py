# app/yolov8_predict.py
from ultralytics import YOLO
from pathlib import Path
import os, uuid, logging, shutil

# 使用預訓練的 YOLOv8 模型
model = YOLO('yolov8n.pt')

def predict_clothing(img_path: str):
    try:
        results = model(img_path)
        classes = results[0].names
        detections = results[0].boxes.cls.cpu().numpy()
        detected = [classes[int(i)] for i in detections]
        return list(set(detected))  # 去重並返回檢測到的物體
    except Exception as e:
        raise RuntimeError(f"模型預測出錯: {e}")