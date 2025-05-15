from openai import OpenAI
from dotenv import load_dotenv
import os
import logging
from typing import Optional, Dict, Any, List
import openai
from app.core.config import settings
import json
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.error("未設定 OPENAI_API_KEY 環境變數！")
    openai_client = None
else:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

class FashionAdvisor:
    def __init__(self):
        if not openai_client:
            raise ValueError("OpenAI client not initialized. Please check OPENAI_API_KEY.")
        openai.api_key = settings.OPENAI_API_KEY
        
    async def get_work_outfit_advice(self, context: str, wardrobe_items: List[Dict]) -> Dict[str, Any]:
        """Get outfit advice for work scenarios based on user's wardrobe."""
        prompt = f"""作為一個專業的時尚顧問，請根據用戶的衣櫃物品和活動情境，給出合適的穿搭建議。\n\n用戶的衣櫃物品：\n{self._format_wardrobe_items(wardrobe_items)}\n\n活動情境：{context}\n\n請根據以上信息，從用戶的衣櫃中選擇合適的衣服進行搭配，並給出詳細的穿搭建議。\n請以**完全一模一樣的 JSON 格式**回傳，欄位順序、型別都要和下方範例一樣：\n```json\n{{\n  \"outfit\": \"...\",\n  \"items_used\": [\n    \"...\",\n    \"...\"\n  ],\n  \"accessories\": \"...\",\n  \"shoes\": \"...\",\n  \"hairstyle\": \"...\",\n  \"explanation\": \"...\",\n  \"style\": \"...\",\n  \"notes\": \"...\"\n}}\n```\n**items_used 必須是陣列，其他欄位必須是字串，欄位順序不可更動，不可多欄位或少欄位。**"""
        return await self._get_gpt_response(prompt)

    def _format_wardrobe_items(self, wardrobe_items: List[Dict]) -> str:
        """將衣櫃物品格式化為易讀的字符串。"""
        formatted_items = []
        for item in wardrobe_items:
            item_str = f"- {item['category']}"
            if item.get('color'):
                item_str += f"，顏色：{item['color']}"
            if item.get('material'):
                item_str += f"，材質：{item['material']}"
            if item.get('style'):
                item_str += f"，風格：{item['style']}"
            formatted_items.append(item_str)
        return "\n".join(formatted_items)

    async def get_date_outfit_advice(self, activity: str) -> Dict[str, Any]:
        """Get outfit advice for date/social scenarios."""
        prompt = f"""你是一位穿搭風格大師，目標對象是一位28歲女性，個性活潑、喜歡嘗試新風格。\n根據「{activity}」，提供一套具有吸引力又舒適的穿搭建議。\n請以**完全一模一樣的 JSON 格式**回傳，欄位順序、型別都要和下方範例一樣：\n```json\n{{\n  \"outfit\": \"...\",\n  \"items_used\": [\n    \"...\",\n    \"...\"\n  ],\n  \"accessories\": \"...\",\n  \"shoes\": \"...\",\n  \"hairstyle\": \"...\",\n  \"explanation\": \"...\",\n  \"style\": \"...\",\n  \"notes\": \"...\"\n}}\n```\n**items_used 必須是陣列，其他欄位必須是字串，欄位順序不可更動，不可多欄位或少欄位。**"""
        return await self._get_gpt_response(prompt)

    async def get_special_occasion_advice(self, occasion: str) -> Dict[str, Any]:
        """Get outfit advice for special occasions."""
        prompt = f"""你是一位專業形象顧問，請根據「{occasion}」，設計一套穿搭建議。\n目標對象為28歲女性，穿搭需具風格但不過度誇張。\n請以**完全一模一樣的 JSON 格式**回傳，欄位順序、型別都要和下方範例一樣：\n```json\n{{\n  \"outfit\": \"...\",\n  \"items_used\": [\n    \"...\",\n    \"...\"\n  ],\n  \"accessories\": \"...\",\n  \"shoes\":\"...\",\n  \"hairstyle\":\"...\",\n  \"explanation\":\"...\",\n  \"style\":\"...\",\n  \"notes\":\"...\"\n}}\n```\n**items_used 必須是陣列，其他欄位必須是字串，欄位順序不可更動，不可多欄位或少欄位。**"""
        return await self._get_gpt_response(prompt)

    async def get_wardrobe_outfit_advice(self, wardrobe_items: list, activity: str) -> Dict[str, Any]:
        """Get outfit advice based on existing wardrobe items."""
        items_str = "、".join(wardrobe_items)
        prompt = f"""你是一位穿搭整理師，使用者提供了衣櫃中的單品：{items_str}。
請根據「{activity}」，利用現有衣物做出一套實用又好看的穿搭建議。
請以JSON格式回傳，包含以下欄位：
- outfit: 整體穿搭建議
- items_used: 使用的衣物清單
- accessories: 配件建議
- shoes: 鞋子建議
- hairstyle: 髮型建議
- explanation: 整體搭配說明與搭配理由
"""
        return await self._get_gpt_response(prompt)

    async def get_weather_based_advice(self, activity: str, temperature: float, season: str) -> Dict[str, Any]:
        """Get outfit advice based on weather and season."""
        prompt = f"""你是一位智慧穿搭助手，請根據以下資訊提供穿搭建議：\n- 活動情境：{activity}\n- 當天溫度：{temperature}度\n- 所處季節：{season}\n\n目標是幫助28歲女性穿得時尚又舒適。\n請以**完全一模一樣的 JSON 格式**回傳，欄位順序、型別都要和下方範例一樣：\n```json\n{{\n  \"outfit\": \"...\",\n  \"items_used\": [\n    \"...\",\n    \"...\"\n  ],\n  \"accessories\": \"...\",\n  \"shoes\": \"...\",\n  \"hairstyle\": \"...\",\n  \"explanation\": \"...\",\n  \"style\": \"...\",\n  \"notes\": \"...\"\n}}\n```\n**items_used 必須是陣列，其他欄位必須是字串，欄位順序不可更動，不可多欄位或少欄位。**"""
        return await self._get_gpt_response(prompt)

    def try_fix_json(self, raw):
        # 去除 markdown code block
        raw = re.sub(r'```json|```', '', raw).strip()
        # 嘗試只取第一個大括號包住的內容
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            raw = match.group(0)
        # 替換單引號為雙引號
        raw = raw.replace("'", '"')
        # 去除多餘逗號（如結尾逗號）
        raw = re.sub(r',\s*([}\]])', r'\1', raw)
        return raw

    async def _get_gpt_response(self, prompt: str) -> Dict[str, Any]:
        """Helper method to get response from GPT-4."""
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位專業的穿搭顧問。你必須以 JSON 格式回答，格式如下，欄位順序、型別都要和下方範例一模一樣，不可多欄位或少欄位：{\"outfit\":\"...\",\"items_used\":[\"...\",\"...\"],\"accessories\":\"...\",\"shoes\":\"...\",\"hairstyle\":\"...\",\"explanation\":\"...\",\"style\":\"...\",\"notes\":\"...\"}。items_used 必須是陣列，其他欄位必須是字串。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse the response
            advice = response.choices[0].message.content
            logging.info(f"GPT-4 回傳的穿搭建議: {advice}")
            
            try:
                # 嘗試修正常見格式錯誤
                advice_fixed = self.try_fix_json(advice)
                advice_dict = json.loads(advice_fixed)
                return advice_dict
            except json.JSONDecodeError as je:
                logging.error(f"JSON 解析失敗: {je}")
                # 如果解析失敗，直接回傳原始內容
                return {
                    "raw_response": advice
                }
            
        except Exception as e:
            logging.error(f"呼叫 GPT-4 API 時發生錯誤: {e}")
            return {
                "raw_response": None
            }

    def get_advice(self, occasion: str, context: str) -> Dict[str, Any]:
        """
        通用方法：根據場合類型調用適當的建議生成方法。
        """
        if occasion == "工作":
            return self.get_work_outfit_advice(context, wardrobe_items=[])
        elif occasion == "約會":
            return self.get_date_outfit_advice(context)
        elif occasion == "特殊場合":
            return self.get_special_occasion_advice(context)
        elif occasion == "天氣相關":
            return self.get_weather_based_advice(context, temperature=25, season="夏季")
        else:
            raise ValueError(f"無效的場合類型: {occasion}")