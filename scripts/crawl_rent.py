import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

# --- 爬虫配置 ---
BASE_URL = "https://cs.lianjia.com/zufang/pg{}/"  # 长沙链家租房列表页
TOTAL_PAGES = 5  # 建议先爬 5-10 页测试，太多容易被封 IP

def get_rent_data():
    all_data = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print(f"🚀 开始抓取长沙租房数据，计划抓取 {TOTAL_PAGES} 页...")

    for page in range(1, TOTAL_PAGES + 1):
        url = BASE_URL.format(page)
        print(f"   正在抓取第 {page} 页: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"   ⚠️ 第 {page} 页访问失败 (状态码: {response.status_code})")
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # 链家租房列表的每一个房源都在 .content__list--item 这个类里
            items = soup.find_all("div", class_="content__list--item")
            
            if not items:
                print("   ⚠️ 未找到房源数据，可能是反爬虫策略生效，请稍后再试。")
                break

            for item in items:
                try:
                    # 1. 提取标题 (包含小区名)
                    title = item.find("p", class_="content__list--item--title").get_text(strip=True)
                    
                    # 2. 提取区域和面积 (在 desc 类里)
                    # 格式通常是：岳麓-梅溪湖-达美溪湖湾-1室1厅1卫-45㎡...
                    desc_text = item.find("p", class_="content__list--item--des").get_text(strip=True)
                    desc_parts = desc_text.split('-')
                    
                    district = desc_parts[0].strip() if len(desc_parts) > 0 else "未知"
                    sub_district = desc_parts[1].strip() if len(desc_parts) > 1 else "未知"
                    area = "0"
                    # 简单粗暴找面积：遍历分割后的文本，找到带"㎡"的那个
                    for part in desc_parts:
                        if '㎡' in part:
                            area = part.replace('㎡', '').strip()
                            break
                    
                    # 3. 提取价格
                    price_span = item.find("span", class_="content__list--item-price")
                    price = price_span.get_text(strip=True).replace('元/月', '')
                    
                    all_data.append({
                        "区域": district,
                        "商圈": sub_district,
                        "小区/标题": title,
                        "面积(㎡)": area,
                        "租金(元/月)": price
                    })
                except Exception as e:
                    # 某一条解析失败不影响整体
                    continue
            
            # 关键：每爬一页休息 3-6 秒，模仿人类浏览，防止被封
            sleep_time = random.uniform(3, 6)
            time.sleep(sleep_time)

        except Exception as e:
            print(f"   ❌ 网络请求报错: {e}")
            break

    # --- 保存数据 ---
    if all_data:
        df = pd.DataFrame(all_data)
        # 清洗数据：把租金转为数字类型，方便后续计算
        df['租金(元/月)'] = pd.to_numeric(df['租金(元/月)'], errors='coerce')
        df['面积(㎡)'] = pd.to_numeric(df['面积(㎡)'], errors='coerce')
        
        filename = "changsha_rent.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n✅ 抓取完成！共获取 {len(df)} 条数据，已保存为 {filename}")
        print("📊 数据预览：")
        print(df.head())
        
        # 🎁 附赠一个小分析：计算各区平均租金
        print("\n🧐 初步分析：各区域平均租金")
        print(df.groupby('区域')['租金(元/月)'].mean().sort_values(ascending=False))
    else:
        print("\n❌ 哎呀，没有抓取到数据，可能是链家检测到了爬虫。")

if __name__ == "__main__":
    get_rent_data()