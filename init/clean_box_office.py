import sys
import os
import asyncio
from sqlalchemy import delete, select, func

# 路径修正
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import AsyncSessionLocal
from models import MovieBoxOffice


async def clean_data():
    print("🧹 开始清洗票房数据...")
    async with AsyncSessionLocal() as db:
        # 1. 统计清洗前数量
        total = await db.execute(select(func.count()).select_from(MovieBoxOffice))
        total_count = total.scalar()

        # 2. 删除 box_office 为空的记录
        stmt = delete(MovieBoxOffice).where(MovieBoxOffice.box_office == None)
        result = await db.execute(stmt)
        deleted_count = result.rowcount

        await db.commit()

        # 3. 统计剩余有效数量
        remaining = total_count - deleted_count
        print(f"✅ 清洗完成！")
        print(f"   - 删除无效数据: {deleted_count} 条")
        print(f"   - 剩余有效样本: {remaining} 条")


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(clean_data())