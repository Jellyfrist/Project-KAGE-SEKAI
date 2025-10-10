import os
from dotenv import load_dotenv
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PERSIST_DIR = "chroma_db"

emb = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)
db = Chroma(persist_directory=PERSIST_DIR, embedding_function=emb, collection_name="kage_products")

llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.1, openai_api_key=OPENAI_API_KEY)

prompt_template = """คุณคือผู้ช่วยตอบลูกค้าเกี่ยวกับสินค้า KAGE — ใช้เฉพาะข้อมูลต่อไปนี้เพื่อให้คำตอบ อย่าเดาหาข้อมูลที่ไม่มีในแหล่งข้อมูล หากข้อมูลไม่พอ ให้แจ้งว่าต้องการข้อมูลเพิ่มและนำทางลูกค้าอย่างสุภาพ

Context:
----
{context}
----

User: {question}

Instructions:
- ตอบสั้น 2–4 ย่อหน้า
- ระบุแหล่งข้อมูล (เช่น: source: faq_B001.json#chunk_id)
- เสนอ 1–2 แนวทางแก้ไข/next steps (ถ้ามี)
- ถ้าต้องข้อมูลเพิ่ม ให้ถามคำถามเชิงเฉพาะ
"""

def build_prompt(question, retrieved_docs):
    context = ""
    for idx, doc in enumerate(retrieved_docs, 1):
        meta = doc.metadata
        context += f"[{idx}] ({meta['source_file']}) {doc.page_content}\n"
    prompt = PromptTemplate(input_variables=["context","question"], template=prompt_template)
    return prompt.format(context=context, question=question)

def answer_question(question, product_id=None, k=6):
    filter = {"product_id": product_id} if product_id else None
    retrieved = db.similarity_search(question, k=k, filter=filter)
    prompt = build_prompt(question, retrieved)
    answer = llm.predict(prompt)
    sources = [{"source_file": doc.metadata["source_file"], "chunk_id": doc.metadata["chunk_id"]} for doc in retrieved]
    return {"answer": answer, "sources": sources}