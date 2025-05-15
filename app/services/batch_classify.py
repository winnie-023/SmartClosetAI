# app/services/batch_classify.py

import os
import shutil
from pathlib import Path
from PIL import Image
from app.yolov8_predict import predict_clothing  # 你自己已經寫好的分類方法
from app.services.background_removal import remove_background  # 你已經寫好的去背方法

# 設定輸入/輸出路徑
INPUT_DIR = "input_images"
OUTPUT_DIR = "classified"

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def batch_process_images():
    ensure_dir(INPUT_DIR)
    ensure_dir(OUTPUT_DIR)

    for file in os.listdir(INPUT_DIR):
        if not file.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        input_path = os.path.join(INPUT_DIR, file)

        # 1️⃣ 去背
        try:
            img_no_bg = remove_background(input_path)  # 傳回 PIL Image 或 numpy array
        except Exception as e:
            print(f"[去背錯誤] {file}: {e}")
            continue

        # 2️⃣ 分類
        try:
            result = predict_clothing(img_no_bg)  # 回傳應該是分類字串，如 "tshirt"
            label = result.lower()
        except Exception as e:
            print(f"[分類錯誤] {file}: {e}")
            continue

        # 3️⃣ 儲存至對應資料夾
        class_dir = os.path.join(OUTPUT_DIR, label)
        ensure_dir(class_dir)

        save_path = os.path.join(class_dir, Path(file).stem + ".png")
        img_no_bg.save(save_path)
        print(f"✅ 已處理並儲存：{save_path}")

if __name__ == "__main__":
    batch_process_images()