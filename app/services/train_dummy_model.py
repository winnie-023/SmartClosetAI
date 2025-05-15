import torch
import torch.nn as nn
from torchvision import models

# 使用 ResNet-18 當作分類器
model = models.resnet18(pretrained=False)
model.fc = nn.Linear(model.fc.in_features, 5)  # 假設有 5 類

# 儲存空的 model 權重（沒訓練過）
torch.save(model.state_dict(), "app/services/fashion_resnet18.pth")
print("Dummy model saved.")
