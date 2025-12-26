from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 数据库连接字符串格式: postgresql+asyncpg://用户名:密码@地址:端口/数据库名
DATABASE_URL = "postgresql+asyncpg://postgresuser:password@192.168.202.155:61010/movie_db"

# 创建异步引擎
engine = create_async_engine(DATABASE_URL, echo=True)

# 创建异步 Session 模板
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 基础模型类
Base = declarative_base()

# 获取数据库连接的工具函数
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session