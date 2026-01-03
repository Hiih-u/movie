from sqlalchemy import select, delete, and_
from database import AsyncSessionLocal
from models import UserFavorite, UserRating


# --- 收藏功能 ---

async def toggle_favorite(user_id: int, tconst: str):
    """切换收藏状态：如果已收藏则取消，未收藏则添加"""
    async with AsyncSessionLocal() as db:
        # 1. 查询是否存在
        stmt = select(UserFavorite).where(
            and_(UserFavorite.user_id == user_id, UserFavorite.tconst == tconst)
        )
        result = await db.execute(stmt)
        record = result.scalars().first()

        if record:
            # 已存在 -> 删除 (取消收藏)
            await db.delete(record)
            await db.commit()
            return False, "已取消收藏"
        else:
            # 不存在 -> 添加
            new_fav = UserFavorite(user_id=user_id, tconst=tconst)
            db.add(new_fav)
            await db.commit()
            return True, "收藏成功"


async def get_user_favorites(user_id: int):
    """获取用户所有收藏的电影ID集合 (用于前端高亮显示)"""
    async with AsyncSessionLocal() as db:
        stmt = select(UserFavorite.tconst).where(UserFavorite.user_id == user_id)
        result = await db.execute(stmt)
        return set(result.scalars().all())


# --- 评分功能 ---

async def set_user_rating(user_id: int, tconst: str, score: float):
    """设置或更新用户评分"""
    async with AsyncSessionLocal() as db:
        # 1. 查询旧评分
        stmt = select(UserRating).where(
            and_(UserRating.user_id == user_id, UserRating.tconst == tconst)
        )
        result = await db.execute(stmt)
        record = result.scalars().first()

        if record:
            record.rating = score  # 更新
        else:
            new_rating = UserRating(user_id=user_id, tconst=tconst, rating=score)  # 新增
            db.add(new_rating)

        await db.commit()
        return True, "评分已保存"


async def get_user_ratings_map(user_id: int):
    """获取用户对所有电影的评分字典 {tconst: score}"""
    async with AsyncSessionLocal() as db:
        stmt = select(UserRating).where(UserRating.user_id == user_id)
        result = await db.execute(stmt)
        # 返回 { 'tt12345': 8.5, ... }
        return {r.tconst: r.rating for r in result.scalars().all()}