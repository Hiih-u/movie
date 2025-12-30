from sqlalchemy import select, delete, update, func
from database import AsyncSessionLocal
from models import User
from services.auth_service import get_password_hash  # 复用加密逻辑


# 【新增】获取用户总数 (用于前端计算页码)
async def get_user_count():
    async with AsyncSessionLocal() as db:
        # select count(*) from users
        result = await db.execute(select(func.count(User.id)))
        return result.scalar()


# 【新增】获取分页用户列表
async def get_users_paginated(page: int, page_size: int):
    async with AsyncSessionLocal() as db:
        # 计算跳过多少条
        offset = (page - 1) * page_size

        # 查询逻辑: 排序 -> 跳过 -> 限制数量
        stmt = (
            select(User)
            .order_by(User.id)
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(stmt)
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