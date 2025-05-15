import torch
from torchvision import transforms, models
from PIL import Image
import numpy as np
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent

# 載入模型與標籤
model = models.resnet18(pretrained=False)
with open(BASE_DIR / 'fashion_label2idx.json') as f:
    label2idx = json.load(f)
with open(BASE_DIR / 'fashion_idx2label.json') as f:
    idx2label = json.load(f)

# 確保模型輸出層的類別數與標籤數量匹配
num_classes = len(label2idx)
model.fc = torch.nn.Linear(model.fc.in_features, num_classes)

try:
    # 嘗試加載模型權重
    state_dict = torch.load(BASE_DIR / 'fashion_resnet18.pth', map_location='cpu')
    # 檢查權重是否匹配
    if state_dict['fc.weight'].shape[0] != num_classes:
        print(f"警告：保存的模型有 {state_dict['fc.weight'].shape[0]} 個類別，但標籤文件有 {num_classes} 個類別")
        # 如果類別數不匹配，使用預訓練模型
        model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
    else:
        model.load_state_dict(state_dict)
except Exception as e:
    print(f"加載模型時出錯：{e}")
    # 如果加載失敗，使用預訓練模型
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    model.fc = torch.nn.Linear(model.fc.in_features, num_classes)

model.eval()

# 預處理轉換
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def predict_fashion_class(image_np):
    """
    預測圖片中的服裝類別
    
    Args:
        image_np: numpy array 格式的圖片，shape 為 (H, W, C)
        
    Returns:
        預測的類別名稱
    """
    # 將 numpy array 轉換為 PIL Image
    image = Image.fromarray(image_np)
    
    # 預處理圖片
    input_tensor = preprocess(image).unsqueeze(0)
    
    # 進行預測
    with torch.no_grad():
        output = model(input_tensor)
        pred = output.argmax(dim=1).item()
    
    # 返回預測的類別名稱
    return idx2label[str(pred)] 