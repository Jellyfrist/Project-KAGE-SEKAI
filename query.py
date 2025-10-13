import os
from dotenv import load_dotenv
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

# โหลด API key
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ตั้งค่า Chroma DB
PERSIST_DIR = "chroma_db"
emb = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)
db = Chroma(
    persist_directory=PERSIST_DIR,
    embedding_function=emb,
    collection_name="kage_products"
)

# สร้าง LLM
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.1, openai_api_key=OPENAI_API_KEY)

# แผนที่ชื่อสินค้า → product_id
PRODUCT_NAME_MAP = {
    "บลัช": "B001",
    "ฟิลเตอร์บลัช": "B001",
    "ฟิลเตอร์บรัช": "B001",
    "บรัช": "B001",
    "คอลซีลเลอร์ยางลบ & คอเรคเตอร์ยางลบ": "C001",
    "คอเรคเตอร์ยางลบ": "C001",
    "คอเรคเตอร์": "C001",
    "คอลซีลเลอร์": "C001",
    "คอนซีลเลอร์": "C001",
    "คอลซีลเล่อ": "C001",
    "คอนซีลเล่อ": "C001",
    "คอเรกเตอร์": "C001",
    "คอเลกเตอร์": "C001",
    "คุชชั่น": "C002",
    "คุชชั่นเสกผิว": "C002",
    "ลิป": "L001",
    "ลิปไก่ทอด": "L001",
    "มาสคาร่า": "M001",
    "มาสคาร่าคิ้ว": "M001",
}

def find_product_by_name(question: str):
    question_lower = question.lower()
    for name, pid in PRODUCT_NAME_MAP.items():
        if name.lower() in question_lower:
            return pid
    return None

prompt_template = """คุณคือเพศหญิง ที่เป็นผู้ช่วยตอบลูกค้าเกี่ยวกับสินค้า KAGE — ใช้เฉพาะข้อมูลต่อไปนี้เพื่อให้คำตอบ อย่าเดาหาข้อมูลที่ไม่มีในแหล่งข้อมูล หากข้อมูลไม่พอ ให้แจ้งว่าต้องการข้อมูลเพิ่มและนำทางลูกค้าอย่างสุภาพ

Context:
----
{context}
----

User: {question}

Instructions:
- ตอบสั้น 2–4 ย่อหน้า
- ระบุแหล่งข้อมูล (เช่น: source: faq_B001.json#chunk_id)
- ถ้าเป็นคำถามเกี่ยวกับปัญหา ให้เสนอแนวทางแก้ไขหรือขั้นตอนต่อไป
- ถ้าเป็นคำถามทั่วไป เช่น สี ขนาด ราคา ให้ตอบข้อมูลเท่านั้น
- ถ้าต้องการข้อมูลเพิ่ม ให้ถามคำถามเชิงเฉพาะ
"""

def build_prompt(retrieved_docs):
    context = ""
    for idx, doc in enumerate(retrieved_docs, 1):
        meta = doc.metadata
        context += f"[{idx}] ({meta.get('source_file')}) {doc.page_content}\n"
    return context

def answer_question(question, product_id=None, k=6):
    # ---------- 1. ตรวจสอบ product_id ----------
    if not product_id:
        product_id = find_product_by_name(question)
        if not product_id:
            return {"answer": "ไม่สามารถระบุสินค้าได้ กรุณาระบุชื่อสินค้าให้ชัดเจน", "sources": []}

    # ---------- 2. ดึงเอกสารเฉพาะสินค้านั้น ----------
    filter = {"product_id": product_id}  # ส่ง filter ให้ถูกต้อง
    retrieved_docs = db.similarity_search(query=question, k=k, filter=filter)
    context_text = build_prompt(retrieved_docs)

    # ---------- 3. ตรวจสอบคำถามว่าเป็นปัญหาหรือไม่ ----------
    problem_keywords = ["เสีย", "พัง", "แก้", "ไม่ติด", "ทำยังไง", "ล้างยังไง"]
    is_problem = any(word in question.lower() for word in problem_keywords)

    # ---------- 4. เลือก prompt ----------
    custom_prompt = prompt_template
    if not is_problem:
        custom_prompt = prompt_template.replace(
            "- ถ้าเป็นคำถามเกี่ยวกับปัญหา ให้เสนอแนวทางแก้ไขหรือขั้นตอนต่อไป\n", ""
        )

    prompt_obj = PromptTemplate(input_variables=["context", "question"], template=custom_prompt)
    prompt_text = prompt_obj.format(context=context_text, question=question)

    # ---------- 5. เรียกโมเดล ----------
    answer = llm.predict(prompt_text)

    # ---------- 6. เก็บ sources ----------
    sources = [
        {"source_file": doc.metadata.get("source_file"), "chunk_id": doc.metadata.get("chunk_id")}
        for doc in retrieved_docs
    ]

    return {"answer": answer, "sources": sources}
