from sqlalchemy import select, func, desc, update, delete, or_, text
from database import AsyncSessionLocal
from models import TitleBasics, TitleRatings, MovieSummary


# --- 数据库操作逻辑 (CRUD) ---

async def create_movie(tconst, title, year, genres, type_str='movie'):
    """
    【新增】创建一部新作品
    :param type_str: 作品类型 (movie, tvSeries, etc.)
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
                titleType=type_str,  # <--- 【关键】使用传入的类型
                primaryTitle=title,
                originalTitle=title,
                isAdult=0,
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
    """
    async with AsyncSessionLocal() as db:
        try:
            # 1. 清空旧表
            await db.execute(text("TRUNCATE TABLE movie_summary"))

            # 2. 执行插入 (注意新增了 titleType 字段)
            # 我们直接从 title_basics 表里取 titletype
            stmt = text("""
                        INSERT INTO movie_summary (tconst, "titleType", "primaryTitle", "startYear", "runtimeMinutes", genres,
                                                   "averageRating", "numVotes", poster_path)
                        SELECT b.tconst,
                               b.titletype,      -- 【新增】写入类型
                               b.primarytitle,
                               b.startyear,
                               b.runtimeminutes,
                               b.genres,
                               r.averagerating,
                               r.numvotes,
                               b.poster_path
                        FROM title_basics b
                                 LEFT JOIN title_ratings r ON b.tconst = r.tconst
                        WHERE b.titletype IN ('movie', 'tvSeries', 'tvMiniSeries', 'tvMovie', 'short')
                        """)
            await db.execute(stmt)
            await db.commit()
            return True, "缓存重建成功！"
        except Exception as e:
            await db.rollback()
            return False, f"同步失败: {e}"


# --- 【修改】首页查询接口 (改用新表) ---
async def get_homepage_movies(page: int, page_size: int, search_query=None, category='all'):
    """
    支持分类筛选的首页查询
    :param category: 'all' | 'movie' | 'tv' | 'anime' | 'variety' | 'doc'
    """
    offset = (page - 1) * page_size
    async with AsyncSessionLocal() as db:
        query = select(MovieSummary)

        # --- 1. 处理搜索 ---
        if search_query:
            query = query.where(MovieSummary.primaryTitle.ilike(f"%{search_query}%"))

        # --- 2. 处理分类导航 (核心逻辑) ---
        if category == 'movie':
            # 电影：类型为 movie 或 tvMovie
            query = query.where(MovieSummary.titleType.in_(['movie', 'tvMovie']))
            # 排除动漫和纪录片，防止混杂 (可选)
            query = query.where(MovieSummary.genres.notilike('%Animation%'))
            query = query.where(MovieSummary.genres.notilike('%Documentary%'))

        elif category == 'tv':
            # 剧集：类型为 tvSeries 或 tvMiniSeries
            query = query.where(MovieSummary.titleType.in_(['tvSeries', 'tvMiniSeries']))
            # 排除动漫
            query = query.where(MovieSummary.genres.notilike('%Animation%'))

        elif category == 'anime':
            # 动漫：类型不限，但题材必须包含 Animation
            query = query.where(MovieSummary.genres.ilike('%Animation%'))

        elif category == 'variety':
            # 综艺：IMDb 中通常是 Reality-TV, Talk-Show, Game-Show
            query = query.where(or_(
                MovieSummary.genres.ilike('%Reality-TV%'),
                MovieSummary.genres.ilike('%Talk-Show%'),
                MovieSummary.genres.ilike('%Game-Show%')
            ))

        elif category == 'doc':
            # 纪录片
            query = query.where(MovieSummary.genres.ilike('%Documentary%'))

        # --- 3. 排序 (按热度) ---
        if search_query:
            query = query.order_by(MovieSummary.tconst)
        else:
            query = query.order_by(desc(MovieSummary.numVotes).nulls_last())

        query = query.offset(offset).limit(page_size)
        result = await db.execute(query)

        return result.scalars().all()


async def get_homepage_movie_count(search_query=None, category='all'):
    """
    获取符合筛选条件的电影总数，用于计算分页
    逻辑必须与 get_homepage_movies 保持完全一致
    """
    async with AsyncSessionLocal() as db:
        query = select(func.count(MovieSummary.tconst))

        # --- 1. 处理搜索 ---
        if search_query:
            query = query.where(MovieSummary.primaryTitle.ilike(f"%{search_query}%"))

        # --- 2. 处理分类导航 (复制 get_homepage_movies 的逻辑) ---
        if category == 'movie':
            query = query.where(MovieSummary.titleType.in_(['movie', 'tvMovie']))
            query = query.where(MovieSummary.genres.notilike('%Animation%'))
            query = query.where(MovieSummary.genres.notilike('%Documentary%'))

        elif category == 'tv':
            query = query.where(MovieSummary.titleType.in_(['tvSeries', 'tvMiniSeries']))
            query = query.where(MovieSummary.genres.notilike('%Animation%'))

        elif category == 'anime':
            query = query.where(MovieSummary.genres.ilike('%Animation%'))

        elif category == 'variety':
            query = query.where(or_(
                MovieSummary.genres.ilike('%Reality-TV%'),
                MovieSummary.genres.ilike('%Talk-Show%'),
                MovieSummary.genres.ilike('%Game-Show%')
            ))

        elif category == 'doc':
            query = query.where(MovieSummary.genres.ilike('%Documentary%'))

        result = await db.execute(query)
        return result.scalar()