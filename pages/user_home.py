from nicegui import ui, app
from services import movie_service, analysis_service
import random

BG_COLORS = ['bg-blue-600', 'bg-rose-600', 'bg-emerald-600', 'bg-violet-600', 'bg-amber-600', 'bg-cyan-600']


def create_user_home():
    # 1. 获取用户状态
    username = app.storage.user.get('username', '访客')
    is_login = app.storage.user.get('authenticated', False)
    user_role = app.storage.user.get('role', 'user')

    # --- 导航栏 ---
    with ui.header().classes('bg-white text-slate-900 shadow-sm border-b items-center h-16 px-6'):
        # 1. Logo 区域
        with ui.row().classes('items-center gap-2 cursor-pointer'):
            ui.icon('movie_filter', color='primary').classes('text-3xl')
            ui.label('MovieRec Sys').classes('text-xl font-bold text-primary tracking-tight')

        # 2. 搜索区域
        # ✅ 修改点：添加 'ml-12' (margin-left) 让搜索框和 Logo 保持一点距离
        with ui.row().classes('items-center gap-0 ml-12'):
            search_input = ui.input(placeholder='搜索电影...').props('rounded-l outlined dense').classes('w-60 md:w-80')
            search_input.on('keydown.enter', lambda: load_movies(query=search_input.value))

            ui.button(icon='search', on_click=lambda: load_movies(query=search_input.value)) \
                .props('unelevated rounded-r color=primary dense') \
                .classes('h-10 px-4')

        # 3. 唯一的空格：把后面的内容（登录/头像）推到最右边
        ui.space()

        if is_login:
            with ui.row().classes('items-center gap-3'):
                ui.avatar(username[0].upper(), color='primary', text_color='white').props('size=sm font-size=14px')
                ui.label(f'{username}').classes('font-medium text-slate-600')

                if user_role == 'admin':
                    ui.button('后台管理', icon='dashboard', on_click=lambda: ui.navigate.to('/admin')) \
                        .props('unelevated dense color=blue') \
                        .tooltip('进入系统后台')

                ui.button(icon='logout', on_click=lambda: (app.storage.user.clear(), ui.navigate.to('/login'))) \
                    .props('flat round dense color=grey') \
                    .tooltip('退出登录')
        else:
            ui.button('登录', on_click=lambda: ui.navigate.to('/login')).props('unelevated color=primary')

    # --- 主容器 ---
    content_div = ui.column().classes('w-full min-h-screen bg-slate-50 items-center')

    async def load_movies(query=None):
        content_div.clear()

        with content_div:
            with ui.column().classes('w-full max-w-[1400px] p-6 gap-8'):

                # --- A. Banner (仅首页显示) ---
                if not query:
                    with ui.row().classes(
                            'w-full h-64 bg-gradient-to-r from-slate-900 to-slate-700 rounded-2xl shadow-lg relative overflow-hidden items-center px-10 text-white'):
                        ui.label('CINEMA').classes(
                            'absolute -right-10 -bottom-10 text-[150px] font-black text-white opacity-5 select-none')
                        with ui.column().classes('gap-2 z-10 max-w-2xl'):
                            ui.label('探索电影的无限可能').classes('text-4xl font-bold mb-2')
                            ui.label('基于千万级 IMDb 数据构建，结合协同过滤算法，为您提供个性化推荐。').classes(
                                'text-slate-200 text-lg')

                # --- 核心布局：左右分栏 ---
                with ui.row().classes('w-full items-start gap-10'):

                    # === 左侧：热门片库 ===
                    with ui.column().classes('flex-1 w-full gap-6'):
                        with ui.row().classes('w-full justify-between items-end'):
                            title = f'🔍 "{query}" 搜索结果' if query else '📚 热门片库'
                            ui.label(title).classes('text-2xl font-bold text-slate-800')
                            if not query:
                                ui.label('数据来源: IMDb Datasets').classes('text-xs text-slate-400')

                        movies_data = await movie_service.get_homepage_movies(page=1, page_size=24, search_query=query)

                        if not movies_data:
                            ui.label('暂无数据').classes('text-slate-400 py-10')
                        else:
                            # Grid 3 列
                            with ui.grid(columns=3).classes('w-full gap-6'):
                                # 【关键修改】这里要解包 (m, rating)
                                for index, (m, rating) in enumerate(movies_data):
                                    bg = BG_COLORS[index % len(BG_COLORS)]

                                    # 处理评分显示：如果没有评分，显示 'N/A'
                                    display_rating = str(rating) if rating else 'N/A'

                                    # 处理时长显示：如果是 None 则显示 '?'
                                    display_runtime = f"{m.runtimeMinutes}" if m.runtimeMinutes else "?"

                                    with ui.card().classes(
                                            'w-full h-[300px] p-0 gap-0 shadow hover:shadow-lg transition-all group'):

                                        # 封面区 (不变)
                                        with ui.column().classes(
                                                f'w-full h-[55%] {bg} items-center justify-center relative overflow-hidden'):
                                            ui.label(m.primaryTitle[:1]).classes(
                                                'text-8xl text-white opacity-30 font-black group-hover:scale-110 transition-transform')
                                            ui.label(str(m.startYear)).classes(
                                                'absolute top-2 right-2 bg-black/40 text-white text-xs px-2 rounded-full')

                                        # 内容区
                                        with ui.column().classes('w-full h-[45%] p-3 justify-between bg-white'):
                                            ui.label(m.primaryTitle).classes(
                                                'font-bold text-sm leading-tight line-clamp-2 h-10 text-slate-800')

                                            with ui.row().classes('gap-1'):
                                                for g in (m.genres or '').split(',')[:2]:
                                                    ui.label(g).classes(
                                                        'text-[10px] text-slate-500 bg-slate-100 px-1.5 rounded')

                                            # 【关键修改】显示真实数据
                                            with ui.row().classes(
                                                    'w-full justify-between border-t pt-2 mt-auto items-center'):
                                                # 真实评分
                                                ui.label(f'★ {display_rating}').classes(
                                                    'text-xs font-bold text-orange-500')
                                                # 真实时长
                                                ui.label(f'{display_runtime} min').classes('text-xs text-slate-400')

                    # === 右侧：侧边栏 ===
                    if is_login and not query:
                        with ui.column().classes('w-80 gap-6 lg:flex'):

                            # 模块：猜你喜欢
                            with ui.card().classes('w-full p-5 gap-4 shadow-sm bg-white'):
                                with ui.row().classes('items-center gap-2'):
                                    ui.icon('recommend', color='orange').classes('text-xl')
                                    ui.label('猜你喜欢').classes('font-bold text-lg text-slate-800')

                                ui.separator()

                                top_movies = await analysis_service.get_top_movies(limit=8)

                                if top_movies:
                                    with ui.column().classes('w-full gap-3'):
                                        for idx, (title, rating) in enumerate(top_movies):
                                            with ui.row().classes('w-full items-center justify-between group'):
                                                with ui.row().classes('items-center gap-2 flex-1 overflow-hidden'):
                                                    color_cls = 'text-orange-500' if idx < 3 else 'text-slate-400'
                                                    ui.label(str(idx + 1)).classes(f'font-bold text-sm {color_cls} w-4')
                                                    ui.label(title).classes(
                                                        'text-sm text-slate-600 truncate group-hover:text-primary transition-colors')
                                                ui.label(str(rating)).classes('text-xs font-bold text-orange-400')
                                else:
                                    ui.label('暂无推荐数据').classes('text-sm text-slate-400')

                            # 模块：快捷入口
                            with ui.card().classes('w-full p-5 gap-3 shadow-sm bg-blue-50 border border-blue-100'):
                                ui.label('🚀 快速通道').classes('font-bold text-slate-800')
                                ui.label('我的收藏').classes('text-sm text-slate-600')
                                ui.label('浏览历史').classes('text-sm text-slate-600')
                                ui.label('个人画像设置').classes('text-sm text-slate-600')

                # --- D. 页脚 ---
                ui.separator().classes('mt-10')
                with ui.column().classes('w-full items-center py-6 text-slate-400 gap-1'):
                    ui.label('© 2026 MovieRec Graduation Project').classes('text-sm')

    # 初始加载
    ui.timer(0, load_movies, once=True)