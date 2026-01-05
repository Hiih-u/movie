# services/analysis_service.py
from sqlalchemy import select, func, desc, or_
from database import AsyncSessionLocal
from models import TitleBasics, TitleRatings

MOOD_MAP = {
    '😄 开心': ['Comedy', 'Animation', 'Family', 'Musical'],
    '😭 难过': ['Drama', 'Romance'],
    '😤 愤怒': ['Action', 'War', 'Crime'],
    '😨 害怕': ['Horror', 'Thriller', 'Mystery'],
    '😎 刺激': ['Action', 'Adventure', 'Sci-Fi'],
    '🧘 平静': ['Documentary', 'Biography', 'History'],
    '🤔 烧脑': ['Mystery', 'Sci-Fi', 'Crime']
}


async def get_movies_by_mood(mood_key: str, limit=12):
    """
    根据心情推荐电影
    原理：心情 -> 映射为 Genre -> 查库
    """
    target_genres = MOOD_MAP.get(mood_key, [])
    if not target_genres:
        return []

    async with AsyncSessionLocal() as db:
        # 构造查询：筛选出包含目标类型之一的电影
        # 且 评分人数 > 5000 (保证质量)，按评分倒序
        conditions = [TitleBasics.genres.ilike(f"%{g}%") for g in target_genres]

        query = (
            select(TitleBasics.primaryTitle, TitleRatings.averageRating, TitleBasics.genres, TitleBasics.startYear,
                   TitleBasics.tconst)
            .join(TitleRatings, TitleBasics.tconst == TitleRatings.tconst)
            .where(or_(*conditions))  # 只要满足其中一个类型即可
            .where(TitleRatings.numVotes > 5000)  # 过滤掉太冷门的
            .order_by(desc(TitleRatings.averageRating))  # 按高分排序
            .limit(limit)
        )

        # 为了增加趣味性，其实这里可以加随机数 (func.random())，但为了性能先按高分排

        result = await db.execute(query)
        # 返回结果转为字典列表，方便前端使用
        movies = []
        for row in result.all():
            movies.append({
                'primaryTitle': row.primaryTitle,
                'averageRating': row.averageRating,
                'genres': row.genres,
                'startYear': row.startYear,
                'tconst': row.tconst
            })
        return movies


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
    """统计近 N 年的影视产量分布"""
    async with AsyncSessionLocal() as db:
        query = (
            select(TitleBasics.startYear, func.count(TitleBasics.tconst))
            .where(TitleBasics.titleType.in_(['movie', 'tvSeries', 'tvMiniSeries', 'tvMovie']))
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