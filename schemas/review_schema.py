from litellm import completion
from config import MODEL
import json

review_schema = {
    "name": "MultiAspectReview",
    "schema": {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "Reference ID of the product analysed.",
                "example": "C001"
            },
            "product_name": {
                "type": "string",
                "description": "Name of the product mentioned in the review.",
                "example": "ลิปไก่ทอด"
            },
            "review_text": {
                "type": "string",
                "description": "Raw review text written by the user.",
                "example": "เนื้อลิปดีมาก เม็ดสีแน่น ชอบความมีสีให้เลือกเยอะมากก และชอบการรีวิว สวอทสีให้ดูบนปากของนางแบบหลากหลายสีผิว และบนปากคล้ำ ส่วนเนื้อลิปดีมาก เม็ดสีแน่น กลิ่นหอม มีแค่ตัวแพคเกจที่ซึมออกมา ซึ่งจะรอของใหม่น้า ชอบ formula มากๆ อย่าเปลี่ยนนะคะ เปลี่ยนแค่แพคเกจจิ้งพอ เพราะเนื้อลิปดีมากกกกกก"
            },
            "aspects": {
                "type": "array",
                "description": "List of aspects analysed for this review.",
                "items": {
                    "type": "object",
                    "properties": {
                        "aspect_name": {
                            "type": "string",
                            "description": "Aspect being evaluated (e.g., 'คุณภาพ', 'ราคา', 'บริการ').",
                            "example": "คุณภาพ"
                        },
                        "sentiment": {
                            "type": "string",
                            "enum": ["positive", "neutral", "negative"],
                            "description": "Sentiment polarity toward this aspect.",
                            "example": "positive"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Short explanation or extracted text supporting the sentiment.",
                            "example": "ลิปไม่ขุยไม่แห้ง"
                        }
                    },
                    "required": ["aspect_name", "sentiment", "reason"]
                }
            },
            "summary": {
                "type": "object",
                "properties": {
                    "overall_sentiment": {
                        "type": "string",
                        "enum": ["positive", "neutral", "negative"],
                        "description": "Overall sentiment across all aspects.",
                        "example": "positive"
                    },
                    "strengths": {
                        "type": "array",
                        "items": { "type": "string" },
                        "description": "Summarized strengths mentioned in the review.",
                        "example": ["มีสีให้เลือกเยอะ", "เม็ดสีแน่น ", "ปากฉ่ำ"]
                    },
                    "weaknesses": {
                        "type": "array",
                        "items": { "type": "string" },
                        "description": "Summarised weaknesses mentioned in the review.",
                        "example": ["แพคเกจซึมออก", "เหนียว"]
                    }
                },
                "required": ["overall_sentiment"]
            }
        },
        "required": ["product_id", "product_name", "review_text", "aspects"],
        "additionalProperties": False
    },
    "strict": True
}

messages = [
    {"role": "system", "content": "Return ONLY a JSON object matching the MultiAspectReview schema."},
    {"role": "user", "content": """
        product_id: L001,
        product_name: ลิปไก่ทอด,
        review_text: เนื้อลิปดีมาก เม็ดสีแน่น ชอบความมีสีให้เลือกเยอะมากก แต่ขัดใจตรงตัวแพคเกจที่ซึมออกมา แต่จะลองใช้ให้หมดแล้วสั่งอีกรอบน้า,
        กรุณาวิเคราะห์รีวิวนี้ตาม schema ที่กำหนด
        """
    }
]

resp = completion(
    model=MODEL,
    messages=messages,
    response_format={"type": "json_schema", "json_schema": review_schema},
)


content = resp.choices[0].message["content"]

print("RAW JSON:\n", content)
print("\nParsed JSON:\n", json.dumps(json.loads(content), indent=2, ensure_ascii=False))
