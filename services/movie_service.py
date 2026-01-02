from sqlalchemy import select, func, desc, update, delete, or_
from database import AsyncSessionLocal
from models import TitleBasics, TitleRatings

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

        # 如果有搜索内容，添加过滤条件 (逻辑同上)
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