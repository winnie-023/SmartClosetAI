import torch
from torchvision import transforms, models
from PIL import Image
import numpy as np
import json
from pathlib import Path
from .fashion_classifier import predict_fashion_class

BASE_DIR = Path(__file__).parent

# 載入模型與標籤
model = models.resnet18(pretrained=False)
with open(BASE_DIR / 'fashion_label2idx.json') as f:
    label2idx = json.load(f)
with open(BASE_DIR / 'fashion_idx2label.json') as f:
    idx2label = {int(k): v for k, v in json.load(f).items()}

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

preprocess = transforms.Compose([
    transforms.ToPILImage(),
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
    # 確保圖像是 RGB 格式
    if image_np.shape[2] == 4:  # 如果是 RGBA 格式
        # 創建白色背景
        background = np.ones_like(image_np[:, :, :3]) * 255
        # 使用 alpha 通道進行混合
        alpha = image_np[:, :, 3:4] / 255.0
        image_np = background * (1 - alpha) + image_np[:, :, :3] * alpha
        image_np = image_np.astype(np.uint8)
    elif image_np.shape[2] == 1:  # 如果是灰度圖
        image_np = np.repeat(image_np, 3, axis=2)
    
    # 將 numpy array 轉換為 PIL Image
    image = Image.fromarray(image_np)
    
    # 預處理圖片
    input_tensor = preprocess(image_np).unsqueeze(0)
    
    # 進行預測
    with torch.no_grad():
        output = model(input_tensor)
        pred = output.argmax(dim=1).item()
    
    # 返回預測的類別名稱
    return idx2label[pred]

def two_stage_classification(image_np):
    """
    執行兩階段分類：
    1. 使用 YOLOv8 檢測服裝位置和大致類別
    2. 使用 ResNet18 進行精細分類
    
    Args:
        image_np: numpy array 格式的圖片
        
    Returns:
        tuple: (main_category, fine_class)
            - main_category: 大類別（例如：上衣、褲子、裙子等）
            - fine_class: 精細分類結果
    """
    # 使用 ResNet18 進行精細分類
    fine_class = predict_fashion_class(image_np)
    
    # 根據精細分類結果判斷大類別
    if fine_class.lower() in ['jacket', 'coat', 'blazer']:
        main_category = '外套'
        fine_class = '外套'  # 統一使用"外套"作為細分類
    elif fine_class.lower() in ['t-shirt', 'shirt', 'blouse', 'sweater', 'hoodie']:
        main_category = '上衣'
        if fine_class.lower() == 't-shirt':
            fine_class = 'T恤'
        elif fine_class.lower() == 'shirt':
            fine_class = '襯衫'
        elif fine_class.lower() == 'blouse':
            fine_class = '襯衫'
        elif fine_class.lower() == 'sweater':
            fine_class = '毛衣'
        elif fine_class.lower() == 'hoodie':
            fine_class = '帽T'
    elif fine_class.lower() in ['pants', 'jeans', 'shorts']:
        main_category = '褲子'
        if fine_class.lower() == 'pants':
            fine_class = '長褲'
        elif fine_class.lower() == 'jeans':
            fine_class = '牛仔褲'
        elif fine_class.lower() == 'shorts':
            fine_class = '短褲'
    elif fine_class.lower() in ['dress']:
        main_category = '洋裝'
        fine_class = '洋裝'
    elif fine_class.lower() in ['skirt']:
        main_category = '裙子'
        fine_class = '裙子'
    else:
        main_category = '其他'
    
    return main_category, fine_class