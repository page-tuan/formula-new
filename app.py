import streamlit as st
import pandas as pd
import numpy as np

# 1. 頁面基本設定 (針對手機版優化：改為置中 centered，營造 App 感)
st.set_page_config(
    page_title="臨床營養品篩選系統",
    page_icon="🏥",
    layout="centered" 
)

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
                
        df = df.fillna('未分類')
        return df
    except Exception as e:
        st.error(f"讀取資料時發生錯誤：{e}")
        return pd.DataFrame()

FILE_NAME = "2026實習生-團膳作業-B4.xlsx"
df = load_data(FILE_NAME)

if df.empty:
    st.stop()

# ==========================================
# 3. 主畫面與搜尋介面 (廢除側邊欄，改為手機友善動線)
# ==========================================
st.title("🏥 臨床營養品篩選系統")
st.markdown("快速查閱並尋找適合患者的臨床營養配方。")

# 最常用的功能放最外面：關鍵字搜尋
keyword = st.text_input("📝 關鍵字搜尋 (品名/特色/適應症)", "")

# 使用摺疊面板收納大量篩選器，避免手機版畫面過長
with st.expander("⚙️ 展開進階條件 (分類、營養素、價位)", expanded=False):
    
    # 建立兩欄式排列，節省垂直空間
    col1, col2 = st.columns(2)
    with col1:
        all_brands = sorted(df['品牌'].unique().tolist())
        selected_brands = st.multiselect("🏢 品牌 (可多選)", options=all_brands)
    with col2:
        all_types = sorted(df['種類'].unique().tolist())
        selected_types = st.multiselect("🥛 種類 (可多選)", options=all_types)
        
    st.markdown("---")
    st.markdown("##### 📊 數值區間設定")
    
    # 建立動態抓取極值的拉桿輔助函式
    def create_slider(label, col_name, step=1.0):
        min_val = float(df[col_name].min())
        max_val = float(df[col_name].max())
        if min_val == max_val: max_val += 1.0
        return st.slider(label, min_value=min_val, max_value=max_val, value=(min_val, max_val), step=step)

    # 依序產出五個過濾拉桿
    kcal_range = create_slider("🔥 熱量密度 (kcal/ml)", 'kcal/ml', 0.1)
    pro_range = create_slider("💪 蛋白質比例 (PRO %)", 'PRO(%)', 1.0)
    cho_range = create_slider("🍞 碳水比例 (CHO %)", 'CHO(%)', 1.0)
    fat_range = create_slider("🥑 脂肪比例 (FAT %)", 'FAT(%)', 1.0)
    price_range = create_slider("💰 每 ml/g 價錢", '每ml/g價錢', 0.1)

# ==========================================
# 4. 資料過濾邏輯處理
# ==========================================
filtered_df = df.copy()

if keyword.strip():
    mask = (
        filtered_df['品名'].astype(str).str.contains(keyword, case=False, na=False) |
        filtered_df['特色'].astype(str).str.contains(keyword, case=False, na=False) |
        filtered_df['疾病/適應症'].astype(str).str.contains(keyword, case=False, na=False)
    )
    filtered_df = filtered_df[mask]

if selected_brands:
    filtered_df = filtered_df[filtered_df['品牌'].isin(selected_brands)]
if selected_types:
    filtered_df = filtered_df[filtered_df['種類'].isin(selected_types)]

# 數值區間過濾 (包含新加入的三大營養素與價位)
filtered_df = filtered_df[
    (filtered_df['kcal/ml'] >= kcal_range[0]) & (filtered_df['kcal/ml'] <= kcal_range[1]) &
    (filtered_df['PRO(%)'] >= pro_range[0]) & (filtered_df['PRO(%)'] <= pro_range[1]) &
    (filtered_df['CHO(%)'] >= cho_range[0]) & (filtered_df['CHO(%)'] <= cho_range[1]) &
    (filtered_df['FAT(%)'] >= fat_range[0]) & (filtered_df['FAT(%)'] <= fat_range[1]) &
    (filtered_df['每ml/g價錢'] >= price_range[0]) & (filtered_df['每ml/g價錢'] <= price_range[1])
]

# ==========================================
# 5. 結果呈現與匯出
# ==========================================
st.info(f"📊 經過篩選後，目前共有 **{len(filtered_df)}** 筆符合條件。")

if len(filtered_df) > 0:
    # 手機版最佳化：精簡顯示最關鍵欄位，避免表格過寬
    compact_columns = ['品名', 'kcal/ml', 'PRO(%)', '每ml/g價錢']
    available_compact_columns = [col for col in compact_columns if col in filtered_df.columns]
    
    st.dataframe(filtered_df[available_compact_columns], hide_index=True, use_container_width=True)
    
    with st.expander("🔎 展開查看【完整詳細資料表】"):
        st.dataframe(filtered_df, hide_index=True, use_container_width=True)
        
    # 一鍵下載功能
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(label="📥 下載篩選結果 (CSV)", data=csv, file_name="營養品篩選結果.csv", mime="text/csv")
    
else:
    st.warning("⚠️ 查無符合條件的營養品，請嘗試在上方⚙️展開進階條件，並放寬您的篩選數值。")