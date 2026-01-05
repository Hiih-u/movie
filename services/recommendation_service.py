# services/recommendation_service.py
import pandas as pd
import pickle
import os
from sqlalchemy import select
from sklearn.metrics.pairwise import cosine_similarity
from database import AsyncSessionLocal
from models import UserRating, MovieSummary, UserFavorite

# === 【修改】路径配置 ===
# 1. 获取当前文件(recommendation_service.py) 的上一级目录 -> 即 services/
# 2. 再上一级 -> 即 项目根目录/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 3. 定义数据存放目录 (建议放在根目录下的 data 文件夹)
DATA_DIR = os.path.join(BASE_DIR, "data")

# 4. 确保这个目录存在，如果不存在代码会自动创建 (这就很健壮了)
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 5. 拼接最终的模型文件路径
MODEL_FILE = os.path.join(DATA_DIR, "recommendation_model.pkl")

_similarity_df = None


# --- 1. 模型训练与保存 (后台调用) ---
async def train_model():
    """
    全量训练模型：读取数据库 -> 计算矩阵 -> 保存到磁盘
    """
    global _similarity_df

    print("🧠 [Training] 开始训练推荐模型...")

    async with AsyncSessionLocal() as db:
        # 1.1 获取所有评分数据
        rating_stmt = select(UserRating.user_id, UserRating.tconst, UserRating.rating)
        rating_res = await db.execute(rating_stmt)
        ratings_data = rating_res.all()

        # 1.2 获取所有收藏数据 (将收藏视为 10分 满分评分，以此增强数据稀疏性)
        fav_stmt = select(UserFavorite.user_id, UserFavorite.tconst)
        fav_res = await db.execute(fav_stmt)
        fav_data = fav_res.all()

    if not ratings_data and not fav_data:
        return False, "数据库中没有足够的互动数据，无法训练。"

    try:
        # 2. 数据预处理
        # 构造评分列表
        data_list = [{'user_id': r[0], 'tconst': r[1], 'rating': r[2]} for r in ratings_data]

        # 将收藏合并进去 (权重设为 10.0)
        for f in fav_data:
            data_list.append({'user_id': f[0], 'tconst': f[1], 'rating': 10.0})

        # 转为 DataFrame
        df = pd.DataFrame(data_list)

        # 去重：如果用户既收藏又评分，取最高分
        df = df.groupby(['user_id', 'tconst'], as_index=False)['rating'].max()

        # 3. 构建透视表 (Item-User Matrix)
        # 行=电影(tconst), 列=用户(user_id), 值=评分
        # 我们基于物品(Item-Based)计算相似度，所以电影做行
        pivot_matrix = df.pivot(index='tconst', columns='user_id', values='rating').fillna(0)

        # 4. 计算余弦相似度
        # 这一步计算量最大，几千条数据很快，几百万条需要优化
        print(f"   - 正在计算 {len(pivot_matrix)} 部电影的相似度矩阵...")
        sparse_matrix = pivot_matrix.values
        cosine_sim = cosine_similarity(sparse_matrix)

        # 5. 转回 DataFrame (方便通过 tconst 索引查找)
        _similarity_df = pd.DataFrame(cosine_sim, index=pivot_matrix.index, columns=pivot_matrix.index)

        # 6. 持久化保存 (Pickle)
        with open(MODEL_FILE, 'wb') as f:
            pickle.dump(_similarity_df, f)

        return True, f"训练完成！模型已保存，包含 {len(_similarity_df)} 部关联电影。"

    except Exception as e:
        print(f"❌ 训练失败: {e}")
        return False, f"训练出错: {str(e)}"


# --- 2. 模型加载 (系统启动调用) ---
def load_model():
    """
    从磁盘加载模型到内存
    """
    global _similarity_df

    if not os.path.exists(MODEL_FILE):
        print("⚠️ [Model] 未找到本地模型文件，系统将使用冷启动策略。")
        return False

    try:
        print("📂 [Model] 正在加载本地模型...")
        with open(MODEL_FILE, 'rb') as f:
            _similarity_df = pickle.load(f)
        print(f"✅ [Model] 模型加载成功！矩阵大小: {_similarity_df.shape}")
        return True
    except Exception as e:
        print(f"❌ [Model] 模型加载失败: {e}")
        return False


# --- 3. 获取推荐结果 (前台调用) ---
async def get_recommendations(user_id: int, limit=8):
    """
    核心推荐逻辑
    """
    # 如果模型没加载，直接返回空（前台会降级到热门推荐）
    if _similarity_df is None:
        return []

    async with AsyncSessionLocal() as db:
        # 1. 获取当前用户喜欢过的电影 (评分>6 或 收藏)
        # 这里为了简化，直接查所有评分记录
        stmt = select(UserRating).where(UserRating.user_id == user_id).order_by(UserRating.rating.desc()).limit(20)
        user_ratings = (await db.execute(stmt)).scalars().all()

        # 同时也查出收藏的
        stmt_fav = select(UserFavorite.tconst).where(UserFavorite.user_id == user_id)
        user_favs = (await db.execute(stmt_fav)).scalars().all()

    # 如果是纯新用户（没看过也没收藏过），返回空
    if not user_ratings and not user_favs:
        return []

    # 2. 收集用户感兴趣的种子电影
    # 格式: {tconst: weight}
    watched_movies = {}

    # 评分作为权重
    for r in user_ratings:
        watched_movies[r.tconst] = r.rating

    # 收藏作为高权重 (10分)
    for tconst in user_favs:
        watched_movies[tconst] = 10.0

    # 3. 开始计算推荐分数
    candidate_scores = {}  # {movie_id: total_score}

    for watched_tconst, weight in watched_movies.items():
        # 如果这部电影不在我们的相似度矩阵里（可能是新入库的），跳过
        if watched_tconst not in _similarity_df.index:
            continue

        # 获取与这部电影最相似的其他电影
        # similar_series 是一个 Series: index=other_tconst, value=similarity
        similar_series = _similarity_df[watched_tconst]

        # 过滤掉相似度太低的 (比如 < 0.1)，减少噪音
        similar_movies = similar_series[similar_series > 0.1]

        for similar_tconst, similarity in similar_movies.items():
            # 排除掉用户已经看过的
            if similar_tconst in watched_movies:
                continue

            # 核心公式：推荐分 += 相似度 * 用户对原电影的喜爱度
            score = similarity * weight
            candidate_scores[similar_tconst] = candidate_scores.get(similar_tconst, 0) + score

    # 4. 排序并取 Top N
    if not candidate_scores:
        return []

    # 按分数倒序排列
    sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
    top_ids = [x[0] for x in sorted_candidates]

    # 5. 查数据库获取电影详情返回
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(MovieSummary).where(MovieSummary.tconst.in_(top_ids)))
        movies = res.scalars().all()

        # 按推荐顺序重新排列 (SQL IN 查询不保证顺序)
        movies_map = {m.tconst: m for m in movies}
        ordered_movies = []
        for mid in top_ids:
            if mid in movies_map:
                ordered_movies.append(movies_map[mid])

        return ordered_movies