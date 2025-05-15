import os
from pycocotools.coco import COCO

def coco_to_yolo(coco_annotation_file, image_dir, label_dir):
    # 載入 COCO 資料
    coco = COCO(coco_annotation_file)

    # 獲取所有圖像的 ID
    img_ids = coco.getImgIds()

    # 檢查標註資料夾是否存在，若不存在則創建
    os.makedirs(label_dir, exist_ok=True)

    for img_id in img_ids:
        img_info = coco.loadImgs(img_id)[0]
        img_filename = img_info['file_name']
        image_path = os.path.join(image_dir, img_filename)

        # 讀取圖像的標註
        annotations = coco.loadAnns(coco.getAnnIds(imgIds=img_id))

        # 準備 YOLO 標註內容
        yolo_annotations = []
        for ann in annotations:
            class_id = ann['category_id'] - 1  # YOLO 的類別從 0 開始
            bbox = ann['bbox']  # [x, y, width, height]

            # 將 bbox 轉換為 YOLO 格式 (中心點, 寬度, 高度) [0, 1] 范圍
            x_center = (bbox[0] + bbox[2] / 2) / img_info['width']
            y_center = (bbox[1] + bbox[3] / 2) / img_info['height']
            width = bbox[2] / img_info['width']
            height = bbox[3] / img_info['height']

            yolo_annotations.append(f"{class_id} {x_center} {y_center} {width} {height}")

        # 如果該圖像有標註，則保存 YOLO 格式的標註檔
        if yolo_annotations:
            label_filename = os.path.splitext(img_filename)[0] + '.txt'
            label_path = os.path.join(label_dir, label_filename)
            with open(label_path, 'w') as f:
                f.write("\n".join(yolo_annotations))

    print(f"COCO to YOLO conversion completed. Labels are saved in {label_dir}")