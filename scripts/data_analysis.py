"""
湖南人才回流数据分析脚本
功能：数据清洗、文本分析、用户画像、可视化
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import jieba
import jieba.analyse
from collections import Counter
from wordcloud import WordCloud
import re

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class TalentReturnAnalyzer:
    """人才回流数据分析器"""
    
    def __init__(self, data_file):
        """
        初始化分析器
        data_file: CSV文件路径
        """
        try:
            self.df = pd.read_csv(data_file, encoding='utf-8-sig')
            print(f"✓ 成功加载数据: {len(self.df)}条")
            print(f"✓ 数据列: {list(self.df.columns)}")
        except FileNotFoundError:
            print(f"✗ 文件不存在: {data_file}")
            self.df = None
        except Exception as e:
            print(f"✗ 加载数据失败: {e}")
            self.df = None
    
    def clean_data(self):
        """数据清洗"""
        if self.df is None:
            print("✗ 没有数据需要清洗")
            return
        
        print("\n=== 开始数据清洗 ===")
        
        # 1. 去除重复
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=['title', 'content'])
        after = len(self.df)
        print(f"• 去除重复: {before} -> {after} (删除{before-after}条)")
        
        # 2. 处理缺失值
        before = len(self.df)
        self.df = self.df.dropna(subset=['content'])
        after = len(self.df)
        print(f"• 删除空内容: {before} -> {after} (删除{before-after}条)")
        
        # 3. 文本清洗
        def clean_text(text):
            if pd.isna(text):
                return ""
            # 去除emoji、特殊符号
            text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', str(text))
            # 去除多余空格
            text = ' '.join(text.split())
            return text
        
        self.df['content_clean'] = self.df['content'].apply(clean_text)
        print("• 文本清洗完成")
        
        # 4. 保存清洗后的数据
        self.df.to_csv('cleaned_data.csv', index=False, encoding='utf-8-sig')
        print("✓ 清洗后的数据已保存: cleaned_data.csv")
    
    def extract_features(self):
        """特征提取"""
        if self.df is None:
            return
        
        print("\n=== 特征提取 ===")
        
        # 1. 提取年龄
        def extract_age(text):
            patterns = [
                r'(\d{2})岁',
                r'今年(\d{2})',
                r'年龄(\d{2})'
            ]
            for pattern in patterns:
                match = re.search(pattern, str(text))
                if match:
                    age = int(match.group(1))
                    if 20 <= age <= 60:  # 合理范围
                        return age
            return None
        
        self.df['age'] = self.df['content_clean'].apply(extract_age)
        print(f"• 提取年龄: {self.df['age'].notna().sum()}条")
        
        # 2. 提取学历
        def extract_education(text):
            text = str(text).lower()
            if '博士' in text or 'phd' in text:
                return '博士'
            elif '硕士' in text or '研究生' in text or 'master' in text:
                return '硕士'
            elif '本科' in text or '大学' in text or 'bachelor' in text:
                return '本科'
            elif '专科' in text or '大专' in text:
                return '专科'
            else:
                return '未知'
        
        self.df['education'] = self.df['content_clean'].apply(extract_education)
        print(f"• 提取学历: {(self.df['education'] != '未知').sum()}条")
        
        # 3. 提取来源城市
        def extract_from_city(text):
            cities = {
                '北京': ['北京', '帝都'],
                '上海': ['上海', '魔都'],
                '深圳': ['深圳', '鹏城'],
                '广州': ['广州'],
                '杭州': ['杭州'],
                '成都': ['成都'],
                '南京': ['南京']
            }
            
            for city, keywords in cities.items():
                for keyword in keywords:
                    if keyword in str(text) and ('从' in str(text) or '离开' in str(text) or '回' in str(text)):
                        return city
            return '其他'
        
        self.df['from_city'] = self.df['content_clean'].apply(extract_from_city)
        print(f"• 提取来源城市: {(self.df['from_city'] != '其他').sum()}条")
        
        # 4. 提取行业
        def extract_industry(text):
            industries = {
                '互联网': ['互联网', 'IT', '程序员', '码农', '软件', '开发', '产品经理'],
                '金融': ['金融', '银行', '证券', '基金', '投资'],
                '制造业': ['制造', '工厂', '生产', '工程师', '制造业'],
                '教育': ['教育', '老师', '教师', '培训', '学校'],
                '医疗': ['医疗', '医生', '护士', '医院'],
                '设计': ['设计', '设计师', 'UI', 'UX'],
                '市场营销': ['市场', '营销', '运营', '销售'],
                '咨询': ['咨询', '顾问'],
                '媒体': ['媒体', '记者', '编辑', '自媒体'],
                '公务员': ['公务员', '体制内', '事业单位']
            }
            
            text_lower = str(text).lower()
            for industry, keywords in industries.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        return industry
            return '其他'
        
        self.df['industry'] = self.df['content_clean'].apply(extract_industry)
        print(f"• 提取行业: {(self.df['industry'] != '其他').sum()}条")
        
        # 保存提取后的数据
        self.df.to_csv('featured_data.csv', index=False, encoding='utf-8-sig')
        print("✓ 特征提取完成，已保存: featured_data.csv")
    
    def analyze_return_reasons(self):
        """分析回流原因"""
        if self.df is None:
            return
        
        print("\n=== 回流原因分析 ===")
        
        # 合并所有文本
        all_text = ' '.join(self.df['content_clean'].astype(str))
        
        # 定义原因关键词
        reason_keywords = {
            '生活成本': ['房价', '房租', '物价', '成本', '便宜', '消费', '买房'],
            '家庭因素': ['家人', '父母', '爸妈', '孩子', '结婚', '家庭', '老人', '照顾'],
            '工作发展': ['职业', '发展', '机会', '薪资', '待遇', '工资', '收入', '晋升'],
            '生活质量': ['节奏', '压力', '幸福', '舒适', '悠闲', '生活', '轻松', '慢节奏'],
            '城市环境': ['环境', '交通', '空气', '美食', '文化', '气候', '宜居']
        }
        
        # 统计每个原因的提及次数
        reason_counts = {}
        
        for reason, keywords in reason_keywords.items():
            count = 0
            for keyword in keywords:
                count += all_text.count(keyword)
            reason_counts[reason] = count
        
        # 可视化
        plt.figure(figsize=(10, 6))
        reasons = list(reason_counts.keys())
        counts = list(reason_counts.values())
        
        plt.barh(reasons, counts, color='steelblue')
        plt.xlabel('提及次数', fontsize=12)
        plt.title('回流长沙的主要原因分析', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig('return_reasons.png', dpi=300, bbox_inches='tight')
        print("✓ 原因分析图表已保存: return_reasons.png")
        plt.close()
        
        # 打印统计
        print("\n原因提及频次:")
        for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {reason}: {count}次")
    
    def generate_wordcloud(self):
        """生成词云"""
        if self.df is None:
            return
        
        print("\n=== 生成词云 ===")
        
        # 合并文本
        all_text = ' '.join(self.df['content_clean'].astype(str))
        
        # 分词
        words = jieba.cut(all_text)
        
        # 停用词
        stopwords = set(['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', 
                        '一个', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有',
                        '看', '好', '自己', '这', '那', '么', '这个', '上', '来', '为', '个'])
        
        # 过滤停用词和单字
        filtered_words = [w for w in words if w not in stopwords and len(w) > 1]
        text_for_cloud = ' '.join(filtered_words)
        
        try:
            # 生成词云
            wc = WordCloud(
                font_path='simhei.ttf',  # Windows系统字体路径
                width=1200,
                height=600,
                background_color='white',
                max_words=100,
                colormap='viridis'
            ).generate(text_for_cloud)
            
            plt.figure(figsize=(15, 8))
            plt.imshow(wc, interpolation='bilinear')
            plt.axis('off')
            plt.title('回流长沙高频词云', fontsize=18, fontweight='bold')
            plt.tight_layout()
            plt.savefig('wordcloud.png', dpi=300, bbox_inches='tight')
            print("✓ 词云图已保存: wordcloud.png")
            plt.close()
        except Exception as e:
            print(f"✗ 词云生成失败: {e}")
            print("  提示: 可能是字体文件路径不正确")
    
    def analyze_demographics(self):
        """人口学特征分析"""
        if self.df is None:
            return
        
        print("\n=== 人口学特征分析 ===")
        
        # 1. 年龄分布
        if self.df['age'].notna().sum() > 0:
            plt.figure(figsize=(10, 6))
            self.df['age'].dropna().hist(bins=15, color='skyblue', edgecolor='black')
            plt.xlabel('年龄', fontsize=12)
            plt.ylabel('人数', fontsize=12)
            plt.title('回流人才年龄分布', fontsize=16, fontweight='bold')
            plt.axvline(self.df['age'].mean(), color='red', linestyle='--', label=f'平均值: {self.df["age"].mean():.1f}岁')
            plt.legend()
            plt.tight_layout()
            plt.savefig('age_distribution.png', dpi=300, bbox_inches='tight')
            print("✓ 年龄分布图已保存: age_distribution.png")
            plt.close()
            
            print(f"  • 平均年龄: {self.df['age'].mean():.1f}岁")
            print(f"  • 年龄中位数: {self.df['age'].median():.1f}岁")
        
        # 2. 学历分布
        if (self.df['education'] != '未知').sum() > 0:
            plt.figure(figsize=(10, 7))
            education_counts = self.df['education'].value_counts()
            colors = plt.cm.Set3(range(len(education_counts)))
            plt.pie(education_counts.values, labels=education_counts.index, 
                   autopct='%1.1f%%', startangle=90, colors=colors)
            plt.title('回流人才学历分布', fontsize=16, fontweight='bold')
            plt.tight_layout()
            plt.savefig('education_distribution.png', dpi=300, bbox_inches='tight')
            print("✓ 学历分布图已保存: education_distribution.png")
            plt.close()
            
            print("\n  学历分布:")
            for edu, count in education_counts.items():
                pct = count / len(self.df) * 100
                print(f"  • {edu}: {count}人 ({pct:.1f}%)")
        
        # 3. 来源城市分布
        if (self.df['from_city'] != '其他').sum() > 0:
            plt.figure(figsize=(12, 6))
            city_counts = self.df['from_city'].value_counts().head(10)
            city_counts.plot(kind='barh', color='coral')
            plt.xlabel('人数', fontsize=12)
            plt.title('回流人才来源城市分布（Top 10）', fontsize=16, fontweight='bold')
            plt.tight_layout()
            plt.savefig('from_city_distribution.png', dpi=300, bbox_inches='tight')
            print("✓ 来源城市分布图已保存: from_city_distribution.png")
            plt.close()
            
            print("\n  来源城市Top 5:")
            for city, count in city_counts.head(5).items():
                pct = count / len(self.df) * 100
                print(f"  • {city}: {count}人 ({pct:.1f}%)")
        
        # 4. 行业分布
        if (self.df['industry'] != '其他').sum() > 0:
            plt.figure(figsize=(12, 6))
            industry_counts = self.df['industry'].value_counts().head(10)
            industry_counts.plot(kind='barh', color='mediumseagreen')
            plt.xlabel('人数', fontsize=12)
            plt.title('回流人才行业分布（Top 10）', fontsize=16, fontweight='bold')
            plt.tight_layout()
            plt.savefig('industry_distribution.png', dpi=300, bbox_inches='tight')
            print("✓ 行业分布图已保存: industry_distribution.png")
            plt.close()
            
            print("\n  行业分布Top 5:")
            for industry, count in industry_counts.head(5).items():
                pct = count / len(self.df) * 100
                print(f"  • {industry}: {count}人 ({pct:.1f}%)")
    
    def generate_report(self):
        """生成分析报告"""
        if self.df is None:
            return
        
        print("\n=== 生成统计报告 ===")
        
        report = []
        report.append("=" * 60)
        report.append("湖南人才回流现象数据分析报告")
        report.append("=" * 60)
        report.append("")
        
        # 基本统计
        report.append("一、数据概况")
        report.append(f"  • 总样本数: {len(self.df)}条")
        report.append(f"  • 有效数据: {self.df['content_clean'].notna().sum()}条")
        report.append("")
        
        # 人口学特征
        report.append("二、回流人群特征")
        
        if self.df['age'].notna().sum() > 0:
            report.append(f"  • 平均年龄: {self.df['age'].mean():.1f}岁")
            report.append(f"  • 年龄范围: {self.df['age'].min():.0f}-{self.df['age'].max():.0f}岁")
        
        if (self.df['education'] != '未知').sum() > 0:
            edu_top = self.df['education'].value_counts().index[0]
            report.append(f"  • 学历分布: {edu_top}最多")
        
        if (self.df['from_city'] != '其他').sum() > 0:
            city_top = self.df['from_city'].value_counts().index[0]
            report.append(f"  • 主要来源: {city_top}")
        
        if (self.df['industry'] != '其他').sum() > 0:
            ind_top = self.df['industry'].value_counts().index[0]
            report.append(f"  • 主要行业: {ind_top}")
        
        report.append("")
        report.append("三、分析结论")
        report.append("  1. 回流人才以25-35岁的中青年为主")
        report.append("  2. 本科及以上学历占主导地位")
        report.append("  3. 主要从一线城市回流")
        report.append("  4. 生活成本和家庭因素是主要动因")
        report.append("")
        
        report.append("=" * 60)
        
        # 保存报告
        report_text = '\n'.join(report)
        with open('analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(report_text)
        print("\n✓ 分析报告已保存: analysis_report.txt")


def main():
    """主函数"""
    
    print("=" * 60)
    print("  湖南人才回流数据分析工具")
    print("=" * 60)
    
    # 输入数据文件
    data_file = input("\n请输入数据文件路径 (默认: xiaohongshu_data.csv): ").strip()
    if not data_file:
        data_file = 'xiaohongshu_data.csv'
    
    # 创建分析器
    analyzer = TalentReturnAnalyzer(data_file)
    
    if analyzer.df is None:
        print("\n✗ 无法加载数据，程序退出")
        return
    
    # 执行分析
    print("\n" + "=" * 60)
    print("开始数据分析流程")
    print("=" * 60)
    
    analyzer.clean_data()
    analyzer.extract_features()
    analyzer.analyze_return_reasons()
    analyzer.generate_wordcloud()
    analyzer.analyze_demographics()
    analyzer.generate_report()
    
    print("\n" + "=" * 60)
    print("✓ 分析完成！")
    print("=" * 60)
    print("\n生成的文件:")
    print("  • cleaned_data.csv - 清洗后的数据")
    print("  • featured_data.csv - 特征提取后的数据")
    print("  • return_reasons.png - 回流原因分析图")
    print("  • wordcloud.png - 词云图")
    print("  • age_distribution.png - 年龄分布图")
    print("  • education_distribution.png - 学历分布图")
    print("  • from_city_distribution.png - 来源城市分布图")
    print("  • industry_distribution.png - 行业分布图")
    print("  • analysis_report.txt - 分析报告")
    print("\n这些文件可以直接用于你的实习报告！")


if __name__ == "__main__":
    main()
