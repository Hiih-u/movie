from sqlalchemy import select, func, update, delete
from database import AsyncSessionLocal
from models import TitleEpisode, TitleBasics

async def get_episode_count():
    """获取剧集总条数"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(func.count(TitleEpisode.tconst)))
        return result.scalar()

async def get_episodes_paginated(page: int, page_size: int):
    """
    分页获取剧集列表
    这里联表查询 TitleBasics，为了显示 parentTconst 对应的剧集名称
    """
    offset = (page - 1) * page_size
    async with AsyncSessionLocal() as db:
        # 查询 TitleEpisode 和 对应的父级剧集名称 (primaryTitle)
        stmt = (
            select(TitleEpisode, TitleBasics.primaryTitle)
            .join(TitleBasics, TitleEpisode.parentTconst == TitleBasics.tconst, isouter=True) # 使用外连接，防止找不到父级时报错
            .order_by(TitleEpisode.tconst)
            .offset(offset)
            .limit(page_size)
        )
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