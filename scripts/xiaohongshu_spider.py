"""
小红书数据采集器 - 正式版
功能：
1. 从cookie.txt读取Cookie
2. 搜索关键词并采集笔记
3. 自动保存数据
4. 错误处理和重试机制
5. 进度显示

作者：Claude
日期：2026-01-28
"""

import requests
import time
import random
import json
import pandas as pd
from datetime import datetime
import os
import sys

class XiaohongshuCrawler:
    """小红书爬虫 - 正式版"""
    
    def __init__(self, cookie_file='cookie.txt'):
        """
        初始化爬虫
        cookie_file: Cookie文件路径
        """
        print("=" * 70)
        print("  小红书数据采集器 v1.0")
        print("=" * 70)
        
        # 读取Cookie
        self.cookie = self._load_cookie(cookie_file)
        if not self.cookie:
            print("\n❌ Cookie加载失败，程序退出")
            print("\n请确保：")
            print("1. cookie.txt 文件存在")
            print("2. 文件中有正确的Cookie内容")
            print("3. Cookie格式正确（从浏览器复制的完整内容）")
            sys.exit(1)
        
        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Cookie': self.cookie,
            'Referer': 'https://www.xiaohongshu.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://www.xiaohongshu.com',
        }
        
        # 数据存储
        self.data_list = []
        self.collected_ids = set()  # 用于去重
        
        # 统计信息
        self.stats = {
            'total_collected': 0,
            'success_requests': 0,
            'failed_requests': 0,
            'start_time': datetime.now()
        }
        
        print("✓ Cookie加载成功")
        print(f"✓ Cookie长度: {len(self.cookie)} 字符")
    
    def _load_cookie(self, cookie_file):
        """从文件加载Cookie"""
        try:
            if not os.path.exists(cookie_file):
                print(f"\n❌ Cookie文件不存在: {cookie_file}")
                print("\n请创建 cookie.txt 文件，并将你的Cookie粘贴进去")
                print("\n获取Cookie的步骤：")
                print("1. 打开小红书网页版并登录")
                print("2. 按F12打开开发者工具")
                print("3. 点击Network标签")
                print("4. 刷新页面（F5）")
                print("5. 点击任意请求")
                print("6. 找到Request Headers中的cookie")
                print("7. 复制cookie的值到cookie.txt文件")
                return None
            
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookie = f.read().strip()
            
            if not cookie:
                print(f"\n❌ Cookie文件是空的: {cookie_file}")
                return None
            
            # 简单验证Cookie格式
            if 'xsecappid' not in cookie or 'a1=' not in cookie:
                print("\n⚠️ Cookie格式可能不正确")
                print("请确保复制了完整的Cookie内容")
            
            return cookie
            
        except Exception as e:
            print(f"\n❌ 读取Cookie文件失败: {e}")
            return None
    
    def test_connection(self):
        """测试Cookie是否有效"""
        print("\n正在测试Cookie有效性...")
        
        try:
            response = requests.get(
                'https://www.xiaohongshu.com/explore',
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✓ Cookie有效！可以开始爬取")
                return True
            elif response.status_code == 403:
                print("❌ Cookie无效或已过期（403 Forbidden）")
                print("\n请重新获取Cookie：")
                print("1. 退出小红书并重新登录")
                print("2. 按F12 → Network → 刷新页面")
                print("3. 复制新的Cookie到cookie.txt")
                return False
            else:
                print(f"⚠️ 状态码异常: {response.status_code}")
                print("可能需要重新获取Cookie")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
            print("\n可能的原因：")
            print("1. 网络连接问题")
            print("2. 小红书服务器问题")
            print("3. 被反爬虫拦截")
            return False
    
    def search_notes(self, keyword, max_notes=50, sort_type='general'):
        """
        搜索笔记
        keyword: 搜索关键词
        max_notes: 最多采集数量
        sort_type: 排序方式 (general=综合, time=最新, popular=最热)
        """
        print(f"\n{'='*70}")
        print(f"开始搜索: '{keyword}'")
        print(f"目标数量: {max_notes}条")
        print(f"排序方式: {sort_type}")
        print(f"{'='*70}")
        
        collected = 0
        page = 1
        consecutive_failures = 0  # 连续失败次数
        
        while collected < max_notes and consecutive_failures < 3:
            try:
                print(f"\n[第{page}页] 正在请求...")
                
                # 构造搜索API URL
                # 注意：这个API可能需要根据实际情况调整
                search_url = "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes"
                
                params = {
                    'keyword': keyword,
                    'page': page,
                    'page_size': 20,
                    'search_id': self._generate_search_id(),
                    'sort': sort_type,
                    'note_type': 0,  # 0=全部，1=视频，2=图文
                }
                
                # 发送请求
                response = requests.get(
                    search_url,
                    headers=self.headers,
                    params=params,
                    timeout=15
                )
                
                self.stats['success_requests'] += 1
                
                # 检查响应状态
                if response.status_code != 200:
                    print(f"  ❌ 请求失败 (状态码: {response.status_code})")
                    self.stats['failed_requests'] += 1
                    consecutive_failures += 1
                    
                    if response.status_code == 403:
                        print("  Cookie可能已失效，请重新获取")
                        break
                    
                    time.sleep(5)
                    continue
                
                # 解析JSON响应
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    print("  ❌ 无法解析JSON响应")
                    print(f"  响应内容: {response.text[:200]}")
                    consecutive_failures += 1
                    time.sleep(5)
                    continue
                
                # 提取笔记数据
                # 注意：数据结构可能需要根据实际API调整
                notes = self._extract_notes(data)
                
                if not notes:
                    print("  ⚠️ 没有找到更多笔记")
                    if page == 1:
                        print("  可能原因：")
                        print("    1. 关键词没有结果")
                        print("    2. API接口已变更")
                        print("    3. 需要更新爬虫代码")
                    break
                
                # 处理每条笔记
                page_collected = 0
                for note in notes:
                    if collected >= max_notes:
                        break
                    
                    # 去重
                    note_id = note.get('id', '')
                    if note_id in self.collected_ids:
                        continue
                    
                    self.collected_ids.add(note_id)
                    
                    # 提取详细信息
                    note_info = self._parse_note(note, keyword)
                    
                    if note_info:
                        self.data_list.append(note_info)
                        collected += 1
                        page_collected += 1
                        self.stats['total_collected'] += 1
                        
                        # 显示进度
                        title = note_info['title'][:30]
                        print(f"  ✓ [{collected}/{max_notes}] {title}... (👍{note_info['likes']} 💬{note_info['comments']})")
                
                print(f"  本页采集: {page_collected}条")
                
                # 重置连续失败计数
                consecutive_failures = 0
                
                # 保存进度
                if collected % 10 == 0 and collected > 0:
                    self._save_progress()
                
                # 随机延时（重要！）
                delay = random.uniform(3, 8)
                print(f"  ⏳ 等待 {delay:.1f} 秒...")
                time.sleep(delay)
                
                page += 1
                
            except KeyboardInterrupt:
                print("\n\n⚠️ 用户中断")
                print(f"已采集 {collected} 条数据")
                break
                
            except Exception as e:
                print(f"\n  ❌ 出错: {str(e)}")
                self.stats['failed_requests'] += 1
                consecutive_failures += 1
                time.sleep(5)
        
        print(f"\n{'='*70}")
        print(f"✓ 关键词 '{keyword}' 采集完成")
        print(f"✓ 采集数量: {collected}条")
        print(f"{'='*70}")
        
        return collected
    
    def _generate_search_id(self):
        """生成搜索ID"""
        return str(int(time.time() * 1000))
    
    def _extract_notes(self, data):
        """从API响应中提取笔记列表"""
        try:
            # 根据实际API结构调整
            if 'data' in data and 'items' in data['data']:
                items = data['data']['items']
                notes = []
                for item in items:
                    if 'note_card' in item:
                        notes.append(item['note_card'])
                return notes
            
            # 备选结构
            elif 'data' in data and 'notes' in data['data']:
                return data['data']['notes']
            
            else:
                print("  ⚠️ 无法识别的数据结构")
                print(f"  返回数据keys: {list(data.keys())}")
                return []
                
        except Exception as e:
            print(f"  ❌ 提取笔记失败: {e}")
            return []
    
    def _parse_note(self, note, keyword):
        """解析单条笔记"""
        try:
            note_info = {
                'keyword': keyword,
                'note_id': note.get('note_id', note.get('id', '')),
                'title': note.get('title', note.get('display_title', '')),
                'content': note.get('desc', note.get('content', '')),
                'type': note.get('type', ''),
                'likes': note.get('liked_count', note.get('likes', 0)),
                'comments': note.get('comment_count', note.get('comments', 0)),
                'collects': note.get('collected_count', note.get('collects', 0)),
                'shares': note.get('share_count', note.get('shares', 0)),
                'url': f"https://www.xiaohongshu.com/explore/{note.get('note_id', note.get('id', ''))}",
                'cover_url': '',
                'author_id': '',
                'author_name': '',
                'publish_time': '',
                'collected_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 提取作者信息
            if 'user' in note:
                user = note['user']
                note_info['author_id'] = user.get('user_id', user.get('id', ''))
                note_info['author_name'] = user.get('nickname', user.get('name', ''))
            
            # 提取封面图
            if 'cover' in note:
                cover = note['cover']
                if isinstance(cover, dict):
                    note_info['cover_url'] = cover.get('url', '')
                else:
                    note_info['cover_url'] = str(cover)
            
            # 提取发布时间
            if 'time' in note:
                note_info['publish_time'] = note['time']
            elif 'create_time' in note:
                note_info['publish_time'] = note['create_time']
            
            return note_info
            
        except Exception as e:
            print(f"  ⚠️ 解析笔记失败: {e}")
            return None
    
    def _save_progress(self):
        """保存进度"""
        if len(self.data_list) > 0:
            df = pd.DataFrame(self.data_list)
            backup_file = 'xiaohongshu_backup.csv'
            df.to_csv(backup_file, index=False, encoding='utf-8-sig')
            print(f"  💾 进度已保存: {backup_file}")
    
    def save_data(self, filename='xiaohongshu_data.csv'):
        """保存最终数据"""
        if len(self.data_list) == 0:
            print("\n⚠️ 没有数据可保存")
            return None
        
        print(f"\n{'='*70}")
        print("正在保存数据...")
        print(f"{'='*70}")
        
        # 创建DataFrame
        df = pd.DataFrame(self.data_list)
        
        # 去重
        before_dedup = len(df)
        df = df.drop_duplicates(subset=['note_id'])
        after_dedup = len(df)
        
        if before_dedup > after_dedup:
            print(f"✓ 去重: {before_dedup} → {after_dedup} (删除{before_dedup-after_dedup}条重复)")
        
        # 排序
        df = df.sort_values('likes', ascending=False)
        
        # 保存
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        print(f"✓ 数据已保存: {filename}")
        print(f"✓ 总计: {len(df)}条")
        
        # 统计信息
        self._print_statistics(df)
        
        return filename
    
    def _print_statistics(self, df):
        """打印统计信息"""
        print(f"\n{'='*70}")
        print("数据统计")
        print(f"{'='*70}")
        
        print(f"\n基本信息:")
        print(f"  • 总数据量: {len(df)}条")
        print(f"  • 关键词数: {df['keyword'].nunique()}个")
        print(f"  • 作者数: {df['author_name'].nunique()}人")
        
        print(f"\n互动数据:")
        print(f"  • 平均点赞: {df['likes'].mean():.0f}")
        print(f"  • 平均评论: {df['comments'].mean():.0f}")
        print(f"  • 平均收藏: {df['collects'].mean():.0f}")
        print(f"  • 最高点赞: {df['likes'].max()}")
        print(f"  • 最高评论: {df['comments'].max()}")
        
        print(f"\n内容类型:")
        if 'type' in df.columns:
            type_counts = df['type'].value_counts()
            for type_name, count in type_counts.items():
                print(f"  • {type_name}: {count}条")
        
        print(f"\nTop 5 热门笔记:")
        top5 = df.nlargest(5, 'likes')[['title', 'likes', 'comments', 'author_name']]
        for idx, row in top5.iterrows():
            title = row['title'][:30]
            print(f"  • {title}... (👍{row['likes']} 💬{row['comments']} by {row['author_name']})")
        
        # 时间统计
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        print(f"\n运行统计:")
        print(f"  • 运行时长: {elapsed/60:.1f}分钟")
        print(f"  • 成功请求: {self.stats['success_requests']}次")
        print(f"  • 失败请求: {self.stats['failed_requests']}次")
        print(f"  • 采集速度: {self.stats['total_collected']/(elapsed/60):.1f}条/分钟")
        
        print(f"\n{'='*70}")


def main():
    """主程序"""
    
    print("\n" + "="*70)
    print("  小红书数据采集器")
    print("="*70)
    
    # 检查cookie.txt是否存在
    if not os.path.exists('cookie.txt'):
        print("\n❌ 找不到 cookie.txt 文件")
        print("\n请按以下步骤创建：")
        print("1. 在当前目录创建一个名为 'cookie.txt' 的文本文件")
        print("2. 打开小红书网页版并登录")
        print("3. 按F12 → Network → 刷新页面 → 点击任意请求")
        print("4. 找到 Request Headers 中的 cookie")
        print("5. 复制cookie的完整内容到 cookie.txt")
        print("6. 保存文件后重新运行本程序")
        
        # 创建示例文件
        with open('cookie.txt.example', 'w', encoding='utf-8') as f:
            f.write("# 将你的Cookie粘贴到这里\n")
            f.write("# 删除这两行注释，只保留Cookie内容\n")
            f.write("# 示例：a1=xxx; webId=xxx; xsecappid=xhs-pc-web; ...\n")
        
        print("\n✓ 已创建示例文件: cookie.txt.example")
        print("  你可以参考这个文件的格式")
        
        return
    
    # 创建爬虫实例
    crawler = XiaohongshuCrawler('cookie.txt')
    
    # 测试连接
    if not crawler.test_connection():
        print("\n❌ Cookie验证失败，无法继续")
        print("\n请检查：")
        print("1. cookie.txt 中的Cookie是否完整")
        print("2. Cookie是否已过期（重新登录获取）")
        print("3. 网络连接是否正常")
        return
    
    # 用户输入
    print("\n" + "="*70)
    print("配置采集参数")
    print("="*70)
    
    # 关键词
    print("\n请输入搜索关键词（多个关键词用逗号分隔）")
    print("示例: 回长沙,长沙工作,逃离北上广回长沙")
    keywords_input = input("关键词: ").strip()
    
    if not keywords_input:
        keywords = ['回长沙', '长沙工作']
        print(f"使用默认关键词: {', '.join(keywords)}")
    else:
        keywords = [k.strip() for k in keywords_input.split(',')]
    
    # 每个关键词采集数量
    max_per_keyword = input("\n每个关键词采集多少条？(默认30，建议10-50): ").strip()
    max_per_keyword = int(max_per_keyword) if max_per_keyword else 30
    
    # 排序方式
    print("\n选择排序方式:")
    print("1. 综合排序（推荐）")
    print("2. 最新发布")
    print("3. 最热门")
    sort_choice = input("选择 (1/2/3，默认1): ").strip()
    
    sort_map = {'1': 'general', '2': 'time', '3': 'popular'}
    sort_type = sort_map.get(sort_choice, 'general')
    
    # 确认
    print("\n" + "="*70)
    print("采集配置确认")
    print("="*70)
    print(f"关键词: {', '.join(keywords)}")
    print(f"每个关键词: {max_per_keyword}条")
    print(f"预计总数: {len(keywords) * max_per_keyword}条")
    print(f"排序方式: {sort_type}")
    print(f"预计时长: {len(keywords) * max_per_keyword * 0.2:.0f}分钟")
    
    confirm = input("\n确认开始采集？(y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return
    
    # 开始采集
    print("\n" + "="*70)
    print("开始采集数据")
    print("="*70)
    print("提示: 按 Ctrl+C 可以随时中断")
    
    total_collected = 0
    
    try:
        for i, keyword in enumerate(keywords, 1):
            print(f"\n\n>>> 关键词 {i}/{len(keywords)}: {keyword}")
            collected = crawler.search_notes(keyword, max_per_keyword, sort_type)
            total_collected += collected
            
            # 关键词之间休息
            if i < len(keywords):
                rest_time = random.uniform(10, 20)
                print(f"\n⏸ 休息 {rest_time:.0f} 秒后继续下一个关键词...")
                time.sleep(rest_time)
    
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断采集")
    
    # 保存数据
    if total_collected > 0:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'xiaohongshu_data_{timestamp}.csv'
        crawler.save_data(filename)
        
        print("\n" + "="*70)
        print("采集完成！")
        print("="*70)
        print(f"\n下一步:")
        print(f"1. 查看数据文件: {filename}")
        print(f"2. 运行分析脚本: python data_analysis.py")
        print(f"3. 生成可视化图表和报告")
    else:
        print("\n❌ 没有采集到数据")
        print("\n可能的原因：")
        print("1. 关键词没有结果")
        print("2. Cookie已失效")
        print("3. 网络问题")
        print("4. API接口已变更")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n❌ 程序异常: {e}")
        print("\n如果问题持续，请：")
        print("1. 检查Cookie是否有效")
        print("2. 检查网络连接")
        print("3. 尝试重新运行程序")