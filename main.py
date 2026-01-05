# main.py
from fastapi import FastAPI
from nicegui import ui, app
from pages import (
    admin_dashboard, login_page, user_management,
    person_management, movie_management, rating_management,
    crew_management, register_page, user_home, episode_management, user_favorites, user_ratings
)
from services import recommendation_service

# 定义 FastAPI
app_fastapi = FastAPI()


# --- 公共工具函数 ---

def check_admin_access():
    """
    权限检查守卫：
    1. 检查是否登录
    2. 检查角色是否为 'admin'
    如果不满足，自动跳转并返回 False
    """
    # 1. 检查登录状态
    if not app.storage.user.get('authenticated', False):
        ui.notify('请先登录！', type='warning')
        ui.navigate.to('/login')
        return False

    # 2. 检查管理员权限
    # 使用 .get('role', 'user') 默认为 user，防止旧数据报错
    if app.storage.user.get('role', 'user') != 'admin':
        ui.notify('⛔️ 权限拒绝：您不是管理员', type='negative')
        ui.navigate.to('/')  # 踢回前台首页
        return False

    return True


def admin_header():
    """后台页面统一的右上角头部"""
    # 增加 items-center 让按钮垂直居中
    with ui.row().classes('absolute-top-right z-50 q-pa-sm items-center'):

        username = app.storage.user.get('username', 'Admin')
        with ui.row().classes('items-center gap-3 q-mr-md'):
            ui.avatar(username[0].upper(), color='primary', text_color='white') \
                .props('size=sm font-size=14px')
            ui.label(username).classes('font-medium text-slate-600')


        # 原有的退出按钮
        ui.button('退出', icon='logout', on_click=lambda: (app.storage.user.clear(), ui.navigate.to('/login'))) \
            .props('flat dense color=red bg-white') \
            .classes('shadow-sm')


# --- 1. 登录页路由 ---
@ui.page('/login')
def login():
    # 如果已经登录，根据角色分流跳转
    if app.storage.user.get('authenticated', False):
        if app.storage.user.get('role') == 'admin':
            ui.navigate.to('/admin')
        else:
            ui.navigate.to('/')
        return

    login_page.create_login_page()

# 添加注册页路由 (建议放在 /login 附近)
@ui.page('/register')
def register():
    # 如果已登录，没必要注册，踢回首页
    if app.storage.user.get('authenticated', False):
        ui.navigate.to('/')
        return
    register_page.create_register_page()

# --- 2. 后台管理路由 (全部加上权限锁) ---

@ui.page('/admin')
def admin():
    if not check_admin_access(): return
    admin_header()
    admin_dashboard.create_admin_page()


@ui.page('/admin/users')
def admin_users():
    if not check_admin_access(): return
    admin_header()
    user_management.create_user_page()


@ui.page('/admin/people')
def admin_people():
    if not check_admin_access(): return
    admin_header()
    person_management.create_person_page()


@ui.page('/admin/movies')
def admin_movies():
    if not check_admin_access(): return
    admin_header()
    movie_management.create_movie_page()


@ui.page('/admin/ratings')
def admin_ratings():
    if not check_admin_access(): return
    admin_header()
    rating_management.create_rating_page()


@ui.page('/admin/episodes')
def admin_episodes():
    if not check_admin_access(): return
    admin_header()
    episode_management.create_episode_page()


@ui.page('/admin/crew')
def admin_crew():
    if not check_admin_access(): return
    admin_header()
    crew_management.create_crew_page()


# --- 3. 前台首页路由 ---
@ui.page('/')
def index():
    user_home.create_user_home()


@ui.page('/user/favorites')
def page_user_favorites():
    # 权限检查
    if not app.storage.user.get('authenticated', False):
        ui.navigate.to('/login')
        return
    user_favorites.create_page()

@ui.page('/user/ratings')
def page_user_ratings():
    if not app.storage.user.get('authenticated', False):
        ui.navigate.to('/login')
        return
    user_ratings.create_page()

# 【新增】启动事件：加载本地模型
def handle_startup():
    print("🚀 系统启动中...")
    recommendation_service.load_model()

app.on_startup(handle_startup)

# --- 启动配置 ---
# 注意：storage_secret 是 Session 加密必须的
ui.run(title='Movie System', storage_secret='jflajsdfoisaiofogklsdfl', port=61081)