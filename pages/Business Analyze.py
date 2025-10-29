import streamlit as st
import pandas as pd
import json
from io import StringIO

try:
    from tc_complete import ToolExecutor
    from tc_analyze_review import ReviewTools
    from tc_get_product_info import ProductTools, PRODUCT_DB
except ImportError as e:
    st.error(f"เกิดข้อผิดพลาดในการนำเข้าโมดูล: {e}")
    st.error("โปรดตรวจสอบว่าไฟล์ tc_complete.py, tc_analyze_review.py, และ tc_get_product_info.py อยู่ในตำแหน่งที่ถูกต้อง")
    st.stop()

@st.cache_resource
def load_executor():
    """Load and register tools into the executor."""
    try:
        executor = ToolExecutor()
        review_tool_instance = ReviewTools()
        product_tool_instance = ProductTools()
        
        executor.register_tools(review_tool_instance)
        executor.register_tools(product_tool_instance)
        
        print("✅ Tools have been successfully registered in Streamlit.")
        return executor
    except Exception as e:
        st.error(f"Tool registration failed: {e}")
        return None

st.set_page_config(
    page_title="Business Insights Dashboard",
    page_icon="✨",
    layout="wide"
)

st.title("✨ KAGE Business Insights Dashboard")
st.markdown("วิเคราะห์รีวิวลูกค้าและข้อมูลสินค้าอย่างชาญฉลาด เพื่อขับเคลื่อนกลยุทธ์ทางธุรกิจของคุณ")

executor = load_executor()

if executor is None:
    st.warning("ไม่สามารถเริ่มต้นการทำงานของแอปพลิเคชันได้ เนื่องจาก Tool Executor ไม่พร้อมใช้งาน")
    st.stop()

tab1, tab2 = st.tabs(["📈 วิเคราะห์รีวิวสินค้า (Review Analysis)", "📦 ข้อมูลสินค้าเชิงกลยุทธ์ (Strategic Product Info)"])

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

    st.subheader("ขั้นตอนที่ 1: เพิ่มข้อมูลรีวิว")
    input_method = st.radio("เลือกวิธีการนำเข้ารีวิว:", ("อัปโหลดไฟล์ CSV", "วางข้อความรีวิว"), horizontal=True)
    
    review_texts = []
    uploaded_file = None
    temp_csv_path = "temp_uploaded_reviews.csv"

    if input_method == "อัปโหลดไฟล์ CSV":
        uploaded_file = st.file_uploader(
            "เลือกไฟล์ CSV (ต้องมีคอลัมน์ชื่อ 'review')", 
            type=['csv']
        )
        if uploaded_file is not None:
            try:
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

    else:  
        pasted_reviews = st.text_area(
            "วางข้อความรีวิว (แต่ละรีวิวให้ขึ้นบรรทัดใหม่)", 
            height=250,
            placeholder="เนื้อลิปดีมาก สีสวย ติดทน\nแพ็กเกจไม่ค่อยแข็งแรงเลย\nส่งของช้า แต่โดยรวมโอเค"
        )
        if pasted_reviews:
            review_texts = [line.strip() for line in pasted_reviews.split('\n') if line.strip()]
            st.info(f"รับข้อมูล {len(review_texts)} รีวิวเรียบร้อยแล้ว")

    st.subheader("ขั้นตอนที่ 2: เริ่มการวิเคราะห์")
    analyze_button = st.button("🚀 เริ่มวิเคราะห์รีวิว!", type="primary", use_container_width=True)

    if analyze_button:

        expert_prompt = """
        คุณคือ **นักวิเคราะห์เชิงกลยุทธ์ผลิตภัณฑ์ (Product Strategy Analyst)** ภารกิจของคุณคือการสรุปรีวิวลูกค้าจำนวนมากให้เป็น “รายงานวิเคราะห์เชิงธุรกิจฉบับเดียว”  
        ที่มีทั้งส่วนสรุปภาพรวมและข้อเสนอแนะเชิงกลยุทธ์  
        ห้ามสร้าง Executive Summary แยกหรือซ้ำอีกชุดหนึ่ง

        **ให้ตอบเป็นรายงาน Markdown เพียงชุดเดียวเท่านั้น** ห้ามมีการสรุปซ้ำตอนท้าย  
        ห้ามมีข้อความนอกเหนือจากรายงาน  
        ห้ามใช้ `<br>` ให้ใช้การขึ้นบรรทัดจริงภายในเซลล์แทน

        ### รูปแบบรายงานที่ต้องการ:
        #### 1. สรุปภาพรวมการวิเคราะห์ (Analysis Overview)
        - แนวโน้มความรู้สึกลูกค้า: บวก / กลาง / ลบ
        - สรุปประเด็นสำคัญในเชิงธุรกิจ

        | แง่มุม (Aspect) | จุดแข็ง (Positive) | จุดอ่อน (Negative) |
        |------------------|---------------------|----------------------|
        | ... | ... | ... |

        #### 2. ข้อเสนอแนะเชิงกลยุทธ์ (Strategic Recommendations)
        | หัวข้อ (Topic) | ข้อเสนอแนะ (Actionable Recommendation) | ผลที่คาดหวัง (Expected KPI) |
        |-----------------|------------------------------------------|-------------------------------|
        | Product & Packaging | ... | ... |
        | Marketing & Communication | ... | ... |
        | Customer Service & Operation | ... | ... |

        **เงื่อนไขเพิ่มเติม:**
        - ใช้ภาษาทางการในเชิงธุรกิจ  
        - ห้ามแสดง JSON, log, หรือข้อมูลระบบ
        - ต้องตอบเป็นภาษาไทย 100%
        """


        if uploaded_file:
            user_message = f"""
            โปรดใช้ Tool 'analyze_review' เพื่อวิเคราะห์รีวิวสำหรับสินค้า '{product_name}' จากไฟล์ csv_path: '{temp_csv_path}'

            {expert_prompt}
            """
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

        st.markdown("---")
        st.subheader(f"✨ Executive Summary: วิเคราะห์รีวิวสินค้า {product_name}")
        st.info("💡 รายงานนี้ผ่านการสังเคราะห์จาก LLM โดยอ้างอิงข้อมูลรีวิวที่ป้อนเข้ามา")
        
        with st.spinner("🧠 AI กำลังวิเคราะห์รีวิว... อาจใช้เวลาสักครู่"):
            try:
                result = executor.execute_with_tools(user_message)
                header_1 = "1. สรุปภาพรวมการวิเคราะห์ (Analysis Overview)"
                header_2 = "2. ข้อเสนอแนะเชิงกลยุทธ์ (Strategic Recommendations)"
                    
                start_1 = result.find(header_1)
                start_2 = result.find(header_2)

                with st.expander("📊 Analysis Overview", expanded=True):
                    if start_1 != -1 and start_2 != -1:
                        st.markdown(result[start_1:start_2], unsafe_allow_html=True)
                    else:
                        st.markdown(result, unsafe_allow_html=True)

                with st.expander("🚀 Strategic Recommendations", expanded=True):
                    if start_2 != -1:
                        st.markdown(result[start_2:], unsafe_allow_html=True)
                    else:
                        st.markdown(result, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดระหว่างการวิเคราะห์: {e}")

with tab2:
    st.header("📦 ข้อมูลสินค้าเชิงกลยุทธ์")
    st.markdown(
        "เลือก ID สินค้าเพื่อดูรายงานเชิงลึก: วิเคราะห์จุดแข็ง-จุดอ่อน, ช่วงราคา, การครอบคลุม Personal Color และข้อเสนอแนะเชิงกลยุทธ์"
    )

    available_ids = list(PRODUCT_DB.keys())
    selected_id = st.selectbox("เลือก Product ID:", options=available_ids)

    if st.button("🔍 สร้างรายงานเชิงกลยุทธ์", key="tab2_generate_report", type="primary", use_container_width=True):
        product_tool_instance = ProductTools()
        product_info = product_tool_instance.get_product_info(selected_id)

        if "error" in product_info:
            st.error(product_info["error"])
        else:
            st.success("✅ ดึงข้อมูลเชิงกลยุทธ์เรียบร้อยแล้ว")

            core_value = product_info["strategic_value_proposition"]
            price_flex = product_info["pricing_flexibility_index"]
            total_shades = product_info["total_number_of_shades"]
            personal_color = product_info["personal_color_coverage"]

            exec_summary_md = f"""
            - **💎 Core Value Proposition:** {core_value}
            - **💰 Pricing Flexibility:** {price_flex}
            - **🎨 Total Number of Shades:** {total_shades}
            """
            with st.expander("📊 Executive Summary", expanded=True):
                st.markdown(exec_summary_md)

            pc_rows = []
            for pc_group, shades_list in personal_color.items():
                for shade in shades_list:
                    if ": " in shade:
                        name, desc = shade.split(": ", 1)
                    else:
                        name, desc = shade, ""
                    pc_rows.append({
                        "Personal Color": pc_group,
                        "Shade Name": name,
                        "Description": desc[:50]+"..."
                    })
            df_pc = pd.DataFrame(pc_rows)
            with st.expander("🎨 Personal Color Coverage", expanded=True):
                st.dataframe(df_pc.style.set_properties(**{'text-align': 'left'}), use_container_width=True)

            prompt_90day = f"""
            คุณคือ **นักวางแผนกลยุทธ์การตลาดและผลิตภัณฑ์** ใช้ข้อมูลเชิงกลยุทธ์สินค้า ID {selected_id} เพื่อสร้าง **90-Day Action Plan** Markdown ตาราง 3 คอลัมน์:
            1. กิจกรรมหลัก  
            2. ผลลัพธ์ที่คาดหวัง  
            3. KPI/Metrics

            ข้อมูลสินค้า:
            - Core Value Proposition: {core_value}
            - Pricing Flexibility: {price_flex}
            - Personal Color Coverage: {list(personal_color.keys())}

            **ข้อบังคับ:** - ตอบเป็น Markdown ตารางเท่านั้น  
            - ใช้ภาษาไทยเชิงธุรกิจ
            """
            
            with st.spinner("🧠 AI กำลังสร้าง 90-Day Action Plan..."):
                try:
                    action_plan_md = executor.execute_with_tools(prompt_90day)
                    with st.expander("🚀 90-Day Action Plan", expanded=True):
                        st.markdown(action_plan_md, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดขณะสร้าง 90-Day Action Plan: {e}")

PASTEL_BLUE = "#AEC6CF" 
ACCENT_BLUE = "#779ECB" 
WHITE = "#FFFFFF" 
LIGHT_PASTEL_BLUE = "#C7DBF0" 
BLACK = "#000000"

st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600;700&display=swap');
        
        /* Global font override */
        body, #root, .stApp, .main, 
        [data-testid="stAppViewContainer"], 
        .main * {{
            font-family: 'Kanit', sans-serif !important;
            color: {BLACK} !important; 
        }}

        /* Paragraphs and markdown text */
        p,
        div[data-testid="stVerticalBlock"] p,
        [data-testid="stMetricValue"], 
        [data-testid="stAlert"] p {{
            font-family: 'Kanit', sans-serif !important;
            font-weight: 400 !important;
        }}

        /* Headings */
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Kanit', sans-serif !important;
            font-weight: 700 !important; 
        }}

        /* Labels & metrics */
        label p,
        [data-testid*="stForm"] label p,
        [data-testid*="stSelectbox"] label p,
        [data-testid="stMetricLabel"] p {{
            font-family: 'Kanit', sans-serif !important;
            font-weight: 500 !important; 
        }}
        
        /* Dataframe font fix */
        .stDataFrame table, 
        .stDataFrame table th, 
        .stDataFrame table td {{
            font-family: 'Kanit', sans-serif !important;
        }}
        
        /* Inputs, selectbox, radio, buttons */
        div[data-baseweb="select"] *,
        div[data-baseweb="input"] *,
        div[data-baseweb="textarea"] *,
        div[data-baseweb="radio"] *,
        div[data-baseweb="button"] * {{
            font-family: 'Kanit', sans-serif !important;
        }}
        
        /* Tabs */
        button[data-baseweb="tab"] * {{
            font-family: 'Kanit', sans-serif !important;
        }}
        
        /* Expanders */
        [data-testid="stExpander"] div[role="button"] p {{
            font-family: 'Kanit', sans-serif !important;
            font-weight: 600 !important; 
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: {LIGHT_PASTEL_BLUE} !important; 
            border-right: 1px solid #CCCCCC;
        }}
        
        /* Global background */
        body, #root, .stApp, .main, 
        [data-testid="stAppViewContainer"], 
        [data-testid="stSpinner"] > div {{
            background-color: {WHITE} !important;
        }}

    </style>
    """, 
    unsafe_allow_html=True
)
