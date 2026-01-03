# init_db.py
import asyncio
from database import engine, Base
from models import TitleBasics, TitleRatings, User, UserFavorite, UserRating, MovieSummary, TitleCrew, NameBasics


async def init_models():
    print("正在连接数据库并检查表结构...")
    async with engine.begin() as conn:
        # 这一步会创建所有 models.py 里定义但数据库里不存在的表
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表结构同步完成！")


if __name__ == "__main__":
    # Windows 下运行 asyncio 可能需要的补丁
    import sys

    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(init_models())