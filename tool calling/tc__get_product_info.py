import json
import logging
from litellm import completion
from config import MODEL
from schemas.product_schema import product_schema

# enable logging to show all INFO logs
logging.basicConfig(level=logging.INFO, format="%(message)s")

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
        "price_range": {"min_price": 159, "max_price": 249}
    },
    "C001": {
        "product_name": "คุชชั่นกะทิพรีเมียม",
        "category": "คุชชั่น",
        "features": ["เนื้อบางเบา", "ปกปิดดี", "กันน้ำ"],
        "pros": ["ผิวโกลว์", "ติดทนทาน"],
        "cons": ["มีเฉดสีให้เลือกน้อย"],
        "warnings": ["ทดสอบก่อนใช้กับผิวแพ้ง่าย"],
        "number_of_shades": 4,
        "price_range": {"min_price": 299, "max_price": 399}
    }
}
