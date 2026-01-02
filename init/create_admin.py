# init/create_admin.py
import asyncio
# 注意：确保 services/auth_service.py 已经修改如上
from services.auth_service import create_user_script


async def main():
    print("🚀 --- 初始化超级管理员 ---")
    user = input("请输入管理员用户名: ")
    pwd = input("请输入密码: ")

    print("\n📝 --- 补充画像信息 (用于测试推荐算法，可直接回车跳过) ---")
    gender_input = input("性别 (M/F): ").strip()
    gender = gender_input if gender_input else None

    age_input = input("年龄: ").strip()
    age = int(age_input) if age_input.isdigit() else None

    occupation_input = input("职业 (如 Student, Engineer): ").strip()
    occupation = occupation_input if occupation_input else None

    print("\n⏳ 正在创建...")

    # 【关键】这里强制指定 role='admin'
    success, msg = await create_user_script(
        username=user,
        password=pwd,
        role='admin',
        gender=gender,
        age=age,
        occupation=occupation
    )

    if success:
        print(f"✅ 成功! 管理员 {user} 已创建。")
    else:
        print(f"❌ 失败: {msg}")


if __name__ == "__main__":
    # Windows 下运行 asyncio 可能需要的补丁
    import sys

    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())