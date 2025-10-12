import re
import json
import csv
from collections import Counter
from typing import List, Dict, Any, Optional
from schemas.review_schema import review_schema

# import completion and MODEL for direct LLM analysis
from litellm import completion
from config import MODEL 

# define prompt template for LLM to perform Aspect-Based Sentiment Analysis (ABSA)
LLM_ANALYSIS_PROMPT_TEMPLATE = """
จากรีวิวต่อไปนี้: "{review_text}"
โปรดวิเคราะห์ความรู้สึกสำหรับแต่ละแง่มุมต่อไปนี้: {aspects_list}

กฎการตอบ:
1. สำหรับแต่ละแง่มุมที่ระบุ (คุณภาพ, ราคา, บริการ, การจัดส่ง, บรรจุภัณฑ์) ให้วิเคราะห์ว่ารีวิวนี้ **เกี่ยวข้องกับแง่มุมนั้นหรือไม่** หากไม่เกี่ยวข้องเลยให้ตั้งค่า sentiment เป็น 'neutral'
2. ระบุ Sentiment เป็น ('positive', 'negative', หรือ 'neutral') สำหรับแต่ละแง่มุม
3. **เหตุผล (Reason)** ต้องดึง **ข้อความเต็ม** จากรีวิวที่เป็นส่วนที่เกี่ยวข้องกับแง่มุมนั้นโดยตรง และต้องเป็นประโยคที่แสดงความรู้สึกนั้น
4. หากแง่มุมใดไม่เกี่ยวข้อง ให้ตั้งค่า Reason เป็น "รีวิวนี้ไม่กล่าวถึงแง่มุมนี้โดยตรง"
5. ตอบกลับในรูปแบบ **JSON Array** ของ Object ดังนี้:
[
    {{
    "aspect_name": "คุณภาพ",
    "sentiment": "positive",
    "reason": "เนื้อลิปดีมาก เม็ดสีแน่น" // ต้องดึงข้อความเต็มจากรีวิว
    }},
    // ... for all other aspects
]
"""

class ReviewTools:
    def analyze_review(
        self,
        product_name: str,
        review_texts: Optional[List[str]] = None,
        aspects: Optional[List[str]] = None,
        csv_path: Optional[str] = None
    ):
        """
        Analyze review and return a JSON structure matching `review_schema`.
        Uses LLM for accurate Aspect-Based Sentiment Analysis (ABSA).
        """

        # --- 1. Data Loading  ---
        if csv_path:
            review_texts = []
            try:
                with open(csv_path, newline='', encoding='utf-8-sig') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        # handle potential BOM issue in CSV header
                        review_text = row.get('review') or row.get('\ufeffreview')
                        if review_text:
                            review_texts.append(review_text)
            except FileNotFoundError:
                raise FileNotFoundError(f"ไม่พบไฟล์ที่: {csv_path}")

        if not review_texts:
            raise ValueError("ไม่มีรีวิวให้วิเคราะห์ ต้องใส่ review_texts หรือ csv_path")

        if not aspects:
            aspects = ["คุณภาพ", "ราคา", "บริการ", "การจัดส่ง", "บรรจุภัณฑ์"]

        # --- 2. LLM-based Aspect Sentiment Analysis ---
        all_aspects_results = []
        strengths_set = set()
        weaknesses_set = set()
        positive_count = 0
        negative_count = 0

        aspects_list_str = ", ".join(aspects)

        print(f"กำลังส่ง {len(review_texts)} รีวิวไปยัง LLM เพื่อวิเคราะห์เชิงลึก...")

        for i, rv in enumerate(review_texts):
            # 2.1 prepare the prompt for a single review
            current_prompt = LLM_ANALYSIS_PROMPT_TEMPLATE.format(
                review_text=rv,
                aspects_list=aspects_list_str
            )

            try:
                # 2.2 call LLM to analyze one review
                llm_response = completion(
                    model=MODEL,
                    messages=[{"role": "user", "content": current_prompt}],
                    # use response_format to ensure LLM returns valid JSON
                    response_format={"type": "json_object"} 
                )

                # 2.3 parse and process the LLM's JSON output
                content = llm_response.choices[0].message.content
                single_review_analysis = json.loads(content) 

                # 2.4 aggregate results and update counts/sets
                for aspect_result in single_review_analysis:
                    # basic data structure check
                    if "sentiment" not in aspect_result or "reason" not in aspect_result:
                        continue 

                    all_aspects_results.append(aspect_result)

                    sentiment = aspect_result.get("sentiment")
                    reason = aspect_result.get("reason", "")
                    aspect_name = aspect_result.get("aspect_name")

                    # check for meaningful reason (not just neutral/not mentioned)
                    if sentiment == "positive":
                        positive_count += 1
                        if reason and "ไม่กล่าวถึง" not in reason:
                            # use the full text reason from the review as a strength
                            strengths_set.add(f"{aspect_name}: {reason[:100]}...") 
                    elif sentiment == "negative":
                        negative_count += 1
                        if reason and "ไม่กล่าวถึง" not in reason:
                            # use the full text reason from the review as a weakness
                            weaknesses_set.add(f"{aspect_name}: {reason[:100]}...")
            except Exception as e:
                print(f"❌ Error (Review {i+1}): LLM ไม่สามารถประมวลผลรีวิวได้: {rv[:50]}... Error: {e}")
                # skip problematic review

        # --- 3. Summary Calculation (using LLM analysis results) ---
        if positive_count > negative_count:
            overall_sentiment = "positive"
        elif negative_count > positive_count:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"

        reasoning = f"วิเคราะห์จาก {len(review_texts)} รีวิว (ผ่านการวิเคราะห์เชิงลึกโดย LLM): พบ Sentiment บวก {positive_count} ครั้ง, พบ Sentiment ลบ {negative_count} ครั้ง"

        # create final result following schema
        result = {
            "product_name": product_name,
            "aspects":  all_aspects_results,
            "summary": {
                "overall_sentiment": overall_sentiment,
                "strengths": list(strengths_set),
                "weaknesses": list(weaknesses_set),
                "reasoning": reasoning
            }
        }
        return result

    @classmethod
    def get_schemas(cls):
        return [{
            "name": "analyze_review",
            "description": "Analyze multiple customer reviews into multiple aspects and output sentiment with reasoning.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": review_schema["schema"]["properties"]["product_name"],
                    "review_texts": {
                        "type": "array",
                        "description": "List of raw review texts for this product.",
                        "items": {"type": "string"}
                    },
                    "aspects": {
                        "type": "array",
                        "description": "Optional list of aspects to analyze.",
                        "items": {"type": "string"}
                    },
                    "csv_path": {
                        "type": "string",
                        "description": "Optional CSV file path to read reviews from (header 'review')"
                    }
                },
                "required": ["product_name"],
            }
        }]
