from nicegui import ui, app
from services import user_service

# 常用职业列表
OCCUPATIONS = [
    "Student (学生)", "Engineer (工程师)", "Programmer (程序员)",
    "Educator (教育工作者)", "Scientist (科学家)", "Artist (艺术家)",
    "Administrator (行政/管理)", "Technician (技术人员)", "Writer (作家)",
    "Healthcare (医疗/护理)", "Entertainment (娱乐/演艺)", "Executive (高管)",
    "Lawyer (律师)", "Marketing (市场/营销)", "Sales (销售)",
    "Retired (退休)", "Unemployed (待业)", "Other (其他)"
]


def create_register_page():
    # 居中卡片容器
    with ui.card().classes('absolute-center w-96 shadow-lg q-pa-md'):
        ui.label('✨ 新用户注册').classes('text-h5 font-bold text-center w-full q-mb-md text-primary')

        # --- 表单区域 ---
        with ui.column().classes('w-full gap-2'):
            # 1. 账号密码
            username = ui.input('用户名 *').classes('w-full')
            password = ui.input('密码 *', password=True, password_toggle_button=True).classes('w-full')
            confirm_pwd = ui.input('确认密码 *', password=True, password_toggle_button=True).classes('w-full')

            ui.separator().classes('q-my-sm')
            ui.label('完善画像 (用于个性化推荐)').classes('text-caption text-grey')

            # 2. 个人画像
            with ui.row().classes('w-full'):
                # 性别选择
                gender = ui.select(
                    options=['M', 'F'],
                    label='性别',
                    value='M'
                ).classes('w-1/3 q-pr-sm')

                # 年龄输入
                age = ui.number(
                    '年龄',
                    format='%.0f',
                    min=1, max=100
                ).classes('col')

            # 3. 职业选择 (带搜索提示框)
            # props='use-input' 允许用户输入文字进行过滤搜索
            occupation = ui.select(
                options=OCCUPATIONS,
                label='职业 (请选择)',
                with_input=True
            ).classes('w-full').props('use-input input-debounce="0" behavior="menu"')

        # --- 提交逻辑 ---
        async def try_register():
            # 基础校验
            if not username.value or not password.value:
                ui.notify('用户名和密码不能为空', type='warning')
                return
            if password.value != confirm_pwd.value:
                ui.notify('两次输入的密码不一致', type='warning')
                return

            # 调用 user_service 创建用户 (默认 role='user')
            # 注意：请确保您的 user_service.create_user 已经支持接收 gender/age/occupation 参数
            success, msg = await user_service.create_user(
                username=username.value,
                password=password.value,
                role='user',  # 强制为普通用户
                gender=gender.value,
                age=int(age.value) if age.value else None,
                occupation=occupation.value
            )

            if success:
                ui.notify('注册成功！正在跳转登录...', type='positive')
                # 延迟 1 秒后跳转，让用户看清提示
                ui.timer(1.0, lambda: ui.navigate.to('/login'), once=True)
            else:
                ui.notify(msg, type='negative')

        # 按钮组
        ui.button('立即注册', on_click=try_register).props('unelevated color=green').classes('w-full q-mt-md')

        # 返回登录链接
        with ui.row().classes('w-full justify-center q-mt-sm'):
            ui.label('已有账号？').classes('text-grey')
            ui.link('去登录', '/login').classes('text-primary font-bold cursor-pointer')