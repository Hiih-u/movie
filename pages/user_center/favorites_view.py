from nicegui import ui
from services import interaction_service

# 颜色常量放这里，或者单独的一个 constants.py
BG_COLORS = ['bg-blue-600', 'bg-rose-600', 'bg-emerald-600', 'bg-violet-600', 'bg-amber-600', 'bg-cyan-600']


async def show(container: ui.column, user_id: int):
    """渲染我的收藏页面"""
    container.clear()  # 先清空容器

    # 状态需要保存在闭包或对象中，这里简单使用字典
    page_state = {'current_page': 1, 'page_size': 12}

    with container:
        ui.label('❤️ 我的收藏夹').classes('text-2xl font-bold text-rose-500 mb-6 self-start')

        # 列表容器
        list_container = ui.column().classes('w-full')

        async def render_list():
            list_container.clear()
            movies = await interaction_service.get_my_favorites_paginated(
                user_id, page_state['current_page'], page_state['page_size']
            )

            with list_container:
                if not movies:
                    ui.label('暂无收藏').classes('text-slate-400 italic')
                    return

                # 分页控制条
                with ui.row().classes('w-full justify-between items-center mb-4'):
                    ui.label(f'第 {page_state["current_page"]} 页').classes('text-sm text-slate-500')
                    with ui.row():
                        ui.button(icon='chevron_left', on_click=lambda: change_page(-1)).props('flat dense')
                        ui.button(icon='chevron_right', on_click=lambda: change_page(1)).props('flat dense')

                # 电影卡片网格
                with ui.grid(columns=4).classes('w-full gap-6'):
                    for index, m in enumerate(movies):
                        bg = BG_COLORS[index % len(BG_COLORS)]
                        with ui.card().classes(
                                'w-full h-[260px] p-0 gap-0 shadow hover:shadow-lg transition-all group relative'):
                            # 删除按钮
                            ui.button(icon='delete', color='white', on_click=lambda e, mid=m.tconst: remove_fav(mid)) \
                                .props('flat round dense').classes(
                                'absolute top-2 right-2 z-20 bg-black/30 backdrop-blur-md hover:bg-red-500') \
                                .tooltip('取消收藏')

                            # 封面与信息 (简化展示)
                            with ui.column().classes(f'w-full h-[60%] {bg} items-center justify-center relative'):
                                ui.label(m.primaryTitle[:1]).classes('text-6xl text-white opacity-30 font-black')
                            with ui.column().classes('w-full h-[40%] p-3 justify-between bg-white'):
                                ui.label(m.primaryTitle).classes('font-bold text-sm leading-tight line-clamp-2')
                                ui.label(f'★ {m.averageRating or "N/A"}').classes(
                                    'text-xs font-bold text-orange-500 self-end')

        async def change_page(delta):
            if page_state['current_page'] + delta < 1: return
            page_state['current_page'] += delta
            await render_list()

        async def remove_fav(tconst):
            await interaction_service.toggle_favorite(user_id, tconst)
            ui.notify('已移除', type='info')
            await render_list()

        # 初始加载
        await render_list()