from sqlalchemy import select, func, update, delete, or_
from database import AsyncSessionLocal
from models import TitleRatings, TitleBasics


async def get_rating_count(search_query=None):
    """获取评分总数 (支持搜索)"""
    async with AsyncSessionLocal() as db:
        query = select(func.count(TitleRatings.tconst))

        # 如果有搜索内容，需要添加过滤条件
        if search_query:
            # 必须联表才能搜到 primaryTitle
            query = query.join(TitleBasics, TitleRatings.tconst == TitleBasics.tconst)
            query = query.where(
                or_(
                    TitleBasics.primaryTitle.ilike(f"%{search_query}%"),  # 搜电影名
                    TitleRatings.tconst.ilike(f"%{search_query}%")  # 搜编号
                )
            )

        result = await db.execute(query)
        return result.scalar()


async def get_ratings_paginated(page: int, page_size: int, search_query=None):
    """
    分页获取评分列表 (支持搜索)
    注意：这里我们做了一个联表查询(join)，为了在列表中直接显示电影名字，
    而不是只显示冷冰冰的 tconst 编号。
    """
    offset = (page - 1) * page_size
    async with AsyncSessionLocal() as db:
        # 基础查询 (已经包含了 Join)
        stmt = (
            select(TitleRatings, TitleBasics.primaryTitle)
            .join(TitleBasics, TitleRatings.tconst == TitleBasics.tconst)
        )

        # 如果有搜索内容，添加过滤条件
        if search_query:
            stmt = stmt.where(
                or_(
                    TitleBasics.primaryTitle.ilike(f"%{search_query}%"),  # 搜电影名
                    TitleRatings.tconst.ilike(f"%{search_query}%")  # 搜编号
                )
            )

        # 排序并分页
        stmt = stmt.order_by(TitleRatings.tconst).offset(offset).limit(page_size)

        result = await db.execute(stmt)
        # 返回的是 [(TitleRatings对象, 电影名字符串), ...] 的列表
        return result.all()

async def create_rating(tconst, average_rating, num_votes):
    """新增评分"""
    async with AsyncSessionLocal() as db:
        try:
            # 1. 检查电影是否存在 (外键约束)
            movie = await db.execute(select(TitleBasics).where(TitleBasics.tconst == tconst))
            if not movie.scalar():
                return False, f"电影编号 {tconst} 不存在，无法添加评分"

            # 2. 检查该电影是否已有评分 (主键唯一)
            existing = await db.execute(select(TitleRatings).where(TitleRatings.tconst == tconst))
            if existing.scalar():
                return False, f"电影 {tconst} 已经存在评分记录"

            # 3. 插入数据
            new_rating = TitleRatings(
                tconst=tconst,
                averageRating=average_rating,
                numVotes=num_votes
            )
            db.add(new_rating)
            await db.commit()
            return True, "创建成功"
        except Exception as e:
            await db.rollback()
            return False, f"数据库错误: {str(e)}"

async def update_rating(tconst, average_rating, num_votes):
    """更新评分"""
    async with AsyncSessionLocal() as db:
        try:
            stmt = (
                update(TitleRatings)
                .where(TitleRatings.tconst == tconst)
                .values(averageRating=average_rating, numVotes=num_votes)
            )
            await db.execute(stmt)
            await db.commit()
            return True, "更新成功"
        except Exception as e:
            await db.rollback()
            return False, str(e)

async def delete_rating(tconst):
    """删除评分"""
    async with AsyncSessionLocal() as db:
        try:
            await db.execute(delete(TitleRatings).where(TitleRatings.tconst == tconst))
            await db.commit()
            return True, "删除成功"
        except Exception as e:
            await db.rollback()
            return False, str(e)