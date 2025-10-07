{
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
        "additionalProperties": false
    },
    "strict": true
}
