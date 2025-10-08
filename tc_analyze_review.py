import json
import logging
from litellm import completion
from config import MODEL
from schemas.review_schema import review_schema

# enable logging to show all INFO logs
logging.basicConfig(level=logging.INFO, format="%(message)s")

# define the TOOL INPUT SCHEMA based on review_schema but only requiring product_id, product_name, review_text
review_input_schema = {
    "type": "object",
    "properties": {
        "product_id": review_schema["schema"]["properties"]["product_id"],
        "product_name": review_schema["schema"]["properties"]["product_name"],
        "review_text": review_schema["schema"]["properties"]["review_text"],
        # aspects is optional in your function, but often helpful to include
        "aspects": {
             "type": "array",
             "description": "Optional list of aspects to analyze (e.g., 'คุณภาพ', 'ราคา').",
             "items": {"type": "string"}
        }
    },
    "required": ["product_id", "product_name", "review_text"], # The LLM must provide these
    "additionalProperties": False 
}

# --------------------------
# TOOL IMPLEMENTATION
# --------------------------
def analyze_review(product_id: str, product_name: str, review_text: str, aspects: list[str] = None):
    """
    Analyze review and return a JSON structure matching `review_schema`.
    """
    # default aspects if not provided
    if not aspects:
        aspects = ["คุณภาพ", "ราคา", "บริการ", "การจัดส่ง", "บรรจุภัณฑ์"]

    # excemplary simple sentiment analysis logic
    positive_words = ["ดี", "ชอบ", "ไว", "แน่น", "หอม", "สวย", "ปัง", "จึ้ง"]
    negative_words = ["แพง", "ช้า", "ไม่", "พัง", "แห้ง", "เลอะ", "หนัก", "โป๊ะ", "ตำหนิ", "ติ"]

    aspects_result = []
    strengths, weaknesses = [], []
    positive_score = 0
    negative_score = 0

    # analyze each aspect
    for asp in aspects:
        asp_sentiment = "neutral"
        reason = ""
        # simple keyword-based sentiment detection
        for word in positive_words:
            if word in review_text:
                asp_sentiment = "positive"
                reason = f"พบคำเชิงบวก '{word}' เกี่ยวกับ {asp}"
                positive_score += 1
                break
        for word in negative_words:
            if word in review_text:
                asp_sentiment = "negative"
                reason = f"พบคำเชิงลบ '{word}' เกี่ยวกับ {asp}"
                negative_score += 1
                break
 
        aspects_result.append({
            "aspect_name": asp,
            "sentiment": asp_sentiment,
            "reason": reason
        })

    # determine overall sentiment
    overall_sentiment = (
        "positive" if positive_score > negative_score
        else "negative" if negative_score > positive_score
        else "neutral"
    )

    result = {
        "product_id": product_id,
        "product_name": product_name,
        "review_text": review_text,
        "aspects": aspects_result,
        "summary": {
            "overall_sentiment": overall_sentiment,
            "strengths": strengths,
            "weaknesses": weaknesses
        }
    }
    return result


# --------------------------
# TOOL DEFINITION (Schema)
# --------------------------
review_tool = [{
    "name": "analyze_review",
    "description": "Analyze customer review into multiple aspects and output sentiment following MultiAspectReview schema.",
    "parameters": review_input_schema
}]

TOOL_IMPL = {"analyze_review": analyze_review}

# --------------------------
# MAIN EXECUTION LOOP
# --------------------------
if __name__ == "__main__":
    messages = [
        {"role": "user", "content": """
        รีวิว: คุชชันจัดส่งมาไวเลยค่ะ ประทับใจมาก พึ่งลองแบรนด์นี้ครั้งแรก แบรนด์ไทยคุณภาพจริงๆค่ะ หมดแล้วมีซ้ำแน่นอน 
        แก้ไขเพิ่มเติม เราว่าตัวนี้ดรอปนะคะ ลองทิ้งไว้1ชมจากตอนแรกที่ลงจะผ่องสวยเลยจะกลายเป็นพอดีผิวค่ะ 
        ใครอยากได้ผิวไบร์ทผ่องทั้งวันลองกดเบอร์สูงกว่าผิวดูนะคะ ขอตินิดหน่อยตรงที่ตัวตลับจะมีตำหนิเป็นรอยสีเปื้อน(เช็ดไม่ออก) 
        ข้างในตลับตรงที่วางพัพมีขนขุยๆดำๆกับเส้นอะไรสักอย่างเล็กๆติดอยู่ทั้งๆที่พึ่งแกะเปิดใหม่ แต่อันนี้เช็ดออกไปแล้วค่ะ อยากให้ดูเรื่องนี้เพิ่มนิดนึงนะคะ รวมๆโอเคเลยค่ะ
        """
        }
    ]

    logging.info("=== STEP 1: Initial request ===")
    logging.info(messages[0]["content"])

    # send initial user message to LLM with tool options
    first = completion(
        model=MODEL,
        messages=messages,
        functions=review_tool,
        function_call="auto"
    )

    # parse LLM response to see if a tool is requested
    msg = first.choices[0].message
    fc = getattr(msg, "function_call", None) if hasattr(msg, "function_call") else msg.get("function_call")

    # Log intermediate tool proposal
    logging.info("\n=== Step 2: INTERMEDIATE (Tool Proposal) ===")
    logging.info("Function name: %s", getattr(fc, "name", None) if fc else None)
    logging.info("Arguments (raw): %s", getattr(fc, "arguments", None) if fc else None)

    if fc:
        name = getattr(fc, "name", None)
        args = json.loads(getattr(fc, "arguments", "{}") or "{}")

        if name in TOOL_IMPL:
            tool_result = TOOL_IMPL[name](**args)
            logging.info("\n=== Step 3: TOOL EXECUTED RESULT ===")
            logging.info(json.dumps(tool_result, indent=2, ensure_ascii=False))

            # send tool result back to LLM for final response
            messages.append({
                "role": "assistant",
                "content": None,
                "function_call": {"name": name, "arguments": getattr(fc, "arguments", "{}")}
            })
            messages.append({
                "role": "function",
                "name": name,
                "content": json.dumps(tool_result, ensure_ascii=False)
            })

            # final LLM response
            final = completion(model=MODEL, messages=messages)
            logging.info("\n=== Step 4: FINALL LLM RESPOND ===")
            logging.info(final.choices[0].message["content"])
        else:
            logging.error("Tool not implemented: %s", name)
    else:
        logging.warning("No tool call proposed.")
        logging.info("Assistant said: %s", getattr(msg, "content", None) or msg["content"])
