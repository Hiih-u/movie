# pages/login_page.py
from nicegui import ui, app
from services import auth_service


def create_login_page():
    # 页面容器
    with ui.card().classes('absolute-center w-96 shadow-lg q-pa-md'):
        ui.label('🔐 用户登录').classes('text-h5 font-bold text-center w-full q-mb-md')

        # 输入框
        username = ui.input('用户名').classes('w-full')
        password = ui.input('密码', password=True).classes('w-full').on('keydown.enter', lambda: try_login())

        # 登录逻辑
        async def try_login():
            if not username.value or not password.value:
                ui.notify('请输入账号密码', type='warning')
                return

            # 【修改 1】接收返回的用户对象和消息
            # auth_service.authenticate_user 已经被修改为返回 (user, msg)
            user, msg = await auth_service.authenticate_user(username.value, password.value)

            if user:
                # 【修改 2】写入更完整的 Session 信息
                app.storage.user['authenticated'] = True
                app.storage.user['username'] = user.username
                app.storage.user['user_id'] = user.id  # 存ID，方便查画像
                app.storage.user['role'] = user.role  # 存角色，方便做权限判断

                ui.notify(msg, type='positive')

                # 【修改 3】根据角色分流跳转
                # 注意：getattr(user, 'role', 'user') 是为了防止旧数据没有 role 字段报错
                user_role = getattr(user, 'role', 'user')

                if user_role == 'admin':
                    ui.navigate.to('/admin')  # 管理员 -> 后台
                else:
                    ui.navigate.to('/')  # 普通用户 -> 前台首页
            else:
                ui.notify(msg, type='negative')

        ui.button('登录', on_click=try_login).props('unelevated color=primary').classes('w-full q-mt-md')
        ui.link('返回首页', '/').classes('text-center block w-full q-mt-sm text-grey')