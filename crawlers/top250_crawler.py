import asyncio
import sys
import os
import requests
import random
from bs4 import BeautifulSoup
from sqlalchemy import select

# --- 1. 路径修正 ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import AsyncSessionLocal
from models import DoubanTop250

# --- 2. 配置区域 ---
# ⚠️ 再次提醒：Cookie 里千万不要有中文分号“；”或中文空格！
MY_COOKIE = 'bid=y2xgMqYFOWE; ll="118201"; _pk_id.100001.4cf6=c498acd40280612b.1770192901.; ap_v=0,6.0; __utmc=30149280; __utmc=223695111; _vwo_uuid_v2=DAE213609D9893E45625F230F8AFF1C92|049f0b004d334026a253c53f406c10e6; _pk_ref.100001.4cf6=%5B%22%22%2C%22%22%2C1770196161%2C%22https%3A%2F%2Fsec.douban.com%2F%22%5D; _pk_ses.100001.4cf6=1; __utma=30149280.1600214363.1764764606.1770192904.1770196164.3; __utmz=30149280.1770196164.3.3.utmcsr=sec.douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/; __utma=223695111.2006860426.1770192904.1770192904.1770196164.2; __utmz=223695111.1770196164.2.2.utmcsr=sec.douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/; __utmt=1; __utmt=1; __utmb=30149280.2.10.1770196164; dbsawcv1=MTc3MDE5Njc1MUBlNzliMDdkYzI1NjRjYWMxOGE3MTZiNWM4Y2RiODhmODU2ZDA2YTc1YzBhYWYzZGRhY2EyZDdjNGVlMDYyNGZmQDhmZTEzZjU2YmZmMzYyNzVANWQ3MTg2MjhkNThh; __utmb=223695111.4.10.1770196164'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://movie.douban.com/top250',
    'Cookie': MY_COOKIE
}


async def crawl_list_only():
    print("🚀 启动极速模式：仅爬取 Top 250 列表页 (不进详情)...")

    # 简单的检查
    if '这里填' in HEADERS['Cookie']:
        print("❌ 错误：请先在代码中填入 Cookie！")
        return

    base_url = "https://movie.douban.com/top250"

    async with AsyncSessionLocal() as db:
        # Top 250 一共 10 页，每页 25 条
        for start in range(0, 250, 25):
            page_num = start // 25 + 1
            print(f"\n📄 正在抓取第 {page_num} 页 (排名 {start + 1}-{start + 25})...")

            url = f"{base_url}?start={start}"

            try:
                # 随机休眠 1-3 秒即可，列表页限制很宽
                await asyncio.sleep(random.uniform(1, 3))

                resp = requests.get(url, headers=HEADERS, timeout=10)
                if resp.status_code != 200:
                    print(f"❌ 请求失败: {resp.status_code}")
                    continue

                soup = BeautifulSoup(resp.text, 'html.parser')
                items = soup.find_all('div', class_='item')

                if not items:
                    print("⚠️ 本页未找到数据，可能被反爬或已结束。")

                # --- 批量处理本页数据 ---
                for item in items:
                    # 1. 抓取基础字段
                    rank = int(item.find('em').get_text())

                    # 标题 (有的电影有多个标题，取第一个)
                    title_span = item.find('span', class_='title')
                    title = title_span.get_text() if title_span else "未知标题"

                    # 链接 & ID
                    link = item.find('div', class_='hd').find('a')['href']
                    douban_id = link.strip('/').split('/')[-1]

                    # 评分
                    rating_num = float(item.find('span', class_='rating_num').get_text())

                    print(f"   [{rank}] {title} (ID:{douban_id})", end="", flush=True)

                    # 2. 存入数据库
                    # 检查是否存在
                    stmt = select(DoubanTop250).where(DoubanTop250.douban_id == douban_id)
                    result = await db.execute(stmt)
                    record = result.scalars().first()

                    if record:
                        # 更新基本信息 (保留原有的 imdb_id，防止覆盖掉已经手动补全的)
                        record.rank = rank
                        record.title = title
                        record.douban_score = rating_num
                        print(" -> 更新", end="")
                    else:
                        # 新增
                        new_movie = DoubanTop250(
                            rank=rank,
                            title=title,
                            douban_id=douban_id,
                            imdb_id=None,  # 暂时留空，以后再补
                            douban_score=rating_num
                        )
                        db.add(new_movie)
                        print(" -> 新增", end="")

                await db.commit()
                print("\n💾 保存成功！")

            except Exception as e:
                print(f"\n❌ 本页发生错误: {e}")

    print("\n🎉 爬取结束！数据已入库。")


if __name__ == "__main__":
    # Windows 平台补丁
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(crawl_list_only())