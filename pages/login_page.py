# pages/login_page.py
from nicegui import ui, app
from services import auth_service


def create_login_page():
    # 页面容器
    with ui.card().classes('absolute-center w-96 shadow-lg q-pa-md'):
        ui.label('🔐 管理员登录').classes('text-h5 font-bold text-center w-full q-mb-md')

        # 输入框
        username = ui.input('用户名').classes('w-full')
        password = ui.input('密码', password=True).classes('w-full').on('keydown.enter', lambda: try_login())

        # 登录逻辑
        async def try_login():
            if not username.value or not password.value:
                ui.notify('请输入账号密码', type='warning')
                return

            # 调用 Service
            if await auth_service.authenticate_user(username.value, password.value):
                # 【关键】写入 Session
                app.storage.user['authenticated'] = True
                app.storage.user['username'] = username.value
                ui.notify('登录成功', type='positive')
                ui.navigate.to('/admin')  # 跳转
            else:
                ui.notify('账号或密码错误', type='negative')

        ui.button('登录', on_click=try_login).props('unelevated color=primary').classes('w-full q-mt-md')
        ui.link('返回首页', '/').classes('text-center block w-full q-mt-sm text-grey')