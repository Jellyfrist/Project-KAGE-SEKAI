import streamlit as st
from PIL import Image
import os
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings 
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from datetime import datetime  # <<< นำเข้า datetime
import traceback
import time

# --- CONFIGURATION & PAGE SETUP ---

st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CONSTANTS ---
FIXED_PRODUCT_ID = "B001"
FIXED_PRODUCT_NAME = "ฟิลเตอร์บลัช (B001)" 

# **การแก้ไขหลัก: ใช้ Key เพื่อแยกการเปลี่ยนหน้ากับการ Rerun**
CURRENT_PAGE_KEY = f"chat_messages_{FIXED_PRODUCT_ID}"

# --- SESSION STATE INITIALIZATION AND CLEAR FUNCTION ---

# 1. กำหนดค่าเริ่มต้นของ Session State
if CURRENT_PAGE_KEY not in st.session_state:
    st.session_state[CURRENT_PAGE_KEY] = []  # เก็บ messages ไว้ใน key เฉพาะของหน้านี้
if "current_page_load_key" not in st.session_state:
    st.session_state["current_page_load_key"] = None 
if "product_context" not in st.session_state:
    st.session_state["product_context"] = None

# 2. ฟังก์ชันเคลียร์แชท เมื่อมีการ "เปลี่ยนหน้า"
def clear_chat_on_page_change():
    """
    Clears the chat history only if the app detects a navigation event (page change).
    If the key doesn't match the last run key, it's considered a new load/navigation.
    """
    # ถ้า Key ของหน้านี้ไม่ตรงกับ Key ล่าสุดที่ถูกบันทึกไว้ใน Session State 
    if st.session_state["current_page_load_key"] != CURRENT_PAGE_KEY:
        st.session_state[CURRENT_PAGE_KEY] = []
        # อัปเดต Key ล่าสุดให้เป็น Key ของหน้านี้
        st.session_state["current_page_load_key"] = CURRENT_PAGE_KEY

# เรียกใช้ฟังก์ชันนี้ก่อนที่จะแสดงผลส่วนอื่น ๆ ทั้งหมด
clear_chat_on_page_change()


# --- HEADER & PRODUCT INFO ---
try:
    header_img = Image.open("assets/Filter Brush.png")
except Exception:
    header_img = None

if header_img:
    st.image(header_img, use_container_width=True)
st.markdown("<br>", unsafe_allow_html=True)

st.title("Filter Brush | ฟิลเตอร์บลัช")
st.markdown("""
ครีมบลัชที่คัดมา 11 สีเข้ากับทุกเฉดผิว ไม่ว่าจะผิวขาว ขาวเหลือง ผิวสองสี ผิวเข้ม 

ทาแล้วฟื้นเหมือนติดฟิลเตอร์ที่ผิวแก้มตลอดเวลา น้องสีสวยมากกก ทาเดี่ยว หรือทาผสม คือปัง!!!
""", unsafe_allow_html=True) 


# --- AI SETUP (ปรับปรุงการจัดการ API Key) ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

PERSIST_DIR = "chroma_db"
llm_ready = True
db = None

# พยายามโหลด embeddings / chroma / llm แต่จับ exception ให้เป็นมิตรกับผู้ใช้
if OPENAI_API_KEY:
    try:
        emb = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)
        # ถ้า Chroma ยังไม่มีไฟล์ DB จะเกิด error ที่นี่ — เราจับไว้แล้วแจ้งผู้ใช้
        db = Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=emb,
            collection_name="kage_products"
        )
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.1, openai_api_key=OPENAI_API_KEY)
    except Exception as e:
        llm_ready = False
        # บันทึก traceback เพื่อ debug (แต่ไม่แสดงเต็มๆ ให้ผู้ใช้)
        st.session_state.setdefault("_internal_errors", []).append(traceback.format_exc())
else:
    llm_ready = False

prompt_template = """
คุณคือผู้ช่วยตอบลูกค้าเกี่ยวกับสินค้า KAGE และต้องทำงานภายใต้กฎเกณฑ์ต่อไปนี้อย่างเคร่งครัด

RULES:
1. **ตรวจสอบแหล่งข้อมูล (Context) เท่านั้น** ห้ามใช้ความรู้ทั่วไปโดยเด็ดขาด
2. **ห้ามตอบคำถาม** หากข้อมูลใน Context ไม่เพียงพอต่อการให้คำตอบอย่างครบถ้วน
3. หากข้อมูลไม่เพียงพอ ให้ตอบด้วยข้อความ **เดียวเท่านั้น**: "ดิฉันต้องขออภัยค่ะ ข้อมูลในขณะนี้ยังไม่เพียงพอต่อการให้คำตอบที่ชัดเจน กรุณาระบุข้อมูลเพิ่มเติมให้ดิฉันด้วยนะคะ"

Context:
----
{context}
----

ขั้นตอนการตอบ:
1. **[EVALUATION]** อ่าน Context และ User Question แล้วประเมิน: Context เพียงพอหรือไม่? (ตอบ YES หรือ NO เท่านั้น)
2. **[REASONING]** อธิบายสั้นๆ ว่าทำไม Context ถึงเพียงพอ/ไม่เพียงพอ
3. **[FINAL ANSWER]** สร้างคำตอบสุดท้ายตาม RULE 2 หรือ RULE 3 (ไม่ต้องใส่ขั้นตอน 1 และ 2 ในคำตอบสุดท้าย)

User: {question}

Instructions:
- ตอบสั้น 2–4 ย่อหน้า และใช้ภาษาที่เป็นมิตร
- ห้ามระบุแหล่งข้อมูล (เช่น source: faq_B001.json) ในคำตอบสุดท้าย
- ถ้าต้องการข้อมูลเพิ่ม ให้ถามคำถามเชิงเฉพาะ
"""

def build_prompt(retrieved_docs):
    context = ""
    for idx, doc in enumerate(retrieved_docs, 1):
        meta = getattr(doc, "metadata", {}) or {}
        source_file = meta.get("source_file", "unknown")
        page_content = getattr(doc, "page_content", str(doc))
        context += f"[{idx}] ({source_file}) {page_content}\n"
    return context

def answer_question(question, product_id=None, k=6):
    """
    ตอบคำถามเกี่ยวกับสินค้าหน้านี้ (FIXED_PRODUCT_ID)
    - product_id: ถ้ามี จะถูก override ให้เป็น FIXED_PRODUCT_ID (ตามโครงสร้างหน้าปัจจุบัน)
    - k: จำนวน chunk ที่จะดึง
    """
    # บังคับใช้ product ของหน้านี้ (เพราะแต่ละไฟล์เป็นหน้าสินค้าเดียว)
    product_id = FIXED_PRODUCT_ID 
    filter = {"product_id": product_id}

    # ตรวจสอบความพร้อมก่อนเริ่มทำงาน
    if not llm_ready or db is None:
        return {"answer": "เนื่องจาก API Key หรือฐานข้อมูลไม่พร้อมใช้งาน ระบบจึงไม่สามารถดึงข้อมูลจาก LLM ได้ กรุณาตรวจสอบการตั้งค่า OPENAI_API_KEY หรือไฟล์ DB.", "sources": []}

    # ทำ similarity search อย่างระมัดระวัง (จับ exception)
    try:
        # สำหรับ Chroma: similarity_search(query, k, filter) หรือ ความแตกต่างแล้วแต่เวอร์ชัน
        # เราจะลองทั้งสองแบบเพื่อให้เข้ากันกับหลายเวอร์ชัน
        try:
            retrieved_docs = db.similarity_search(question, k=k, filter=filter)
        except TypeError:
            # บางเวอร์ชันใช้ arguments ชื่อ 'query'
            retrieved_docs = db.similarity_search(query=question, k=k, filter=filter)
    except Exception as e:
        # ถ้าการค้นหาเกิดปัญหา ให้คืนข้อความที่เป็นมิตร
        st.session_state.setdefault("_internal_errors", []).append(traceback.format_exc())
        return {"answer": "เกิดข้อผิดพลาดขณะค้นหาข้อมูลในฐานความรู้ กรุณาลองใหม่อีกครั้ง", "sources": []}

    if not retrieved_docs:
        # หากไม่มีเอกสารที่เกี่ยวข้องเลย ให้ตอบปฏิเสธทันที ไม่ต้องเรียก LLM
        return {
            "answer": f"ดิฉันต้องขออภัยค่ะ ข้อมูลในขณะนี้ยังไม่เพียงพอต่อการให้คำตอบที่ชัดเจนเกี่ยวกับ '{question}' สำหรับสินค้า {FIXED_PRODUCT_NAME} ค่ะ", 
            "sources": []
        }

    context_text = build_prompt(retrieved_docs)

    # ตรวจสอบคำถามว่าเป็นปัญหาหรือไม่ (ใช้เพื่อปรับ prompt ถ้าจำเป็น)
    problem_keywords = ["เสีย", "พัง", "แก้", "ไม่ติด", "ทำยังไง", "ล้างยังไง"]
    is_problem = any(word in question.lower() for word in problem_keywords)

    # ถ้าต้องการ ปรับ prompt (ที่นี่ใช้ prompt_template เดียวกัน แต่สามารถปรับเพิ่มเติมได้)
    custom_prompt = prompt_template

    # สร้าง prompt และเรียก LLM
    try:
        prompt_obj = PromptTemplate(input_variables=["context", "question"], template=custom_prompt)
        prompt_text = prompt_obj.format(context=context_text, question=question)
        answer = llm.invoke(prompt_text) 
    except Exception as e:
        st.session_state.setdefault("_internal_errors", []).append(traceback.format_exc())
        return {"answer": "เกิดข้อผิดพลาดขณะเรียกโมเดล LLM กรุณาตรวจสอบการตั้งค่า API หรือสภาวะแวดล้อม", "sources": []}

    # เก็บแหล่งที่มา (ถ้ามี)
    sources = []
    for doc in retrieved_docs:
        meta = getattr(doc, "metadata", {}) or {}
        sources.append({"source_file": meta.get("source_file", "unknown"), "chunk_id": meta.get("chunk_id", "unknown")})

    return {"answer": answer, "sources": sources}

# --- CHAT DISPLAY FUNCTION (เพิ่มการแสดงเวลา) ---
def display_chat_message_content(message):
    content = message["content"]
    timestamp = message.get("time", "") # ดึงเวลาที่บันทึกไว้
    
    # รูปแบบการแสดงผล: (เวลา) ข้อความ
    # ใช้ span แยกเวลาและข้อความเพื่อให้จัดรูปแบบ CSS ได้ง่าย (แม้จะถูกห่อด้วย p tag ของ streamlit)
    full_content = f"<span style='font-size: 0.8em; color: gray;'>({timestamp})</span> {content}"
    
    st.markdown(full_content, unsafe_allow_html=True) 

# --- DISPLAY OLD MESSAGES ---

# ใช้ st.container ห่อข้อความแชทเพื่อจัดการพื้นที่
chat_container = st.container()

with chat_container:
    # **ใช้ CURRENT_PAGE_KEY ในการดึง messages**
    for msg in st.session_state[CURRENT_PAGE_KEY]:
        avatar = "💖" if msg["role"] == "assistant" else "🙋‍♀️" 
        with st.chat_message(msg["role"], avatar=avatar):
            display_chat_message_content(msg)

# --- CHAT INPUT & PROCESSING (เพิ่มการบันทึกเวลา) ---
prompt = st.chat_input("พิมพ์คำถามของลูกค้า...")

if prompt:
    current_time = datetime.now().strftime("%H:%M") # <<< ดึงเวลาปัจจุบัน

    # 1. User message
    st.session_state[CURRENT_PAGE_KEY].append({
        "role": "user", 
        "content": prompt, 
        "sources": [], 
        "time": current_time # <<< บันทึกเวลา
    })
    
    # 2. Display user message
    with st.chat_message("user", avatar="🙋‍♀️"): 
        # แสดงผลพร้อมเวลา
        st.markdown(f"<span style='font-size: 0.8em; color: gray;'>({current_time})</span> {prompt}", unsafe_allow_html=True) 

    product_id = FIXED_PRODUCT_ID
    st.session_state["product_context"] = product_id

    # 3. Get and display assistant response
    with st.chat_message("assistant", avatar="💖"): 
        with st.spinner("กำลังดึงข้อมูลและตอบคำถาม..."):
            resp = answer_question(question=prompt, product_id=product_id)
        
        assistant_time = datetime.now().strftime("%H:%M") # <<< ดึงเวลาผู้ช่วยตอบ

        # แสดงผลพร้อมเวลา
        st.markdown(f"<span style='font-size: 0.8em; color: gray;'>({assistant_time})</span> {resp['answer']}", unsafe_allow_html=True) 
        
        # 4. Save assistant response
        st.session_state[CURRENT_PAGE_KEY].append({ # **ใช้ CURRENT_PAGE_KEY ในการบันทึก**
            "role":"assistant",
            "content": resp["answer"],
            "context_used": True,
            "sources": resp.get("sources", []),
            "time": assistant_time # <<< บันทึกเวลา
        })

# --- CUSTOM CSS: FONT KANIT & UI STYLING (Final Cleaned Version) ---
PASTEL_BLUE = "#AEC6CF" 
ACCENT_BLUE = "#779ECB" 
WHITE = "#FFFFFF" 
LIGHT_PASTEL_BLUE = "#C7DBF0" 
BLACK = "#000000"

st.markdown("""
    <style>
        /* Import Kanit Font */
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600;700&display=swap');

        /* 0. SCROLL FIX - Make the main content area scrollable if content exceeds height */
        [data-testid="stAppViewContainer"] > div > [data-testid="stVerticalBlock"] {{
            overflow-y: auto;
            max-height: calc(100vh - 100px); 
        }}

        /* 1. GLOBAL FONT FIX (Highest Specificity) */
        /* Targets the whole app and the most common text/div containers */
        body, #root, .stApp, .main, 
        [data-testid="stAppViewContainer"], 
        .main * {{
            font-family: 'Kanit', sans-serif !important;
            color: {BLACK} !important; 
        }}

        /* 2. HEADING FIXES */
        h1, h2, h3, h4, h5, h6, 
        [data-testid^="stHeader"] h1, 
        [data-testid^="stHeader"] h2
        {{
            font-family: 'Kanit', sans-serif !important;
            font-weight: 700 !important; 
        }}
        
        /* 3. PARAGRAPH/MARKDOWN FIX (Targets ALL generic text including the product description) */
        p,
        div[data-testid="stVerticalBlock"] p, 
        [data-testid="stAlert"] p,
        
        /* Fix text in input/select areas and expanders */
        label p,
        [data-baseweb="select"] *, 
        [data-baseweb="input"] *,
        [data-baseweb="textarea"] *,
        [data-baseweb="button"] *,
        [data-testid="stExpander"] div[role="button"] p 
        {{
            font-family: 'Kanit', sans-serif !important;
            font-weight: 400 !important; 
            line-height: 1.6; 
        }}
        
        /* === 4. CRITICAL CHAT BUBBLE FONT FIXES === */
        
        /* Targets all paragraph text inside a chat message, regardless of role */
        [data-testid="stChatMessage"] p {{
            font-family: 'Kanit', sans-serif !important;
            font-weight: 400 !important; 
            line-height: 1.6; 
        }}

        /* === 5. CHAT MESSAGE BOX STYLING (เดิม) === */
        
        /* Background & Text Color */
        body, #root, .stApp, .main, [data-testid="stAppViewContainer"], [data-testid="stSpinner"] > div {{ background-color: {WHITE} !important; }}
        section[data-testid="stSidebar"] {{ background-color: {LIGHT_PASTEL_BLUE} !important; border-right: 1px solid #CCCCCC; }}
        [data-testid="stSidebar"] * {{ color: {BLACK} !important; }}
        
        /* Message box width limit */
        [data-testid="stChatMessage"] div[data-testid="stVerticalBlock"] {{ max-width: 65% !important; }}
        
        /* Message box general shape */
        [data-testid="stChatMessage"] div.st-emotion-cache-p5m6iv {{ 
            border-radius: 15px !important;
            padding: 10px !important;
        }}
        
        /* USER: Align box right */
        [data-testid="stChatMessage"][data-testid^="stChatMessage-user"] {{ flex-direction: row-reverse; }}
        /* ASSISTANT: Align box left */
        [data-testid="stChatMessage"][data-testid^="stChatMessage-assistant"] {{ flex-direction: row; }}

        /* ASSISTANT: Box color */
        [data-testid="stChatMessage"][data-testid^="stChatMessage-assistant"] div.st-emotion-cache-p5m6iv {{
            background-color: {LIGHT_PASTEL_BLUE} !important;
            color: {BLACK} !important;
        }}
        
        /* USER: Box color */
        [data-testid="stChatMessage"][data-testid^="stChatMessage-user"] div.st-emotion-cache-p5m6iv {{
            background-color: {ACCENT_BLUE} !important;
            color: {WHITE} !important;
        }}
        
        /* USER: Text align right (Applies to Kanit text inside the box) */
        [data-testid="stChatMessage"][data-testid^="stChatMessage-user"] div.st-emotion-cache-p5m6iv p {{
            text-align: right !important;
        }}
        
        /* ASSISTANT: Text align left (Applies to Kanit text inside the box) */
        [data-testid="stChatMessage"][data-testid^="stChatMessage-assistant"] div.st-emotion-cache-p5m6iv p {{
            text-align: left !important;
        }}
        
        /* Chat Input Area */
        [data-testid="stAppViewContainer"] > div > div {{ background-color: {WHITE} !important; }}
        [data-testid="stChatInput"] {{
            background-color: {WHITE} !important;
            border: none !important;
            padding: 10px 0 !important;
        }}
        [data-testid="stChatInput"] > div > div {{
            background-color: {WHITE} !important; 
            color: {BLACK} !important; 
            border-radius: 8px !important;
            border: none !important;
        }}
        
    </style>
""".format(PASTEL_BLUE=PASTEL_BLUE, WHITE=WHITE, LIGHT_PASTEL_BLUE=LIGHT_PASTEL_BLUE, BLACK=BLACK, ACCENT_BLUE=ACCENT_BLUE), unsafe_allow_html=True)

