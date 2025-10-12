import streamlit as st
import pandas as pd
import json
from io import StringIO

# --- [สำคัญ] นำเข้าคลาสและ Executor จากโปรเจกต์ของคุณ ---
# สมมติว่าไฟล์ทั้งหมดอยู่ใน Directory เดียวกัน
try:
    from tc_complete import ToolExecutor
    from tc_analyze_review import ReviewTools
    from tc_get_product_info import ProductTools, PRODUCT_DB
except ImportError as e:
    st.error(f"เกิดข้อผิดพลาดในการนำเข้าโมดูล: {e}")
    st.error("โปรดตรวจสอบว่าไฟล์ tc_complete.py, tc_analyze_review.py, และ tc_get_product_info.py อยู่ในตำแหน่งที่ถูกต้อง")
    st.stop()

# --- [ส่วนการตั้งค่า] การโหลด Tool และ Executor ---
# ใช้ @st.cache_resource เพื่อให้โหลดแค่ครั้งเดียว
@st.cache_resource
def load_executor():
    """Loads and registers tools into the executor."""
    try:
        executor = ToolExecutor()
        review_tool_instance = ReviewTools()
        product_tool_instance = ProductTools()
        
        executor.register_tools(review_tool_instance)
        executor.register_tools(product_tool_instance)
        
        print("✅ Tools have been successfully registered in Streamlit.")
        return executor
    except Exception as e:
        st.error(f"การลงทะเบียน Tools ล้มเหลว: {e}")
        return None

# --- [ส่วนแสดงผลหลัก] การออกแบบ UI ---
st.set_page_config(
    page_title="Business Insights Dashboard",
    page_icon="✨",
    layout="wide"
)

st.title("✨ Business Insights Dashboard")
st.markdown("เครื่องมือวิเคราะห์ข้อมูลสินค้าและรีวิวลูกค้าด้วย AI สำหรับการตัดสินใจเชิงกลยุทธ์")

# โหลด Executor
executor = load_executor()

if executor is None:
    st.warning("ไม่สามารถเริ่มต้นการทำงานของแอปพลิเคชันได้ เนื่องจาก Tool Executor ไม่พร้อมใช้งาน")
    st.stop()

# --- สร้าง Tabs สำหรับแต่ละฟังก์ชัน ---
tab1, tab2 = st.tabs(["📈 วิเคราะห์รีวิวสินค้า (Review Analysis)", "📦 ข้อมูลสินค้าเชิงกลยุทธ์ (Strategic Product Info)"])

# --- Tab 1: Review Analysis ---
with tab1:
    st.header("วิเคราะห์รีวิวจากลูกค้า")
    st.markdown("อัปโหลดไฟล์ CSV หรือวางข้อความรีวิว เพื่อให้ LLM วิเคราะห์ sentiment, สรุปจุดแข็ง-จุดอ่อน, และให้คำแนะนำเชิงกลยุทธ์")

    product_options = [
        "ลิปไก่ทอด (Syrup Glossy Lip)",
        "ฟิลเตอร์บลัช (Filter Brush)",
        "คอลซีลเลอร์ & คอเรคเตอร์ยางลบ (Fluffy Cloud Concealer & Corrector)",
        "คุชชั่นเสกผิว (Velvet Cloud Cushion)",
        "มาสคาร่าคิ้ว (Truebrow Mybrow Macara)"
    ]
    product_name = st.selectbox(
        "เลือกสินค้าที่ต้องการวิเคราะห์",
        options=product_options
    )

    # --- ส่วนรับข้อมูลรีวิว ---
    st.subheader("ขั้นตอนที่ 1: เพิ่มข้อมูลรีวิว")
    input_method = st.radio("เลือกวิธีการนำเข้ารีวิว:", ("อัปโหลดไฟล์ CSV", "วางข้อความรีวิว"), horizontal=True)
    
    review_texts = []
    temp_csv_path = "temp_uploaded_reviews.csv"

    if input_method == "อัปโหลดไฟล์ CSV":
        uploaded_file = st.file_uploader(
            "เลือกไฟล์ CSV (ต้องมีคอลัมน์ชื่อ 'review')", 
            type=['csv']
        )
        if uploaded_file is not None:
            try:
                # อ่านไฟล์และบันทึกชั่วคราวเพื่อให้ Tool ใช้งานได้
                df = pd.read_csv(uploaded_file)
                if 'review' not in df.columns and '\ufeffreview' not in df.columns:
                     st.error("ไม่พบคอลัมน์ 'review' ในไฟล์ CSV ที่อัปโหลด")
                else:
                    df.to_csv(temp_csv_path, index=False, encoding='utf-8-sig')
                    review_count = len(df)
                    st.success(f"อัปโหลดไฟล์สำเร็จ! พบ {review_count} รีวิว")
                    st.dataframe(df.head(), use_container_width=True)

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")

    else: # วางข้อความ
        pasted_reviews = st.text_area(
            "วางข้อความรีวิว (แต่ละรีวิวให้ขึ้นบรรทัดใหม่)", 
            height=250,
            placeholder="เนื้อลิปดีมาก สีสวย ติดทน\nแพ็กเกจไม่ค่อยแข็งแรงเลย\nส่งของช้า แต่โดยรวมโอเค"
        )
        if pasted_reviews:
            review_texts = [line.strip() for line in pasted_reviews.split('\n') if line.strip()]
            st.info(f"รับข้อมูล {len(review_texts)} รีวิวเรียบร้อยแล้ว")


    # --- ส่วนปุ่มวิเคราะห์ ---
    st.subheader("ขั้นตอนที่ 2: เริ่มการวิเคราะห์")
    analyze_button = st.button("🚀 เริ่มวิเคราะห์รีวิว!", type="primary", use_container_width=True)

    if analyze_button:
        # กำหนด Prompt Engineering หลักก่อน
        expert_prompt = """
        คุณคือ "นักกลยุทธ์ผลิตภัณฑ์และผู้เชี่ยวชาญด้านประสบการณ์ลูกค้า" (Product Strategist & CX Expert)
        ภารกิจของคุณคือการเปลี่ยนรีวิวลูกค้าจำนวนมากให้กลายเป็นรายงานวิเคราะห์เชิงลึกเพื่อการตัดสินใจทางธุรกิจ
        เมื่อวิเคราะห์เสร็จสิ้นด้วย Tool แล้ว โปรดจัดทำรายงานสรุปฉบับผู้บริหาร (Executive Summary) ในรูปแบบ Markdown ดังนี้:
    
        **1. สรุปภาพรวมการวิเคราะห์ (Analysis Overview):**
        - ระบุ Overall Sentiment (บวก/ลบ/กลาง) พร้อมสัดส่วนรีวิวที่สำคัญ
        - **ตารางเปรียบเทียบจุดแข็งและจุดอ่อนหลัก** ที่พบในรีวิว โดยแยกตามแง่มุมที่สำคัญที่สุด 3-5 แง่มุม (เช่น คุณภาพ, ราคา, บรรจุภัณฑ์)
    
        **2. ข้อเสนอแนะเชิงกลยุทธ์ (Strategic Recommendations):**
        ให้คำแนะนำที่ชัดเจน 3-5 ข้อแก่เจ้าของธุรกิจ โดยแยกตามเสาหลักของธุรกิจ:
        - **Product & Packaging Improvement:** (สิ่งที่ควรปรับปรุงทันทีจากจุดอ่อน)
        - **Customer Service & Operation:** (การแก้ไขปัญหาด้านบริการ/การจัดส่ง)
        - **Marketing & Communication Strategy:** (สิ่งที่ควรนำไปสื่อสาร/โปรโมตจากจุดแข็ง)
    
        **ข้อบังคับการตอบ:** ต้องตอบกลับเป็นข้อความ Markdown ที่สวยงามและมีโครงสร้างตามที่กำหนดเท่านั้น ห้ามตอบกลับด้วยผลลัพธ์ JSON ดิบ หรือข้อความใดๆ ที่แสดงถึงการทำงานของ Tool
        """

        # 1. กรณีอัปโหลดไฟล์
        if uploaded_file:
            user_message = f"""
            โปรดใช้ Tool 'analyze_review' เพื่อวิเคราะห์รีวิวสำหรับสินค้า '{product_name}' จากไฟล์ csv_path: '{temp_csv_path}'

            {expert_prompt}
            """
        
        # 2. กรณีวางข้อความ
        elif review_texts:
            reviews_str = "\\n".join(review_texts)
            user_message = f"""
            โปรดใช้ Tool 'analyze_review' เพื่อวิเคราะห์รีวิวต่อไปนี้สำหรับสินค้า '{product_name}' (ข้อมูลรีวิวอยู่ด้านล่าง):
            ---
            {reviews_str}
            ---
        
            {expert_prompt}
            """
        
        else:
            st.warning("กรุณาอัปโหลดไฟล์หรือวางข้อความรีวิวก่อนเริ่มการวิเคราะห์")
            st.stop()

        # --- แสดงผลลัพธ์ ---
        st.markdown("---")
        with st.spinner("🧠 AI กำลังวิเคราะห์รีวิว... อาจใช้เวลาสักครู่"):
            try:
                result = executor.execute_with_tools(user_message)
                cleaned_result = result.replace("<br>", "\n")
            
                # สร้าง Container สำหรับแสดงผลลัพธ์ทั้งหมด
                with st.container(border=True): 
                    st.subheader(f"✨ Executive Summary: วิเคราะห์รีวิวสินค้า {product_name}")
                    st.info("💡 รายงานนี้ผ่านการสังเคราะห์จาก LLM โดยอ้างอิงข้อมูลรีวิวที่ป้อนเข้ามา")
                
                    # แยกรายงานตามหัวข้อหลักใน Prompt
                    # ค้นหาส่วนของ "สรุปภาพรวม" และ "ข้อเสนอแนะเชิงกลยุทธ์"
                
                    if "2. ข้อเสนอแนะเชิงกลยุทธ์" in cleaned_result:
                        # แบ่งข้อความออกเป็นสองส่วนตามหัวข้อหลัก
                        parts = cleaned_result.split("**2. ข้อเสนอแนะเชิงกลยุทธ์ (Strategic Recommendations):**", 1)
                    
                        # 1. ส่วนสรุปภาพรวม
                        summary_part = parts[0]
                        with st.expander("**📊 สรุปภาพรวมการวิเคราะห์ (Analysis Overview)**", expanded=True):
                            st.markdown(summary_part)

                        # 2. ส่วนข้อเสนอแนะ
                        recommendation_part = "**2. ข้อเสนอแนะเชิงกลยุทธ์ (Strategic Recommendations):**" + (parts[1] if len(parts) > 1 else "")
                        with st.expander("**🚀 ข้อเสนอแนะเชิงกลยุทธ์ (Strategic Recommendations)**", expanded=True):
                            st.markdown(recommendation_part)
                    else:
                        # ถ้า LLM ไม่ได้จัดรูปแบบตามที่เราสั่งเป๊ะ ๆ ก็แสดงผลรวมไปเลย
                        st.markdown(cleaned_result)
                    
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดระหว่างการวิเคราะห์: {e}")

# --- Tab 2: Product Information ---
with tab2:
    st.header("ดึงข้อมูลสินค้าเชิงกลยุทธ์")
    st.markdown("เลือก ID สินค้าเพื่อดูรายงานสรุปเชิงลึกที่ AI วิเคราะห์สำหรับวางแผนการตลาดและพัฒนาผลิตภัณฑ์")

    # ดึง Product ID ทั้งหมดจาก PRODUCT_DB ที่โหลดไว้ (ต้องแน่ใจว่า PRODUCT_DB โหลดได้)
    # NOTE: หาก PRODUCT_DB ยังไม่ถูกโหลดใน app.py ให้เพิ่มโค้ดโหลดตรงนี้ หรือปรับ import
    try:
        available_ids = list(PRODUCT_DB.keys())
    except NameError:
        available_ids = ["C002", "B001", "C001", "L001", "M001"] # ใช้รายการสำรองหากโหลดไม่ได้
        st.warning("ไม่สามารถโหลด `PRODUCT_DB` ได้โดยตรง, ใช้รายการสินค้าสำรอง")

    if not available_ids:
        st.error("ไม่สามารถโหลดฐานข้อมูลสินค้าได้")
    else:
        selected_id = st.selectbox("เลือก Product ID ที่ต้องการดูข้อมูล:", options=available_ids)

        if st.button("🔍 สร้างรายงานเชิงกลยุทธ์", type="primary", use_container_width=True):
            # สั่งให้ AI ทำการวิเคราะห์และสรุปผลลัพธ์จาก Tool เป็น Markdown ทันที
            user_message = f"""
            ฉันต้องการข้อมูลเชิงกลยุทธ์ของสินค้า ID {selected_id} เพื่อวางแผนการตลาด
            
            คุณคือ "นักวางแผนกลยุทธ์การตลาดและพัฒนาผลิตภัณฑ์" (Marketing & Product Development Planner)
            ภารกิจของคุณคือการใช้ข้อมูลผลิตภัณฑ์เชิงลึกเพื่อจัดทำ "แผนกลยุทธ์ 90 วัน" ที่พร้อมนำไปปฏิบัติได้จริง
            โปรดใช้ Tool 'get_product_info' เพื่อดึงข้อมูลเชิงกลยุทธ์ทั้งหมดของสินค้า ID {selected_id}
            เมื่อได้รับผลลัพธ์จาก Tool แล้ว ให้สังเคราะห์ข้อมูลและจัดทำรายงาน "Strategic Product Roadmap" ในรูปแบบ Markdown/ตารางที่สวยงาม ดังนี้:
                **1. ข้อมูลสรุปเชิงกลยุทธ์ (Executive Summary):** - **Core Value Proposition:** ระบุคุณค่าหลัก (USP) ที่ AI วิเคราะห์ได้ - **Pricing Flexibility:** วิเคราะห์ดัชนีความยืดหยุ่นราคา และให้ข้อเสนอแนะ 1 ข้อในการใช้ประโยชน์จากช่องว่างราคานั้น - **Personal Color Coverage:** สรุปว่าสินค้าครอบคลุมกลุ่ม Personal Color ใดมากที่สุด/น้อยที่สุด และผลกระทบต่อตลาดเป้าหมาย
                **2. แผนปฏิบัติการ 90 วัน (90-Day Action Plan):** จัดทำแผนปฏิบัติการโดยสรุปในรูปแบบตาราง Markdown 3 คอลัมน์ (กิจกรรมหลัก, ผลลัพธ์ที่คาดหวัง, KPI/Metrics) โดยเน้นกิจกรรมที่แก้ไขจุดอ่อนและส่งเสริมจุดแข็งของผลิตภัณฑ์ - กำหนดกลยุทธ์ด้านการตลาดดิจิทัล 2 ข้อ (เช่น Influencer Campaign, SEO) - กำหนดกลยุทธ์ด้านผลิตภัณฑ์ 1 ข้อ (เช่น การขยายเฉดสี, การปรับปรุงบรรจุภัณฑ์)
            **ข้อบังคับการตอบ:** ต้องตอบกลับเป็นภาษาไทยที่อยู่ในรูปแบบรายงานฉบับสมบูรณ์ในรูปแบบ Markdown/ตารางเท่านั้น ห้ามแสดงผลลัพธ์ JSON ดิบ ข้อความการทำงานของ Tool หรือข้อความใดๆ ที่ไม่ใช่ส่วนหนึ่งของรายงาน  
            """
            
            with st.spinner(f"🧠 AI กำลังดึงข้อมูลและวิเคราะห์..."):
                try:
                    result_from_llm = executor.execute_with_tools(user_message)

                    st.markdown("---")
            
                    # สร้าง Container สำหรับผลลัพธ์ทั้งหมด
                    with st.container(border=True):
                        st.subheader(f"✨ Strategic Product Roadmap: **ID: {selected_id}**")
                        st.success("✅ รายงานฉบับสมบูรณ์ถูกสังเคราะห์โดย AI เพื่อวางแผนกลยุทธ์")
                
                        cleaned_result = result_from_llm.replace("<br>", "\n")
                
                        # 1. ดึง Core Value Proposition มาแสดงในรูปแบบ Metric/ตารางย่อ
                        try:
                            # ค้นหาส่วน Executive Summary เพื่อแยก Core Value และ Pricing Flexibility (ถ้า LLM สร้างตาราง)
                            if "Core Value Proposition" in cleaned_result:
                        
                                # แยกรายงานตามหัวข้อหลักใน Prompt (Executive Summary และ 90-Day Plan)
                                executive_part, action_part = cleaned_result.split("**2. แผนปฏิบัติการ 90 วัน", 1)
                        
                                # A. แสดง Executive Summary (ใช้ st.dataframe หรือ st.expander)
                                with st.expander("📊 Executive Summary (ข้อมูลเชิงกลยุทธ์หลัก)", expanded=True):
                                    st.markdown(executive_part)

                                # B. แสดง 90-Day Action Plan
                                st.divider()
                                with st.expander("🚀 แผนปฏิบัติการ 90 วัน (90-Day Action Plan)", expanded=True):
                                    st.markdown("**2. แผนปฏิบัติการ 90 วัน" + action_part)

                            else:
                                # Fallback: แสดงผลลัพธ์รวม
                                st.markdown(cleaned_result)

                        except:
                            # Fallback: หากการแยกส่วนล้มเหลว (แสดงผลรวม)
                            st.markdown(cleaned_result)

                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")