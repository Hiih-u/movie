# services/analysis_service.py
import os

from sqlalchemy import select, func, desc, or_
from database import AsyncSessionLocal
from models import TitleBasics, TitleRatings
# 引入 Hugging Face 的 Pipeline
from transformers import pipeline
import functools

MOOD_MAP = {
    '😄 开心': ['Comedy', 'Animation', 'Family', 'Musical'],
    '😭 难过': ['Drama', 'Romance'],
    '😤 愤怒': ['Action', 'War', 'Crime'],
    '😨 害怕': ['Horror', 'Thriller', 'Mystery'],
    '😎 刺激': ['Action', 'Adventure', 'Sci-Fi'],
    '🧘 平静': ['Documentary', 'Biography', 'History'],
    '🤔 烧脑': ['Mystery', 'Sci-Fi', 'Crime']
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_MODEL_PATH = os.path.join(BASE_DIR, "ml_models", "chinese_xlm_xnli")

@functools.lru_cache(maxsize=1)
def get_nlp_classifier():
    print(f"📂 [NLP] 正在加载本地模型: {LOCAL_MODEL_PATH}")

    # 检查 pytorch_model.bin 是否存在 (这是判断下载是否成功的关键)
    if not os.path.exists(os.path.join(LOCAL_MODEL_PATH, 'pytorch_model.bin')):
        print("❌ 未找到模型文件！请确认路径正确。")
        return None

    try:
        # 加载模型
        classifier = pipeline("zero-shot-classification", model=LOCAL_MODEL_PATH, tokenizer=LOCAL_MODEL_PATH)
        print("✅ [NLP] 模型加载完成！")
        return classifier
    except Exception as e:
        print(f"❌ [NLP] 模型加载失败: {e}")
        return None


def analyze_text_mood(text: str):
    """
    【深度学习算法】使用 Transformer 进行零样本意图识别
    """
    if not text or len(text.strip()) < 2:
        return None

    try:
        # 1. 获取模型
        classifier = get_nlp_classifier()

        # 2. 定义我们的候选标签 (去掉emoji，只要文字部分给AI理解)
        # MOOD_MAP.keys() 是类似 '😄 开心'，我们只取 '开心'
        labels_map = {k.split(' ')[1]: k for k in MOOD_MAP.keys()}
        candidate_labels = list(labels_map.keys())  # ['开心', '难过', '愤怒'...]

        # 3. 让 AI 进行预测
        # multi_label=False 表示必须要选出一个最像的
        result = classifier(text, candidate_labels, multi_label=False)

        # 4. 解析结果
        # result 格式: {'labels': ['难过', '愤怒'...], 'scores': [0.95, 0.02...]}
        top_label = result['labels'][0]
        top_score = result['scores'][0]

        print(f"🤖 AI 分析结果: '{text}' -> {top_label} (置信度: {top_score:.2f})")

        # 设置一个阈值，如果 AI 都不太确定（比如置信度低于 0.3），就返回 None
        if top_score < 0.3:
            return None

        # 5. 返回带 Emoji 的完整 Key (例如 '😭 难过')
        return labels_map.get(top_label)

    except Exception as e:
        print(f"❌ 模型推理失败: {e}")
        # 降级策略：如果模型挂了，可以用回简单的关键词匹配，或者直接返回 None
        return None

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