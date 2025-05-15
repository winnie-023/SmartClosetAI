# app/services/fashion_dataset_loader.py

import pandas as pd
import os
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import torch
from torchvision import transforms
import torch.nn as nn
import torch.optim as optim
from torchvision import models

DATASET_PATH = Path("datasets/fashion-product-images")
IMAGE_PATH = DATASET_PATH / "images"
CSV_PATH = DATASET_PATH / "master.csv"

def load_fashion_dataset(limit=None):
    df = pd.read_csv(CSV_PATH)

    # 丟掉缺欄位的
    df = df.dropna(subset=["subCategory", "baseColour", "season", "usage"])

    # 篩選圖片存在的樣本
    df["image_path"] = df["id"].astype(str) + ".jpg"
    df["image_path"] = df["image_path"].apply(lambda x: IMAGE_PATH / x)
    df = df[df["image_path"].apply(lambda x: x.exists())]

    if limit:
        df = df.head(limit)

    # 回傳 list of (image_path, label)
    records = df[["image_path", "subCategory", "baseColour", "usage", "season"]].to_dict(orient="records")
    return records

def get_dataloader(batch_size=32, train=True):
    # 回傳 PyTorch DataLoader
    ...

class FashionDataset(Dataset):
    def __init__(self, samples, transform=None):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert('RGB')
        if self.transform:
            image = self.transform(image)
        return image, label

# 載入資料
train_samples = load_fashion_dataset(limit=1000)  # 或不設 limit
# 定義資料增強
train_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])
# 包裝成 Dataset
train_dataset = FashionDataset(train_samples, transform=train_transform)
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

model = models.resnet18(pretrained=True)
model.fc = nn.Linear(model.fc.in_features, num_classes)  # num_classes 根據你的類別數

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=1e-4)

for epoch in range(10):
    model.train()
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
    print(f'Epoch {epoch+1} 完成')
torch.save(model.state_dict(), 'fashion_resnet18.pth')