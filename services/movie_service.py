from sqlalchemy import select, func, desc, update, delete, or_, text
from database import AsyncSessionLocal
from models import TitleBasics, TitleRatings, MovieSummary


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

# 3. 修改分页查询函数，接收搜索关键词
async def get_movies_paginated(page: int, page_size: int, search_query=None):
    offset = (page - 1) * page_size
    async with AsyncSessionLocal() as db:
        query = select(TitleBasics)

        # 如果有搜索内容，添加过滤条件
        if search_query:
            query = query.where(
                or_(
                    TitleBasics.primaryTitle.ilike(f"%{search_query}%"),
                    TitleBasics.tconst.ilike(f"%{search_query}%")
                )
            )

        # 保持原有排序和分页
        query = query.order_by(TitleBasics.tconst).offset(offset).limit(page_size)
        result = await db.execute(query)
        return result.scalars().all()


# 2. 修改计数函数，接收搜索关键词
async def get_movie_count(search_query=None):
    async with AsyncSessionLocal() as db:
        query = select(func.count(TitleBasics.tconst))

        # 如果有搜索内容，添加过滤条件
        if search_query:
            query = query.where(
                or_(
                    TitleBasics.primaryTitle.ilike(f"%{search_query}%"),  # 模糊匹配标题 (忽略大小写)
                    TitleBasics.tconst.ilike(f"%{search_query}%")  # 模糊匹配编号
                )
            )

        result = await db.execute(query)
        return result.scalar()


# --- 【新增】数据同步功能 (ETL) ---
async def refresh_movie_summary():
    """
    全量刷新 movie_summary 表
    修正：源表(title_basics, title_ratings)的列名使用小写，目标表(movie_summary)保持模型定义的大小写
    """
    async with AsyncSessionLocal() as db:
        try:
            # 1. 清空旧表
            await db.execute(text("TRUNCATE TABLE movie_summary"))

            # 2. 执行插入
            # 注意：
            # - INSERT INTO 部分：对应 MovieSummary 表的列名，SQLAlchemy 默认创建为 "primaryTitle" (带引号区分大小写)
            # - SELECT 部分：对应 title_basics/ratings 表的真实列名，全都是小写！
            stmt = text("""
                        INSERT INTO movie_summary (tconst, "primaryTitle", "startYear", "runtimeMinutes", genres,
                                                   "averageRating", "numVotes")
                        SELECT b.tconst,
                               b.primarytitle,   -- 改为小写
                               b.startyear,      -- 改为小写
                               b.runtimeminutes, -- 改为小写
                               b.genres,
                               r.averagerating,  -- 改为小写
                               r.numvotes        -- 改为小写
                        FROM title_basics b
                                 LEFT JOIN title_ratings r ON b.tconst = r.tconst
                        WHERE b.titletype IN ('movie', 'tvSeries', 'tvMiniSeries', 'tvMovie')
                        """)
            await db.execute(stmt)
            await db.commit()
            return True, "缓存重建成功！"
        except Exception as e:
            await db.rollback()
            return False, f"同步失败: {e}"


# --- 【修改】首页查询接口 (改用新表) ---
async def get_homepage_movies(page: int, page_size: int, search_query=None):
    """
    【极速版】首页查询
    直接查 movie_summary 单表，无需 Join
    """
    offset = (page - 1) * page_size
    async with AsyncSessionLocal() as db:
        # 直接查 MovieSummary
        query = select(MovieSummary)

        if search_query:
            # 这里的字段名要和 MovieSummary 定义的一致
            query = query.where(MovieSummary.primaryTitle.ilike(f"%{search_query}%"))
            # 搜索时按匹配度/ID排序
            query = query.order_by(MovieSummary.tconst)
        else:
            # 首页默认按热度倒序 (利用 numVotes 索引)
            query = query.order_by(desc(MovieSummary.numVotes).nulls_last())

        query = query.offset(offset).limit(page_size)
        result = await db.execute(query)

        # 返回的是 MovieSummary 对象列表 (不是元组了！)
        return result.scalars().all()