# main.py
from fastapi import FastAPI
from nicegui import ui, app
from pages import admin_dashboard, login_page, user_management, person_management

# 定义 FastAPI
app_fastapi = FastAPI()


# --- 1. 登录页路由 ---
@ui.page('/login')
def login():
    # 如果已经登录，直接踢到后台
    if app.storage.user.get('authenticated', False):
        ui.navigate.to('/admin')
        return
    login_page.create_login_page()


# --- 2. 后台页路由 (加保护) ---
@ui.page('/admin')
def admin():
    # 【鉴权守卫】检查 Session
    if not app.storage.user.get('authenticated', False):
        ui.notify('请先登录！', type='warning')
        ui.navigate.to('/login')
        return  # 阻止加载后台

    # 登出按钮 (放在右上角)
    with ui.row().classes('absolute-top-right z-50 q-pa-sm'):
        ui.label(f"用户: {app.storage.user.get('username')}").classes('self-center q-mr-sm')
        ui.button('退出', on_click=lambda: logout(), icon='logout').props('flat dense color=red')

    def logout():
        app.storage.user.clear()
        ui.navigate.to('/login')

    # 加载原来的后台 UI
    admin_dashboard.create_admin_page()


# --- 3. 首页路由 ---
@ui.page('/')
def index():
    ui.label('这是前台首页')
    ui.link('去后台', '/admin')

# --- 新增：用户管理页路由 ---
@ui.page('/admin/users')
def admin_users():
    # 鉴权守卫 (和 /admin 保持一致)
    if not app.storage.user.get('authenticated', False):
        ui.notify('请先登录！', type='warning')
        ui.navigate.to('/login')
        return

    # 右上角用户信息条 (可选，保持统一体验)
    with ui.row().classes('absolute-top-right z-50 q-pa-sm'):
        ui.label(f"用户: {app.storage.user.get('username')}").classes('self-center q-mr-sm')
        ui.button('退出', on_click=lambda: (app.storage.user.clear(), ui.navigate.to('/login')), icon='logout').props('flat dense color=red')

    user_management.create_user_page()

# --- 新增：演职人员管理页路由 ---
@ui.page('/admin/people')
def admin_people():
    # 鉴权
    if not app.storage.user.get('authenticated', False):
        ui.notify('请先登录！', type='warning')
        ui.navigate.to('/login')
        return

    # 右上角用户信息
    with ui.row().classes('absolute-top-right z-50 q-pa-sm'):
        ui.label(f"用户: {app.storage.user.get('username')}").classes('self-center q-mr-sm')
        ui.button('退出', on_click=lambda: (app.storage.user.clear(), ui.navigate.to('/login')), icon='logout').props('flat dense color=red')

    person_management.create_person_page()


# --- 启动配置 ---
# 注意：必须加 storage_secret 才能用 Session
ui.run(title='Movie System', storage_secret='jflajsdfoisaiofogklsdfl',port=61081)