from sqlalchemy import select, func, desc, update, delete
from database import AsyncSessionLocal
from models import TitleBasics, TitleRatings

# --- 数据库操作逻辑 (CRUD) ---

async def create_movie(tconst, title, year, genres):
    """
    【新增】创建一部新电影
    :param tconst: 电影唯一编号 (如 tt1234567)
    :param title: 电影标题
    :param year: 上映年份
    :param genres: 类型字符串
    """
    async with AsyncSessionLocal() as db:
        try:
            # 1. 检查 ID 是否已存在
            existing = await db.execute(select(TitleBasics).where(TitleBasics.tconst == tconst))
            if existing.scalar():
                return False, f"编号 {tconst} 已存在，请更换"

            # 2. 构造新对象
            new_movie = TitleBasics(
                tconst=tconst,
                titleType='movie',
                primaryTitle=title,
                originalTitle=title, # 默认原名与现名一致
                isAdult=0,          # 默认非成人内容
                startYear=year,
                genres=genres
            )
            db.add(new_movie)
            await db.commit()
            return True, "创建成功"
        except Exception as e:
            print(f"创建失败: {e}")
            await db.rollback()
            return False, f"数据库错误: {str(e)}"

async def update_movie_details(tconst, new_title, new_year, new_genres):
    """同时更新电影的标题、年份和类型"""
    async with AsyncSessionLocal() as db:
        try:
            stmt = (
                update(TitleBasics)
                .where(TitleBasics.tconst == tconst)
                .values(
                    primaryTitle=new_title,
                    startYear=new_year,
                    genres=new_genres
                )
            )
            await db.execute(stmt)
            await db.commit()
            return True
        except Exception as e:
            print(f"更新失败: {e}")
            await db.rollback()
            return False

async def delete_movie(tconst):
    """物理删除电影记录"""
    async with AsyncSessionLocal() as db:
        try:
            await db.execute(delete(TitleBasics).where(TitleBasics.tconst == tconst))
            await db.commit()
            return True
        except Exception as e:
            print(f"删除失败: {e}")
            await db.rollback()
            return False

async def get_top_movies(limit=10):
    """查询评分最高的N部电影 (需有评分数据)"""
    async with AsyncSessionLocal() as db:
        query = (
            select(TitleBasics.primaryTitle, TitleRatings.averageRating)
            .join(TitleRatings, TitleBasics.tconst == TitleRatings.tconst)
            .where(TitleRatings.numVotes > 10000)
            .order_by(desc(TitleRatings.averageRating))
            .limit(limit)
        )
        result = await db.execute(query)
        return result.all()

async def get_year_stats(limit=20):
    """统计近 N 年的电影产量分布"""
    async with AsyncSessionLocal() as db:
        query = (
            select(TitleBasics.startYear, func.count(TitleBasics.tconst))
            .where(TitleBasics.titleType == 'movie')
            .where(TitleBasics.startYear.is_not(None))
            .group_by(TitleBasics.startYear)
            .order_by(desc(TitleBasics.startYear))
            .limit(limit)
        )
        result = await db.execute(query)
        return result.all()

async def get_stats_summary():
    """获取总数和平均分概览"""
    async with AsyncSessionLocal() as db:
        movie_count = await db.execute(select(func.count(TitleBasics.tconst)))
        avg_rating = await db.execute(select(func.avg(TitleRatings.averageRating)))
        return movie_count.scalar(), round(avg_rating.scalar() or 0, 2)

async def get_movies_paginated(page: int, page_size: int):
    """获取分页的电影列表数据"""
    offset = (page - 1) * page_size
    async with AsyncSessionLocal() as db:
        # 按 tconst 排序保证分页稳定
        query = select(TitleBasics).order_by(TitleBasics.tconst).offset(offset).limit(page_size)
        result = await db.execute(query)
        return result.scalars().all()