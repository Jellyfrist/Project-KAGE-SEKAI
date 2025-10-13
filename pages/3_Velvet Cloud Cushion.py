import streamlit as st
from PIL import Image
import os
from dotenv import load_dotenv
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from datetime import datetime # <<< นำเข้า datetime เพื่อใช้ในการบันทึกเวลา

# --- CONFIGURATION & PAGE SETUP ---

st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CONSTANTS ---
FIXED_PRODUCT_ID = "C002"
FIXED_PRODUCT_NAME = "คุชชั่นเสกผิว (C002)" 

# **การแก้ไขหลัก: ใช้ Key เพื่อแยกการเปลี่ยนหน้ากับการ Rerun**
CURRENT_PAGE_KEY = f"chat_messages_{FIXED_PRODUCT_ID}"

# --- SESSION STATE INITIALIZATION AND CLEAR FUNCTION ---

# 1. กำหนดค่าเริ่มต้นของ Session State
if CURRENT_PAGE_KEY not in st.session_state:
    st.session_state[CURRENT_PAGE_KEY] = [] # เก็บ messages ไว้ใน key เฉพาะของหน้านี้
if "current_page_load_key" not in st.session_state:
    st.session_state["current_page_load_key"] = None 

# 2. ฟังก์ชันเคลียร์แชท เมื่อมีการ "เปลี่ยนหน้า"
def clear_chat_on_page_change():
    """
    Clears the chat history only if the app detects a navigation event (page change).
    It compares the CURRENT_PAGE_KEY with the last loaded key in session state.
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
    header_img = Image.open("assets/Cushion.png")
except FileNotFoundError:
    header_img = None

if header_img:
    st.image(header_img, use_container_width=True)
st.markdown("<br>", unsafe_allow_html=True)

st.title("KAGE VELVET CLOUD CUSHION SPF 50 PA+++ | คุชชั่นเสกผิว")
st.markdown("""
ผลิตภัณฑ์รองพื้นในรูปแบบคุชชั่น เนื้อสัมผัสบางเบา เกลี่ยง่าย ช่วยปรับสีผิวให้ดูเรียบเนียนอย่างเป็นธรรมชาติ มอบการปกปิดตั้งแต่ระดับ Medium–Full Coverage  

สามารถเพิ่มเลเยอร์ตามความต้องการ พร้อมคุณสมบัติกันน้ำ กันเหงื่อ ติดทน 12 ชม. และปกป้องผิวจากแสงแดดด้วย SPF 50 PA+++
""", unsafe_allow_html=True)


# --- AI SETUP ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

PERSIST_DIR = "chroma_db"
# ตรวจสอบว่ามี API Key ก่อนสร้าง Embedding
llm_ready = True
db = None

if OPENAI_API_KEY:
    try:
        emb = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)
        db = Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=emb,
            collection_name="kage_products"
        )
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.1, openai_api_key=OPENAI_API_KEY)
    except Exception:
        llm_ready = False
else:
    llm_ready = False


PRODUCT_NAME_MAP = {
    "บลัช": "B001", "ฟิลเตอร์บลัช": "B001", "ฟิลเตอร์บรัช": "B001", "บรัช": "B001",
    "คอลซีลเลอร์ยางลบ & คอเรคเตอร์ยางลบ": "C001", "คอเรคเตอร์ยางลบ": "C001", "คอเรคเตอร์": "C001",
    "คอลซีลเลอร์": "C001", "คอนซีลเลอร์": "C001", "คอลซีลเล่อ": "C001", "คอนซีลเล่อ": "C001",
    "คอเรกเตอร์": "C001", "คอเลกเตอร์": "C001", "คุชชั่น": "C002", "คุชชั่นเสกผิว": "C002",
    "ลิป": "L001", "ลิปไก่ทอด": "L001", "มาสคาร่า": "M001", "มาสคาร่าคิ้ว": "M001",
}

prompt_template = """คุณคือเพศหญิง ที่เป็นผู้ช่วยตอบลูกค้าเกี่ยวกับสินค้า KAGE — ใช้เฉพาะข้อมูลต่อไปนี้เพื่อให้คำตอบ อย่าเดาหาข้อมูลที่ไม่มีในแหล่งข้อมูล หากข้อมูลไม่พอ ให้แจ้งว่าต้องการข้อมูลเพิ่มและนำทางลูกค้าอย่างสุภาพ

Context:
----
{context}
----

User: {question}

Instructions:
- ตอบสั้น 2–4 ย่อหน้า
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
    product_id = FIXED_PRODUCT_ID 
    filter = {"product_id": product_id}
    
    if not llm_ready:
        return {"answer": "เนื่องจาก API Key ไม่พร้อมใช้งาน ระบบจึงไม่สามารถดึงข้อมูลจาก LLM ได้ กรุณาตรวจสอบการตั้งค่า OPENAI_API_KEY.", "sources": []}
        
    if db is None:
        return {"answer": "ขออภัยค่ะ ระบบฐานข้อมูลไม่พร้อมใช้งานในขณะนี้", "sources": []}

    retrieved_docs = db.similarity_search(query=question, k=k, filter=filter)
    context_text = build_prompt(retrieved_docs)

    problem_keywords = ["เสีย", "พัง", "แก้", "ไม่ติด", "ทำยังไง", "ล้างยังไง"]
    is_problem = any(word in question.lower() for word in problem_keywords)

    custom_prompt = prompt_template
    if not is_problem:
        # ลบเฉพาะบรรทัดที่เกี่ยวกับปัญหา
        custom_prompt = "".join([line for line in prompt_template.splitlines() if not line.startswith("- ถ้าเป็นคำถามเกี่ยวกับปัญหา ให้เสนอแนวทางแก้ไขหรือขั้นตอนต่อไป")])
    
    prompt_obj = PromptTemplate(input_variables=["context", "question"], template=custom_prompt)
    prompt_text = prompt_obj.format(context=context_text, question=question)

    answer = llm.predict(prompt_text)

    sources = [
        {"source_file": doc.metadata.get("source_file"), "chunk_id": doc.metadata.get("chunk_id")}
        for doc in retrieved_docs
    ]

    return {"answer": answer, "sources": sources}

# --- CHAT DISPLAY FUNCTION (เพิ่มการแสดงเวลา, ลบ Sources) ---
def display_chat_message_content(message):
    content = message["content"]
    timestamp = message.get("time", "") # ดึงเวลาที่บันทึกไว้

    # รูปแบบการแสดงผล: (เวลา) ข้อความ
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


# --- CHAT INPUT & PROCESSING (เพิ่มการบันทึกเวลา, ลบ Sources) ---
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

# --- CUSTOM CSS: FONT KANIT & UI STYLING (FINAL FIX) ---
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