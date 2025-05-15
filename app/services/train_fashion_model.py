import pandas as pd
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import torch
from torchvision import transforms, models
import torch.nn as nn
import torch.optim as optim
import json
import os
import numpy as np
from sklearn.model_selection import train_test_split
import logging

# 設定路徑
DATASET_PATH = Path("../../datasets/fashion-product-images")
IMAGE_PATH = DATASET_PATH / "images"
CSV_PATH = DATASET_PATH / "styles.csv"

# 定義類別對應
CATEGORY_MAPPING = {
    "Topwear": "T-shirt",  # 將所有上衣歸類為 T-shirt
    "Dress": "Dress",      # 保持不變
    "Bottomwear": "Pants", # 將所有下裝歸類為 Pants
    "Jacket": "Jacket",    # 添加外套類別
}

# 設定每個類別的最小樣本數
MIN_SAMPLES_PER_CATEGORY = 2000

TARGET_CATEGORIES = list(CATEGORY_MAPPING.values())

def load_fashion_dataset(limit=None):
    print(f"正在讀取數據集：{CSV_PATH}")
    print(f"圖片目錄：{IMAGE_PATH}")
    
    # 檢查文件是否存在
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"找不到數據集文件：{CSV_PATH}")
    if not IMAGE_PATH.exists():
        raise FileNotFoundError(f"找不到圖片目錄：{IMAGE_PATH}")
    
    # 使用更寬鬆的 CSV 解析設定
    df = pd.read_csv(CSV_PATH, on_bad_lines='skip', encoding='utf-8')
    print(f"成功讀取數據集，共有 {len(df)} 條記錄")
    
    # 只保留目標類別
    df = df[df['subCategory'].isin(CATEGORY_MAPPING.keys())]
    df = df.dropna(subset=["subCategory"])
    print(f"過濾後剩餘 {len(df)} 條記錄")
    
    # 映射類別
    df['subCategory'] = df['subCategory'].map(CATEGORY_MAPPING)
    
    # 處理圖片路徑
    df["image_path"] = df["id"].astype(str) + ".jpg"
    df["image_path"] = df["image_path"].apply(lambda x: IMAGE_PATH / x)
    df = df[df["image_path"].apply(lambda x: x.exists())]
    print(f"找到 {len(df)} 張有效圖片")
    
    # 確保每個類別至少有 MIN_SAMPLES_PER_CATEGORY 個樣本
    balanced_samples = []
    for category in TARGET_CATEGORIES:
        category_samples = df[df['subCategory'] == category]
        print(f"類別 {category} 有 {len(category_samples)} 個樣本")
        
        if len(category_samples) == 0:
            print(f"警告：類別 {category} 沒有樣本！")
            continue
            
        if len(category_samples) < MIN_SAMPLES_PER_CATEGORY:
            # 如果樣本不足，進行重複採樣
            category_samples = category_samples.sample(n=MIN_SAMPLES_PER_CATEGORY, replace=True, random_state=42)
        else:
            # 如果樣本充足，隨機選擇
            category_samples = category_samples.sample(n=MIN_SAMPLES_PER_CATEGORY, random_state=42)
        balanced_samples.append(category_samples)
    
    if not balanced_samples:
        raise ValueError("沒有找到任何有效的樣本！")
        
    df = pd.concat(balanced_samples)
    
    if limit:
        df = df.sample(n=min(limit, len(df)), random_state=42)
    
    print("\n最終類別分布：")
    print(df['subCategory'].value_counts())
    print()
    
    records = df[["image_path", "subCategory"]].to_dict(orient="records")
    return records

class FashionDataset(Dataset):
    def __init__(self, records, transform=None):
        self.records = records
        self.transform = transform
        self.label2idx = {label: idx for idx, label in enumerate(TARGET_CATEGORIES)}
        self.idx2label = {idx: label for label, idx in self.label2idx.items()}
        
    def __len__(self):
        return len(self.records)
    
    def __getitem__(self, idx):
        record = self.records[idx]
        image = Image.open(record["image_path"]).convert("RGB")
        label = self.label2idx[record["subCategory"]]
        
        if self.transform:
            image = self.transform(image)
            
        return image, label

def main():
    # 1. 載入資料
    print("載入資料中...")
    samples = load_fashion_dataset()  # 使用所有可用的圖片
    print(f"找到 {len(samples)} 張圖片")
    
    if len(samples) == 0:
        print("錯誤：沒有找到任何符合條件的圖片！")
        return
    
    # 2. 準備標籤對應
    label2idx = {label: idx for idx, label in enumerate(TARGET_CATEGORIES)}
    idx2label = {idx: label for label, idx in label2idx.items()}
    
    # 保存標籤對應
    with open("fashion_label2idx.json", "w") as f:
        json.dump(label2idx, f)
    with open("fashion_idx2label.json", "w") as f:
        json.dump(idx2label, f)
    
    # 3. 分割訓練集和驗證集
    train_samples, val_samples = train_test_split(samples, test_size=0.2, random_state=42)
    
    # 4. 定義數據轉換
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
        transforms.RandomPerspective(distortion_scale=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    # 5. 創建數據集
    train_dataset = FashionDataset(train_samples, transform=train_transform)
    val_dataset = FashionDataset(val_samples, transform=val_transform)
    
    # 6. 創建數據加載器
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=4)
    
    # 7. 創建模型
    model = models.resnet50(pretrained=True)  # 使用更強大的 ResNet50
    model.fc = torch.nn.Linear(model.fc.in_features, len(TARGET_CATEGORIES))
    
    # 8. 設定訓練參數
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    criterion = torch.nn.CrossEntropyLoss()
    
    # 使用更複雜的學習率策略
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(
        optimizer,
        max_lr=0.001,
        epochs=50,
        steps_per_epoch=len(train_loader),
        pct_start=0.3,
        anneal_strategy='cos'
    )
    
    # 9. 訓練模型
    num_epochs = 50  # 增加訓練輪數
    best_val_loss = float('inf')
    best_val_acc = 0.0
    
    for epoch in range(num_epochs):
        # 訓練階段
        model.train()
        train_loss = 0
        train_correct = 0
        train_total = 0
        
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            scheduler.step()
            
            train_loss += loss.item()
            _, predicted = outputs.max(1)
            train_total += labels.size(0)
            train_correct += predicted.eq(labels).sum().item()
        
        train_loss = train_loss / len(train_loader)
        train_acc = 100. * train_correct / train_total
        
        # 驗證階段
        model.eval()
        val_loss = 0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item()
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()
        
        val_loss = val_loss / len(val_loader)
        val_acc = 100. * val_correct / val_total
        
        # 保存最佳模型（基於驗證準確率）
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), "fashion_resnet50.pth")
            print(f"保存新的最佳模型！驗證準確率: {val_acc:.2f}%")
        
        print(f"Epoch [{epoch+1}/{num_epochs}]")
        print(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
        print(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        print(f"Learning Rate: {scheduler.get_last_lr()[0]:.6f}")
        print()
    
    print("訓練完成！")
    print(f"最佳驗證準確率: {best_val_acc:.2f}%")

if __name__ == "__main__":
    main() 