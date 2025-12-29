# create_admin.py
import asyncio
from services.auth_service import create_user_script


async def main():
    user = input("请输入管理员用户名: ")
    pwd = input("请输入密码: ")
    success, msg = await create_user_script(user, pwd)
    print(f"结果: {msg}")


if __name__ == "__main__":
    # Windows 下运行 asyncio 可能需要的补丁
    import sys

    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())