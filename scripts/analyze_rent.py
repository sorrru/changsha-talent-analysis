import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

# 1. 读取数据
file_path = 'changsha_rent_selenium.csv'
df = pd.read_csv(file_path)

print("原始数据预览：")
print(df.head(2))

# --- 2. 数据清洗 (ETL) ---

# 定义一个函数：用正则表达式提取数字
def extract_number(text):
    # 寻找类似于 "40.00" 或者 "105" 这样的数字
    match = re.search(r'(\d+\.?\d*)', str(text))
    if match:
        return float(match.group(1))
    return None

# 应用清洗逻辑
df['面积_clean'] = df['面积'].apply(extract_number)
df['租金_clean'] = pd.to_numeric(df['租金'], errors='coerce')

# 去掉清洗失败的空行
df.dropna(subset=['面积_clean', '租金_clean'], inplace=True)

# 计算“每平米租金” (单价)
df['单价'] = df['租金_clean'] / df['面积_clean']

print(f"\n清洗后剩余有效数据：{len(df)} 条")
print(df[['区域', '面积_clean', '租金_clean', '单价']].head())

# --- 插入这段代码在画图之前 ---

# 1. 清洗区域名称：去掉包含“精选”这种广告词的行
df = df[~df['区域'].str.contains('精选')]

# 2. 剔除价格异常值：只保留单价在 100元/平米以下的数据
# (长沙普通租房单价很难超过 100，超过的大概率是面积提取错了)
df = df[df['单价'] < 100]

print(f"再次清洗后剩余数据：{len(df)} 条")

# --- 下面接着写原来的画图代码 ---
plt.figure(figsize=(10, 6))
# ...
# --- 3. 可视化分析 ---

# 设置中文字体 (防止乱码)
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS'] # Mac专用
plt.rcParams['axes.unicode_minus'] = False

# 图表 1: 各行政区“租金单价”箱线图 (Boxplot)
# 这个图能一眼看出哪个区最贵，哪个区性价比高
plt.figure(figsize=(10, 6))
sns.boxplot(x='区域', y='单价', data=df, palette="Set3")
plt.title('长沙各区租房性价比分析 (元/平米/月)')
plt.ylabel('每平米租金 (元)')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.savefig('rent_analysis_boxplot.png') # 保存图片
print("\n✅ 图表已保存: rent_analysis_boxplot.png")

# 图表 2: 租金 vs 面积 散点图
# 帮你发现“大房子反而便宜”的捡漏机会
plt.figure(figsize=(10, 6))
sns.scatterplot(x='面积_clean', y='租金_clean', hue='区域', data=df, s=100, alpha=0.8)
plt.title('长沙租房：面积 vs 租金分布图')
plt.xlabel('面积 (㎡)')
plt.ylabel('月租金 (元)')
plt.grid(True, linestyle='--', alpha=0.3)
plt.savefig('rent_analysis_scatter.png')
print("✅ 图表已保存: rent_analysis_scatter.png")

plt.show()