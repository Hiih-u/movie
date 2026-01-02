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
    """验证登录，成功返回 User 对象 (包含 role)"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalars().first()

        if not user:
            return None, "用户不存在"
        if not verify_password(password, user.hashed_password):
            return None, "密码错误"
        return user, "登录成功"

# 【修改】增加 role 和画像字段参数
async def create_user_script(username, password, role='user', gender=None, age=None, occupation=None):
    """(工具函数) 用于创建初始管理员或用户"""
    async with AsyncSessionLocal() as db:
        hashed = get_password_hash(password)
        new_user = User(
            username=username,
            hashed_password=hashed,
            role=role,             # 【关键】写入角色
            gender=gender,         # 写入画像数据
            age=age,
            occupation=occupation
        )
        db.add(new_user)
        try:
            await db.commit()
            return True, "创建成功"
        except Exception as e:
            await db.rollback()
            return False, str(e)