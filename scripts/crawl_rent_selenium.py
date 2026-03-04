from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import random

def crawl_lianjia_with_login():
    print("🚀 正在启动模拟浏览器...")
    options = webdriver.ChromeOptions()
    # 屏蔽自动化特征
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # --- 🛑 关键修改步骤：人工登录环节 🛑 ---
    try:
        # 1. 先打开登录页或首页
        login_url = "https://cs.lianjia.com/" 
        driver.get(login_url)
        
        print("\n" + "="*50)
        print("🚨 【请手动操作】 🚨")
        print("1. 浏览器已打开，请在网页上点击‘登录’（通常在右上角）。")
        print("2. 使用手机扫码登录，直到你看到网页右上角显示了你的头像。")
        print("3. 确认登录成功后，请回到这里（终端窗口）。")
        # 这一行代码会让程序“死等”，直到你按回车，绝不会自动刷新打断你
        input("👉 登录好了吗？请按【回车键 (Enter)】继续运行爬虫...") 
        print("="*50 + "\n")
        
        # --- 登录完成，开始正式干活 ---
        all_data = []
        base_url = "https://cs.lianjia.com/zufang/pg{}/"
        total_pages = 3 

        for page in range(1, total_pages + 1):
            url = base_url.format(page)
            print(f"🌐 正在访问第 {page} 页: {url}")
            driver.get(url) # 这时候已经是登录状态了，不会再弹窗

            # 等待房源加载
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "content__list--item"))
                )
            except:
                print("⚠️ 等待超时，可能该页无数据。")

            items = driver.find_elements(By.CLASS_NAME, "content__list--item")
            print(f"   ✅ 抓取到 {len(items)} 套房源...")

            for item in items:
                try:
                    # 提取逻辑保持不变
                    title = item.find_element(By.CLASS_NAME, "content__list--item--title").text.strip()
                    desc = item.find_element(By.CLASS_NAME, "content__list--item--des").text.strip()
                    parts = desc.split('-')
                    district = parts[0].strip() if len(parts) > 0 else "未知"
                    sub_district = parts[1].strip() if len(parts) > 1 else "未知"
                    
                    area = "0"
                    for p in parts:
                        if '㎡' in p:
                            area = p.replace('㎡', '').strip()
                            break
                    
                    price_text = item.find_element(By.CLASS_NAME, "content__list--item-price").text.strip()
                    price = price_text.replace("元/月", "").strip()

                    all_data.append({
                        "区域": district,
                        "商圈": sub_district,
                        "房源标题": title,
                        "面积": area,
                        "租金": price
                    })
                except:
                    continue
            
            time.sleep(random.uniform(2, 4)) # 模拟人类翻页停顿

    except Exception as e:
        print(f"❌ 出错啦: {e}")
    
    finally:
        driver.quit()
        if all_data:
            df = pd.DataFrame(all_data)
            df.to_csv("changsha_rent_selenium.csv", index=False, encoding='utf-8-sig')
            print(f"\n🎉 成功抓取 {len(df)} 条数据！已保存。")
        else:
            print("\n😭 依然没有抓到数据，请检查登录是否成功。")

if __name__ == "__main__":
    crawl_lianjia_with_login()