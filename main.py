import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title='TikTok ad analyzer', layout='wide')
st.title('TikTok广告素材筛选工具 - 最终版')

uploaded_file = st.file_uploader('上传广告消耗Excel', type=['xlsx','xls'])

def to_excel_bytes(df):
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return output

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=0)
    df.columns = df.columns.str.strip()

    # 转换数值
    df['Cost'] = pd.to_numeric(df['Cost'], errors='coerce').fillna(0)
    df['SKU orders'] = pd.to_numeric(df['SKU orders'], errors='coerce').fillna(0)

    # =========================
    # ① 0消耗出单素材
    # =========================
    zero_orders = df[(df['Cost'] == 0) & (df['SKU orders'] > 0)]

    st.subheader('=== 0消耗出单素材 ===')
    st.write(f'共 {len(zero_orders)} 条')

    zero_display = zero_orders[['Video ID','SKU orders','Status']]
    st.dataframe(zero_display)

    st.download_button(
        '下载0消耗出单素材',
        to_excel_bytes(zero_display),
        file_name='zero_cost_orders.xlsx'
    )

    # =========================
    # ② Unavailable 达人统计
    # =========================
    unavailable = zero_orders[
        zero_orders['Status'].astype(str).str.strip() == 'Unavailable'
    ]

    if not unavailable.empty:
        unavailable_summary = (
            unavailable
            .groupby('TikTok account')[['SKU orders']]
            .sum()
            .reset_index()
            .sort_values(by='SKU orders', ascending=False)
        )

        st.subheader('=== Unavailable 达人统计 ===')
        st.dataframe(unavailable_summary)

        st.download_button(
            '下载Unavailable达人统计',
            to_excel_bytes(unavailable_summary),
            file_name='unavailable_summary.xlsx'
        )

    # =========================
    # ③ Learning 高 CTR
    # =========================
    def norm_ctr(x):
        try:
            x = str(x).replace('%','').strip()
            val = float(x)
            if val > 1:
                val = val / 100
            return val
        except:
            return 0

    df['CTR'] = df['Product ad click rate'].apply(norm_ctr)

    learning = df[
        (df['Status'] == 'Learning') &
        (df['CTR'] > 0.03)
    ]

    st.subheader('=== Learning 高CTR素材 ===')
    st.write(f'共 {len(learning)} 条')

    learning_display = learning[
        ['Video ID','Cost','Product ad click rate','SKU orders']
    ]

    st.dataframe(learning_display)

    st.download_button(
        '下载Learning高CTR素材',
        to_excel_bytes(learning_display),
        file_name='learning_high_ctr.xlsx'
    )