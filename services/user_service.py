from sqlalchemy import select, delete, update, func
from database import AsyncSessionLocal
from models import User
from services.auth_service import get_password_hash  # 复用加密逻辑


# 【新增】获取用户总数 (用于前端计算页码)
async def get_user_count(search_query=None):
    async with AsyncSessionLocal() as db:
        query = select(func.count(User.id))

        # 如果有搜索内容，添加过滤条件
        if search_query:
            # 模糊匹配用户名 (忽略大小写)
            query = query.where(User.username.ilike(f"%{search_query}%"))

        result = await db.execute(query)
        return result.scalar()


# 2. 修改分页查询函数，接收搜索关键词
async def get_users_paginated(page: int, page_size: int, search_query=None):
    async with AsyncSessionLocal() as db:
        offset = (page - 1) * page_size

        query = select(User)

        # 如果有搜索内容，添加过滤条件
        if search_query:
            query = query.where(User.username.ilike(f"%{search_query}%"))

        # 排序 -> 跳过 -> 限制数量
        query = query.order_by(User.id).offset(offset).limit(page_size)

        result = await db.execute(query)
        return result.scalars().all()

async def create_user(username, password):
    """创建新用户"""
    async with AsyncSessionLocal() as db:
        # 1. 检查用户名是否已存在
        existing = await db.execute(select(User).where(User.username == username))
        if existing.scalar():
            return False, "用户名已存在"

        # 2. 加密密码并保存
        hashed = get_password_hash(password)
        new_user = User(username=username, hashed_password=hashed)
        db.add(new_user)
        try:
            await db.commit()
            return True, "创建成功"
        except Exception as e:
            await db.rollback()
            return False, str(e)


async def delete_user(user_id):
    """删除用户"""
    async with AsyncSessionLocal() as db:
        try:
            # 执行删除
            await db.execute(delete(User).where(User.id == user_id))
            await db.commit()
            return True, "删除成功"
        except Exception as e:
            await db.rollback()
            return False, str(e)


async def change_password(user_id, new_password):
    """修改指定用户的密码"""
    async with AsyncSessionLocal() as db:
        try:
            hashed = get_password_hash(new_password)
            stmt = update(User).where(User.id == user_id).values(hashed_password=hashed)
            await db.execute(stmt)
            await db.commit()
            return True, "密码修改成功"
        except Exception as e:
            await db.rollback()
            return False, str(e)