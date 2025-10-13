import streamlit as st
from query import answer_question, find_product_by_name

# ---------- 1. Session state ----------
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "product_context" not in st.session_state:
    st.session_state["product_context"] = None

# ---------- 2. Page layout & Theme ----------
st.title("💘 KAGE Chat")
st.set_page_config(page_title="KAGE Support Chat", layout="wide", page_icon="💖")

# CSS ตกแต่งโทนชมพู + bubble chat
st.markdown(
    """
    <style>
    .stApp { background-color: #FF3399; color: #FFFFFF; }
    .chat-box { padding:10px; border-radius:10px; margin:5px; max-width:75%; }
    .user-box { background-color:#FF3399; text-align:right; margin-left:auto; }
    .assistant-box { background-color:#FF3399; text-align:left; margin-right:auto; }
    .chat-container { display:flex; flex-direction:column; }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- 3. Sidebar ----------
import os

logo_path = "/Users/allabout._ca/Downloads/OC4HQAAAAZJREFUAwD9H3BYn5vhaQAAAABJRU5ErkJggg.png.webp"
if os.path.exists(logo_path):
    try:
        st.sidebar.image(logo_path, use_column_width=True)
    except Exception as e:
        st.sidebar.markdown("💖 KAGE Chat (Logo failed to load)")
        st.error(f"Cannot load logo: {e}")
else:
    st.sidebar.markdown("💖 KAGE Chat")

st.sidebar.markdown("💖 **KAGE Support Chat**")
st.sidebar.markdown("### 🧺 เลือกสินค้า")
PRODUCT_MAP = {
    "ฟิลเตอร์บลัช (B001)": "B001",
    "คอลซีลเลอร์ยางลบ & คอเรคเตอร์ยางลบ (C001)": "C001",
    "คุชชั่นเสกผิว (C002)": "C002",
    "ลิปไก่ทอด (L001)": "L001",
    "มาสคาร่าคิ้ว (M001)": "M001",
}
product = st.sidebar.selectbox(
    "สินค้า", options=["(ไม่ระบุ)"] + list(PRODUCT_MAP.keys())
)
if st.sidebar.button("🗑️ Clear Chat"):
    st.session_state["messages"] = []
    st.session_state["product_context"] = None
    st.success("เคลียร์แชทเรียบร้อย ✅")

# ---------- 4. ฟังก์ชันแสดง chat ----------
def display_chat_message(message):
    role = message["role"]
    content = message["content"]
    sources = message.get("sources", [])

    box_class = "user-box" if role=="user" else "assistant-box"
    st.markdown(
        f"<div class='chat-box {box_class}'>{content}</div>", unsafe_allow_html=True
    )

    if sources:
        with st.expander("📄 Retrieved Context / Sources"):
            for s in sources:
                st.markdown(f"- {s['source_file']} (chunk_id: {s['chunk_id']})")

# ---------- 5. แสดง chat เก่า ----------
for msg in st.session_state["messages"]:
    display_chat_message(msg)

# ---------- 6. Chat input ----------
prompt = st.chat_input("พิมพ์คำถามของลูกค้า...")

if prompt:
    # บันทึกข้อความผู้ใช้
    st.session_state["messages"].append({"role": "user", "content": prompt, "sources": []})
    display_chat_message({"role":"user","content":prompt})

    # ---------- อัปเดต product_context ----------
    if product != "(ไม่ระบุ)":
        st.session_state["product_context"] = PRODUCT_MAP.get(product)
    else:
        pid_from_question = find_product_by_name(prompt)
        if pid_from_question:
            st.session_state["product_context"] = pid_from_question

    product_id = st.session_state.get("product_context")

    # ---------- ใช้ spinner ขณะดึงข้อมูล ----------
    with st.chat_message("assistant", avatar="🧜🏻‍♀️"):
        with st.spinner("กำลังดึงข้อมูลและตอบคำถาม..."):
            resp = answer_question(question=prompt, product_id=product_id)

        # ---------- แสดงคำตอบ ----------
        display_chat_message({"role":"assistant","content":resp["answer"], "sources": resp.get("sources", [])})

        # ---------- บันทึกคำตอบลง session ----------
        st.session_state["messages"].append({
            "role":"assistant",
            "content": resp["answer"],
            "context_used": True,
            "sources": resp.get("sources", [])
        })
