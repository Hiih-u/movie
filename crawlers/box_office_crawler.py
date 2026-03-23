import sys
import os
import asyncio
import httpx
import random
from bs4 import BeautifulSoup
from sqlalchemy import select, update, desc
from sqlalchemy.dialects.postgresql import insert

# --- 环境配置 ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import AsyncSessionLocal
from models import TitleBasics, TitleRatings, MovieBoxOffice

# --- 爬虫配置 ---
TARGET_COUNT = 600  # 目标: Top 1000
CONCURRENCY = 8  # 并发数

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}


async def fetch_mojo_box_office(client, tconst):
    url = f"https://www.boxofficemojo.com/title/{tconst}/"
    try:
        await asyncio.sleep(random.uniform(0.5, 1.5))  # 随机延迟
        resp = await client.get(url)
        if resp.status_code != 200: return None

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 提取全球票房 (Worldwide Lifetime Gross)
        performance_div = soup.find('div', class_='mojo-performance-summary-table')
        if not performance_div: return None

        spans = performance_div.find_all('span', class_='money')
        if not spans: return None

        # 提取货币格式字符串并清洗为整数
        max_money = 0
        for span in spans:
            text = span.get_text().strip().replace('$', '').replace(',', '')
            if text.isdigit():
                val = int(text)
                if val > max_money:
                    max_money = val
        return max_money
    except Exception:
        return None


async def worker(queue, client, db):
    while True:
        data = await queue.get()
        tconst, title, rank = data

        try:
            money = await fetch_mojo_box_office(client, tconst)

            if money:
                print(f"✅ [Rank {rank}] {title[:15]}... ${money:,}")

                # 使用 Upsert (有则更新，无则插入)
                stmt = insert(MovieBoxOffice).values(
                    tconst=tconst,
                    box_office=money,
                    rank=rank
                ).on_conflict_do_update(
                    index_elements=['tconst'],
                    set_=dict(box_office=money, rank=rank)
                )
                await db.execute(stmt)
                await db.commit()
            else:
                print(f"⚪ [Rank {rank}] {title[:15]}... 无数据")

        except Exception as e:
            print(f"❌ Error {tconst}: {e}")
            await db.rollback()
        finally:
            queue.task_done()


async def main():
    print(f"🚀 开始爬取 Top {TARGET_COUNT} 热门电影票房...")

    async with AsyncSessionLocal() as db:
        # 1. 选取 Top 1000 (按投票数 numVotes 倒序)
        stmt = (
            select(TitleBasics.tconst, TitleBasics.primaryTitle)
            .join(TitleRatings, TitleBasics.tconst == TitleRatings.tconst)
            .where(TitleBasics.titleType == 'movie')
            .order_by(desc(TitleRatings.numVotes))
            .limit(TARGET_COUNT)
        )
        result = await db.execute(stmt)
        movies = result.all()  # [(tconst, title), ...]

        print(f"📋 已加载 {len(movies)} 部电影，启动爬虫...")

        queue = asyncio.Queue()
        for idx, (tconst, title) in enumerate(movies):
            # idx+1 就是 rank
            queue.put_nowait((tconst, title, idx + 1))

        async with httpx.AsyncClient(headers=HEADERS, timeout=15.0) as client:
            tasks = [asyncio.create_task(worker(queue, client, db)) for _ in range(CONCURRENCY)]
            await queue.join()
            for task in tasks: task.cancel()

    print("\n🎉 爬取结束！数据已存入 movie_box_office 表。")


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())