import pandas as pd
import os
import glob

# 1. 定义你的文件夹路径 (请根据你的实际路径修改)
# 假设你把 12 个 CSV 放到了当前目录下的 '2025_Flight_Data' 文件夹中
FOLDER_PATH = './2025_Flight_Data' 
OUTPUT_FILE = 'AA_Flights_2025_Full.csv'

def merge_and_clean_aa_data():
    # 使用 glob 获取文件夹下所有的 .csv 文件路径
    all_files = glob.glob(os.path.join(FOLDER_PATH, "*.csv"))
    
    if not all_files:
        print(f"❌ 在 {FOLDER_PATH} 中没有找到任何 CSV 文件。")
        return
    
    print(f"🔍 找到 {len(all_files)} 个 CSV 文件，开始处理...")
    
    # 创建一个空列表来存放每个月清理后的数据
    df_list = []
    
    for file in all_files:
        print(f"⏳ 正在处理: {os.path.basename(file)}")
        try:
            # 读取单个文件
            # 如果文件很大，可以通过 usecols 参数只读取你需要的列来节省内存
            # 这里假设你下载时已经精简了列，所以直接全读
            df = pd.read_csv(file, low_memory=False) 
            
            # 关键过滤：只保留 AA 航空
            aa_only = df[df['OP_UNIQUE_CARRIER'] == 'AA']
            
            # 将过滤后的数据加入列表
            df_list.append(aa_only)
        except Exception as e:
             print(f"⚠️ 读取文件 {file} 时出错: {e}")

    # 将列表中所有的 DataFrame 合并成一个
    print("🔄 正在合并所有数据...")
    combined_df = pd.concat(df_list, ignore_index=True)
    
    # 导出为最终的 CSV 文件
    print(f"💾 正在保存为 {OUTPUT_FILE} ... (合并后共 {len(combined_df)} 行)")
    combined_df.to_csv(OUTPUT_FILE, index=False)
    print("✅ 处理完成！")

if __name__ == "__main__":
    merge_and_clean_aa_data()