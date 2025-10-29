import streamlit as st
from PIL import Image
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings 
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from datetime import datetime  
import traceback

st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
)

FIXED_PRODUCT_ID = "B001"
FIXED_PRODUCT_NAME = "ฟิลเตอร์บลัช (B001)" 

CURRENT_PAGE_KEY = f"chat_messages_{FIXED_PRODUCT_ID}"


if CURRENT_PAGE_KEY not in st.session_state:
    st.session_state[CURRENT_PAGE_KEY] = []  
if "current_page_load_key" not in st.session_state:
    st.session_state["current_page_load_key"] = None 
if "product_context" not in st.session_state:
    st.session_state["product_context"] = None

def clear_chat_on_page_change():
    """
    Clears the chat history only if the app detects a navigation event (page change).
    If the key doesn't match the last run key, it's considered a new load/navigation.
    """
     
    if st.session_state["current_page_load_key"] != CURRENT_PAGE_KEY:
        st.session_state[CURRENT_PAGE_KEY] = []
        st.session_state["current_page_load_key"] = CURRENT_PAGE_KEY

clear_chat_on_page_change()

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

ทาออกมาแล้วทั้ง 11 สีจะมีเฉดที่ต่างกันตามผิวของเรา เป็นเอกลักษณ์ของเรา

ทาแล้วฟื้นเหมือนติดฟิลเตอร์ที่ผิวแก้มตลอดเวลา น้องสีสวยมากกก ทาเดี่ยว หรือทาผสม คือปัง
""", unsafe_allow_html=True) 

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

PERSIST_DIR = "chroma_db"
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
    except Exception as e:
        llm_ready = False
        st.session_state.setdefault("_internal_errors", []).append(traceback.format_exc())
else:
    llm_ready = False

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

    product_id = FIXED_PRODUCT_ID 
    filter = {"product_id": product_id}

    if not llm_ready or db is None:
        return {"answer": "เนื่องจาก API Key หรือฐานข้อมูลไม่พร้อมใช้งาน ระบบจึงไม่สามารถดึงข้อมูลจาก LLM ได้ กรุณาตรวจสอบการตั้งค่า OPENAI_API_KEY หรือไฟล์ DB.", "sources": []}

    try:
        try:
            retrieved_docs = db.similarity_search(question, k=k, filter=filter)
        except TypeError:
            retrieved_docs = db.similarity_search(query=question, k=k, filter=filter)
    except Exception as e:
        st.session_state.setdefault("_internal_errors", []).append(traceback.format_exc())
        return {"answer": "เกิดข้อผิดพลาดขณะค้นหาข้อมูลในฐานความรู้ กรุณาลองใหม่อีกครั้ง", "sources": []}

    context_text = build_prompt(retrieved_docs) if retrieved_docs else " (ไม่มีข้อมูลที่เกี่ยวข้องในฐานข้อมูลสำหรับสินค้านี้) "

    problem_keywords = ["เสีย", "พัง", "แก้", "ไม่ติด", "ทำยังไง", "ล้างยังไง"]
    is_problem = any(word in question.lower() for word in problem_keywords)

    custom_prompt = prompt_template

    try:
        prompt_obj = PromptTemplate(input_variables=["context", "question"], template=custom_prompt)
        prompt_text = prompt_obj.format(context=context_text, question=question)
        answer = llm.predict(prompt_text)
    except Exception as e:
        st.session_state.setdefault("_internal_errors", []).append(traceback.format_exc())
        return {"answer": "เกิดข้อผิดพลาดขณะเรียกโมเดล LLM กรุณาตรวจสอบการตั้งค่า API หรือสภาวะแวดล้อม", "sources": []}

    sources = []
    for doc in retrieved_docs:
        meta = getattr(doc, "metadata", {}) or {}
        sources.append({"source_file": meta.get("source_file", "unknown"), "chunk_id": meta.get("chunk_id", "unknown")})

    return {"answer": answer, "sources": sources}

def display_chat_message_content(message):
    content = message["content"]
    timestamp = message.get("time", "") 
    
    full_content = f"<span style='font-size: 0.8em; color: gray;'>({timestamp})</span> {content}"
    
    st.markdown(full_content, unsafe_allow_html=True) 

chat_container = st.container()

with chat_container:
    for msg in st.session_state[CURRENT_PAGE_KEY]:
        avatar = "💖" if msg["role"] == "assistant" else "🙋‍♀️" 
        with st.chat_message(msg["role"], avatar=avatar):
            display_chat_message_content(msg)

prompt = st.chat_input("พิมพ์คำถามของลูกค้า...")

if prompt:
    current_time = datetime.now().strftime("%H:%M") 

    st.session_state[CURRENT_PAGE_KEY].append({
        "role": "user", 
        "content": prompt, 
        "sources": [], 
        "time": current_time 
    })
    
    with st.chat_message("user", avatar="🙋‍♀️"): 
        st.markdown(f"<span style='font-size: 0.8em; color: gray;'>({current_time})</span> {prompt}", unsafe_allow_html=True) 

    product_id = FIXED_PRODUCT_ID
    st.session_state["product_context"] = product_id

    with st.chat_message("assistant", avatar="💖"): 
        with st.spinner("กำลังดึงข้อมูลและตอบคำถาม..."):
            resp = answer_question(question=prompt, product_id=product_id)
        
        assistant_time = datetime.now().strftime("%H:%M") 

        st.markdown(f"<span style='font-size: 0.8em; color: gray;'>({assistant_time})</span> {resp['answer']}", unsafe_allow_html=True) 
        
        st.session_state[CURRENT_PAGE_KEY].append({ 
            "role":"assistant",
            "content": resp["answer"],
            "context_used": True,
            "sources": resp.get("sources", []),
            "time": assistant_time 
        })

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
