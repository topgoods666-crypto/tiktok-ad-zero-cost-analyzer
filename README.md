# TikTok广告素材筛选工具

基于 Streamlit 的本地网页工具，用于筛选 TikTok 广告素材数据。

## 功能

- 上传 Excel 文件（.xlsx / .xls）
- 筛选0消耗但有出单的素材（Cost == 0 且 SKU orders > 0）
- 筛选 Learning 状态且 CTR 大于 3% 的素材
- 结果表格展示 + Excel 下载

## 使用方法

```bash
pip install -r requirements.txt
streamlit run main.py
```

## Excel 文件要求

必须包含以下列：

- Video ID
- Cost
- Product ad click rate
- SKU orders
- Status
