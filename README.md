# Project KAGE SEKAI: COLORFUL STAGE! (Chicken Chicken Banana)

204203 COMPUTER SCIENCE TECHNOLOGY

โครงการนี้เป็นศูนย์รวมเครื่องมือ AI สำหรับการวิเคราะห์ข้อมูลสินค้า ความเห็นลูกค้า และระบบตอบคำถาม (RAG Chat) เพื่อสนับสนุนงานการตลาดและการขายของแบรนด์ KAGE

- วิเคราะห์รีวิวลูกค้า (CSV) เพื่อหาประเด็น จุดแข็ง/จุดอ่อนของสินค้า
- แสดงข้อมูลสินค้า/คำถามที่พบบ่อย จากไฟล์ JSON แยกตามสินค้า
- ระบบ RAG (Retrieval-Augmented Generation) สำหรับตอบคำถามเกี่ยวกับสินค้า พร้อมอ้างอิงแหล่งที่มา
- UI บน Streamlit ใช้งานง่าย และมีหน้าแยกตามผลิตภัณฑ์

## โครงสร้างโปรเจกต์
```
  assets/                     # รูปภาพที่ใช้ในหน้า UI
  chroma_db/                  # ฐานข้อมูลเวกเตอร์ Chroma (ถ้ามีการสร้างไว้แล้ว)
  data/                       # ข้อมูลสินค้า/FAQ/Complaint ในรูปแบบ JSON
  pages/                      # หน้าแอป Streamlit แยกตามสินค้า/ฟังก์ชัน
  RAG/                        # โมดูลระบบ RAG (ingest / query / app)
  reviews/                    # รีวิวลูกค้า (.csv)
  schemas/                    # สคีมาข้อมูลสำหรับ validate
  Home.py                     # หน้าแรกของ Streamlit App หลัก
  config.py                   # การตั้งค่าโมเดลผ่าน .env
  requirements.txt            # รายการไลบรารีที่ใช้
  README.md                   # เอกสารโครงการ (ไฟล์นี้)
```

## การติดตั้ง
1) สร้างและเปิดใช้งาน virtual environment (แนะนำ Python 3.10+)
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) ติดตั้ง dependencies
```bash
pip install -r requirements.txt
```

## การตั้งค่า Environment Variables (.env)
สร้างไฟล์ `.env` ที่รากโปรเจกต์ และระบุค่าอย่างน้อยดังนี้
```bash
# เลือกโมเดลหลักของ LLM (ขึ้นกับผู้ให้บริการ)
MODEL=gpt-4o-mini

# โมเดลสร้างเวกเตอร์ฝังความหมาย (สำหรับ RAG)
EMBED_MODEL=text-embedding-3-small

# ถ้าใช้ OpenAI ให้ตั้งคีย์ต่อไปนี้
OPENAI_API_KEY=your_openai_api_key
```

## วิธีรันแอป
```bash
streamlit run HOME.py
```

แมพพอร์ตเริ่มต้นของ Streamlit คือ `8501` (หรือจะแจ้งในเทอร์มินัลหากชนพอร์ต)

## ขั้นตอนทำงานของ RAG
1) เตรียมคอร์ปัสข้อมูลใน `RAG/corpus.jsonl` (หรือดึงจากไฟล์ใน `data/`)
2) สร้างดัชนีเวกเตอร์ด้วยคำสั่ง ingest (ถ้ามีสคริปต์ `ingest.py`):
```bash
python RAG/ingest.py
```
3) เริ่มใช้งานหน้าแชตใน `RAG/app.py` เพื่อถาม-ตอบ พร้อมแสดงแหล่งที่มา

ไฟล์สำคัญในโมดูล RAG:
- `RAG/ingest.py`: สร้างเวกเตอร์จากคอร์ปัสไปยัง Chroma/FAISS
- `RAG/query.py`: ดึงข้อมูลที่เกี่ยวข้องและเรียก LLM เพื่อสังเคราะห์คำตอบ
- `RAG/app.py`: UI Streamlit สำหรับสนทนา

## แหล่งข้อมูล
- `data/*.json`: ข้อมูลสินค้า, FAQ, ข้อร้องเรียน แยกตามรหัสสินค้า (B001, C001, C002, L001, M001)
- `reviews/*.csv`: รีวิวลูกค้าตามสินค้า ใช้ประกอบการวิเคราะห์เชิงคุณภาพ
- `schemas/*.py` และ `schemas/*.json`: สคีมาโครงสร้างข้อมูลผลิตภัณฑ์และรีวิว

## การแก้ปัญหาเบื้องต้น
- ImportError/ModuleNotFoundError: ตรวจสอบว่าได้ `pip install -r requirements.txt` ใน environment ที่เปิดใช้งานแล้ว
- AssertionError จาก `config.py`: ตรวจสอบไฟล์ `.env` ว่ามี `MODEL` และ `EMBED_MODEL` ถูกต้อง
- ข้อมูล/รีวิวไม่แสดง: ตรวจชื่อไฟล์ JSON/CSV ให้ตรง และโครงสร้างตาม `schemas/`
