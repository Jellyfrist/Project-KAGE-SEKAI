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

# --------------------------
# TOOL IMPLEMENTATION
# --------------------------
def get_product_info(product_id: str) -> dict:
    """
    Fetch detailed information about a cosmetic product based on its unique product ID.

    Args:
        product_id (str): The unique identifier for the cosmetic product.

    Returns:
        dict: A dictionary containing detailed product information conforming to the ProductInfo schema.
    """
    # Simulate fetching data from a database
    product = PRODUCT_DB.get(product_id)
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

# --------------------------
# TOOL DEFINITION (Schema)
# --------------------------
product_tool = [{
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

TOOL_IMPL = {"get_product_info": get_product_info}


# --------------------------
# MAIN EXECUTION LOOP
# --------------------------
if __name__ == "__main__":
    messages = [{"role": "user", "content": "แสดงข้อมูลสินค้ารหัส C001"}]

    logging.info("=== STEP 1: Initial request ===")
    logging.info(messages[0]["content"])

    first = completion(model=MODEL, messages=messages, functions=product_tool, function_call="auto")
    msg = first.choices[0].message
    fc = getattr(msg, "function_call", None) if hasattr(msg, "function_call") else msg.get("function_call")

    logging.info("\n=== STEP 2: Tool Proposal ===")
    logging.info("Function name: %s", getattr(fc, "name", None) if fc else None)
    logging.info("Arguments: %s", getattr(fc, "arguments", None) if fc else None)

    if fc:
        name = getattr(fc, "name", None)
        args = json.loads(getattr(fc, "arguments", "{}") or "{}")

        if name in TOOL_IMPL:
            result = TOOL_IMPL[name](**args)
            logging.info("\n=== STEP 3: Tool Result ===")
            logging.info(json.dumps(result, indent=2, ensure_ascii=False))

            messages.append({"role": "assistant", "content": None, "function_call": {"name": name, "arguments": getattr(fc, "arguments", "{}")}})
            messages.append({"role": "function", "name": name, "content": json.dumps(result, ensure_ascii=False)})

            final = completion(model=MODEL, messages=messages)
            logging.info("\n=== STEP 4: Final Response ===")
            logging.info(final.choices[0].message["content"])
        else:
            logging.error("Tool not implemented: %s", name)
    else:
        logging.warning("No tool call proposed.")
        logging.info("Assistant said: %s", getattr(msg, "content", None) or msg["content"])
