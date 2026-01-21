from nicegui import ui, app
from services import movie_service, analysis_service, interaction_service, recommendation_service
import random
import math

# 卡片背景色池
BG_COLORS = ['bg-blue-600', 'bg-rose-600', 'bg-emerald-600', 'bg-violet-600', 'bg-amber-600', 'bg-cyan-600']

# --- [新增] 导航菜单配置 ---
NAV_ITEMS = [
    {'label': '全部', 'value': 'all', 'icon': 'apps'},
    {'label': '电影', 'value': 'movie', 'icon': 'movie'},
    {'label': '电视剧', 'value': 'tv', 'icon': 'tv'},
    {'label': '动漫', 'value': 'anime', 'icon': 'palette'},
    {'label': '综艺', 'value': 'variety', 'icon': 'mic'},
    {'label': '纪录片', 'value': 'doc', 'icon': 'menu_book'}
]


# --- 情感推荐弹窗逻辑 ---
async def open_mood_dialog(mood, category='all'):
    ui.notify(f'正在感知您的情绪: "{mood}" ...', type='info')

    # 【核心修改】解包返回结果：电影列表 + 暖心文案
    # 注意：analysis_service.MOOD_SCENARIOS 需要在文件头部确保能访问到 keys 用于 Chip 渲染
    # 但这里我们是直接调用函数，只需要改接收部分

    # 调用后端 (返回的是 tuple: (list, str))
    movies, warm_msg = await analysis_service.get_movies_by_mood(mood, category=category)

    with ui.dialog() as dialog, ui.card().classes('w-[600px] h-[80vh] p-0 flex flex-col'):
        # 1. 头部：使用更柔和的渐变色
        with ui.column().classes('w-full p-6 bg-gradient-to-r from-purple-600 to-indigo-600 text-white gap-2 relative'):
            # 关闭按钮
            ui.button(icon='close', on_click=dialog.close) \
                .props('flat round dense text-color=white') \
                .classes('absolute top-2 right-2')

            # 标题
            with ui.row().classes('items-center gap-2'):
                ui.label(f'{mood} 专属片单').classes('text-2xl font-bold')

            # 【新增】展示暖心文案
            # 使用 italic 字体增加情感度
            ui.label(warm_msg).classes('text-sm text-purple-100 italic font-medium leading-relaxed')

        # 2. 内容区
        with ui.scroll_area().classes('flex-1 p-4 bg-slate-50'):
            if not movies:
                with ui.column().classes('w-full items-center py-10 gap-2'):
                    ui.icon('sentiment_dissatisfied', size='xl', color='grey')
                    ui.label('暂未找到匹配的影片，不过没关系，休息一下也是很好的选择。').classes('text-slate-400')
            else:
                with ui.column().classes('w-full gap-3'):
                    for m in movies:
                        # 卡片样式优化
                        with ui.card().classes(
                                'w-full p-3 shadow-sm border border-purple-50 hover:shadow-md transition-all'):
                            with ui.row().classes('w-full justify-between items-start no-wrap'):
                                with ui.column().classes('gap-1 flex-1'):
                                    ui.label(m['primaryTitle']).classes(
                                        'font-bold text-md leading-tight text-slate-800')
                                    with ui.row().classes('items-center gap-2'):
                                        ui.label(str(m['startYear'])).classes(
                                            'text-xs text-slate-500 bg-slate-100 px-1.5 rounded')
                                        # 简单截取 genres
                                        ui.label(m['genres'].replace(',', ' / ')).classes('text-xs text-purple-500')

                                with ui.column().classes('items-end'):
                                    ui.label(f"★ {m['averageRating']}").classes('font-bold text-orange-500 text-lg')

        # 3. 底部
        with ui.row().classes('w-full p-3 border-t justify-end bg-white'):
            ui.button('关闭', on_click=dialog.close).props('unelevated color=indigo-600')

    dialog.open()


def create_user_home():
    # 1. 获取用户状态
    username = app.storage.user.get('username', '访客')
    is_login = app.storage.user.get('authenticated', False)
    user_role = app.storage.user.get('role', 'user')
    user_id = app.storage.user.get('user_id', None)

    # [新增] 当前选中的分类 (默认全部)
    current_category = {'value': 'all'}

    pagination = {
        'page': 1,
        'page_size': 24,
        'total_pages': 1
    }

    # --- 顶部导航栏 ---
    with ui.header().classes('bg-white text-slate-900 shadow-sm border-b items-center h-16 px-6'):
        with ui.row().classes('items-center gap-2 cursor-pointer'):
            ui.icon('movie_filter', color='primary').classes('text-3xl')
            ui.label('影视系统').classes('text-xl font-bold text-primary tracking-tight')

        with ui.row().classes('items-center gap-0 ml-12'):
            search_input = ui.input(placeholder='搜索电影...').props('rounded-l outlined dense').classes('w-60 md:w-80')
            search_input.on('keydown.enter', lambda: load_movies(query=search_input.value))
            ui.button(icon='search', on_click=lambda: load_movies(query=search_input.value)) \
                .props('unelevated rounded-r color=primary dense').classes('h-10 px-4')

        ui.space()

        if is_login:
            with ui.row().classes('items-center gap-3'):
                ui.avatar(username[0].upper(), color='primary', text_color='white').props('size=sm font-size=14px')
                ui.label(f'{username}').classes('font-medium text-slate-600')
                if user_role == 'admin':
                    ui.button('后台管理', icon='dashboard', on_click=lambda: ui.navigate.to('/admin')) \
                        .props('outline rounded-full dense color=primary').classes('px-4')
                ui.button(icon='logout', on_click=lambda: (app.storage.user.clear(), ui.navigate.to('/login'))) \
                    .props('flat round dense color=grey')
        else:
            ui.button('登录', on_click=lambda: ui.navigate.to('/login')).props('unelevated color=primary')

    # --- 主内容容器 ---
    content_div = ui.column().classes('w-full min-h-screen bg-slate-50 items-center')

    # --- 交互逻辑 (收藏/评分) ---
    async def toggle_fav(e, tconst):
        if not is_login:
            ui.notify('请先登录', type='warning')
            return
        is_added, msg = await interaction_service.toggle_favorite(user_id, tconst)
        ui.notify(msg, type='positive' if is_added else 'info')
        btn = e.sender
        btn.props('icon=favorite color=red' if is_added else 'icon=favorite_border color=white')

    async def change_page(delta):
        """
        翻页处理
        """
        new_page = pagination['page'] + delta
        if new_page < 1 or new_page > pagination['total_pages']:
            return

        # 【修改点】先执行滚动，再加载数据
        # 这样做的时候，按钮还存在，上下文是安全的
        ui.run_javascript('window.scrollTo(0, 0)')

        pagination['page'] = new_page

        # 加载数据 (这一步会执行 content_div.clear() 删除旧按钮)
        await load_movies(query=search_input.value)

    def open_rate_dialog(tconst, title, current_score=0):
        if not is_login:
            ui.notify('请先登录', type='warning')
            return
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label(f'给 "{title}" 打分').classes('text-lg font-bold')
            slider = ui.slider(min=1, max=10, step=0.5, value=current_score or 8.0).props('label-always color=orange')

            async def save():
                await interaction_service.set_user_rating(user_id, tconst, slider.value)
                ui.notify('评分成功！', type='positive')
                dialog.close()
                await load_movies(search_input.value)

            with ui.row().classes('w-full justify-end q-mt-md'):
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('提交', on_click=save).props('unelevated color=orange')
        dialog.open()

    # --- [核心] 加载数据逻辑 ---
    async def load_movies(query=None):
        content_div.clear()

        # 预加载用户数据
        my_favs = set()
        my_ratings = {}
        if is_login and user_id:
            my_favs = await interaction_service.get_user_favorite_ids(user_id)
            my_ratings = await interaction_service.get_user_ratings_map(user_id)

        total_count = await movie_service.get_homepage_movie_count(
            search_query=query,
            category=current_category['value']
        )

        pagination['total_pages'] = math.ceil(total_count / pagination['page_size']) if total_count > 0 else 1

        cat_val = current_category['value']

        # 修正当前页码 (防止搜索后页码超出范围)
        if pagination['page'] > pagination['total_pages']:
            pagination['page'] = 1

        with content_div:
            with ui.column().classes('w-full max-w-[1400px] p-6 gap-6'):

                # 1. 顶部 Banner (仅在 "全部" 分类且无搜索时显示)
                if not query and current_category['value'] == 'all':
                    with ui.row().classes(
                            'w-full h-64 bg-gradient-to-r from-slate-900 to-slate-700 rounded-2xl shadow-lg relative overflow-hidden items-center px-10 text-white'):
                        ui.label('CINEMA').classes(
                            'absolute -right-10 -bottom-10 text-[150px] font-black text-white opacity-5 select-none')
                        with ui.column().classes('gap-3 z-10 max-w-3xl'):
                            ui.label('基于 Python 的影视推荐系统').classes('text-4xl font-bold mb-1 tracking-wide')
                            ui.label('千万级 IMDb 知识库，深度融合 协同过滤、情感计算 与 语义分析 技术。').classes(
                                'text-slate-200 text-lg font-medium')
                            with ui.row().classes('items-center gap-2 text-slate-400 text-sm'):
                                ui.icon('hub', size='xs')
                                ui.label('不仅是精准推荐，更是连接您与影视世界的智慧桥梁。')

                # 2. [新增] 分类导航栏 (无搜索时显示)
                if not query:
                    with ui.card().classes(
                            'w-full p-2 shadow-sm bg-white sticky top-0 z-40 rounded-xl border border-slate-100'):
                        with ui.row().classes('gap-2 justify-center'):
                            for item in NAV_ITEMS:
                                is_active = (current_category['value'] == item['value'])
                                btn_props = 'unelevated' if is_active else 'flat'
                                btn_color = 'primary' if is_active else 'grey-8'
                                # 点击切换分类
                                ui.button(item['label'], icon=item['icon'],
                                          on_click=lambda _, v=item['value']: switch_category(v)) \
                                    .props(f'{btn_props} rounded color={btn_color}') \
                                    .classes('px-5 font-bold transition-all')

                # 3. 主内容区：左右分栏
                with ui.row().classes('w-full items-start gap-10'):

                    # === 左侧：片库列表 ===
                    with ui.column().classes('flex-1 w-full gap-6'):
                        # 动态标题
                        cat_label = next((x['label'] for x in NAV_ITEMS if x['value'] == current_category['value']),
                                         '列表')
                        title_text = f'🔍 "{query}" 搜索结果' if query else f'📚 {cat_label}精选'

                        with ui.row().classes('w-full justify-between items-end'):
                            ui.label(title_text).classes('text-2xl font-bold text-slate-800')
                            if not query: ui.label('数据来源: IMDb Datasets').classes('text-xs text-slate-400')

                        # 调用 Service (传入 category)
                        movies = await movie_service.get_homepage_movies(
                            page=pagination['page'],  # <--- 使用状态里的 page
                            page_size=pagination['page_size'],
                            search_query=query,
                            category=current_category['value']
                        )

                        if not movies:
                            ui.label('该分类下暂无数据...').classes('text-slate-400 py-10')
                        else:
                            with ui.grid(columns=3).classes('w-full gap-6'):
                                for index, m in enumerate(movies):
                                    bg = BG_COLORS[index % len(BG_COLORS)]
                                    display_rating = str(m.averageRating) if m.averageRating else 'N/A'

                                    with ui.card().classes(
                                            'w-full h-[320px] p-0 gap-0 shadow hover:shadow-lg transition-all group relative'):
                                        # 收藏按钮
                                        if is_login:
                                            is_fav = m.tconst in my_favs
                                            fav_icon = 'favorite' if is_fav else 'favorite_border'
                                            fav_color = 'red' if is_fav else 'white'
                                            ui.button(icon=fav_icon,
                                                      on_click=lambda e, mid=m.tconst: toggle_fav(e, mid)) \
                                                .props(f'flat round color={fav_color} dense') \
                                                .classes('absolute top-2 right-2 z-20 bg-black/20 backdrop-blur-sm')

                                        # 封面
                                        with ui.column().classes(
                                                f'w-full h-[55%] {bg} items-center justify-center relative overflow-hidden'):
                                            ui.label(m.primaryTitle[:1]).classes(
                                                'text-8xl text-white opacity-30 font-black group-hover:scale-110 transition-transform')
                                            ui.label(str(m.startYear)).classes(
                                                'absolute bottom-2 left-2 bg-black/40 text-white text-xs px-2 rounded-full')

                                        # 内容
                                        with ui.column().classes('w-full h-[45%] p-3 justify-between bg-white'):
                                            ui.label(m.primaryTitle).classes(
                                                'font-bold text-sm leading-tight line-clamp-2 h-10 text-slate-800')
                                            with ui.row().classes('gap-1'):
                                                # 简单的类型展示
                                                genres = (m.genres or '').split(',')[:2]
                                                for g in genres:
                                                    ui.label(g).classes(
                                                        'text-[10px] text-slate-500 bg-slate-100 px-1.5 rounded')
                                            ui.separator().classes('my-1')

                                            with ui.row().classes('w-full justify-between items-center'):
                                                ui.label(f'IMDb: {display_rating}').classes(
                                                    'text-xs font-bold text-slate-500')
                                                if is_login:
                                                    my_score = my_ratings.get(m.tconst)
                                                    btn_text = str(my_score) if my_score else '打分'
                                                    btn_color = 'orange' if my_score else 'grey-5'
                                                    ui.button(btn_text, icon='star' if my_score else 'star_outline',
                                                              on_click=lambda mid=m.tconst, t=m.primaryTitle,
                                                                              s=my_score: open_rate_dialog(mid, t, s)) \
                                                        .props(f'flat dense size=sm color={btn_color}')
                                                else:
                                                    ui.label(f'{m.runtimeMinutes or "?"} min').classes(
                                                        'text-xs text-slate-400')

                            with ui.row().classes('w-full justify-center items-center mt-10 gap-4'):
                                # 上一页按钮
                                ui.button('上一页', on_click=lambda: change_page(-1)) \
                                    .props('flat color=grey-7 icon=chevron_left') \
                                    .bind_visibility_from(pagination, 'page', backward=lambda p: p > 1)

                                # 页码显示 (直接使用 f-string 显示，不需要 bind)
                                ui.label(f"第 {pagination['page']} 页 / 共 {pagination['total_pages']} 页") \
                                    .classes('text-slate-600 font-medium bg-slate-100 px-4 py-1 rounded-full text-sm')

                                # 下一页按钮
                                ui.button('下一页', on_click=lambda: change_page(1)) \
                                    .props('flat color=primary icon-right=chevron_right') \
                                    .bind_visibility_from(pagination, 'page', backward=lambda p: p < pagination['total_pages'])

                    # === 右侧：侧边栏 ===
                    if is_login and not query:
                        with ui.column().classes('w-80 gap-6 flex-none'):  # 移动端隐藏侧边栏

                            # 1. 情感树洞
                            with ui.card().classes(
                                    'w-full p-5 gap-3 shadow-sm bg-gradient-to-r from-indigo-500 to-purple-600 text-white'):
                                with ui.row().classes('items-center gap-2'):
                                    ui.icon('psychology', color='white').classes('text-xl')
                                    ui.label('情感树洞').classes('font-bold text-lg')
                                ui.label('说出你的故事，树洞 为你配电影').classes('text-xs text-indigo-100')
                                mood_input = ui.input(placeholder='例如：今天加班好累...') \
                                    .props('dark dense standoutless input-class="text-white"').classes('w-full')

                                async def analyze_and_open():
                                    if not mood_input.value:
                                        ui.notify('请先写下您的感受~', type='warning')
                                        return
                                    detected_mood = analysis_service.analyze_text_mood(mood_input.value)
                                    if detected_mood:
                                        ui.notify(f'感知到您可能觉得 "{detected_mood}"', type='positive',
                                                  icon='auto_awesome')
                                        await open_mood_dialog(detected_mood, category=current_category['value'])
                                    else:
                                        ui.notify('抱歉，没读懂您的情绪，请试着换个说法', type='info')

                                ui.button('生成推荐', icon='auto_awesome', on_click=analyze_and_open) \
                                    .props('unelevated color=white text-color=indigo-600 w-full')

                            # 2. 心情推荐
                            with ui.card().classes(
                                    'w-full p-5 gap-3 shadow-sm bg-gradient-to-br from-purple-50 to-pink-50 border border-purple-100'):
                                with ui.row().classes('items-center gap-2'):
                                    ui.label('🎭 此刻心情').classes('font-bold text-lg text-purple-900')
                                    ui.badge('New', color='purple').props('text-color=white dense')
                                with ui.row().classes('gap-2'):
                                    moods = analysis_service.MOOD_SCENARIOS.keys()
                                    for m in moods:
                                        # 点击标签触发函数 (记得传 category)
                                        ui.chip(m, on_click=lambda e, mood=m: open_mood_dialog(mood, category=
                                        current_category['value'])) \
                                            .props(
                                            'clickable color=white text-color=purple-800 icon-right=chevron_right') \
                                            .classes('shadow-sm hover:bg-purple-100 transition-colors')

                            # 3. 猜你喜欢 (推荐系统)
                            with ui.card().classes('w-full p-5 gap-4 shadow-sm bg-white'):
                                with ui.row().classes('items-center gap-2'):
                                    ui.icon('recommend', color='orange').classes('text-xl')
                                    # 动态标题：让用户知道推荐变了
                                    rec_title = '猜你喜欢'
                                    if cat_val == 'variety':
                                        rec_title = '为您推荐的综艺'
                                    elif cat_val == 'anime':
                                        rec_title = '为您推荐的动漫'
                                    elif cat_val == 'movie':
                                        rec_title = '为您推荐的电影'

                                    ui.label(rec_title).classes('font-bold text-lg text-slate-800')

                                ui.separator()

                                # 推荐策略：Spark -> 实时CF -> 热门
                                data_source = await recommendation_service.get_spark_recommendations(
                                    user_id, limit=8, category=cat_val
                                )
                                is_personalized = True

                                # 2. 实时协同过滤 (带过滤)
                                if not data_source:
                                    data_source = await recommendation_service.get_recommendations(
                                        user_id, limit=8, category=cat_val
                                    )

                                # 3. 兜底策略：如果个性化推荐在这个分类下没结果，就取该分类的“热门榜单”
                                if not data_source:
                                    is_personalized = False
                                    # 我们需要 modify analysis_service 来支持 category，或者直接调用 movie_service 获取热门
                                    # 最简单的方法：复用 movie_service.get_homepage_movies (它本身就是按热度排序的)
                                    top_raw = await movie_service.get_homepage_movies(
                                        page=1, page_size=8, category=cat_val
                                    )
                                    data_source = top_raw  # movie_service 返回的就是 MovieSummary 对象列表

                                # --- UI 渲染逻辑 ---
                                if is_personalized:
                                    ui.label('✨ 根据您的口味生成').classes('text-xs text-purple-500 q-mb-xs')
                                else:
                                    ui.label('🔥 热门榜单 (暂无个性化数据)').classes('text-xs text-orange-400 q-mb-xs')

                                if data_source:
                                    with ui.column().classes('w-full gap-3'):
                                        for idx, m in enumerate(data_source):
                                            title = m.primaryTitle if hasattr(m, 'primaryTitle') else m['primaryTitle']
                                            rating = m.averageRating if hasattr(m, 'averageRating') else m[
                                                'averageRating']
                                            with ui.row().classes('w-full items-start justify-between group'):
                                                with ui.row().classes('gap-2 flex-1 flex-nowrap items-start'):
                                                    color_cls = 'text-orange-500' if idx < 3 else 'text-slate-400'
                                                    ui.label(str(idx + 1)).classes(
                                                        f'font-bold text-sm {color_cls} w-4 flex-shrink-0 leading-tight')
                                                    ui.label(title).classes(
                                                        'text-sm text-slate-600 group-hover:text-primary transition-colors leading-tight flex-1 break-words')
                                                ui.label(str(rating)).classes(
                                                    'text-xs font-bold text-orange-400 q-ml-sm')
                                else:
                                    ui.label('暂无数据').classes('text-sm text-slate-400')

                            # 4. 快捷通道
                            with ui.card().classes('w-full p-5 gap-3 shadow-sm bg-blue-50 border border-blue-100'):
                                ui.label('🚀 快速通道').classes('font-bold text-slate-800')
                                with ui.row().classes('items-center gap-2'):
                                    ui.icon('favorite', size='xs', color='red')
                                    ui.link('我的收藏列表', '/user/favorites').classes(
                                        'text-sm text-slate-700 hover:text-rose-600')
                                with ui.row().classes('items-center gap-2'):
                                    ui.icon('star', size='xs', color='orange')
                                    ui.link('我的评分管理', '/user/ratings').classes(
                                        'text-sm text-slate-700 hover:text-orange-600')

                # 4. 页脚
                ui.separator().classes('mt-10')
                with ui.column().classes('w-full items-center py-6 text-slate-400 gap-1'):
                    ui.label('© 2026 MovieRec Graduation Project').classes('text-sm')

    # --- 切换分类函数 ---
    async def switch_category(val):
        current_category['value'] = val
        # 切换分类时清空搜索框
        search_input.value = ''
        # 重新加载数据 (必须 await，否则会报错 coroutine never awaited)
        pagination['page'] = 1
        await load_movies()

    # 初始加载
    ui.timer(0, load_movies, once=True)