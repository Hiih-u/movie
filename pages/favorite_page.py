from nicegui import ui, app
from services import interaction_service
import math

BG_COLORS = ['bg-blue-600', 'bg-rose-600', 'bg-emerald-600', 'bg-violet-600', 'bg-amber-600', 'bg-cyan-600']


def create_favorite_page():
    # 1. 权限检查
    user_id = app.storage.user.get('user_id')
    if not app.storage.user.get('authenticated', False) or not user_id:
        ui.notify('请先登录', type='warning')
        ui.navigate.to('/login')
        return

    # 2. 状态管理
    page_state = {'current_page': 1, 'page_size': 12}

    # --- 顶部导航栏 (简版) ---
    with ui.header().classes('bg-white text-slate-900 shadow-sm border-b items-center h-16 px-6'):
        with ui.row().classes('items-center gap-2 cursor-pointer').on('click', lambda: ui.navigate.to('/')):
            ui.icon('arrow_back', color='primary').classes('text-2xl')
            ui.label('返回首页').classes('text-lg font-bold text-primary')

        ui.space()
        ui.label('❤️ 我的收藏夹').classes('text-lg font-bold text-rose-500')

    # --- 内容区域 ---
    content_div = ui.column().classes('w-full min-h-screen bg-slate-50 items-center p-6')

    async def load_data():
        content_div.clear()

        # 获取数据 (使用之前定义的优化版查询接口)
        movies = await interaction_service.get_my_favorites_paginated(
            user_id,
            page_state['current_page'],
            page_state['page_size']
        )

        # 如果没数据
        if not movies:
            with content_div:
                ui.icon('favorite_border').classes('text-6xl text-slate-300 mt-20')
                ui.label('还没有收藏任何电影').classes('text-slate-400 text-lg')
                ui.button('去发现好电影', on_click=lambda: ui.navigate.to('/')).props('flat color=primary')
            return

        with content_div:
            with ui.column().classes('w-full max-w-[1200px] gap-6'):
                # 标题与分页信息
                with ui.row().classes('w-full justify-between items-center'):
                    ui.label(f'已收藏 {len(movies)} 部 (本页)').classes('text-slate-500')

                    # 简易翻页
                    with ui.row().classes('gap-2'):
                        ui.button(icon='chevron_left', on_click=lambda: change_page(-1)).props(
                            'flat dense').disable() if page_state['current_page'] == 1 else ui.button(
                            icon='chevron_left', on_click=lambda: change_page(-1)).props('flat dense')
                        ui.label(f"第 {page_state['current_page']} 页").classes('self-center text-sm')
                        ui.button(icon='chevron_right', on_click=lambda: change_page(1)).props('flat dense')

                # 电影网格 (Grid)
                with ui.grid(columns=4).classes('w-full gap-6'):
                    for index, m in enumerate(movies):
                        bg = BG_COLORS[index % len(BG_COLORS)]

                        with ui.card().classes(
                                'w-full h-[280px] p-0 gap-0 shadow hover:shadow-lg transition-all group relative'):
                            # --- 移除按钮 (悬浮) ---
                            ui.button(icon='delete', color='white', on_click=lambda e, mid=m.tconst: remove_fav(mid)) \
                                .props('flat round dense') \
                                .classes(
                                'absolute top-2 right-2 z-20 bg-black/30 backdrop-blur-md hover:bg-red-500/80 transition-colors') \
                                .tooltip('取消收藏')

                            # 封面
                            with ui.column().classes(f'w-full h-[60%] {bg} items-center justify-center relative'):
                                ui.label(m.primaryTitle[:1]).classes('text-6xl text-white opacity-30 font-black')
                                ui.label(str(m.startYear)).classes(
                                    'absolute bottom-2 left-2 bg-black/40 text-white text-xs px-2 rounded-full')

                            # 信息
                            with ui.column().classes('w-full h-[40%] p-3 justify-between bg-white'):
                                ui.label(m.primaryTitle).classes('font-bold text-sm leading-tight line-clamp-2')
                                with ui.row().classes('w-full justify-between items-center mt-auto'):
                                    ui.label(f'★ {m.averageRating or "N/A"}').classes(
                                        'text-xs font-bold text-orange-500')
                                    ui.label(m.genres.split(',')[0] if m.genres else '').classes(
                                        'text-[10px] text-slate-400 bg-slate-100 px-1 rounded')

    # --- 交互逻辑 ---
    async def remove_fav(tconst):
        # 调用服务取消收藏
        success, msg = await interaction_service.toggle_favorite(user_id, tconst)
        ui.notify(msg, type='info')
        # 重新加载列表
        await load_data()

    async def change_page(delta):
        new_page = page_state['current_page'] + delta
        if new_page < 1: return
        page_state['current_page'] = new_page
        await load_data()

    # 初始加载
    ui.timer(0, load_data, once=True)