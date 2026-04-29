# services/analysis_service.py
import os
from datetime import datetime
from sqlalchemy import select, func, desc, or_
from database import AsyncSessionLocal
from models import TitleBasics, TitleRatings, DoubanTop250, MovieBoxOffice
from transformers import pipeline
import functools
import random
import pandas as pd

# === 【核心修改】升级为更具人文关怀的情绪场景配置 ===
MOOD_SCENARIOS = {
    '😄 开心': {
        'genres': ['Comedy', 'Animation', 'Family', 'Musical'],
        'msg': '✨ 保持这份好心情！这些电影会让笑容延续，愿你的快乐加倍 ~'
    },
    '😭 难过': {
        # 策略：50% 共情 (Drama/Romance) + 50% 治愈 (Family/Animation/Comedy)
        'genres': ['Drama', 'Romance'],
        'healing': ['Family', 'Animation', 'Comedy'],
        'msg': '🌻 抱抱你。哭出来没关系，或者让这些温暖治愈的故事陪陪你，一切都会好起来的。'
    },
    '😤 愤怒': {
        # 策略：发泄 (Action) + 冷静 (Documentary/Music)
        'genres': ['Action', 'Crime', 'War'],
        'healing': ['Documentary', 'Music', 'Biography'],
        'msg': '🍃 深呼吸。去电影里宣泄压力，或者在真实静谧的故事里找回内心的平静。'
    },
    '😨 害怕': {
        # 策略：以毒攻毒 (Horror) + 壮胆 (Adventure/Comedy)
        'genres': ['Horror', 'Thriller', 'Mystery'],
        'healing': ['Adventure', 'Comedy', 'Fantasy'],
        'msg': '💡 别怕，光影与你同在。如果觉得冷，选一部冒险喜剧找回勇气吧！'
    },
    '😎 刺激': {
        'genres': ['Action', 'Adventure', 'Sci-Fi'],
        'msg': '🚀 准备好起飞了吗？系好安全带，肾上腺素飙升的旅程即将开始！'
    },
    '🧘 平静': {
        'genres': ['Documentary', 'Biography', 'History', 'Music'],
        'msg': '☕ 享受这段独处的时光，慢下来，让心灵在流动的光影中漫步。'
    },
    '🤔 烧脑': {
        'genres': ['Mystery', 'Sci-Fi', 'Crime'],
        'msg': '🧩 大脑开始运转！准备好挑战这些迷宫般的谜题了吗？'
    }
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_MODEL_PATH = os.path.join(BASE_DIR, "ml_models", "chinese_xlm_xnli")


@functools.lru_cache(maxsize=1)
def get_nlp_classifier():
    print(f"📂 [NLP] 正在加载本地模型: {LOCAL_MODEL_PATH}")
    if not os.path.exists(os.path.join(LOCAL_MODEL_PATH, 'pytorch_model.bin')):
        print("❌ 未找到模型文件！请确认路径正确。")
        return None
    try:
        classifier = pipeline("zero-shot-classification", model=LOCAL_MODEL_PATH, tokenizer=LOCAL_MODEL_PATH)
        print("✅ [NLP] 模型加载完成！")
        return classifier
    except Exception as e:
        print(f"❌ [NLP] 模型加载失败: {e}")
        return None


def analyze_text_mood(text: str):
    """
    意图识别：输入文字 -> 返回带 Emoji 的情绪 Key
    """
    if not text or len(text.strip()) < 2:
        return None

    try:
        classifier = get_nlp_classifier()
        # 从新的配置中提取标签
        labels_map = {k.split(' ')[1]: k for k in MOOD_SCENARIOS.keys()}
        candidate_labels = list(labels_map.keys())

        result = classifier(text, candidate_labels, multi_label=False)
        top_label = result['labels'][0]
        top_score = result['scores'][0]

        print(f"分析结果: '{text}' -> {top_label} (置信度: {top_score:.2f})")
        if top_score < 0.2:
            return None
        return labels_map.get(top_label)
    except Exception as e:
        print(f"❌ 模型推理失败: {e}")
        return None


# --- 分类过滤辅助函数 (保持不变) ---
def _apply_category_filter(query, category):
    if category == 'movie':
        query = query.where(TitleBasics.titleType.in_(['movie', 'tvMovie']))
        query = query.where(TitleBasics.genres.notilike('%Documentary%'))
    elif category == 'tv':
        query = query.where(TitleBasics.titleType.in_(['tvSeries', 'tvMiniSeries']))
    elif category == 'anime':
        query = query.where(TitleBasics.genres.ilike('%Animation%'))
    elif category == 'variety':
        query = query.where(or_(
            TitleBasics.genres.ilike('%Reality-TV%'),
            TitleBasics.genres.ilike('%Talk-Show%'),
            TitleBasics.genres.ilike('%Game-Show%')
        ))
    elif category == 'doc':
        query = query.where(TitleBasics.genres.ilike('%Documentary%'))
    return query


async def get_movies_by_mood(mood_key: str, limit=12, category='all'):
    """
    根据心情推荐电影 (升级版：混合推荐 + 返回文案)
    """
    scenario = MOOD_SCENARIOS.get(mood_key)
    if not scenario:
        return [], ""

    # 1. 提取主要类型 和 治愈类型
    primary_genres = scenario.get('genres', [])
    healing_genres = scenario.get('healing', [])

    # 2. 混合策略：如果有治愈类型，我们将查询范围扩大
    target_genres = primary_genres + healing_genres

    # 获取暖心文案
    warm_msg = scenario.get('msg', '愿电影陪你度过美好时光。')

    async with AsyncSessionLocal() as db:
        # 构建基础查询
        conditions = [TitleBasics.genres.ilike(f"%{g}%") for g in target_genres]

        query = (
            select(TitleBasics.primaryTitle, TitleRatings.averageRating, TitleBasics.genres, TitleBasics.startYear,
                   TitleBasics.tconst)
            .join(TitleRatings, TitleBasics.tconst == TitleRatings.tconst)
            .where(or_(*conditions))
            .where(TitleRatings.numVotes > 5000)  # 只要高分
        )

        # 应用分类过滤
        if category != 'all':
            query = _apply_category_filter(query, category)

        # 随机取样策略：
        # 为了让结果每次不同且包含“治愈”元素，我们可以取稍多一点(比如 50个)，然后在内存里打乱
        query = query.order_by(desc(TitleRatings.averageRating)).limit(50)

        result = await db.execute(query)
        all_movies = []
        for row in result.all():
            all_movies.append({
                'primaryTitle': row.primaryTitle,
                'averageRating': row.averageRating,
                'genres': row.genres,
                'startYear': row.startYear,
                'tconst': row.tconst
            })

        # 内存中随机打乱，实现“偶遇”感
        random.shuffle(all_movies)

        # 返回截取后的列表 和 暖心文案
        return all_movies[:limit], warm_msg


async def get_top_movies(limit=10):
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
    current_year = datetime.now().year
    async with AsyncSessionLocal() as db:
        query = (
            select(TitleBasics.startYear, func.count(TitleBasics.tconst))
            .where(TitleBasics.titleType.in_(['movie', 'tvSeries', 'tvMiniSeries', 'tvMovie']))
            .where(TitleBasics.startYear.is_not(None))
            .where(TitleBasics.startYear <= current_year)
            .group_by(TitleBasics.startYear)
            .order_by(desc(TitleBasics.startYear))
            .limit(limit)
        )
        result = await db.execute(query)
        data = result.all()
        return list(reversed(data))


async def get_stats_summary():
    async with AsyncSessionLocal() as db:
        movie_count = await db.execute(select(func.count(TitleBasics.tconst)))
        avg_rating = await db.execute(select(func.avg(TitleRatings.averageRating)))
        return movie_count.scalar(), round(avg_rating.scalar() or 0, 2)


async def get_genre_distribution(limit=5000):
    """1. 题材偏好 (玫瑰图数据)"""
    async with AsyncSessionLocal() as db:
        # 取最热门的 N 部电影的类型
        stmt = (
            select(TitleBasics.genres)
            .join(TitleRatings, TitleBasics.tconst == TitleRatings.tconst)
            .order_by(desc(TitleRatings.numVotes))
            .limit(limit)
        )
        res = await db.execute(stmt)
        genres_list = []
        for row in res.scalars().all():
            if row and row != '\\N':
                # 'Action,Adventure' -> ['Action', 'Adventure']
                genres_list.extend(row.split(','))

        # 统计频次
        if not genres_list: return []
        df = pd.DataFrame(genres_list, columns=['genre'])
        # 过滤掉无效数据
        df = df[df['genre'] != '\\N']
        counts = df['genre'].value_counts().reset_index()
        counts.columns = ['genre', 'count']
        return counts.head(15).to_dict('records')  # 取前15个主流类型


async def get_rating_distribution_by_genre(limit=5000):
    """2. 评分深度分析 (箱线图/小提琴图数据)"""
    async with AsyncSessionLocal() as db:
        # 获取 热门电影的 类型 和 评分
        stmt = (
            select(TitleBasics.genres, TitleRatings.averageRating)
            .join(TitleRatings, TitleBasics.tconst == TitleRatings.tconst)
            .order_by(desc(TitleRatings.numVotes))
            .limit(limit)
        )
        res = await db.execute(stmt)
        data = []
        for genres, rating in res.all():
            if genres and rating:
                # 一部电影属于多个类型，拆开来算
                for g in genres.split(','):
                    if g != '\\N':
                        data.append({'genre': g, 'rating': rating})

        df = pd.DataFrame(data)
        # 只要前 10 大类型，防止图表太挤
        top_genres = df['genre'].value_counts().head(10).index
        df_filtered = df[df['genre'].isin(top_genres)]
        return df_filtered.to_dict('records')


async def get_genre_evolution(limit=10000):
    """3. 时空演变 (热力图数据: 年代 vs 类型)"""
    async with AsyncSessionLocal() as db:
        # 取 1980 年以后的数据
        stmt = (
            select(TitleBasics.startYear, TitleBasics.genres)
            .join(TitleRatings, TitleBasics.tconst == TitleRatings.tconst)
            .where(TitleBasics.startYear >= 1980)
            .order_by(desc(TitleRatings.numVotes))
            .limit(limit)
        )
        res = await db.execute(stmt)
        data = []
        for year, genres in res.all():
            if year and genres:
                for g in genres.split(','):
                    if g != '\\N':
                        # 将年份归类为年代 (1993 -> 1990s)
                        decade = (year // 10) * 10
                        data.append({'decade': decade, 'genre': g})

        if not data: return [], [], []
        df = pd.DataFrame(data)
        # 聚合计数
        pivot = df.groupby(['decade', 'genre']).size().reset_index(name='count')
        # 筛选主要类型
        top_genres = pivot.groupby('genre')['count'].sum().nlargest(10).index
        pivot = pivot[pivot['genre'].isin(top_genres)]
        # 格式化为 Plotly Heatmap 需要的格式
        # x: decades, y: genres, z: counts matrix
        years = sorted(pivot['decade'].unique())
        genres = sorted(pivot['genre'].unique())

        # 构建矩阵
        z = [[0] * len(years) for _ in range(len(genres))]
        for _, row in pivot.iterrows():
            y_idx = genres.index(row['genre'])
            x_idx = years.index(row['decade'])
            z[y_idx][x_idx] = row['count']

        return years, genres, z


async def get_scatter_data(limit=2000):
    """4. 质量与热度 (散点图数据)"""
    async with AsyncSessionLocal() as db:
        stmt = (
            select(TitleBasics.primaryTitle, TitleRatings.averageRating, TitleRatings.numVotes, TitleBasics.genres)
            .join(TitleRatings, TitleBasics.tconst == TitleRatings.tconst)
            .order_by(desc(TitleRatings.numVotes))
            .limit(limit)
        )
        res = await db.execute(stmt)
        data = []
        for row in res.all():
            data.append({
                'title': row.primaryTitle,
                'rating': row.averageRating,
                'votes': row.numVotes,
                'genre': row.genres.split(',')[0] if row.genres else 'Unknown'  # 取主类型用于着色
            })
        return data


async def get_cultural_comparison():
    """5. 中西审美差异 (双向柱状图)"""
    async with AsyncSessionLocal() as db:
        # 连接 DoubanTop250 和 TitleRatings
        # 注意：这需要 DoubanTop250 表里的 imdb_id 字段有值
        # 如果你的 crawler 还没填 imdb_id，这里会查不到数据
        stmt = (
            select(DoubanTop250.title, DoubanTop250.douban_score, TitleRatings.averageRating)
            .join(TitleRatings, DoubanTop250.imdb_id == TitleRatings.tconst)
            .order_by(DoubanTop250.rank)
            .limit(20)  # 取前20名对比，避免图表太长
        )
        res = await db.execute(stmt)
        data = res.all()

        # 如果通过 ID 关联不到，尝试通过标题关联 (兜底策略)
        if not data:
            print("⚠️ 无法通过 ID 关联豆瓣与IMDb，尝试通过标题关联...")
            stmt = (
                select(DoubanTop250.title, DoubanTop250.douban_score, TitleRatings.averageRating)
                .join(TitleBasics, DoubanTop250.title == TitleBasics.primaryTitle)  # 标题匹配
                .join(TitleRatings, TitleBasics.tconst == TitleRatings.tconst)
                .order_by(DoubanTop250.rank)
                .limit(20)
            )
            res = await db.execute(stmt)
            data = res.all()

        return [{'title': r[0], 'douban': r[1], 'imdb': r[2]} for r in data]


async def get_roi_scatter_data(limit=1000):
    """
    【新增】获取 商业价值(票房) vs 艺术口碑(评分) 散点图数据
    用于生成 ROI Bubble Chart
    """
    async with AsyncSessionLocal() as db:
        stmt = (
            select(
                TitleBasics.primaryTitle,
                TitleBasics.genres,
                TitleRatings.averageRating,
                TitleRatings.numVotes,
                MovieBoxOffice.box_office
            )
            .join(MovieBoxOffice, TitleBasics.tconst == MovieBoxOffice.tconst)
            .join(TitleRatings, TitleBasics.tconst == TitleRatings.tconst)
            .where(MovieBoxOffice.box_office > 0)  # 只取有票房的数据
            .order_by(desc(MovieBoxOffice.box_office))
            .limit(limit)
        )
        res = await db.execute(stmt)
        data = []
        for row in res.all():
            title, genres, rating, votes, box_office = row
            # 处理类型: 'Action,Adventure' -> 取 'Action' 主类型，简化颜色分类
            main_genre = genres.split(',')[0] if genres and genres != '\\N' else 'Other'

            data.append({
                'title': title,
                'genre': main_genre,
                'rating': rating,
                'votes': votes,  # 气泡大小 (热度)
                'box_office': box_office  # X轴 (票房)
            })
        return data