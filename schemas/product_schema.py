from litellm import completion
from config import MODEL
import json

product_schema = {
    "name": "ProductInfo",
    "schema": {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "Unique product ID",
                "example": "C001"
            },
            "product_name": {
                "type": "string",
                "description": "The name of the cosmetic product.",
                "example": "ลิปไก่ทอด"
            },
            "category": {
                "type": "string",
                "description": "The category of the product.",
                "example": "ลิปกลอส"
            },
            "features": {
                "type": "array",
                "items": { "type": "string" },
                "description": "A list of product claims or highlighted features.",
                "example": ["ให้ความชุ่มชื้น", "กลบสีปาก", "ไม่เหนียวเหนอะหนะ"]
            },
            "pros": {
                "type": "array",
                "items": { "type": "string" },
                "description": "Positive points or advantages of the product.",
                "example": ["บำรุงปาก", "บางเบา ไม่หนักหน้า"]
            },
            "cons": {
                "type": "array",
                "items": { "type": "string" },
                "description": "Negative points or weaknesses of the product.",
                "example": ["ไม่ติดทน", "แพ็คเกจเลอะง่าย"]
            },
            "warnings": {
                "type": "array",
                "items": { "type": "string" },
                "description": "Warnings or precautions about using the product.",
                "example": ["ระวังแพ็คเกจเลอะ", "อาจเกิดการระคายเคืองในบางคน"]
            },
            "number_of_shades": {
                "oneOf": [
                    { "type": "integer" },
                    { "type": "null" }
                ],
                "description": "The number of available colours or shades. Null if not applicable.",
                "example": 9
            },
            "price_range": {
                "type": "object",
                "description": "The minimum and maximum prices of the product, including currency information.",
                "properties": {
                    "currency": {
                        "type": "string",
                        "enum": ["THB", "USD"],
                        "default": "THB",
                        "example": "THB"
                    },
                    "min_price": {
                        "type": "integer",
                        "example": 299
                    },
                    "max_price": {
                        "type": "integer",
                        "example": 349
                    }
                },
                "required": ["min_price", "max_price"]
            }
        },
        "required": [
        "product_id",
        "product_name",
        "category",
        "features",
        "pros",
        "cons",
        "warnings",
        "price_range"
        ],
        "additionalProperties": False
    },
    "strict": True
}
