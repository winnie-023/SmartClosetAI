from rembg import remove
from PIL import Image
import io
import openai 
import logging
import base64

def process_image(image_path: str, ):
    with open(image_path, "rb") as f:
        input_bytes = f.read()

    output_bytes = remove(input_bytes)
    output_image = Image.open(io.BytesIO(output_bytes)).convert("RGBA")

    # 強制轉成 .png 檔名
    output_path = (
        image_path.rsplit('.', 1)[0] + "_processed.png"
    )
    output_image.save(output_path)  # 會自動用 png 格式儲存

    return {
        "processed_image_path": output_path,
    }

def gpt_classify_image_from_file(image_path: str) -> str:
    """
    使用 GPT API 根據圖片本身進行分類。
    """
    try:
        with open(image_path, "rb") as img_file:
            base64_image = base64.b64encode(img_file.read()).decode("utf-8")

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是專業的服裝分類助手，根據圖片內容判斷衣物種類。"},
                {"role": "user", "content": "請看這張圖片並分類衣物為以下其中一類：上衣、下身、外套、洋裝、鞋子、包包、帽子、襪子、飾品、特殊。"},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"GPT 圖像分類失敗: {e}")
        return "特殊"

def analyze_clothing_type(image_path: str) -> str:
    """
    直接透過 GPT 分析圖片的衣物種類。
    """
    return gpt_classify_image_from_file(image_path)