from nicegui import ui, app
# 【修改 1】导入 interaction_service 服务
from services import movie_service, analysis_service, interaction_service
import random

BG_COLORS = ['bg-blue-600', 'bg-rose-600', 'bg-emerald-600', 'bg-violet-600', 'bg-amber-600', 'bg-cyan-600']


def create_user_home():
    # 1. 获取用户状态
    username = app.storage.user.get('username', '访客')
    is_login = app.storage.user.get('authenticated', False)
    user_role = app.storage.user.get('role', 'user')
    # 【修改 2】获取 user_id (用于数据库操作)
    user_id = app.storage.user.get('user_id', None)

    # --- 导航栏 ---
    with ui.header().classes('bg-white text-slate-900 shadow-sm border-b items-center h-16 px-6'):
        # 1. Logo 区域
        with ui.row().classes('items-center gap-2 cursor-pointer'):
            ui.icon('movie_filter', color='primary').classes('text-3xl')
            ui.label('MovieRec Sys').classes('text-xl font-bold text-primary tracking-tight')

        # 2. 搜索区域
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
                        .props('outline rounded-full dense color=primary') \
                        .classes('px-4') \
                        .tooltip('进入系统后台')

                ui.button(icon='logout', on_click=lambda: (app.storage.user.clear(), ui.navigate.to('/login'))) \
                    .props('flat round dense color=grey') \
                    .tooltip('退出登录')
        else:
            ui.button('登录', on_click=lambda: ui.navigate.to('/login')).props('unelevated color=primary')

    # --- 主容器 ---
    content_div = ui.column().classes('w-full min-h-screen bg-slate-50 items-center')

    # --- 【修改 3】交互逻辑函数 (收藏与评分) ---

    async def toggle_fav(e, tconst):
        """点击收藏/取消收藏"""
        if not is_login:
            ui.notify('请先登录', type='warning')
            return

        # 调用后端切换状态
        is_added, msg = await interaction_service.toggle_favorite(user_id, tconst)
        ui.notify(msg, type='positive' if is_added else 'info')

        # 刷新当前图标状态
        btn = e.sender
        if is_added:
            btn.props('icon=favorite color=red')
        else:
            btn.props('icon=favorite_border color=white')

    def open_rate_dialog(tconst, title, current_score=0):
        """打开评分弹窗"""
        if not is_login:
            ui.notify('请先登录', type='warning')
            return

        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label(f'给 "{title}" 打分').classes('text-lg font-bold')
            ui.label('拖动滑块进行评价 (1-10分)').classes('text-xs text-slate-400')

            # 滑块组件 (默认值设为8.0或当前评分)
            slider = ui.slider(min=1, max=10, step=0.5, value=current_score or 8.0).props('label-always color=orange')

            async def save():
                await interaction_service.set_user_rating(user_id, tconst, slider.value)
                ui.notify('评分成功！', type='positive')
                dialog.close()
                # 刷新列表以更新显示的“我的评分”
                await load_movies(search_input.value)

            with ui.row().classes('w-full justify-end q-mt-md'):
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('提交', on_click=save).props('unelevated color=orange')
        dialog.open()

    # --- 加载数据主逻辑 ---

    async def load_movies(query=None):
        content_div.clear()

        # 【修改 4】预先获取当前用户的收藏列表和评分字典
        my_favs = set()
        my_ratings = {}
        if is_login and user_id:
            my_favs = await interaction_service.get_user_favorite_ids(user_id)
            my_ratings = await interaction_service.get_user_ratings_map(user_id)

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

                        movies = await movie_service.get_homepage_movies(page=1, page_size=24, search_query=query)

                        if not movies:
                            ui.label('暂无数据').classes('text-slate-400 py-10')
                        else:
                            # Grid 3 列
                            with ui.grid(columns=3).classes('w-full gap-6'):
                                for index, m in enumerate(movies):
                                    bg = BG_COLORS[index % len(BG_COLORS)]

                                    display_rating = str(m.averageRating) if m.averageRating else 'N/A'
                                    display_runtime = f"{m.runtimeMinutes}" if m.runtimeMinutes else "?"

                                    # 卡片容器 (增加 relative 以便定位收藏按钮)
                                    with ui.card().classes(
                                            'w-full h-[320px] p-0 gap-0 shadow hover:shadow-lg transition-all group relative'):

                                        # 【修改 5】右上角收藏按钮 (绝对定位)
                                        if is_login:
                                            is_fav = m.tconst in my_favs
                                            fav_icon = 'favorite' if is_fav else 'favorite_border'
                                            fav_color = 'red' if is_fav else 'white'

                                            ui.button(icon=fav_icon,
                                                      on_click=lambda e, mid=m.tconst: toggle_fav(e, mid)) \
                                                .props(f'flat round color={fav_color} dense') \
                                                .classes('absolute top-2 right-2 z-20 bg-black/20 backdrop-blur-sm')

                                        # 封面区
                                        with ui.column().classes(
                                                f'w-full h-[55%] {bg} items-center justify-center relative overflow-hidden'):
                                            ui.label(m.primaryTitle[:1]).classes(
                                                'text-8xl text-white opacity-30 font-black group-hover:scale-110 transition-transform')
                                            ui.label(str(m.startYear)).classes(
                                                'absolute bottom-2 left-2 bg-black/40 text-white text-xs px-2 rounded-full')

                                        # 内容区
                                        with ui.column().classes('w-full h-[45%] p-3 justify-between bg-white'):
                                            ui.label(m.primaryTitle).classes(
                                                'font-bold text-sm leading-tight line-clamp-2 h-10 text-slate-800')

                                            with ui.row().classes('gap-1'):
                                                for g in (m.genres or '').split(',')[:2]:
                                                    ui.label(g).classes(
                                                        'text-[10px] text-slate-500 bg-slate-100 px-1.5 rounded')

                                            ui.separator().classes('my-1')

                                            # 【修改 6】底部信息栏：左侧 IMDb 分，右侧“我的评分”
                                            with ui.row().classes(
                                                    'w-full justify-between items-center'):
                                                # IMDb 评分
                                                ui.label(f'IMDb: {display_rating}').classes(
                                                    'text-xs font-bold text-slate-500')

                                                # 用户评分按钮
                                                if is_login:
                                                    my_score = my_ratings.get(m.tconst)
                                                    # 如果评过分，显示分数；没评过，显示“打分”
                                                    btn_text = str(my_score) if my_score else '打分'
                                                    btn_color = 'orange' if my_score else 'grey-5'
                                                    btn_icon = 'star' if my_score else 'star_outline'

                                                    ui.button(btn_text, icon=btn_icon,
                                                              on_click=lambda mid=m.tconst, t=m.primaryTitle,
                                                                              s=my_score: open_rate_dialog(mid, t, s)) \
                                                        .props(f'flat dense size=sm color={btn_color}') \
                                                        .tooltip('点击进行个人评分')
                                                else:
                                                    # 未登录只显示时长
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
                                ui.link('进入个人中心', '/user-center').classes(
                                    'text-sm text-blue-600 font-bold cursor-pointer hover:underline text-lg')
                                # 【修改】将 Label 改为 Link 或 Button，并绑定跳转
                                ui.link('我的收藏列表', '/favorites').classes(
                                    'text-sm text-blue-600 font-bold cursor-pointer hover:underline')
                                ui.link('我的评分管理', '/my-ratings').classes(
                                    'text-sm text-orange-600 font-bold cursor-pointer hover:underline')
                                ui.label('个人画像设置').classes('text-sm text-slate-600')

                # --- D. 页脚 ---
                ui.separator().classes('mt-10')
                with ui.column().classes('w-full items-center py-6 text-slate-400 gap-1'):
                    ui.label('© 2026 MovieRec Graduation Project').classes('text-sm')

    # 初始加载
    ui.timer(0, load_movies, once=True)