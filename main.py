import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title='TikTok自动投流分析系统', layout='wide')
st.title('TikTok自动投流分析系统')

uploaded_file = st.file_uploader('上传广告消耗Excel', type=['xlsx', 'xls'])

REQUIRED_COLUMNS = ['Video ID', 'Cost', 'Product ad click rate', 'SKU orders', 'Status', 'TikTok account', 'Creative type']


def to_excel_bytes(df):
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return output


def norm_ctr(x):
    try:
        x = str(x).replace('%', '').strip()
        val = float(x)
        if val > 1:
            val = val / 100
        return val
    except Exception:
        return 0


def get_recommendation(row):
    cost = row['Cost']
    orders = row['SKU orders']
    status = str(row['Status']).strip()
    ctr = row['CTR']

    if cost == 0 and orders > 0:
        return '自然爆款｜优先关注'
    if status == 'Authorization needed' and orders > 0:
        return '需授权｜优先联系达人'
    if status == 'Unavailable' and orders > 0:
        return '达人不可用｜检查合作/授权状态'
    if status == 'Learning' and ctr > 0.03 and orders > 0:
        return 'Learning高CTR有单｜可测试放量'
    if status == 'Learning' and ctr > 0.03 and orders == 0:
        return '高CTR无单｜观察转化问题'
    return '普通素材｜暂不处理'


def get_contact_info(g):
    if 'Contact info' in g.columns:
        vals = g['Contact info'].dropna().astype(str).str.strip()
        vals = vals[vals != '']
        if not vals.empty:
            return ', '.join(vals.unique())
    return '表格未提供联系方式'


if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name=0)
        df.columns = df.columns.str.strip()

        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            st.error(f'缺少必要列: {missing}')
        else:
            df['Cost'] = pd.to_numeric(df['Cost'], errors='coerce').fillna(0)
            df['SKU orders'] = pd.to_numeric(df['SKU orders'], errors='coerce').fillna(0)
            df['CTR'] = df['Product ad click rate'].apply(norm_ctr)
            df['Status_clean'] = df['Status'].astype(str).str.strip()

            # 排除 Creative type = Product card
            df = df[df['Creative type'].astype(str).str.strip() != 'Product card']

            zero_orders = df[(df['Cost'] == 0) & (df['SKU orders'] > 0)]
            unavailable = zero_orders[zero_orders['Status_clean'] == 'Unavailable']
            auth_needed = zero_orders[zero_orders['Status_clean'] == 'Authorization needed']
            learning = df[(df['Status_clean'] == 'Learning') & (df['CTR'] > 0.03)]
            contact_creators = zero_orders[
                zero_orders['Status_clean'].isin(['Unavailable', 'Authorization needed'])
            ]

            # ========== 核心指标卡片 ==========
            c1, c2, c3, c4 = st.columns(4)
            c1.metric('0消耗出单素材', len(zero_orders))
            c2.metric('0消耗总订单', int(zero_orders['SKU orders'].sum()))
            c3.metric('Learning高CTR素材', len(learning))
            c4.metric('需联系达人数', contact_creators['TikTok account'].nunique())

            st.divider()
            # ========== ① 0消耗出单素材 ==========
            st.subheader('=== 0消耗出单素材 ===')
            st.write(f'共 {len(zero_orders)} 条')
            zero_display = zero_orders[['Video ID', 'SKU orders', 'Status']]
            st.dataframe(zero_display, use_container_width=True)
            st.download_button('下载0消耗出单素材', to_excel_bytes(zero_display), file_name='zero_cost_orders.xlsx')

            # ========== ② Unavailable 达人统计 ==========
            if not unavailable.empty:
                unavailable_summary = (
                    unavailable.groupby('TikTok account')[['SKU orders']]
                    .sum().reset_index()
                    .sort_values(by='SKU orders', ascending=False)
                )
                st.subheader('=== Unavailable 达人统计 ===')
                st.dataframe(unavailable_summary, use_container_width=True)
                st.download_button('下载Unavailable达人统计', to_excel_bytes(unavailable_summary), file_name='unavailable_summary.xlsx')

            # ========== ③ Authorization needed 达人统计 ==========
            if not auth_needed.empty:
                auth_summary = (
                    auth_needed.groupby('TikTok account')[['SKU orders']]
                    .sum().reset_index()
                    .sort_values(by='SKU orders', ascending=False)
                )
                st.subheader('=== Authorization needed 达人统计 ===')
                st.dataframe(auth_summary, use_container_width=True)
                st.download_button('下载Authorization needed达人统计', to_excel_bytes(auth_summary), file_name='auth_needed_summary.xlsx')

            # ========== ④ Learning 高CTR素材 ==========
            st.subheader('=== Learning 高CTR素材 ===')
            st.write(f'共 {len(learning)} 条')
            learning_display = learning[['Video ID', 'Cost', 'Product ad click rate', 'SKU orders']]
            st.dataframe(learning_display, use_container_width=True)
            st.download_button('下载Learning高CTR素材', to_excel_bytes(learning_display), file_name='learning_high_ctr.xlsx')
            # ========== ⑤ 投放建议总表 ==========
            df['Recommendation'] = df.apply(get_recommendation, axis=1)
            rec_filtered = df[df['Recommendation'] != '普通素材｜暂不处理']
            st.subheader('=== 投放建议总表 ===')
            st.write(f'共 {len(rec_filtered)} 条（已过滤普通素材）')
            rec_display = rec_filtered[['Video ID', 'Cost', 'Product ad click rate', 'SKU orders', 'Status', 'TikTok account', 'Recommendation']]
            st.dataframe(rec_display, use_container_width=True)
            st.download_button('下载投放建议总表', to_excel_bytes(rec_display), file_name='recommendation_table.xlsx')

            # ========== ⑥ 优先联系达人名单 ==========
            if not contact_creators.empty:
                contact_summary = (
                    contact_creators.groupby('TikTok account')
                    .apply(lambda g: pd.Series({
                        'Total SKU orders': g['SKU orders'].sum(),
                        'Video count': g['Video ID'].nunique(),
                        'Status list': ', '.join(sorted(g['Status_clean'].dropna().astype(str).unique())),
                        'Contact info': get_contact_info(g)
                    }))
                    .reset_index()
                    .sort_values(by='Total SKU orders', ascending=False)
                )
                st.subheader('=== 优先联系达人名单 ===')
                st.write(f'共 {len(contact_summary)} 位达人')
                st.dataframe(contact_summary, use_container_width=True)
                st.download_button('下载优先联系达人名单', to_excel_bytes(contact_summary), file_name='priority_creator_contact_list.xlsx')
            else:
                st.write("暂无需要联系的达人。")

    except Exception as e:
        st.error(f"读取或分析 Excel 失败：{e}")
