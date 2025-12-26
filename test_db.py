import asyncio
from sqlalchemy import text
from database import engine  # 确保这里导入了你刚才写的那个 engine

async def test_connection():
    print("正在尝试连接到 PostgreSQL...")
    try:
        # 建立异步连接并执行简单查询
        async with engine.connect() as conn:
            # 执行 SELECT 1 来检查连接是否通畅
            result = await conn.execute(text("SELECT 1"))
            print("---" * 10)
            print("✅ 数据库连接成功！")
            print(f"服务器响应: {result.scalar()}")
            print("---" * 10)
    except Exception as e:
        print("---" * 10)
        print("❌ 数据库连接失败！")
        print(f"错误信息: {e}")
        print("---" * 10)
    finally:
        # 测试完毕关闭引擎释放资源
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_connection())