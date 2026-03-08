# services/tmdb_service.py
import httpx
from sqlalchemy import update, select
from sqlalchemy.orm import joinedload
from database import AsyncSessionLocal
from models import TitleBasics, MovieSummary, NameBasics  # <--- 确保引入 MovieSummary

# 【配置】请替换为你申请的 TMDB API Key
TMDB_API_KEY = "0c58404536be73794e2b11afedfbd6b7"
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


async def get_movie_info(tconst: str):
    """
    获取电影详情 (包含导演、编剧信息)
    """
    print(f"\n🔍 [TMDB] 开始获取详情: {tconst}")

    async with AsyncSessionLocal() as db:
        # 1. 查库 (同时预加载 评分 和 剧组信息)
        stmt = (
            select(TitleBasics)
            .options(
                joinedload(TitleBasics.rating),
                joinedload(TitleBasics.crew)  # 【修改】预加载剧组表
            )
            .where(TitleBasics.tconst == tconst)
        )
        result = await db.execute(stmt)
        movie = result.scalars().first()

        if not movie:
            print(f"❌ [TMDB] 本地数据库未找到电影: {tconst}")
            return None

        # --- 【新增】解析导演和编剧姓名 ---
        directors_names = []
        writers_names = []

        # 内部函数：将 "nm1,nm2" 转换为 ["Name1", "Name2"]
        async def resolve_names(nconst_str):
            if not nconst_str:
                return []
            # 分割 ID 字符串
            nconst_list = nconst_str.split(',')
            # 查询 NameBasics 表
            stmt_names = select(NameBasics.primaryName).where(NameBasics.nconst.in_(nconst_list))
            res = await db.execute(stmt_names)
            return res.scalars().all()

        # 如果有剧组信息，开始解析
        if movie.crew:
            if movie.crew.directors:
                directors_names = await resolve_names(movie.crew.directors)
            if movie.crew.writers:
                writers_names = await resolve_names(movie.crew.writers)

        # Log 打印一下看看
        if directors_names:
            print(f"   - 导演: {', '.join(directors_names)}")
        if writers_names:
            print(f"   - 编剧: {', '.join(writers_names)}")

        # --- 2. 准备基础数据 ---
        info = {
            "title": movie.primaryTitle,
            "year": movie.startYear,
            "poster_url": f"{IMAGE_BASE_URL}{movie.poster_path}" if movie.poster_path else None,
            "backdrop_url": f"{IMAGE_BASE_URL}{movie.backdrop_path}" if movie.backdrop_path else None,
            "overview": movie.overview if movie.overview else "暂无剧情简介（数据完善中...）",
            "genres": movie.genres,
            "rating": movie.rating.averageRating if movie.rating else "N/A",

            # 【新增】返回导演和编剧列表
            "directors": directors_names,
            "writers": writers_names
        }

        # --- 3. 检查是否需要更新  ---
        if movie.poster_path and movie.overview:
            print(f"✅ [TMDB] 命中本地缓存")
            return info

        # --- 4. 尝试调用 API 补全海报/简介 ---
        print(f"🚀 [TMDB] 本地缺失海报/简介，正在请求 API... (ID: {tconst})")

        try:
            async with httpx.AsyncClient() as client:
                url = f"{BASE_URL}/find/{tconst}"
                params = {
                    "api_key": TMDB_API_KEY,
                    "external_source": "imdb_id",
                    "language": "zh-CN"
                }

                resp = await client.get(url, params=params, timeout=10.0)

                if resp.status_code == 200:
                    data = resp.json()
                    tmdb_data = None
                    if data.get("movie_results"):
                        tmdb_data = data["movie_results"][0]
                    elif data.get("tv_results"):
                        tmdb_data = data["tv_results"][0]

                    if tmdb_data:
                        poster = tmdb_data.get("poster_path")
                        backdrop = tmdb_data.get("backdrop_path")
                        overview = tmdb_data.get("overview")
                        tmdb_id = str(tmdb_data.get("id"))

                        # 更新数据库
                        movie.poster_path = poster
                        movie.backdrop_path = backdrop
                        movie.overview = overview
                        movie.tmdb_id = tmdb_id

                        if poster:
                            stmt_summary = (
                                update(MovieSummary)
                                .where(MovieSummary.tconst == tconst)
                                .values(poster_path=poster)
                            )
                            await db.execute(stmt_summary)

                        await db.commit()
                        print("✅ [TMDB] API 数据更新成功！")

                        # 更新 info
                        info["poster_url"] = f"{IMAGE_BASE_URL}{poster}" if poster else None
                        info["backdrop_url"] = f"{IMAGE_BASE_URL}{backdrop}" if backdrop else None
                        info["overview"] = overview
                    else:
                        print(f"⚠️ [TMDB] API 未找到匹配项")
                else:
                    print(f"❌ [TMDB] API 请求失败: {resp.status_code}")

        except Exception as e:
            print(f"🔥 [TMDB] 异常: {str(e)}")

        return info