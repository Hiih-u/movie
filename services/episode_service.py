from sqlalchemy import select, func, update, delete, or_
from database import AsyncSessionLocal
from models import TitleEpisode, TitleBasics


async def get_episode_count(search_query=None):
    """获取剧集总条数 (支持搜索)"""
    async with AsyncSessionLocal() as db:
        query = select(func.count(TitleEpisode.tconst))

        # 如果有搜索内容，需要添加过滤条件
        if search_query:
            # 必须联表才能搜到 parentTitle (使用左外连接防止数据丢失)
            query = query.join(TitleBasics, TitleEpisode.parentTconst == TitleBasics.tconst, isouter=True)
            query = query.where(
                or_(
                    TitleEpisode.tconst.ilike(f"%{search_query}%"),  # 搜本集编号
                    TitleEpisode.parentTconst.ilike(f"%{search_query}%"),  # 搜父级编号
                    TitleBasics.primaryTitle.ilike(f"%{search_query}%")  # 搜父级剧集名
                )
            )

        result = await db.execute(query)
        return result.scalar()


async def get_episodes_paginated(page: int, page_size: int, search_query=None):
    """
    分页获取剧集列表 (支持搜索)
    联表查询 TitleBasics 以便显示 parentTconst 对应的剧集名称
    """
    offset = (page - 1) * page_size
    async with AsyncSessionLocal() as db:
        # 基础查询
        stmt = (
            select(TitleEpisode, TitleBasics.primaryTitle)
            .join(TitleBasics, TitleEpisode.parentTconst == TitleBasics.tconst, isouter=True)
        )

        # 如果有搜索内容，添加过滤条件
        if search_query:
            stmt = stmt.where(
                or_(
                    TitleEpisode.tconst.ilike(f"%{search_query}%"),  # 搜本集编号
                    TitleEpisode.parentTconst.ilike(f"%{search_query}%"),  # 搜父级编号
                    TitleBasics.primaryTitle.ilike(f"%{search_query}%")  # 搜父级剧集名
                )
            )

        # 排序与分页
        stmt = stmt.order_by(TitleEpisode.tconst).offset(offset).limit(page_size)

        result = await db.execute(stmt)
        return result.all()

async def create_episode(tconst, parent_tconst, season_number, episode_number):
    """新增剧集"""
    async with AsyncSessionLocal() as db:
        try:
            # 1. 查重 (tconst 作为主键)
            existing = await db.execute(select(TitleEpisode).where(TitleEpisode.tconst == tconst))
            if existing.scalar():
                return False, f"编号 {tconst} 已存在"

            # 2. (可选) 检查 parent_tconst 是否存在于 movie 表中
            # parent = await db.execute(select(TitleBasics).where(TitleBasics.tconst == parent_tconst))
            # if not parent.scalar():
            #     return False, f"父级编号 {parent_tconst} 不存在"

            new_episode = TitleEpisode(
                tconst=tconst,
                parentTconst=parent_tconst,
                seasonNumber=season_number,
                episodeNumber=episode_number
            )
            db.add(new_episode)
            await db.commit()
            return True, "创建成功"
        except Exception as e:
            await db.rollback()
            return False, f"数据库错误: {str(e)}"

async def update_episode(tconst, parent_tconst, season_number, episode_number):
    """更新剧集信息"""
    async with AsyncSessionLocal() as db:
        try:
            stmt = (
                update(TitleEpisode)
                .where(TitleEpisode.tconst == tconst)
                .values(
                    parentTconst=parent_tconst,
                    seasonNumber=season_number,
                    episodeNumber=episode_number
                )
            )
            await db.execute(stmt)
            await db.commit()
            return True, "更新成功"
        except Exception as e:
            await db.rollback()
            return False, str(e)

async def delete_episode(tconst):
    """删除剧集"""
    async with AsyncSessionLocal() as db:
        try:
            await db.execute(delete(TitleEpisode).where(TitleEpisode.tconst == tconst))
            await db.commit()
            return True, "删除成功"
        except Exception as e:
            await db.rollback()
            return False, str(e)