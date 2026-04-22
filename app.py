import streamlit as st
import pandas as pd
import datetime

# 页面基本配置
st.set_page_config(page_title="Flight Connection Risk Dashboard", layout="wide")

# 1. 数据加载与缓存 (针对 100万+ 行数据优化)
@st.cache_data
def load_data():
    df = pd.read_csv('Pair_risk_index_data.csv')
    df['FlightDate'] = pd.to_datetime(df['FlightDate'])
    return df

df = load_data()

# --- 侧边栏：筛选控制 (对应你图片的左侧布局) ---
st.sidebar.title("🔍 航班筛选")
st.sidebar.markdown("---")

# 日期选择
min_date = df['FlightDate'].min().date()
max_date = df['FlightDate'].max().date()
selected_date = st.sidebar.date_input("选择日期", value=min_date, min_value=min_date, max_value=max_date)

# 动态联动筛选：根据日期选路线
df_filtered_by_date = df[df['FlightDate'].dt.date == selected_date]

# 第一段航程选择 (in_route)
in_routes = df_filtered_by_date['in_route'].unique()
selected_in = st.sidebar.selectbox("选择航班 1 (Inbound Route)", sorted(in_routes))

# 第二段航程选择 (out_route)
out_routes = df_filtered_by_date[df_filtered_by_date['in_route'] == selected_in]['out_route'].unique()
selected_out = st.sidebar.selectbox("选择航班 2 (Outbound Route)", sorted(out_routes))

# 获取最终匹配的数据行
final_data = df_filtered_by_date[
    (df_filtered_by_date['in_route'] == selected_in) & 
    (df_filtered_by_date['out_route'] == selected_out)
].iloc[0]

# --- 主界面展示 (对应你图片的中部和右侧布局) ---
st.title("✈️ Flytplan: 航班连接风险评估")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 航班详情 (Flight Details)")
    
    # 使用表格或美化的容器展示
    detail_box = st.container(border=True)
    with detail_box:
        c1, c2 = st.columns(2)
        c1.write(f"**出发机场:** {final_data.get('Origin_in', 'N/A')}")
        c1.write(f"**中转航点:** {selected_in.split('_')[1]}")
        c2.write(f"**到达机场:** {final_data.get('Dest_out', 'N/A')}")
        c2.write(f"**连接间隔:** {final_data['interval_min']} 分钟")
    
    # 历史趋势图 (基于该路线组合的历史风险指数)
    st.subheader("📈 该航线历史风险趋势")
    history_df = df[(df['in_route'] == selected_in) & (df['out_route'] == selected_out)].sort_values('FlightDate')
    st.line_chart(history_df.set_index('FlightDate')['Pair_Risk_Index'])

with col2:
    st.subheader("⚠️ 风险预测")
    
    # 模仿原图的大数字显示
    risk_score = final_data['Pair_Risk_Index']
    risk_level = final_data['Pair_Risk_Level']
    
    # 设置风险等级颜色
    color = "red" if risk_level == "High" else "orange" if risk_level == "Medium" else "green"
    
    st.markdown(f"""
        <div style="background-color:#f0f2f6; padding: 20px; border-radius: 10px; text-align: center;">
            <p style="font-size: 20px; color: #31333F; margin-bottom: 0;">当前组合风险指数</p>
            <h1 style="font-size: 72px; color: {color}; margin-top: 0;">{int(risk_score)}</h1>
            <p style="font-size: 24px; font-weight: bold; color: {color};">等级: {risk_level}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.info(f"建议：此连接间隔为 {final_data['interval_min']} 分钟，属于 {risk_level} 风险级别。")

# 底部数据表预览
if st.checkbox("查看原始数据明细"):
    st.write(final_data.to_frame().T)