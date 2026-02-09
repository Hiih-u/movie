# init/init_db.py
import asyncio
from sqlalchemy import inspect, text
from database import engine, Base
# 确保导入了所有模型，这样 Base.metadata 才能获取到它们
from models import TitleBasics, TitleRatings, User, UserFavorite, UserRating, MovieSummary, TitleCrew, NameBasics, \
    TitleEpisode, SparkRecommendation, MovieBoxOffice, DoubanTop250


def check_and_upgrade_tables(conn):
    """
    同步函数：检查现有表，如果发现模型中有定义但数据库中缺失的字段，执行 ALTER TABLE 添加。
    """
    inspector = inspect(conn)

    # 遍历所有模型中定义的表
    for table_name, table_obj in Base.metadata.tables.items():
        # 1. 如果表已经存在 (create_all 会负责创建不存在的表，这里只处理存在的表)
        if inspector.has_table(table_name):
            # 获取数据库中该表当前所有的列名
            existing_columns = [col['name'] for col in inspector.get_columns(table_name)]

            # 遍历模型定义的列，查找缺失项
            for column in table_obj.columns:
                if column.name not in existing_columns:
                    print(f"🔄 [自动迁移] 检测到表 '{table_name}' 缺少字段 '{column.name}'，正在添加...")

                    # 获取该字段在当前数据库方言(PostgreSQL)下的类型定义
                    # 例如: String -> VARCHAR, Integer -> INTEGER
                    col_type = column.type.compile(conn.dialect)

                    # 构造 ALTER TABLE 语句
                    # 注意：
                    # 1. 这是一个简易迁移，只添加字段和类型，忽略了复杂的约束(如外键、默认值)
                    # 2. 如果表里已经有数据，且新增字段设为 nullable=False 也没给默认值，这里可能会报错。
                    #    通常建议新增字段先允许为空 (nullable=True)。
                    alter_stmt = text(f'ALTER TABLE "{table_name}" ADD COLUMN "{column.name}" {col_type}')

                    try:
                        conn.execute(alter_stmt)
                        print(f"✅ 字段 '{table_name}.{column.name}' 添加成功！")
                    except Exception as e:
                        print(f"❌ 字段 '{table_name}.{column.name}' 添加失败: {e}")


async def init_models():
    print("🔌 正在连接数据库...")
    async with engine.begin() as conn:
        # 步骤 1: 创建所有完全不存在的表 (SQLAlchemy 原生功能)
        print("🔨 [1/2] 正在检查并创建缺失的表...")
        await conn.run_sync(Base.metadata.create_all)

        # 步骤 2: 检查现有表是否有新增字段 (自定义功能)
        print("🔍 [2/2] 正在检查现有表的字段变更...")
        await conn.run_sync(check_and_upgrade_tables)

    print("✅ 数据库结构初始化/更新完成！")


if __name__ == "__main__":
    import sys

    # Windows 下运行 asyncio 的兼容性设置
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(init_models())