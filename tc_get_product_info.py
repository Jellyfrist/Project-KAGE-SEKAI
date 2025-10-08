import json
import logging
from litellm import completion
from config import MODEL
from schemas.product_schema import product_schema

# mock database
PRODUCT_DB = {
    "L001": {
        "product_name": "ลิปไก่ทอด",
        "category": "ลิปกลอส",
        "features": ["เม็ดสีแน่น", "กลิ่นหอม", "ไม่ทำให้ปากแห้ง"],
        "pros": ["สีชัด", "ติดทน"],
        "cons": ["แพคเกจซึมง่าย"],
        "warnings": ["ควรเก็บให้ห่างจากแสงแดด"],
        "number_of_shades": 23,
        "price_range": {"min_price": 299, "max_price": 349}
    },
    "C001": {
        "product_name": "คุชชั่นเสกผิว",
        "category": "คุชชั่น",
        "features": ["เนื้อบางเบา", "ปกปิดดี", "กันน้ำ"],
        "pros": ["ผิวโกลว์", "ติดทน"],
        "cons": ["มีเฉดสีให้เลือกน้อย"],
        "warnings": ["ทดสอบก่อนใช้กับผิวแพ้ง่าย"],
        "number_of_shades": 7,
        "price_range": {"min_price": 495, "max_price": 790}
    }
}

class ProductTools:
    """Tool class for product-related operations."""

    def get_product_info(self, product_id: str) -> dict:
        # Simulate fetching data from a database
        product = PRODUCT_DB.get(product_id)

        # Handle case where product ID is not found
        if not product:
            return {"error": f"Product ID '{product_id}' not found."}

        # Construct the response based on the schema
        product_info = {
            "product_id": product_id,
            "product_name": product["product_name"],
            "category": product["category"],
            "features": product["features"],
            "pros": product["pros"],
            "cons": product["cons"],
            "warnings": product["warnings"],
            "number_of_shades": product["number_of_shades"],
            "price_range": {
                "min_price": product["price_range"]["min_price"],
                "max_price": product["price_range"]["max_price"],
                "currency": "THB"
            }
        }
        return product_info

    @classmethod
    def get_schemas(cls):
        """Return the product info schema."""
        return [{
            "name": "get_product_info",
            "description": "Fetch detailed product information using the product ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": product_schema["schema"]["properties"]["product_id"]
                },
                "required": ["product_id"]
            }
        }]
