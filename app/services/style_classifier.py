# app/services/style_classifier.py
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models, transforms
from torchvision.models import ResNet18_Weights
from PIL import Image
import os

# 定義一個簡單的 CNN 模型進行風格分類（這裡使用預訓練的 ResNet18 作為例子）
class StyleClassifier(nn.Module):
    def __init__(self, num_classes: int):
        super(StyleClassifier, self).__init__()
        self.resnet18 = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        self.resnet18.fc = nn.Linear(self.resnet18.fc.in_features, num_classes)

    def forward(self, x):
        return self.resnet18(x)

# 用預訓練的 ResNet18 做風格分類
def analyze_style(image_path: str) -> str:
    model_path = os.path.join(os.path.dirname(__file__), '../style_classifier.pth')
    model_path = os.path.abspath(model_path)
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"模型文件未找到: {model_path}")

    model = torch.load(model_path)  # 這會加載整個模型（包括結構和權重）
    model.eval()  # 設定為評估模式

    # 預處理圖片
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    img = Image.open(image_path)
    img = transform(img).unsqueeze(0)  # 增加 batch 维度

    # 預測
    with torch.no_grad():
        output = model(img)
        _, predicted = torch.max(output, 1)

    # 返回分類結果
    style_labels = ["Casual", "Formal", "Street", "Sporty"]
    if predicted.item() >= len(style_labels):
        raise ValueError(f"無法對應風格類別: index {predicted.item()}")
    return style_labels[predicted.item()]
