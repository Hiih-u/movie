# main.py
from fastapi import FastAPI
from nicegui import ui, app
from pages import (
    admin_dashboard, login_page, user_management,
    person_management, movie_management, rating_management,
    crew_management, episode_management
)

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
        # 【新增】前往前台按钮
        # props: flat(扁平) dense(紧凑) color=primary(主色) bg-white(白底)
        ui.button('前往前台', icon='home', on_click=lambda: ui.navigate.to('/')) \
            .props('flat dense color=primary bg-white') \
            .classes('q-mr-sm shadow-sm') \
            .tooltip('返回前台首页')

        # 原有的管理员标签
        ui.label(f"管理员: {app.storage.user.get('username')}") \
            .classes('self-center q-mr-sm text-white bg-primary q-px-sm rounded shadow')

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


@ui.page('/admin/crew')
def admin_crew():
    if not check_admin_access(): return
    admin_header()
    crew_management.create_crew_page()


@ui.page('/admin/episodes')
def admin_episodes():
    if not check_admin_access(): return
    admin_header()
    episode_management.create_episode_page()


# --- 3. 前台首页路由 ---
@ui.page('/')
def index():
    # 获取当前用户信息
    username = app.storage.user.get('username', '访客')
    is_login = app.storage.user.get('authenticated', False)
    role = app.storage.user.get('role', 'user')

    with ui.column().classes('w-full items-center q-pa-xl'):
        ui.label('🎬 电影推荐系统前台').classes('text-h3 font-bold text-primary')
        ui.label(f'欢迎回来，{username}').classes('text-h5 q-mt-md text-gray-600')

        # 根据状态显示不同按钮
        with ui.row().classes('q-mt-lg gap-4'):
            if is_login:
                # 只有管理员才显示“进入后台”
                if role == 'admin':
                    ui.button('进入后台管理', on_click=lambda: ui.navigate.to('/admin'), icon='settings').props(
                        'unelevated color=deep-orange')
                else:
                    ui.button('我的片单', icon='favorite').props('outline color=pink')

                # 退出按钮
                ui.button('退出登录', on_click=lambda: (app.storage.user.clear(), ui.navigate.to('/login')),
                          icon='logout').props('outline color=red')
            else:
                ui.button('登录 / 注册', on_click=lambda: ui.navigate.to('/login'), icon='login').props(
                    'unelevated color=primary')


# --- 启动配置 ---
# 注意：storage_secret 是 Session 加密必须的
ui.run(title='Movie System', storage_secret='jflajsdfoisaiofogklsdfl', port=61081)