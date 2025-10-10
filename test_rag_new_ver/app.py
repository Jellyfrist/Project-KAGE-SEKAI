import streamlit as st
from query import answer_question

st.set_page_config(page_title="KAGE Support Chat (RAG)", layout="wide")
st.title("KAGE — Support Chat (RAG Prototype)")

product = st.selectbox("เลือกสินค้า (หรือไม่ระบุ)", options=["(ไม่ระบุ)","B001","C001","C002","L001","M001"])
q = st.text_area("พิมพ์คำถามของลูกค้า")

if st.button("ถาม"):
    with st.spinner("กำลังดึงข้อมูล..."):
        resp = answer_question(question=q, product_id=product if product != "(ไม่ระบุ)" else None)
    st.markdown("**คำตอบ:**")
    st.write(resp["answer"])
    st.markdown("**แหล่งที่มา:**")
    for s in resp["sources"]:
        st.write(f"- {s['source_file']} (chunk_id: {s['chunk_id']})")