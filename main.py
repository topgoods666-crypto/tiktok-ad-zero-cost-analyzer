import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="TikTok广告素材筛选工具", layout="wide")
st.title("TikTok广告素材筛选工具")

REQUIRED_COLUMNS = ["Video ID", "Cost", "Product ad click rate", "SKU orders", "Status"]
DISPLAY_COLUMNS = ["Video ID", "Cost", "Product ad click rate", "SKU orders"]


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return buf.getvalue()


uploaded = st.file_uploader("上传 Excel 文件", type=["xlsx", "xls"])

if uploaded is not None:
    df = pd.read_excel(uploaded, sheet_name=0, engine="openpyxl")
    df.columns = df.columns.str.strip()

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.error(f"Excel 缺少以下必要列：{', '.join(missing)}")
        st.info(f"当前文件包含的列：{', '.join(df.columns.tolist())}")
        st.stop()

    df["Cost"] = pd.to_numeric(df["Cost"], errors="coerce").fillna(0)
    df["SKU orders"] = pd.to_numeric(df["SKU orders"], errors="coerce").fillna(0)
    df["Product ad click rate"] = pd.to_numeric(
        df["Product ad click rate"].astype(str).str.rstrip("%"),
        errors="coerce",
    ).fillna(0)

    max_ctr = df["Product ad click rate"].max()
    if max_ctr > 1:
        df["Product ad click rate"] = df["Product ad click rate"] / 100

    df["Status"] = df["Status"].astype(str).str.strip()

    st.markdown("---")

    # ---- 结果区一 ----
    st.subheader("【0消耗但有出单的素材】")
    r1 = df[(df["Cost"] == 0) & (df["SKU orders"] > 0)][DISPLAY_COLUMNS].reset_index(drop=True)
    st.write(f"符合条件的素材数量：**{len(r1)}**")
    if r1.empty:
        st.info("没有符合条件的素材。")
    else:
        st.dataframe(r1, use_container_width=True)
        st.download_button(
            label="下载结果 Excel",
            data=to_excel_bytes(r1),
            file_name="0消耗有出单素材.xlsx",
            key="dl_r1",
        )

    st.markdown("---")

    # ---- 结果区二 ----
    st.subheader("【Learning状态且CTR大于3%的素材】")
    r2 = df[(df["Status"] == "Learning") & (df["Product ad click rate"] > 0.03)][DISPLAY_COLUMNS].reset_index(drop=True)
    st.write(f"符合条件的素材数量：**{len(r2)}**")
    if r2.empty:
        st.info("没有符合条件的素材。")
    else:
        st.dataframe(r2, use_container_width=True)
        st.download_button(
            label="下载结果 Excel",
            data=to_excel_bytes(r2),
            file_name="Learning高CTR素材.xlsx",
            key="dl_r2",
        )
