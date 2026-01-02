from sqlalchemy import select, func, update, delete, or_
from database import AsyncSessionLocal
from models import NameBasics


async def get_person_count(search_query=None):
    """获取总人数 (支持搜索)"""
    async with AsyncSessionLocal() as db:
        query = select(func.count(NameBasics.nconst))

        # 如果有搜索关键词，添加过滤条件
        if search_query:
            query = query.where(
                or_(
                    NameBasics.primaryName.ilike(f"%{search_query}%"),  # 模糊匹配姓名
                    NameBasics.nconst.ilike(f"%{search_query}%")  # 模糊匹配编号
                )
            )

        result = await db.execute(query)
        return result.scalar()


async def get_people_paginated(page: int, page_size: int, search_query=None):
    """分页获取人员列表 (支持搜索)"""
    offset = (page - 1) * page_size
    async with AsyncSessionLocal() as db:
        query = select(NameBasics)

        # 如果有搜索关键词，添加过滤条件
        if search_query:
            query = query.where(
                or_(
                    NameBasics.primaryName.ilike(f"%{search_query}%"),  # 模糊匹配姓名
                    NameBasics.nconst.ilike(f"%{search_query}%")  # 模糊匹配编号
                )
            )

        # 排序并分页
        query = query.order_by(NameBasics.nconst).offset(offset).limit(page_size)

        result = await db.execute(query)
        return result.scalars().all()

async def create_person(nconst, name, birth_year, death_year, profession, titles):
    """新增人员"""
    async with AsyncSessionLocal() as db:
        try:
            # 查重
            existing = await db.execute(select(NameBasics).where(NameBasics.nconst == nconst))
            if existing.scalar():
                return False, f"编号 {nconst} 已存在"

            new_person = NameBasics(
                nconst=nconst,
                primaryName=name,
                birthYear=birth_year,
                deathYear=death_year,
                primaryProfession=profession,
                knownForTitles=titles
            )
            db.add(new_person)
            await db.commit()
            return True, "创建成功"
        except Exception as e:
            await db.rollback()
            return False, f"数据库错误: {str(e)}"

async def update_person(nconst, name, birth_year, death_year, profession, titles):
    """更新人员信息"""
    async with AsyncSessionLocal() as db:
        try:
            stmt = (
                update(NameBasics)
                .where(NameBasics.nconst == nconst)
                .values(
                    primaryName=name,
                    birthYear=birth_year,
                    deathYear=death_year,
                    primaryProfession=profession,
                    knownForTitles=titles
                )
            )
            await db.execute(stmt)
            await db.commit()
            return True, "更新成功"
        except Exception as e:
            await db.rollback()
            return False, str(e)

async def delete_person(nconst):
    """删除人员"""
    async with AsyncSessionLocal() as db:
        try:
            await db.execute(delete(NameBasics).where(NameBasics.nconst == nconst))
            await db.commit()
            return True, "删除成功"
        except Exception as e:
            await db.rollback()
            return False, str(e)