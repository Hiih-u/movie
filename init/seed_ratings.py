# init/seed_ratings.py
import asyncio
import random
import sys
import os

# --- 路径修正：确保能导入项目根目录的模块 ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from database import AsyncSessionLocal
from models import User, MovieSummary, UserRating, TitleBasics, UserFavorite  # 【新增】UserFavorite
from services.auth_service import get_password_hash

# --- 配置区域 ---
NUM_FAKE_USERS = 50  # 生成 50 个虚拟用户
RATINGS_PER_USER = 20  # 每个用户评 20 部电影
FAVORITES_PER_USER = 5  # 【新增】每个用户收藏 5 部电影
TARGET_TOP_MOVIES = 200  # 评分池范围

# 职业列表
OCCUPATIONS = [
    "Student (学生)", "Engineer (工程师)", "Programmer (程序员)",
    "Educator (教育工作者)", "Scientist (科学家)", "Artist (艺术家)",
    "Administrator (行政/管理)", "Technician (技术人员)", "Writer (作家)",
    "Healthcare (医疗/护理)", "Entertainment (娱乐/演艺)", "Executive (高管)",
    "Lawyer (律师)", "Marketing (市场/营销)", "Sales (销售)",
    "Retired (退休)", "Unemployed (待业)", "Other (其他)"
]


async def seed_data():
    print(f"🚀 开始生成全量模拟数据...")
    print(f"   - 用户数: {NUM_FAKE_USERS}")
    print(f"   - 每个人: {RATINGS_PER_USER} 条评分 + {FAVORITES_PER_USER} 条收藏")

    async with AsyncSessionLocal() as db:
        # 1. 准备热门电影列表
        try:
            stmt = select(MovieSummary.tconst).order_by(MovieSummary.numVotes.desc().nulls_last()).limit(
                TARGET_TOP_MOVIES)
            res = await db.execute(stmt)
            movie_ids = res.scalars().all()
        except Exception:
            print("   (movie_summary 为空，尝试读取 title_basics...)")
            stmt = select(TitleBasics.tconst).limit(TARGET_TOP_MOVIES)
            res = await db.execute(stmt)
            movie_ids = res.scalars().all()

        if not movie_ids:
            print("❌ 错误：数据库里没有电影数据！")
            return

        print(f"✅ 锁定热门电影池：{len(movie_ids)} 部")

        # 2. 批量创建/获取虚拟用户
        base_password = get_password_hash("123456")
        created_count = 0

        for i in range(NUM_FAKE_USERS):
            username = f"bot_user_{i + 1:03d}"
            exists = await db.execute(select(User).where(User.username == username))
            if not exists.scalar():
                user = User(
                    username=username,
                    hashed_password=base_password,
                    role='user',
                    gender=random.choice(['M', 'F']),
                    age=random.randint(18, 60),
                    occupation=random.choice(OCCUPATIONS)
                )
                db.add(user)
                created_count += 1

        await db.commit()
        if created_count > 0:
            print(f"✅ 新增虚拟用户：{created_count} 个")

        # 3. 获取所有 bot 用户
        stmt_users = select(User).where(User.username.like("bot_user_%"))
        res_users = await db.execute(stmt_users)
        all_bots = res_users.scalars().all()

        if not all_bots:
            return

        # 4. 生成评分 & 收藏
        new_ratings = []
        new_favorites = []

        print("⏳ 正在计算互动数据...")
        for user in all_bots:
            # --- A. 生成评分 ---
            # 随机选 N 部电影评分
            rate_movies = random.sample(movie_ids, min(len(movie_ids), RATINGS_PER_USER))
            for tconst in rate_movies:
                score = round(random.uniform(3.0, 10.0), 1)
                new_ratings.append(UserRating(user_id=user.id, tconst=tconst, rating=score))

            # --- B. 生成收藏 (新增逻辑) ---
            # 随机选 N 部电影收藏 (可以和评分的电影重叠，这很正常)
            fav_movies = random.sample(movie_ids, min(len(movie_ids), FAVORITES_PER_USER))
            for tconst in fav_movies:
                new_favorites.append(UserFavorite(user_id=user.id, tconst=tconst))

        # 5. 批量写入 (分开写入以处理异常)

        # 写入评分
        try:
            if new_ratings:
                # 簡單去重逻辑太复杂，直接依赖数据库不做处理，或者分批
                # 这里为了演示方便，采用“暴力尝试”法，实际生产应用 insert on conflict
                for i in range(0, len(new_ratings), 500):
                    db.add_all(new_ratings[i:i + 500])
                    await db.commit()
                print(f"✅ 评分数据写入尝试完成 (目标: {len(new_ratings)} 条)")
        except Exception as e:
            await db.rollback()
            print(f"⚠️ 评分写入部分跳过 (可能是重复): {e}")

        # 写入收藏
        try:
            if new_favorites:
                for i in range(0, len(new_favorites), 500):
                    db.add_all(new_favorites[i:i + 500])
                    await db.commit()
                print(f"✅ 收藏数据写入尝试完成 (目标: {len(new_favorites)} 条)")
        except Exception as e:
            await db.rollback()
            print(f"⚠️ 收藏写入部分跳过 (可能是重复): {e}")

    print("\n🎉 全量数据播种完成！推荐算法现在有充足的“燃料”了。")


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_data())