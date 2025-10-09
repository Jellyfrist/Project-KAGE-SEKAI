import re
import json
from collections import Counter
from typing import List, Dict, Any
from schemas.review_schema import review_schema

class ReviewTools:
    def analyze_review(self, product_name: str, review_texts: List[str], aspects: list[str] = None):
        """
        Analyze review and return a JSON structure matching `review_schema`.
        """

        # default aspects if not provided
        if not aspects:
            aspects = ["คุณภาพ", "ราคา", "บริการ", "การจัดส่ง", "บรรจุภัณฑ์"]

        # excemplary simple sentiment analysis logic
        positive_words = ["ดี", "ชอบ", "ไว", "แน่น", "หอม", "สวย", "ปัง", "จึ้ง", "ประทับใจ"]
        negative_words = ["แพง", "ช้า", "ไม่", "พัง", "แห้ง", "เลอะ", "หนัก", "โป๊ะ", "ตำหนิ", "ติ"]

        all_aspects_results = []
        strengths_set = set()
        weaknesses_set = set()
        positive_count = 0
        negative_count = 0

        for rv in review_texts:
            review_aspects = []

            for asp in aspects:
                asp_sentiment = "neutral"
                reasons = []

                # Simple keyword-based sentiment detection
            
                # check for positive words
                for word in positive_words:
                    if word in rv:
                        asp_sentiment = "positive"
                        reason = f"พบคำเชิงบวก '{word}' เกี่ยวกับ {asp}"
                        positive_count += 1
                        strengths_set.add(f"{asp}: {word}")
                        break
        
                # only check for negative if not already positive
                if asp_sentiment != "positive":
                    for word in negative_words:
                        if word in rv:
                            asp_sentiment = "negative"
                            reason = f"พบคำเชิงลบ '{word}' เกี่ยวกับ {asp}"
                            negative_count += 1
                            weaknesses_set.add(f"{asp}: {word}")
                            break

                # collect review aspect results
                review_aspects.append({
                    "aspect_name": asp,
                    "sentiment": asp_sentiment,
                    "reason": reason if reason else "ไม่มีคำเชิงบวกหรือลบที่ชัดเจน"
                })

            all_aspects_results.extend(review_aspects)

        # determine overall sentiment
        if positive_count > negative_count:
            overall_sentiment = "positive"
        elif negative_count > positive_count:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"

        # reasoning based on counts
        reasoning = f"วิเคราะห์จาก {len(review_texts)} รีวิว: มีคำเชิงบวก {positive_count} ครั้ง, คำเชิงลบ {negative_count} ครั้ง"

        # create final result following schema
        result = {
            "product_name": product_name,
            "review_texts": review_texts,   # list of reviews
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
        """
        Return the function schemas for all tools in this class.
        """
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
                    }
                },
                "required": ["product_name", "review_texts"],
            }
        }]
