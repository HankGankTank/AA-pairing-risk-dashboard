import streamlit as st
import pandas as pd
import datetime
from pathlib import Path

# 页面基本配置
st.set_page_config(page_title="Flight Connection Risk Dashboard", layout="wide")


# 1. 数据加载与缓存 (针对 100万+ 行数据优化)
#@st.cache_data

#def load_airport_dict():
#    """读取 CSV 文件并自动生成机场名称映射字典"""
#    DICT_PATH = Path(__file__).parent / 'data' / 'Airport_dict.csv'
#
#    try:
#        # 读取文件
#        airport_df = pd.read_csv(DICT_PATH)
#        # 提取 IATA 列作为键，Airport_Name 列作为值，转成字典
#        return airport_df.set_index('IATA')['Airport_Name'].to_dict()
#    except Exception as e:
#        st.warning(f"Can't load dictonary, show IATA instead: {e}")
#        return {} # 如果读取失败，返回空字典，程序不会崩溃

# 获取字典
#AIRPORT_DICT = load_airport_dict()

# --- 2. 格式化转换函数 ---
#def format_route_name(route_code):
#    """将 MSN_DFW 转换成 完整机场名 ➔ 完整机场名"""
#    try:
#        origin_code, dest_code = route_code.split('_')
#        
#        # 从自动生成的字典中获取全称，找不到就用原缩写
#        origin_name = AIRPORT_DICT.get(origin_code, origin_code)
#        dest_name = AIRPORT_DICT.get(dest_code, dest_code)
        
#        return f"{origin_name} ➔ {dest_name}"
#    except:
#        return route_code

@st.cache_data    
def load_data():
    DATA_FILENAME = Path(__file__).parent / 'data' / 'Pair_risk_index_data.csv'
    
    if not DATA_FILENAME.exists():
        st.error(f"Unablt to find the file: {DATA_FILENAME}")
        return None
    
    df = pd.read_csv(DATA_FILENAME)
    df.columns = df.columns.str.strip()
    
    if 'FlightDate' not in df.columns:
        st.error(f"Unable to find the column 'FlightDate' Curently only found: {list(df.columns)}")
        st.stop()
        
    df['FlightDate'] = pd.to_datetime(df['FlightDate'])
    return df

df = load_data()

# --- 1. 加载航班号映射 (新增加的部分) ---
@st.cache_data
def load_flight_mapping():
    """从你的 AA 全年数据中提取航线与航班号的映射"""
    # 路径请根据你实际存放 AA_Flights_2025_Full.csv 的位置修改
    mapping_path = Path(__file__).parent / 'data' / 'AA_Flights_2025_Full.csv'
    
    try:
        # 只读取需要的列以节省内存
        # 假设你的 CSV 列名是 Origin, Dest, OP_CARRIER_FL_NUM
        df_map = pd.read_csv(mapping_path, usecols=['ORIGIN', 'DEST', 'OP_CARRIER_FL_NUM'])
        
        # 创建 Route 键 (如 DFW_LAX)
        df_map['Route'] = df_map['ORIGIN'] + '_' + df_map['DEST']
        
        # 为每个航线取最常出现的一个航班号
        mapping = df_map.groupby('Route')['OP_CARRIER_FL_NUM'].agg(lambda x: x.mode()[0]).to_dict()
        
        # 变成 AA1234 的格式
        return {k: f"AA{int(v)}" for k, v in mapping.items()}
    except Exception as e:
        st.warning(f"无法加载航班号映射: {e}")
        return {}

FLIGHT_NUM_DICT = load_flight_mapping()

# --- 2. 修改后的格式化函数 ---
def format_route_name(route_code):
    """显示机场代码和航班号"""
    try:
        origin_code, dest_code = route_code.split('_')
#        origin_name = AIRPORT_DICT.get(origin_code, origin_code)
#        dest_name = AIRPORT_DICT.get(dest_code, dest_code)
        
        # 获取航班号，如果没有则不显示
        f_num = FLIGHT_NUM_DICT.get(route_code, "")
        f_info = f" ({f_num})" if f_num else ""
        
#        return f"{origin_name} ➔ {dest_name}{f_info}"
        return f"{origin_code} ➔ {dest_code}{f_info}"
    except:
        return route_code

# --- 侧边栏：筛选控制 (对应你图片的左侧布局) ---
st.sidebar.title("Flight Search")
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
#        selected_in = st.sidebar.selectbox(
#            "Choose flight 1 (Inbound Route)", 
#            in_routes,
#            format_func=format_route_name  # Replace airport name
#        )

        out_routes = sorted(df_filtered_by_date[df_filtered_by_date['in_route'] == selected_in]['out_route'].unique())
        selected_out = st.sidebar.selectbox("Choose flight 2 (Outbound Route)", out_routes)
#        selected_out = st.sidebar.selectbox(
#            "Choose flight 2 (Outbound Route)", 
#            out_routes,
#            format_func=format_route_name  # Replace airport name
#        )

        # 获取最终匹配的数据
        match = df_filtered_by_date[
            (df_filtered_by_date['in_route']    == selected_in) & 
            (df_filtered_by_date['out_route'] == selected_out)
        ]

        if not match.empty:
            final_data = match.iloc[0]
            
            # --- 主界面展示 ---
            st.title("Flight Connection Risk Assessment")
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("Flight Info")
                with st.container(border=True):
                    c1, c2 = st.columns(2)
                    c1.write(f"**Depature:** {final_data.get('Origin_in', 'N/A')}")
                    c1.write(f"**Transit:** {selected_in.split('_')[1]}")
                    f_num1 = FLIGHT_NUM_DICT.get(selected_in, "N/A")
                    c1.write(f"**Flight No:** :blue[{f_num1}]")
                    c2.write(f"**Arrival:** {final_data.get('Dest_out', 'N/A')}")
                    f_num2 = FLIGHT_NUM_DICT.get(selected_out, "N/A")
                    c2.write(f"**Flight No:** :blue[{f_num2}]")
#                    c1.write(f"**Departure:** {AIRPORT_DICT.get(final_data.get('Origin_in', ''), final_data.get('Origin_in', 'N/A'))}")
#                    c1.write(f"**Transit:** {AIRPORT_DICT.get(selected_in.split('_')[1], selected_in.split('_')[1])}")
#                    c2.write(f"**Arrival:** {AIRPORT_DICT.get(final_data.get('Dest_out', ''), final_data.get('Dest_out', 'N/A'))}")
                    c2.write(f"**Interval time:** {final_data['interval_min']} min")
                
                # 历史趋势
                st.subheader("Historical Risk Trends for This Route")
                history_df = df[(df['in_route'] == selected_in) & (df['out_route'] == selected_out)].sort_values('FlightDate')
                st.line_chart(history_df.set_index('FlightDate')['Pair_Risk_Index'])

            with col2:
                st.subheader("Risk Prediction")
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
            st.error("Unable to find the paired flight")