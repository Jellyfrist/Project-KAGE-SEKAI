import json
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_json(file_path):
    abs_path = os.path.join(ROOT_DIR, file_path)
    with open(abs_path, "r", encoding="utf-8") as f:
        return json.load(f)

def create_documents():
    products = load_json("data/products.json")
    faqs = load_json("data/faq.json")
    complaints = load_json("data/complaints.json")
    descriptions = load_json("data/descriptions.json")
    
    documents = []

    for p in products:
        doc = {
            "id": p["product_id"],
            "content": f"ชื่อ: {p['name_th']} / {p['name_en']}\nจุดเด่น: {p.get('highlights','')}\nข้อดี: {p.get('pros','')}\nข้อเสีย: {p.get('cons','')}\nควรระวัง: {p.get('cautions','')}\nสี: {p.get('colors','')}\nอื่นๆ: {p.get('other','')}"
        }
        documents.append(doc)

    for faq in faqs:
        doc = {
            "id": f"faq_{faq['product_id']}_{faqs.index(faq)}",
            "content": f"คำถาม: {faq['question']}\nคำตอบ: {faq['solution']}"
        }
        documents.append(doc)

    for c in complaints:
        doc = {
            "id": f"complaint_{c['product_id']}_{complaints.index(c)}",
            "content": c["complaint"]
        }
        documents.append(doc)

    for d in descriptions:
        doc = {
            "id": d["product_id"] + "_desc",
            "content": f"สี: {d['color_range']}, ปริมาณ: {d['volume']}, เหมาะกับ: {d['suitable_skin']}, เนื้อสัมผัส: {d['texture']}, ฟินิช: {d['finish']}, ราคา: {d['price_range']}"
        }
        documents.append(doc)

    return documents