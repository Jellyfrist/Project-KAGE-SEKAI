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
                        "description": "Summarized weaknesses mentioned in the review.",
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

'''
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

try:
    if hasattr(resp, "choices") and resp.choices and hasattr(resp.choices[0], "message") and "content" in resp.choices[0].message:
        content = resp.choices[0].message["content"]
        import logging
        logging.basicConfig(level=logging.INFO)
        logging.info("RAW JSON:\n%s", content)
        try:
            parsed = json.loads(content)
            logging.info("Parsed:\n%s", json.dumps(parsed, indent=2))
        except Exception as parse_err:
            logging.error("Error parsing JSON content: %s", parse_err)
    else:
        import logging
        logging.basicConfig(level=logging.ERROR)
        logging.error("Error: Response does not contain expected content.")
except Exception as e:
    import logging
    logging.basicConfig(level=logging.ERROR)
    logging.error("Error parsing response: %s", e)
        print("\nParsed:\n", json.dumps(json.loads(content), indent=2))
    else:
        print("Error: Response does not contain expected content.")
except Exception as e:
    print(f"Error parsing response: {e}")
'''
