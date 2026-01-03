import asyncio
from sqlalchemy import text
from database import engine

async def add_indexes():
    async with engine.begin() as conn:
        print("正在为 title_basics 表添加索引，数据量大可能需要几分钟...")
        # 为 titleType 添加索引，加速 WHERE titletype IN (...)
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_title_basics_titletype ON title_basics (titletype)"))
        # 为 primaryTitle 添加索引，加速搜索
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_title_basics_primarytitle ON title_basics (primarytitle)"))
        print("✅ 索引添加完成！")

if __name__ == "__main__":
    # Windows 补丁
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(add_indexes())