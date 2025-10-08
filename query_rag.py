import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
import openai
import os
from dotenv import load_dotenv

os.environ["TOKENIZERS_PARALLELISM"] = "false" #ซ่อน warning

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# โหลด index และ id_map
index = faiss.read_index("index/faiss_index.index")
with open("index/id_map.pkl", "rb") as f:
    id_map = pickle.load(f)

# โหลด embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

def retrieve_docs(query, top_k=5):
    query_emb = model.encode(query).astype('float32')
    distances, indices = index.search(np.array([query_emb]), top_k)
    return [id_map[i]['content'] for i in indices[0]]

def generate_answer(query, retrieved_docs):
    context = "\n\n".join(retrieved_docs)
    prompt = f"นี่คือข้อมูลสินค้าที่เกี่ยวข้อง:\n{context}\n\nคำถาม: {query}\n\nกรุณาตอบคำถามนี้อย่างละเอียด"
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "คุณเป็นผู้ช่วยขายสินค้าเครื่องสำอาง"},
            {"role": "user", "content": prompt}
        ]
    )
    return response['choices'][0]['message']['content']

# example
# if __name__ == "__main__":
#     query = "คุชชั่นใช้แล้วเป็นคราบ ต้องทำยังไง?"
#     docs = retrieve_docs(query)
#     answer = generate_answer(query, docs)
#     print(answer)

if __name__ == "__main__":
    query = "ลิปไก่ทอดสี 09 เหมาะกับคนประเภทไหน"
    docs = retrieve_docs(query)
    answer = generate_answer(query, docs)
    print(answer)