from sqlalchemy import select, delete, and_, desc, func
from database import AsyncSessionLocal
from models import UserFavorite, MovieSummary, UserRating



async def get_my_favorites_count(user_id: int):
    async with AsyncSessionLocal() as db:
        stmt = select(func.count(UserFavorite.id)).where(UserFavorite.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar()

async def get_my_ratings_count(user_id: int):
    async with AsyncSessionLocal() as db:
        stmt = select(func.count(UserRating.id)).where(UserRating.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar()

# --- 增/删 (Toggle) ---
async def toggle_favorite(user_id: int, tconst: str):
    """
    切换收藏状态 (原子操作优化)
    """
    async with AsyncSessionLocal() as db:
        # 1. 查询是否存在
        stmt = select(UserFavorite).where(
            and_(UserFavorite.user_id == user_id, UserFavorite.tconst == tconst)
        )
        result = await db.execute(stmt)
        record = result.scalars().first()

        if record:
            # 存在 -> 删除
            await db.delete(record)
            msg = "已取消收藏"
            is_fav = False
        else:
            # 不存在 -> 新增
            new_fav = UserFavorite(user_id=user_id, tconst=tconst)
            db.add(new_fav)
            msg = "收藏成功"
            is_fav = True

        await db.commit()
        return is_fav, msg


# --- 查 (List - 性能优化版) ---
async def get_my_favorites_paginated(user_id: int, page: int = 1, page_size: int = 20):
    """
    【性能优化】直接联表查询 MovieSummary，一次性返回电影详情
    """
    offset = (page - 1) * page_size
    async with AsyncSessionLocal() as db:
        # Select MovieSummary ... Join UserFavorite
        stmt = (
            select(MovieSummary)
            .join(UserFavorite, MovieSummary.tconst == UserFavorite.tconst)
            .where(UserFavorite.user_id == user_id)
            .order_by(desc(UserFavorite.created_at))  # 按收藏时间倒序
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        return result.scalars().all()


async def get_user_favorite_ids(user_id: int):
    """获取用户所有收藏的ID集合 (用于前端高亮状态判断)"""
    async with AsyncSessionLocal() as db:
        stmt = select(UserFavorite.tconst).where(UserFavorite.user_id == user_id)
        result = await db.execute(stmt)
        return set(result.scalars().all())


# --- 评分相关 (保留) ---
async def set_user_rating(user_id: int, tconst: str, score: float):
    async with AsyncSessionLocal() as db:
        stmt = select(UserRating).where(and_(UserRating.user_id == user_id, UserRating.tconst == tconst))
        result = await db.execute(stmt)
        record = result.scalars().first()
        if record:
            record.rating = score
        else:
            db.add(UserRating(user_id=user_id, tconst=tconst, rating=score))
        await db.commit()


async def get_user_ratings_map(user_id: int):
    async with AsyncSessionLocal() as db:
        stmt = select(UserRating).where(UserRating.user_id == user_id)
        result = await db.execute(stmt)
        return {r.tconst: r.rating for r in result.scalars().all()}


async def get_my_ratings_paginated(user_id: int, page: int = 1, page_size: int = 20):
    """分页获取我的个人评分记录，并关联电影基本信息"""
    offset = (page - 1) * page_size
    async with AsyncSessionLocal() as db:
        # 联表查询 UserRating 和 MovieSummary (或 TitleBasics)
        stmt = (
            select(UserRating, MovieSummary.primaryTitle)
            .join(MovieSummary, UserRating.tconst == MovieSummary.tconst)
            .where(UserRating.user_id == user_id)
            .order_by(desc(UserRating.created_at))
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        return result.all() # 返回 (UserRating对象, 电影名) 的列表

async def delete_user_rating(user_id: int, tconst: str):
    """物理删除某条评分记录"""
    async with AsyncSessionLocal() as db:
        try:
            stmt = delete(UserRating).where(
                and_(UserRating.user_id == user_id, UserRating.tconst == tconst)
            )
            await db.execute(stmt)
            await db.commit()
            return True, "删除成功"
        except Exception as e:
            await db.rollback()
            return False, str(e)