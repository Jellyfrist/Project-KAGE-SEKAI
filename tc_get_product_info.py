import json
import os
from typing import Dict, List, Any
from schemas.product_schema import product_schema

# Simulated product database
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE_DIR = os.getcwd() 
JSON_FILE_PATH = os.path.join(BASE_DIR, 'products.json')

def load_product_db_from_json(file_path: str) -> Dict[str, Any]:
    """Loads product data from a JSON file and structures it with 'id' as the key."""
    try:
        if not os.path.exists(file_path):
            print(f"ERROR: The file '{file_path}' was not found.")
            raise FileNotFoundError(f"File not found at: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            # download data that is List of Dictionary
            product_list: List[Dict[str, Any]] = json.load(f)
    
        # Create a dictionary with product_id as key for easy lookup
        product_db = {
            product['id']: product 
            for product in product_list if product.get('id') 
        }
        return product_db

    except FileNotFoundError:
        print(f"ERROR: The file '{file_path}' was not found. Check your file path.")
        return {}
    except json.JSONDecodeError:
        print(f"ERROR: Could not decode JSON from '{file_path}'. Check file format.")
        return {}

PRODUCT_DB = load_product_db_from_json(JSON_FILE_PATH)

class ProductTools:
    """Tool class for product-related operations."""

    def get_product_info(self, product_id: str) -> dict:
        # Simulate fetching data from a database
        product_raw = PRODUCT_DB.get(product_id)

        # Handle case where product ID is not found
        if not product_id or not product_raw:
            return {"error": f"Product ID '{product_id}' not found."}

        # 1. Price Range
        # change string "299–349 บาท" to min_price and max_price
        price_str = product_raw.get("price", "0–0 บาท").replace(" บาท", "")
        if "–" in price_str:
            min_price_str, max_price_str = price_str.split("–")
            min_price = int(min_price_str.strip())
            max_price = int(max_price_str.strip())
        else:
            min_price = max_price = int(price_str.strip())

        # 2. Counting Shades (main_colors + new_colors)
        shades = product_raw.get("shades", {})
        num_main = len(shades.get("main_colors", []))
        num_new = len(shades.get("new_colors", []))
        number_of_shades = num_main + num_new
        # if have other keys example 'blend' -> do not count

        # features, pros, cons, warnings
        features = product_raw.get("key_features", [])
        pros = product_raw.get("advantages", [])
        cons = product_raw.get("disadvantages", [])
        warnings = product_raw.get("cautions", [])

        # Construct the response based on the schema
        product_info = {
            "product_id": product_raw["id"],
            "product_name": product_raw["name_th"],
            "category": product_raw["type"],
            "features": features, 
            "pros": pros,
            "cons": cons,
            "warnings": warnings,
            "number_of_shades": number_of_shades,
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
            "description": "Fetch detailed product information using the product ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": product_schema["schema"]["properties"]["product_id"]
                },
                "required": ["product_id"]
            }
        }]
