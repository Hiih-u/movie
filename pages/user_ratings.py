# pages/user_ratings.py
from nicegui import ui, app
from services import interaction_service
from pages import user_layout


def create_page():
    # 1. 渲染公共布局 (高亮 'ratings')
    user_layout.render_header_and_drawer('ratings')

    # 2. 页面主体内容
    user_id = app.storage.user.get('user_id')
    page_state = {'current_page': 1, 'page_size': 15}

    content_div = ui.column().classes('w-full p-6 items-center')

    async def load_data():
        content_div.clear()
        data = await interaction_service.get_my_ratings_paginated(
            user_id, page_state['current_page'], page_state['page_size']
        )

        with content_div:
            ui.label('⭐ 我的评分记录').classes('text-2xl font-bold text-orange-500 mb-6 self-start')

            if not data:
                ui.label('暂无评分数据').classes('text-slate-400')
                return

            # 构造 AgGrid 数据
            rows = [{
                'tconst': r.tconst,
                'title': title,
                'rating': r.rating,
                'date': r.created_at.strftime('%Y-%m-%d %H:%M') if r.created_at else ''
            } for r, title in data]

            # 表格
            grid = ui.aggrid({
                'columnDefs': [
                    {'headerName': '电影名称', 'field': 'title'},
                    {'headerName': '我的评分', 'field': 'rating',
                     'cellStyle': {'color': 'orange', 'fontWeight': 'bold'}},
                    {'headerName': '时间', 'field': 'date'},
                ],
                'rowData': rows,
                'rowSelection': 'single',
            }).classes('w-full h-[500px] shadow-sm border')

            # 操作区
            with ui.row().classes('mt-4 w-full justify-end gap-2'):
                async def do_delete():
                    rows = await grid.get_selected_rows()
                    if not rows: return
                    await interaction_service.delete_user_rating(user_id, rows[0]['tconst'])
                    ui.notify('删除成功', type='positive')
                    await load_data()

                ui.button('删除记录', icon='delete', color='red', on_click=do_delete).props('flat')

            # 翻页
            with ui.row().classes('mt-4 justify-center'):
                ui.button('上一页', on_click=lambda: change_page(-1)).props('flat dense')
                ui.label(f"Page {page_state['current_page']}").classes('mx-2 self-center')
                ui.button('下一页', on_click=lambda: change_page(1)).props('flat dense')

    async def change_page(delta):
        if page_state['current_page'] + delta < 1: return
        page_state['current_page'] += delta
        await load_data()

    ui.timer(0, load_data, once=True)