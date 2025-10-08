import json
from typing import List
from schemas.review_schema import review_schema

class ReviewTools:
    def analyze_review(self, product_name: str, review_text: str, aspects: List[str] = None):
        """
        Analyze review and return a JSON structure matching `review_schema`.
        """

        # default aspects if not provided
        if not aspects:
            aspects = ["คุณภาพ", "ราคา", "บริการ", "การจัดส่ง", "บรรจุภัณฑ์"]

        # excemplary simple sentiment analysis logic
        positive_words = ["ดี", "ชอบ", "ไว", "แน่น", "หอม", "สวย", "ปัง", "จึ้ง", "ประทับใจ"]
        negative_words = ["แพง", "ช้า", "ไม่", "พัง", "แห้ง", "เลอะ", "หนัก", "โป๊ะ", "ตำหนิ", "ติ"]

        aspects_result = []
        positive_score = 0
        negative_score = 0

        for asp in aspects:
            asp_sentiment = "neutral"
            reason = ""
            for word in positive_words:
                if word in review_text:
                    asp_sentiment = "positive"
                    reason = f"พบคำเชิงบวก '{word}'"
                    positive_score += 1
                    break
        
            # only check for negative if not already positive
            if asp_sentiment != "positive":
                for word in negative_words:
                    if word in review_text:
                        asp_sentiment = "negative"
                        reason = f"พบคำเชิงลบ '{word}'"
                        negative_score += 1
                        break
    
            aspects_result.append({
                "aspect_name": asp,
                "sentiment": asp_sentiment,
                "reason": reason
            })

        # strengths and weaknesses
        strengths = [f"มีคำเชิงบวก '{word}'" for word in positive_words if word in review_text]
        weaknesses = [f"มีคำเชิงลบ '{word}'" for word in negative_words if word in review_text]

        # determine overall sentiment
        overall_sentiment = (
            "positive" if positive_score > negative_score
            else "negative" if negative_score > positive_score
            else "neutral"
        )

        result = {
            "product_name": product_name,
            "review_text": review_text,
            "aspects": aspects_result,
            "summary": {
                "overall_sentiment": overall_sentiment,
                "strengths": strengths,
                "weaknesses": weaknesses
            }
        }
        return result

    @classmethod
    def get_schemas(cls):
        """
        Return the function schemas for all tools in this class.
        """
        return [{
            "name": "analyze_review",
            "description": "Analyze customer review into multiple aspects and output sentiment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": review_schema["schema"]["properties"]["product_name"],
                    "review_text": review_schema["schema"]["properties"]["review_text"],
                    "aspects": {
                        "type": "array",
                        "description": "Optional list of aspects to analyze.",
                        "items": {"type": "string"}
                    }
                },
                "required": ["product_name", "review_text"],
            }
        }]
