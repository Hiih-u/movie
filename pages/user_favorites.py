# pages/user_favorites.py
from nicegui import ui, app
from services import interaction_service
from pages import user_layout  # 引入布局

BG_COLORS = ['bg-blue-600', 'bg-rose-600', 'bg-emerald-600', 'bg-violet-600', 'bg-amber-600', 'bg-cyan-600']


def create_page():
    # 1. 渲染公共布局 (高亮 'favorites')
    user_layout.render_header_and_drawer('favorites')

    # 2. 页面主体内容
    user_id = app.storage.user.get('user_id')
    page_state = {'current_page': 1, 'page_size': 12}

    content_div = ui.column().classes('w-full p-6 items-center')

    async def load_data():
        content_div.clear()
        movies = await interaction_service.get_my_favorites_paginated(
            user_id, page_state['current_page'], page_state['page_size']
        )

        with content_div:
            # 标题
            ui.label('❤️ 我的收藏夹').classes('text-2xl font-bold text-rose-500 mb-6 self-start')

            if not movies:
                ui.label('暂无收藏数据').classes('text-slate-400')
                return

            # 网格列表 (逻辑保持不变)
            with ui.grid(columns=4).classes('w-full gap-6'):
                for index, m in enumerate(movies):
                    bg = BG_COLORS[index % len(BG_COLORS)]
                    with ui.card().classes('w-full h-[260px] p-0 gap-0 shadow hover:shadow-lg transition-all relative'):
                        # 删除按钮
                        ui.button(icon='delete', color='white', on_click=lambda e, mid=m.tconst: remove_fav(mid)) \
                            .props('flat round dense').classes(
                            'absolute top-2 right-2 z-20 bg-black/30 backdrop-blur-md hover:bg-red-500')

                        # 封面
                        with ui.column().classes(f'w-full h-[60%] {bg} items-center justify-center relative'):
                            ui.label(m.primaryTitle[:1]).classes('text-6xl text-white opacity-30 font-black')
                        # 信息
                        with ui.column().classes('w-full h-[40%] p-3 justify-between bg-white'):
                            ui.label(m.primaryTitle).classes('font-bold text-sm leading-tight line-clamp-2')
                            ui.label(f'★ {m.averageRating or "N/A"}').classes(
                                'text-xs font-bold text-orange-500 self-end')

            # 简易翻页
            with ui.row().classes('mt-4'):
                ui.button('上一页', on_click=lambda: change_page(-1)).props('flat dense')
                ui.label(f"Page {page_state['current_page']}").classes('mx-2 self-center')
                ui.button('下一页', on_click=lambda: change_page(1)).props('flat dense')

    async def change_page(delta):
        if page_state['current_page'] + delta < 1: return
        page_state['current_page'] += delta
        await load_data()

    async def remove_fav(tconst):
        await interaction_service.toggle_favorite(user_id, tconst)
        ui.notify('已移除')
        await load_data()

    ui.timer(0, load_data, once=True)