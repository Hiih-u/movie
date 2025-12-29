# services/auth_service.py
from passlib.context import CryptContext
from sqlalchemy import select
from database import AsyncSessionLocal
from models import User

# 密码加密配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def authenticate_user(username, password):
    """验证登录，成功返回 True"""
    async with AsyncSessionLocal() as db:
        # 1. 查用户
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalars().first()

        # 2. 验密码
        if not user:
            return False
        if not verify_password(password, user.hashed_password):
            return False
        return True


async def create_user_script(username, password):
    """(工具函数) 用于创建初始管理员"""
    async with AsyncSessionLocal() as db:
        hashed = get_password_hash(password)
        new_user = User(username=username, hashed_password=hashed)
        db.add(new_user)
        try:
            await db.commit()
            return True, "创建成功"
        except Exception as e:
            await db.rollback()
            return False, str(e)