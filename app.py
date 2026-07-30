import streamlit as st
import pandas as pd
import numpy as np

# 頁面基本設定 (需放在所有 streamlit 語法最上方)
st.set_page_config(
    page_title="臨床營養品分類篩選系統",
    page_icon="🏥",
    layout="wide"
)

# 1. 資料讀取與清理
@st.cache_data # 使用快取避免每次操作都重新讀取 Excel，提升效能
def load_data(file_path):
    try:
        # 讀取「統整」分頁
        df = pd.read_excel(file_path, sheet_name='統整')
        
        # 重新命名第一欄為「包裝劑型」
        cols = list(df.columns)
        cols[0] = '包裝劑型'
        df.columns = cols
        
        # 定義需要轉換為數值型態的欄位
        numeric_cols = [
            'kcal/ml', '滲透壓', '熱量(kcal)', 'CHO(g)', 'PRO(g)', 'FAT(g)', 
            '膳食纖維(g)', '鈉(mg)', '鉀(mg)', '磷(mg)', 'CHO(%)', 'PRO(%)', 
            'FAT(%)', '價位', '每ml/g價錢'
        ]
        
        # 確保數值欄位型態正確，若有無法轉換的字串則轉為 NaN，再補為 0
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        # 將其他非數值欄位的空值 (NaN) 填上「未分類」
        df = df.fillna('未分類')
        
        return df
    except Exception as e:
        st.error(f"讀取資料時發生錯誤：{e}")
        return pd.DataFrame()

# 載入資料 (請確保 Excel 檔案與此 app.py 在同一資料夾)
FILE_NAME = "2026實習生-團膳作業-B4.xlsx"
df = load_data(FILE_NAME)

if df.empty:
    st.stop() # 若資料空白則停止執行後續程式碼

# ==========================================
# 2. 側邊欄篩選器 (Sidebar)
# ==========================================
st.sidebar.header("🔍 篩選條件")
st.sidebar.markdown("請設定您的搜尋條件：")

# 關鍵字搜尋：涵蓋「品名」、「特色」或「疾病/適應症」
keyword = st.sidebar.text_input("📝 關鍵字搜尋 (品名/特色/適應症)", "")

# 下拉式多選單：「品牌」與「種類」
all_brands = sorted(df['品牌'].unique().tolist())
all_types = sorted(df['種類'].unique().tolist())

selected_brands = st.sidebar.multiselect("🏢 品牌 (可多選)", options=all_brands)
selected_types = st.sidebar.multiselect("🥛 種類 (可多選)", options=all_types)

# 數值區間滑桿：「熱量密度」與「蛋白質比例」 (自動抓取資料庫最大最小值)
# 確保抓出的 max/min 是 float 型態以相容 slider
min_kcal = float(df['kcal/ml'].min())
max_kcal = float(df['kcal/ml'].max())
# 給予預設的最大最小值，避免全站資料皆相同導致 min=max 的報錯
if min_kcal == max_kcal: 
    max_kcal += 1.0

kcal_range = st.sidebar.slider(
    "🔥 熱量密度區間 (kcal/ml)",
    min_value=min_kcal,
    max_value=max_kcal,
    value=(min_kcal, max_kcal),
    step=0.1
)

min_pro = float(df['PRO(%)'].min())
max_pro = float(df['PRO(%)'].max())
if min_pro == max_pro:
    max_pro += 1.0

pro_range = st.sidebar.slider(
    "💪 蛋白質比例區間 (PRO(%))",
    min_value=min_pro,
    max_value=max_pro,
    value=(min_pro, max_pro),
    step=1.0
)


# ==========================================
# 資料過濾邏輯處理
# ==========================================
filtered_df = df.copy()

# 根據關鍵字過濾
if keyword.strip():
    # 使用 regex=False 與 case=False 實現不分大小寫的關鍵字搜尋
    mask = (
        filtered_df['品名'].astype(str).str.contains(keyword, case=False, na=False) |
        filtered_df['特色'].astype(str).str.contains(keyword, case=False, na=False) |
        filtered_df['疾病/適應症'].astype(str).str.contains(keyword, case=False, na=False)
    )
    filtered_df = filtered_df[mask]

# 根據品牌過濾
if selected_brands:
    filtered_df = filtered_df[filtered_df['品牌'].isin(selected_brands)]

# 根據種類過濾
if selected_types:
    filtered_df = filtered_df[filtered_df['種類'].isin(selected_types)]

# 根據數值區間過濾
filtered_df = filtered_df[
    (filtered_df['kcal/ml'] >= kcal_range[0]) & 
    (filtered_df['kcal/ml'] <= kcal_range[1])
]
filtered_df = filtered_df[
    (filtered_df['PRO(%)'] >= pro_range[0]) & 
    (filtered_df['PRO(%)'] <= pro_range[1])
]


# ==========================================
# 3. 主畫面資料呈現
# ==========================================
st.title("🏥 臨床營養品分類篩選系統")
st.markdown("快速查閱並尋找適合患者的臨床營養配方。")

# 顯示符合條件的總筆數
st.info(f"📊 經過篩選後，目前共有 **{len(filtered_df)}** 筆符合條件的營養品。")

if len(filtered_df) > 0:
    st.subheader("📌 快速預覽 (精簡資料)")
    # 定義精簡版資料表的欄位
    compact_columns = [
        '包裝劑型', '品牌', '品名', '種類', 
        '疾病/適應症', 'kcal/ml', 'PRO(%)', '價位'
    ]
    # 確保所選欄位確實存在於資料表中
    available_compact_columns = [col for col in compact_columns if col in filtered_df.columns]
    
    # 呈現精簡版 DataFrame 並隱藏預設的 Index 欄位
    st.dataframe(filtered_df[available_compact_columns], hide_index=True, use_container_width=True)
    
    st.markdown("---")
    
    # 可展開的區塊，讓使用者查看完整所有欄位的詳細資料
    with st.expander("🔎 點此展開查看【完整詳細資料表】"):
        st.dataframe(filtered_df, hide_index=True, use_container_width=True)
else:
    st.warning("⚠️ 查無符合條件的營養品，請嘗試放寬您的篩選條件。")