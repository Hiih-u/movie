# services/tmdb_service.py
import httpx
from sqlalchemy import update, select
from sqlalchemy.orm import joinedload
from database import AsyncSessionLocal
from models import TitleBasics, MovieSummary  # <--- 确保引入 MovieSummary

# 【配置】请替换为你申请的 TMDB API Key
TMDB_API_KEY = "0c58404536be73794e2b11afedfbd6b7"
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


async def get_movie_info(tconst: str):
    """
    获取电影详情 (修复版：同步更新 MovieSummary)
    """
    async with AsyncSessionLocal() as db:
        # 1. 查库 (带预加载)
        stmt = (
            select(TitleBasics)
            .options(joinedload(TitleBasics.rating))
            .where(TitleBasics.tconst == tconst)
        )
        result = await db.execute(stmt)
        movie = result.scalars().first()

        if not movie:
            return None

        # --- 2. 准备基础数据 ---
        info = {
            "title": movie.primaryTitle,
            "year": movie.startYear,
            "poster_url": f"{IMAGE_BASE_URL}{movie.poster_path}" if movie.poster_path else None,
            "backdrop_url": f"{IMAGE_BASE_URL}{movie.backdrop_path}" if movie.backdrop_path else None,
            "overview": movie.overview if movie.overview else "暂无剧情简介（数据完善中...）",
            "genres": movie.genres,
            "rating": movie.rating.averageRating if movie.rating else "N/A"
        }

        # --- 3. 检查是否需要更新 ---
        # 如果已经有图和简介，直接返回
        if movie.poster_path and movie.overview:
            return info

        # --- 4. 尝试调用 API 补全数据 ---
        try:
            async with httpx.AsyncClient() as client:
                url = f"{BASE_URL}/find/{tconst}"
                params = {
                    "api_key": TMDB_API_KEY,
                    "external_source": "imdb_id",
                    "language": "zh-CN"
                }
                resp = await client.get(url, params=params, timeout=5.0)

                if resp.status_code == 200:
                    data = resp.json()
                    tmdb_data = None
                    # 查找匹配结果
                    if data.get("movie_results"):
                        tmdb_data = data["movie_results"][0]
                    elif data.get("tv_results"):
                        tmdb_data = data["tv_results"][0]

                    if tmdb_data:
                        poster = tmdb_data.get("poster_path")
                        backdrop = tmdb_data.get("backdrop_path")
                        overview = tmdb_data.get("overview")
                        tmdb_id = str(tmdb_data.get("id"))

                        # [更新 A] 更新主表 TitleBasics
                        movie.poster_path = poster
                        movie.backdrop_path = backdrop
                        movie.overview = overview
                        movie.tmdb_id = tmdb_id

                        # [更新 B] 同步更新首页缓存表 MovieSummary (关键修改！)
                        # 只有当 MovieSummary 里也有这部电影时才更新
                        if poster:
                            stmt_summary = (
                                update(MovieSummary)
                                .where(MovieSummary.tconst == tconst)
                                .values(poster_path=poster)
                            )
                            await db.execute(stmt_summary)

                        # 提交所有修改
                        await db.commit()

                        # 更新返回的 info 对象
                        info["poster_url"] = f"{IMAGE_BASE_URL}{poster}" if poster else None
                        info["backdrop_url"] = f"{IMAGE_BASE_URL}{backdrop}" if backdrop else None
                        info["overview"] = overview

        except Exception as e:
            print(f"⚠️ [TMDB API] 获取详情失败 ({tconst}): {e}")
            # 失败不回滚，返回已有信息

        return info