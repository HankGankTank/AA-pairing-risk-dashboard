import streamlit as st
import pandas as pd
import datetime
from pathlib import Path

# 页面基本配置
st.set_page_config(page_title="Flight Connection Risk Dashboard", layout="wide")

# 1. 数据加载与缓存 (针对 100万+ 行数据优化)
@st.cache_data
def load_data():
    DATA_FILENAME = Path(__file__).parent / 'data' / 'Pair_risk_index_data.csv'
    
    if not DATA_FILENAME.exists():
        st.error(f"找不到文件: {DATA_FILENAME}")
        return None
    
    df = pd.read_csv(DATA_FILENAME)
    df.columns = df.columns.str.strip()
    
    if 'FlightDate' not in df.columns:
        st.error(f"文件中缺少 'FlightDate' 列！当前找到的列有: {list(df.columns)}")
        st.stop()
        
    df['FlightDate'] = pd.to_datetime(df['FlightDate'])
    return df

df = load_data()

# --- 侧边栏：筛选控制 (对应你图片的左侧布局) ---
st.sidebar.title("🔍 Flight Search")
st.sidebar.markdown("---")

# 日期选择
min_date = df['FlightDate'].min().date()
max_date = df['FlightDate'].max().date()
selected_date = st.sidebar.date_input("Choose Date", value=min_date, min_value=min_date, max_value=max_date)

# 动态联动筛选：根据日期选路线
df_filtered_by_date = df[df['FlightDate'].dt.date == selected_date]

if df_filtered_by_date.empty:
        st.warning(f"No flight data found for the date {selected_date} ")
else:
        # 航程选择
        in_routes = sorted(df_filtered_by_date['in_route'].unique())
        selected_in = st.sidebar.selectbox("Choose flight 1 (Inbound Route)", in_routes)

        out_routes = sorted(df_filtered_by_date[df_filtered_by_date['in_route'] == selected_in]['out_route'].unique())
        selected_out = st.sidebar.selectbox("Choose flight 2 (Outbound Route)", out_routes)

        # 获取最终匹配的数据
        match = df_filtered_by_date[
            (df_filtered_by_date['in_route']    == selected_in) & 
            (df_filtered_by_date['out_route'] == selected_out)
        ]

        if not match.empty:
            final_data = match.iloc[0]
            
            # --- 主界面展示 ---
            st.title("✈️ Flytplan: Flight Connection Risk Assessment")
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("📋 Flight Info")
                with st.container(border=True):
                    c1, c2 = st.columns(2)
                    c1.write(f"**Depature:** {final_data.get('Origin_in', 'N/A')}")
                    c1.write(f"**Transit:** {selected_in.split('_')[1]}")
                    c2.write(f"**Arrival:** {final_data.get('Dest_out', 'N/A')}")
                    c2.write(f"**Interval time:** {final_data['interval_min']} min")
                
                # 历史趋势
                st.subheader("📈 Historical Risk Trends for This Route")
                history_df = df[(df['in_route'] == selected_in) & (df['out_route'] == selected_out)].sort_values('FlightDate')
                st.line_chart(history_df.set_index('FlightDate')['Pair_Risk_Index'])

            with col2:
                st.subheader("⚠️ Risk Prediction")
                risk_score = final_data['Pair_Risk_Index']
                risk_level = final_data['Pair_Risk_Level']
                color = "red" if risk_level == "High" else "orange" if risk_level == "Medium" else "green"
                
                st.markdown(f"""
                    <div style="background-color:#f0f2f6; padding: 20px; border-radius: 10px; text-align: center;">
                        <p style="font-size: 20px; color: #31333F; margin-bottom: 0;">Risk Index</p>
                        <h1 style="font-size: 72px; color: {color}; margin-top: 0;">{int(risk_score)}</h1>
                        <p style="font-size: 24px; font-weight: bold; color: {color};">Risk Level: {risk_level}</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.error("无法找到匹配的航班组合。")