import streamlit as st
from PIL import Image
import os
# ลบ import: dotenv, langchain.embeddings, langchain.vectorstores, langchain.chat_models, langchain.prompts (เพราะไม่ใช้แล้ว)

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="KAGE Intelligence Hub",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- 2. LOAD ASSETS & HEADER ---
try:
    # สมมติว่าไฟล์นี้มีอยู่จริง
    header_img = Image.open("assets/header_banner.png")
except FileNotFoundError:
    header_img = None 

if header_img:
    st.image(header_img, use_container_width=True)
st.markdown("<br>", unsafe_allow_html=True)

# --- 3. TITLE & SUBHEADER ---
st.title("ยินดีต้อนรับสู่ Project KAGE SEKAI: COLORFUL STAGE")

# นี่คือส่วนข้อความที่ต้องการให้เปลี่ยนเป็น Kanit
st.markdown("""
แพลตฟอร์มรวมเครื่องมือ AI อัจฉริยะสำหรับ **วิเคราะห์ข้อมูลสินค้า** และ **สนับสนุนกลยุทธ์การขาย** ของแบรนด์ KAGE  

คุณสามารถทำได้ดังนี้:
- ใช้งาน **Auto Bot** สำหรับตอบคำถามลูกค้าอัตโนมัติ ตามสินค้าแต่ละประเภท  
- **วิเคราะห์รีวิวลูกค้า** แสดงให้เห็นจุดแข็ง-จุดอ่อนของสินค้า  
- สร้าง **แผนปฏิบัติการเชิงกลยุทธ์ 90 วัน** อย่างรวดเร็ว  

กรุณาเลือกฟีเจอร์ที่ต้องการจากแถบด้านข้าง (Sidebar) เพื่อเริ่มใช้งาน
""")

# --- 4. CUSTOM CSS (FINAL FIX: เพิ่ม Specificity สำหรับ Markdown/List) ---
PASTEL_BLUE = "#AEC6CF" 
ACCENT_BLUE = "#779ECB" 
WHITE = "#FFFFFF" 
LIGHT_PASTEL_BLUE = "#C7DBF0" 
BLACK = "#000000"

st.markdown("""
    <style>
        /* Import Kanit Font */
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600;700&display=swap');
        
        /* 1. GLOBAL FONT FIX (Ultimate Specificity) */
        
        /* Targets the entire app container and all children */
        [data-testid="stAppViewContainer"], 
        .main, 
        .stApp, 
        #root {{
            font-family: 'Kanit', sans-serif !important;
        }}

        /* 1.1 **ULTIMATE FIX FOR MARKDOWN/PARAGRAPHS/LISTS** */
        /* Targets ALL paragraph and list items in the main body (the content you pointed out) */
        .main p, 
        .main ul li, 
        .main ol li,
        [data-testid="stVerticalBlock"] p,
        p {{
            font-family: 'Kanit', sans-serif !important;
            font-weight: 400 !important; /* Normal weight for body text */
            line-height: 1.6; 
            color: {BLACK} !important; /* Ensure color is applied too */
        }}
        
        /* 2. HEADING FIXES (Titles and Headers) */
        h1, h2, h3, h4, h5, h6
        {{
            font-family: 'Kanit', sans-serif !important;
            font-weight: 700 !important; 
        }}
        
        /* 3. CORE COMPONENT FIXES (Inputs, Buttons, Sidebar) */

        /* Targets Input/Select boxes, Buttons, Tabs, etc. */
        div[data-baseweb="select"] *,
        div[data-baseweb="input"] *,
        div[data-baseweb="textarea"] *,
        div[data-baseweb="button"] *,
        button[data-baseweb="tab"] *,
        label p {{
            font-family: 'Kanit', sans-serif !important;
            font-weight: 500 !important;
        }}
        
        /* 4. THEME & BACKGROUND (Theme colors maintained) */
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {{
            background-color: {LIGHT_PASTEL_BLUE} !important; 
            border-right: 1px solid #CCCCCC;
        }}
        
        /* Global Background Color */
        body, #root, .stApp, .main, 
        [data-testid="stAppViewContainer"], 
        [data-testid="stSpinner"] > div {{
            background-color: {WHITE} !important;
        }}

    </style>
    """.format(PASTEL_BLUE=PASTEL_BLUE, WHITE=WHITE, LIGHT_PASTEL_BLUE=LIGHT_PASTEL_BLUE, BLACK=BLACK, ACCENT_BLUE=ACCENT_BLUE), 
    unsafe_allow_html=True
)
