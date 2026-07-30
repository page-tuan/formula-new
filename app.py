import streamlit as st
import pandas as pd
import numpy as np

# 1. 頁面與字體設定
st.set_page_config(page_title="臨床營養品篩選系統", page_icon="🏥", layout="centered")

# 【優化：字體放大】透過 CSS 強制將全站基礎字體放大
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 18px !important; }
    .stMarkdown, .stText, label { font-size: 18px !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

# 2. 資料讀取與清理
@st.cache_data 
def load_data(file_path):
    try:
        df = pd.read_excel(file_path, sheet_name='統整')
        cols = list(df.columns)
        cols[0] = '包裝劑型'
        df.columns = cols
        
        numeric_cols = [
            'kcal/ml', '熱量(kcal)', 'CHO(g)', 'PRO(g)', 'FAT(g)', 
            'CHO(%)', 'PRO(%)', 'FAT(%)', '價位', '每ml/g價錢'
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        df = df.fillna('') # 空白不補字，保持畫面乾淨
        return df
    except Exception as e:
        st.error(f"讀取資料時發生錯誤：{e}")
        return pd.DataFrame()

FILE_NAME = "2026實習生-團膳作業-B4.xlsx"
df = load_data(FILE_NAME)

if df.empty:
    st.stop()

# ==========================================
# 3. 主畫面與聰明搜尋介面
# ==========================================
st.title("🏥 臨床營養品篩選系統")

# 【優化：聰明搜尋】提示使用者可以用空白鍵分隔
keyword = st.text_input("📝 關鍵字搜尋 (可用空白鍵分隔多個關鍵字，如：雀巢 糖尿病)", "")

with st.expander("⚙️ 展開進階篩選 (劑型、分類、營養素、價位)", expanded=False):
    
    # 【優化：新增包裝劑型分類】
    all_forms = sorted(df['包裝劑型'].unique().tolist())
    selected_forms = st.multiselect("📦 包裝劑型 (罐裝/粉末等)", options=all_forms)

    col1, col2 = st.columns(2)
    with col1:
        all_brands = sorted(df['品牌'].unique().tolist())
        selected_brands = st.multiselect("🏢 品牌", options=all_brands)
    with col2:
        all_types = sorted(df['種類'].unique().tolist())
        selected_types = st.multiselect("🥛 種類", options=all_types)
        
    st.markdown("---")
    
    def create_slider(label, col_name, step=1.0):
        min_val = float(df[col_name].min())
        max_val = float(df[col_name].max())
        if min_val == max_val: max_val += 1.0
        return st.slider(label, min_value=min_val, max_value=max_val, value=(min_val, max_val), step=step)

    kcal_range = create_slider("🔥 熱量密度 (kcal/ml)", 'kcal/ml', 0.1)
    pro_range = create_slider("💪 蛋白質比例 (PRO %)", 'PRO(%)', 1.0)
    cho_range = create_slider("🍞 碳水比例 (CHO %)", 'CHO(%)', 1.0)
    fat_range = create_slider("🥑 脂肪比例 (FAT %)", 'FAT(%)', 1.0)
    price_range = create_slider("💰 每 ml/g 價錢", '每ml/g價錢', 0.1)

# ==========================================
# 4. 資料過濾邏輯處理 (聰明關鍵字機制)
# ==========================================
filtered_df = df.copy()

if keyword.strip():
    keywords = keyword.strip().split() # 依空白鍵切割關鍵字
    mask = pd.Series(True, index=filtered_df.index)
    
    for kw in keywords:
        kw_mask = (
            filtered_df['品名'].astype(str).str.contains(kw, case=False, na=False) |
            filtered_df['特色'].astype(str).str.contains(kw, case=False, na=False) |
            filtered_df['疾病/適應症'].astype(str).str.contains(kw, case=False, na=False) |
            filtered_df['品牌'].astype(str).str.contains(kw, case=False, na=False) |
            filtered_df['包裝劑型'].astype(str).str.contains(kw, case=False, na=False) |
            filtered_df['種類'].astype(str).str.contains(kw, case=False, na=False)
        )
        mask = mask & kw_mask # 取交集，必須同時符合所有輸入的關鍵字
    filtered_df = filtered_df[mask]

# 套用其他分類過濾
if selected_forms:
    filtered_df = filtered_df[filtered_df['包裝劑型'].isin(selected_forms)]
if selected_brands:
    filtered_df = filtered_df[filtered_df['品牌'].isin(selected_brands)]
if selected_types:
    filtered_df = filtered_df[filtered_df['種類'].isin(selected_types)]

# 數值過濾
filtered_df = filtered_df[
    (filtered_df['kcal/ml'] >= kcal_range[0]) & (filtered_df['kcal/ml'] <= kcal_range[1]) &
    (filtered_df['PRO(%)'] >= pro_range[0]) & (filtered_df['PRO(%)'] <= pro_range[1]) &
    (filtered_df['CHO(%)'] >= cho_range[0]) & (filtered_df['CHO(%)'] <= cho_range[1]) &
    (filtered_df['FAT(%)'] >= fat_range[0]) & (filtered_df['FAT(%)'] <= fat_range[1]) &
    (filtered_df['每ml/g價錢'] >= price_range[0]) & (filtered_df['每ml/g價錢'] <= price_range[1])
]

# ==========================================
# 5. 結果呈現 (廢除大表格，改為精簡清單 + 專屬資訊卡)
# ==========================================
st.info(f"📊 目前共有 **{len(filtered_df)}** 筆符合條件。")

if len(filtered_df) > 0:
    # 上半部：精簡預覽表
    compact_columns = ['包裝劑型', '品名', 'kcal/ml']
    available_compact_columns = [col for col in compact_columns if col in filtered_df.columns]
    st.dataframe(filtered_df[available_compact_columns], hide_index=True, use_container_width=True)
    
    st.markdown("---")
    
    # 【優化：專屬詳細資訊卡】避免在手機上表格過擠
    st.subheader("💡 查看產品詳細資訊")
    selected_product = st.selectbox("👇 請從篩選結果中選擇要查看的營養品：", filtered_df['品名'].tolist())
    
    if selected_product:
        # 抓取該產品的所有資料
        p_data = filtered_df[filtered_df['品名'] == selected_product].iloc[0]
        
        # 使用容器繪製卡片樣式
        with st.container():
            st.markdown(f"### {p_data['品名']}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**🏢 品牌：** {p_data.get('品牌', '')}")
                st.write(f"**📦 劑型：** {p_data.get('包裝劑型', '')}")
                st.write(f"**🥛 種類：** {p_data.get('種類', '')}")
                st.write(f"**💰 每 ml/g 價位：** {p_data.get('每ml/g價錢', '')}")
            with c2:
                st.write(f"**🔥 熱量密度：** {p_data.get('kcal/ml', '')} kcal/ml")
                st.write(f"**💪 蛋白質：** {p_data.get('PRO(%)', '')} %")
                st.write(f"**🍞 碳水：** {p_data.get('CHO(%)', '')} %")
                st.write(f"**🥑 脂肪：** {p_data.get('FAT(%)', '')} %")
                
            st.markdown("##### 🩺 疾病/適應症")
            st.info(p_data.get('疾病/適應症', '無特別註記'))
            st.markdown("##### ✨ 產品特色")
            st.success(p_data.get('特色', '無特別註記'))
            
    # 下載按鈕維持不變
    st.markdown("---")
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(label="📥 下載完整篩選結果 (CSV)", data=csv, file_name="營養品篩選結果.csv", mime="text/csv")
    
else:
    st.warning("⚠️ 查無符合條件，請嘗試縮減搜尋關鍵字或放寬拉桿數值。")