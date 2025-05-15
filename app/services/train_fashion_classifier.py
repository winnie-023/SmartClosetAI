import pandas as pd
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import torch
from torchvision import transforms, models
import torch.nn as nn
import torch.optim as optim
import json

DATASET_PATH = Path("datasets/fashion-product-images")
IMAGE_PATH = DATASET_PATH / "images"
CSV_PATH = DATASET_PATH / "master.csv"

def load_fashion_dataset(limit=None):
    df = pd.read_csv(CSV_PATH)
    df = df.dropna(subset=["subCategory", "baseColour", "season", "usage"])
    df["image_path"] = df["id"].astype(str) + ".jpg"
    df["image_path"] = df["image_path"].apply(lambda x: IMAGE_PATH / x)
    df = df[df["image_path"].apply(lambda x: x.exists())]
    if limit:
        df = df.head(limit)
    records = df[["image_path", "subCategory"]].to_dict(orient="records")
    return records

# 1. 載入資料
samples = load_fashion_dataset(limit=5000)  # 可調整
labels = [r["subCategory"] for r in samples]
label2idx = {label: idx for idx, label in enumerate(sorted(set(labels)))}
idx2label = {idx: label for label, idx in label2idx.items()}

# 2. Dataset
class FashionDataset(Dataset):
    def __init__(self, samples, label2idx, transform=None):
        self.samples = samples
        self.label2idx = label2idx
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path = self.samples[idx]["image_path"]
        label = self.samples[idx]["subCategory"]
        image = Image.open(img_path).convert('RGB')
        if self.transform:
            image = self.transform(image)
        label_idx = self.label2idx[label]
        return image, label_idx

# 3. Transform
train_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# 4. DataLoader
dataset = FashionDataset(samples, label2idx, transform=train_transform)
train_loader = DataLoader(dataset, batch_size=32, shuffle=True)

# 5. Model
num_classes = len(label2idx)
model = models.resnet18(pretrained=True)
model.fc = nn.Linear(model.fc.in_features, num_classes)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=1e-4)

# 6. 訓練
for epoch in range(10):
    model.train()
    running_loss = 0.0
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
    print(f'Epoch {epoch+1} 完成, Loss: {running_loss/len(train_loader):.4f}')

# 7. 儲存模型與標籤對應表
torch.save(model.state_dict(), 'fashion_resnet18.pth')
with open('fashion_label2idx.json', 'w') as f:
    json.dump(label2idx, f)
with open('fashion_idx2label.json', 'w') as f:
    json.dump(idx2label, f)

print("模型與標籤對應表已儲存！")
