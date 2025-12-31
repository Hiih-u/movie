from sqlalchemy import select, func, update, delete
from database import AsyncSessionLocal
from models import TitleCrew, TitleBasics

async def get_crew_count():
    """获取剧组信息总条数"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(func.count(TitleCrew.tconst)))
        return result.scalar()

async def get_crew_paginated(page: int, page_size: int):
    """
    分页获取剧组列表
    联表查询 TitleBasics 以便显示电影名称
    """
    offset = (page - 1) * page_size
    async with AsyncSessionLocal() as db:
        stmt = (
            select(TitleCrew, TitleBasics.primaryTitle)
            .join(TitleBasics, TitleCrew.tconst == TitleBasics.tconst)
            .order_by(TitleCrew.tconst)
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        return result.all()

async def create_crew(tconst, directors, writers):
    """新增剧组信息"""
    async with AsyncSessionLocal() as db:
        try:
            # 1. 检查电影是否存在
            movie = await db.execute(select(TitleBasics).where(TitleBasics.tconst == tconst))
            if not movie.scalar():
                return False, f"电影编号 {tconst} 不存在"

            # 2. 检查是否已存在记录
            existing = await db.execute(select(TitleCrew).where(TitleCrew.tconst == tconst))
            if existing.scalar():
                return False, f"电影 {tconst} 的剧组信息已存在"

            new_crew = TitleCrew(
                tconst=tconst,
                directors=directors,
                writers=writers
            )
            db.add(new_crew)
            await db.commit()
            return True, "创建成功"
        except Exception as e:
            await db.rollback()
            return False, f"数据库错误: {str(e)}"

async def update_crew(tconst, directors, writers):
    """更新剧组信息"""
    async with AsyncSessionLocal() as db:
        try:
            stmt = (
                update(TitleCrew)
                .where(TitleCrew.tconst == tconst)
                .values(directors=directors, writers=writers)
            )
            await db.execute(stmt)
            await db.commit()
            return True, "更新成功"
        except Exception as e:
            await db.rollback()
            return False, str(e)

async def delete_crew(tconst):
    """删除剧组信息"""
    async with AsyncSessionLocal() as db:
        try:
            await db.execute(delete(TitleCrew).where(TitleCrew.tconst == tconst))
            await db.commit()
            return True, "删除成功"
        except Exception as e:
            await db.rollback()
            return False, str(e)