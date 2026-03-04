import pandas as pd
import requests
import json
import time
import random

# --- 1. 复用你之前的爬虫函数 (稍作优化，增加容错) ---
def get_migration_data(date, city_code="430100", move_type="move_in"):
    url = "https://huiyan.baidu.com/migration/cityrank.jsonp"
    params = {"dt": "city", "id": city_code, "type": move_type, "date": date}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0",
        "Referer": "https://huiyan.baidu.com/migration/province.html"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        content = response.text
        # 处理 jsonp
        json_str = content[content.find("({") + 1 : content.find("})") + 1]
        data = json.loads(json_str)
        
        if data['errmsg'] == 'SUCCESS':
            df = pd.DataFrame(data['data']['list'])
            df['date'] = date  # 这一步很关键：加上日期标签
            return df
        else:
            print(f"[{date}] 接口报错: {data['errmsg']}")
            return pd.DataFrame()
    except Exception as e:
        print(f"[{date}] 请求异常: {e}")
        return pd.DataFrame()

# --- 2. 批量执行主程序 ---

# 设定你想抓取的时间段（例如：最近30天，或者覆盖春节假期）
# 建议：包含“平日”和“周末”，看看是否有周期性波动
start_date = "20251220" 
end_date = "20260120"

# 生成日期列表
date_range = pd.date_range(start=start_date, end=end_date, freq='D').strftime('%Y%m%d').tolist()

all_data = []
print(f"开始抓取 {start_date} 到 {end_date} 的数据，共 {len(date_range)} 天...")

for date in date_range:
    print(f"正在抓取: {date} ...")
    df_daily = get_migration_data(date)
    
    if not df_daily.empty:
        all_data.append(df_daily)
    
    # !!! 关键：反爬虫机制，每次抓完歇 1-3 秒，防止IP被封
    time.sleep(random.uniform(1, 3))

# --- 3. 合并保存 ---
if all_data:
    final_df = pd.concat(all_data, ignore_index=True)
    # 保存为 CSV，作为你的“数据仓库”底表
    final_df.to_csv("changsha_migration_30days.csv", index=False, encoding='utf-8-sig')
    print(f"成功！数据已保存，共 {len(final_df)} 条记录。")
    print(final_df.head())
else:
    print("未能抓取到任何数据。")