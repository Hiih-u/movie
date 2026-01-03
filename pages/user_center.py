# pages/user_center.py
from nicegui import ui, app
from services import interaction_service
import math

# 用于收藏卡片的背景色
BG_COLORS = ['bg-blue-600', 'bg-rose-600', 'bg-emerald-600', 'bg-violet-600', 'bg-amber-600', 'bg-cyan-600']


def create_user_center_page():
    # --- 1. 权限检查 ---
    user_id = app.storage.user.get('user_id')
    username = app.storage.user.get('username', '用户')

    if not app.storage.user.get('authenticated', False) or not user_id:
        ui.notify('请先登录', type='warning')
        ui.navigate.to('/login')
        return

    # --- 2. 页面布局 ---

    # 2.1 顶部导航 (Header)
    with ui.header().classes('bg-white text-slate-900 shadow-sm border-b items-center h-16 px-6'):
        with ui.row().classes('items-center gap-2 cursor-pointer').on('click', lambda: ui.navigate.to('/')):
            ui.icon('arrow_back', color='primary').classes('text-2xl')
            ui.label('返回首页').classes('text-lg font-bold text-primary')

        ui.space()
        ui.avatar(username[0].upper(), color='primary', text_color='white').classes('mr-2')
        ui.label(f'{username} 的个人中心').classes('text-lg font-bold text-slate-700')

    # 2.2 侧边栏 (Left Drawer)
    with ui.left_drawer(value=True).classes('bg-slate-50 border-r') as drawer:
        with ui.column().classes('w-full q-pa-md gap-2'):
            ui.label('菜单').classes('text-xs font-bold text-slate-400 q-mb-sm')

            # 定义侧边栏按钮样式
            def menu_btn(label, icon, func):
                ui.button(label, icon=icon, on_click=func) \
                    .props('flat align=left').classes('w-full text-slate-700')

            menu_btn('我的收藏', 'favorite', lambda: load_favorites_view())
            menu_btn('我的评分', 'star', lambda: load_ratings_view())
            # 未来可以加 menu_btn('个人资料', 'person', ...)

    # 2.3 主内容区域 (Main Content)
    # 我们用一个 clearable 的容器来动态切换内容
    content_container = ui.column().classes('w-full p-6 min-h-screen items-center bg-white')

    # --- 3. 模块逻辑：我的收藏 ---
    async def load_favorites_view():
        content_container.clear()
        page_state = {'current_page': 1, 'page_size': 12}

        with content_container:
            ui.label('❤️ 我的收藏夹').classes('text-2xl font-bold text-rose-500 mb-6 self-start')

            # 容器用于放置 grid 和分页
            list_container = ui.column().classes('w-full')

            async def render_list():
                list_container.clear()
                # 获取数据
                movies = await interaction_service.get_my_favorites_paginated(
                    user_id, page_state['current_page'], page_state['page_size']
                )

                with list_container:
                    if not movies:
                        ui.label('暂无收藏').classes('text-slate-400 italic')
                        return

                    # 顶部工具条 (页码)
                    with ui.row().classes('w-full justify-between items-center mb-4'):
                        ui.label(f'第 {page_state["current_page"]} 页').classes('text-sm text-slate-500')
                        with ui.row():
                            ui.button(icon='chevron_left', on_click=lambda: change_page(-1)).props('flat dense')
                            ui.button(icon='chevron_right', on_click=lambda: change_page(1)).props('flat dense')

                    # 电影网格
                    with ui.grid(columns=4).classes('w-full gap-6'):
                        for index, m in enumerate(movies):
                            bg = BG_COLORS[index % len(BG_COLORS)]
                            with ui.card().classes(
                                    'w-full h-[260px] p-0 gap-0 shadow hover:shadow-lg transition-all group relative'):
                                # 删除按钮
                                ui.button(icon='delete', color='white',
                                          on_click=lambda e, mid=m.tconst: remove_fav(mid)) \
                                    .props('flat round dense').classes(
                                    'absolute top-2 right-2 z-20 bg-black/30 backdrop-blur-md hover:bg-red-500') \
                                    .tooltip('取消收藏')

                                # 封面
                                with ui.column().classes(f'w-full h-[60%] {bg} items-center justify-center relative'):
                                    ui.label(m.primaryTitle[:1]).classes('text-6xl text-white opacity-30 font-black')
                                    ui.label(str(m.startYear)).classes(
                                        'absolute bottom-2 left-2 bg-black/40 text-white text-xs px-2 rounded-full')

                                # 信息
                                with ui.column().classes('w-full h-[40%] p-3 justify-between bg-white'):
                                    ui.label(m.primaryTitle).classes('font-bold text-sm leading-tight line-clamp-2')
                                    ui.label(f'★ {m.averageRating or "N/A"}').classes(
                                        'text-xs font-bold text-orange-500 self-end')

            async def change_page(delta):
                new_page = page_state['current_page'] + delta
                if new_page < 1: return
                page_state['current_page'] = new_page
                await render_list()

            async def remove_fav(tconst):
                await interaction_service.toggle_favorite(user_id, tconst)
                ui.notify('已移除', type='info')
                await render_list()

            # 初始渲染列表
            await render_list()

    # --- 4. 模块逻辑：我的评分 ---
    async def load_ratings_view():
        content_container.clear()
        page_state = {'current_page': 1, 'page_size': 15}

        with content_container:
            ui.label('⭐ 我的评分历史').classes('text-2xl font-bold text-orange-500 mb-6 self-start')

            # 表格容器
            table_container = ui.column().classes('w-full')

            async def render_table():
                table_container.clear()
                # 获取数据
                data = await interaction_service.get_my_ratings_paginated(
                    user_id, page_state['current_page'], page_state['page_size']
                )

                with table_container:
                    if not data:
                        ui.label('暂无评分记录').classes('text-slate-400 italic')
                        return

                    # 准备 AgGrid 数据
                    rows = []
                    for r, title in data:
                        rows.append({
                            'tconst': r.tconst,
                            'title': title,
                            'rating': f"{r.rating}",
                            'date': r.created_at.strftime('%Y-%m-%d %H:%M') if r.created_at else ''
                        })

                    # AgGrid
                    grid = ui.aggrid({
                        'columnDefs': [
                            {'headerName': '电影名称', 'field': 'title'},
                            {'headerName': '我的打分', 'field': 'rating',
                             'cellStyle': {'color': 'orange', 'fontWeight': 'bold'}},
                            {'headerName': '评价时间', 'field': 'date'},
                        ],
                        'rowData': rows,
                        'rowSelection': 'single',
                        'pagination': False
                    }).classes('w-full h-[500px] shadow-sm border')

                    # 底部操作栏
                    with ui.row().classes('w-full justify-between items-center mt-4'):
                        # 翻页按钮
                        with ui.row():
                            ui.button('上一页', on_click=lambda: change_page(-1)).props('flat dense')
                            ui.label(f"第 {page_state['current_page']} 页").classes('self-center mx-2')
                            ui.button('下一页', on_click=lambda: change_page(1)).props('flat dense')

                        # 操作按钮
                        with ui.row().classes('gap-2'):
                            ui.button('修改评分', icon='edit', on_click=lambda: edit_rate(grid)).props(
                                'flat color=primary')
                            ui.button('删除记录', icon='delete', on_click=lambda: delete_rate(grid)).props(
                                'flat color=red')

            async def change_page(delta):
                if page_state['current_page'] + delta < 1: return
                page_state['current_page'] += delta
                await render_table()

            # 删除逻辑
            async def delete_rate(grid):
                rows = await grid.get_selected_rows()
                if not rows:
                    ui.notify('请先选择一行', type='warning')
                    return
                success, msg = await interaction_service.delete_user_rating(user_id, rows[0]['tconst'])
                if success:
                    ui.notify(msg, type='positive')
                    await render_table()

            # 修改逻辑 (弹窗)
            async def edit_rate(grid):
                rows = await grid.get_selected_rows()
                if not rows: return
                row = rows[0]

                with ui.dialog() as d, ui.card().classes('w-80'):
                    ui.label(f"修改: {row['title']}").classes('font-bold')
                    slider = ui.slider(min=1, max=10, step=0.5, value=float(row['rating'])).props(
                        'label-always color=orange')

                    async def save():
                        await interaction_service.set_user_rating(user_id, row['tconst'], slider.value)
                        ui.notify('修改成功', type='positive')
                        d.close()
                        await render_table()

                    ui.button('保存', on_click=save).props('unelevated color=primary w-full')
                d.open()

            # 初始渲染表格
            await render_table()

    # --- 5. 默认显示 ---
    # 默认加载收藏页
    ui.timer(0, load_favorites_view, once=True)