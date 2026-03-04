import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter

# 1. 读取你收集的评论数据
with open('comments.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# 2. 中文分词 (把句子切成词)
# 添加一些长沙专属词汇，防止被切碎
jieba.add_word("茶颜悦色")
jieba.add_word("文和友")
jieba.add_word("低房价")
jieba.add_word("幸福感")
jieba.add_word("解放西")
jieba.add_word("岳麓山")

words_list = jieba.lcut(text)

# 3. 数据清洗 (去掉无意义的词)
stopwords = {'的', '了', '在', '是', '我', '也', '都', '去', '这就', '可以说', '人', '有', '和', '就'}
clean_words = [word for word in words_list if len(word) > 1 and word not in stopwords]

# 4. 统计高频词 (为了做条形图)
word_counts = Counter(clean_words)
top_10_words = word_counts.most_common(10)
print("高频词 Top 10:", top_10_words)

# 5. 生成词云图
wc = WordCloud(
    font_path='/System/Library/Fonts/STHeiti Light.ttc', # Mac自带的华文细黑
    width=1000, height=600,
    background_color='white',
    colormap='Blues' # 蓝色系，呼应科技感
)

wc.generate(" ".join(clean_words))

# 6. 可视化展示
plt.figure(figsize=(15, 6))

output_filename = "changsha_wordcloud.png"
wc.to_file(output_filename) # 保存图片

try:
    img = plt.imread(output_filename) # 读取图片
    plt.subplot(1, 2, 1)
    plt.imshow(img)
    plt.axis('off')
    # 修改这里：把标题改成英文
    plt.title("Core Word Cloud: Young People's Impressions of Changsha", fontsize=14)
except Exception as e:
    print("图片显示出错，请直接查看保存的文件。")

# --- 右图：高频词统计 ---
plt.subplot(1, 2, 2)
x_words = [x[0] for x in top_10_words]
y_counts = [x[1] for x in top_10_words]
plt.barh(x_words[::-1], y_counts[::-1], color='#4e79a7')

# 修改这里：把标题和坐标轴标签改成英文
plt.title('Top 10 High-Frequency Keywords', fontsize=14)
plt.xlabel('Frequency', fontsize=12)
plt.yticks(fontsize=10) # 设置y轴标签字体大小

plt.tight_layout()
plt.show()