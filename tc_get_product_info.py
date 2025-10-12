import json
import os
from typing import Dict, List, Any
from schemas.product_schema import product_schema

try:
    # BASE_DIR is the directory where this script resides
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # fallback to current working directory if __file__ is not defined
    BASE_DIR = os.getcwd() 

PRODUCT_FILES = [
    'product_B001.json', 'product_C001.json', 'product_C002.json', 
    'product_L001.json', 'product_M001.json'
]

def load_product_db() -> Dict[str, Any]:
    """Dynamically loads product data from multiple individual JSON files."""
    product_db = {}
    print("--- เริ่มโหลดฐานข้อมูลสินค้า ---")
    
    for filename in PRODUCT_FILES:
        # construct full file path
        file_path = os.path.join(BASE_DIR, 'data', filename) 

        try:
            if not os.path.exists(file_path):
                print(f"⚠️ ไม่พบไฟล์สินค้า '{filename}' ที่ตำแหน่ง {file_path} จึงข้ามการโหลด")
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                # data in each file is expected to be a list of product dicts
                product_list: List[Dict[str, Any]] = json.load(f)
                
                # check and save each product in the file
                if product_list and isinstance(product_list, list) and isinstance(product_list[0], dict):
                    product = product_list[0]
                    product_id = product.get('product_id')
                    if product_id:
                        # save the product Dictionary using its ID as key
                        product_db[product_id] = product
                        print(f"✅ โหลดสินค้า ID: {product_id} (ชื่อ: {product.get('name_th', 'ไม่มีชื่อ')}) สำเร็จ")
                else:
                    print(f"⚠️ คำเตือน: ไฟล์ '{filename}' มีรูปแบบไม่ถูกต้อง (ไม่ใช่ List ที่มี Dictionary)")
                    
        except json.JSONDecodeError:
            print(f"❌ ไม่สามารถถอดรหัส JSON จากไฟล์ '{filename}' ได้ กรุณาตรวจสอบรูปแบบไฟล์")
        except Exception as e:
            print(f"❌ ข้อผิดพลาดที่ไม่คาดคิดในการโหลดไฟล์ {filename}: {e}")
            
    print(f"--- ✅ โหลดฐานข้อมูลสินค้าแล้ว รวม {len(product_db)} รายการ ---")
    return product_db

PRODUCT_DB = load_product_db()


class ProductTools:
    """Tool class for product-related operations, enhanced for business strategy."""

    def get_product_info(self, product_id: str) -> dict:
        """
        Fetches detailed product information, calculates strategic metrics, 
        and structures shade data for LLM analysis.
        """
        # access the globally defined PRODUCT_DB variable
        product_raw = PRODUCT_DB.get(product_id)

        # 1. handle case where ID is not found or data is empty
        if not product_id or not product_raw:
            available_ids = list(PRODUCT_DB.keys())
            return {"error": f"ไม่พบรหัสสินค้า '{product_id}' ในฐานข้อมูลรหัสสินค้าที่ใช้งานได้: {available_ids}"}

        # 2. convert data to a Dictionary if it was saved as a List
        if isinstance(product_raw, list):
            if product_raw and isinstance(product_raw[0], list):
                product_raw = product_raw[0][0] if product_raw[0] else {}
            elif product_raw and isinstance(product_raw[0], dict):
                product_raw = product_raw[0]
            else:
                return {"error": f"ข้อมูลสินค้า ID '{product_id}' มีรูปแบบผิดพลาด (list ไม่ถูกต้อง)"}

        # 3. price range calculation
        price_str = product_raw.get("price", "0–0 บาท").replace(" บาท", "")
        min_price, max_price = 0, 0
        if "–" in price_str:
            try:
                min_price_str, max_price_str = price_str.split("–")
                min_price = int(min_price_str.strip())
                max_price = int(max_price_str.strip())
            except ValueError:
                 pass
        else:
            try:
                min_price = max_price = int(price_str.strip())
            except ValueError:
                pass


        # 4. STRATEGIC INSIGHTS: Pricing Flexibility Index
        if max_price > 0 and min_price < max_price:
            price_range_percent = ((max_price - min_price) / max_price) * 100
            pricing_flexibility_index = f"{price_range_percent:.1f}% (ชี้ช่วงราคาสำหรับการทำโปรโมชั่น/ช่องทางจำหน่าย)"
        elif max_price > 0 and min_price == max_price:
            pricing_flexibility_index = "0.0% (กำหนดราคาตายตัว)"
        else:
            pricing_flexibility_index = "N/A"
            
        # 5. STRATEGIC INSIGHTS: Core Value Proposition
        pros = product_raw.get("advantages", [])
        features = product_raw.get("key_features", [])
        cons = product_raw.get("disadvantages", [])
        
        if pros:
            core_value_proposition = pros[0].capitalize() 
        elif features:
            core_value_proposition = features[0].capitalize()
        else:
            core_value_proposition = "ไม่ได้กำหนด"

        # 6. Shade Analysis (Crucial for Cosmetics)
        shades = product_raw.get("shades", {})
        if isinstance(shades, list):
            shades_dict = {"main_colors": shades, "new_colors": []}
            shades = shades_dict
        
        # a. count
        num_main = len(shades.get("main_colors", []))
        num_new = len(shades.get("new_colors", []))
        number_of_shades = num_main + num_new

        # b. group shades by personal colour
        all_shade_details = shades.get("main_colors", []) + shades.get("new_colors", [])
        
        personal_color_coverage = {}
        for detail in all_shade_details:
            pc_raw = detail.get("personal_color", "N/A").split('/')
            for pc in pc_raw:
                pc_clean = pc.strip()
                if pc_clean not in personal_color_coverage:
                    personal_color_coverage[pc_clean] = []
                personal_color_coverage[pc_clean].append(f"{detail.get('color_name')}: {detail.get('description', '')[:20]}...")

        # construct the final strategically-enriched response
        product_info = {
            "product_id": product_raw["product_id"],
            "product_name": product_raw["name_th"],
            "category": product_raw["type"],
            
            # --- STRATEGIC INSIGHTS ---
            "strategic_value_proposition": core_value_proposition,
            "pricing_flexibility_index": pricing_flexibility_index,
            "total_number_of_shades": number_of_shades,
            "personal_color_coverage": personal_color_coverage,
            
            # --- RAW DATA ---
            "key_features": features, 
            "advantages": pros,
            "disadvantages": cons,
            "warnings": product_raw.get("cautions", []),
            "price_range": {
                "min_price": min_price,
                "max_price": max_price,
                "currency": "THB"
            }
        }
        return product_info

    @classmethod
    def get_schemas(cls):
        """Return the product info schema."""
        return [{
            "name": "get_product_info",
            "description": "Fetch detailed product information using the product ID. The output is enriched with **strategic insights (e.g., Core Value Proposition, Pricing Flexibility)** and **detailed Personal Color coverage data** for business decision-making.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": product_schema["schema"]["properties"]["product_id"]
                },
                "required": ["product_id"]
            }
        }]
