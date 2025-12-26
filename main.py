from fastapi import FastAPI
from nicegui import ui
from pages import admin_dashboard
# from pages import user_home (假设你把之前的推荐页放在这)

app = FastAPI(title="IMDB 电影推荐系统")

# --- 路由 1: 用户端 (推荐系统) ---
@ui.page('/')
def user_interface():
    # 这里放你之前的电影搜索和推荐代码
    ui.label('这里是用户看到的推荐主页').classes('text-h3')
    ui.link('进入后台管理系统', '/admin').classes('text-lg text-blue')

# --- 路由 2: 管理端 (可视化后台) ---
@ui.page('/admin')
def admin_interface():
    # 鉴权逻辑可以在这里加 (比如检查 cookie)
    admin_dashboard.create_admin_page()

# 启动
ui.run(title='Movie System')
# 注意：如果是新版 NiceGUI，使用 ui.run(title='Movie System')
# 并将 app 逻辑按照我上一个回答的方式挂载