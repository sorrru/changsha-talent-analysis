import pandas as pd
import matplotlib.pyplot as plt

# 1. 录入数据（基于你的图表和年鉴）
data = {
    'city': ['湘潭市', '株洲市', '岳阳市', '益阳市', '衡阳市', '邵阳市'],
    'migration_ratio': [11.72, 9.74, 10.83, 9.70, 4.81, 4.30], # 数据来自你的工作日图表 (12月17日)
    'population': [269.18, 383.78, 498.75, 373.52, 643.43, 629.97] # 数据来自统计年鉴 图21-3
}

df = pd.DataFrame(data)

# 2. 核心计算：虹吸强度 (为了数值好看，结果乘以 100)
df['siphon_index'] = (df['migration_ratio'] / df['population']) * 100
df = df.sort_values(by='siphon_index', ascending=True)

# 3. 可视化：双轴图（柱状图看流量，折线图看强度）
fig, ax1 = plt.subplots(figsize=(12, 6))

# 设置中文字体 (根据你的系统调整，Mac用 Arial Unicode MS, Windows用 SimHei)
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS'] 
plt.rcParams['axes.unicode_minus'] = False

# 绘制柱状图 (左轴：迁入占比)
bars = ax1.bar(df['city'], df['migration_ratio'], color='#a8c6fa', label='迁入人口占比(%)', alpha=0.7)
ax1.set_ylabel('迁入人口占比 (%)', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')

# 在柱子上标数值
for bar in bars:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height, f'{height}%', ha='center', va='bottom')

# 绘制折线图 (右轴：虹吸强度)
ax2 = ax1.twinx()
line = ax2.plot(df['city'], df['siphon_index'], color='#d93025', marker='o', linewidth=2, label='虹吸强度指数')
ax2.set_ylabel('虹吸强度指数 (占比/总人口)', color='#d93025')
ax2.tick_params(axis='y', labelcolor='#d93025')

# 在折线上标数值
for i, v in enumerate(df['siphon_index']):
    ax2.text(i, v + 0.1, f'{v:.2f}', color='#d93025', ha='center', va='bottom', fontweight='bold')

plt.title('长沙对省内主要城市人口“虹吸强度”分析 (2025工作日版)')
plt.show()