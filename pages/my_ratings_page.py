from nicegui import ui, app
from services import interaction_service
import math

def create_my_ratings_page():
    user_id = app.storage.user.get('user_id')
    if not app.storage.user.get('authenticated', False) or not user_id:
        ui.notify('请先登录', type='warning')
        ui.navigate.to('/login')
        return

    page_state = {'current_page': 1, 'page_size': 15}

    # 头部
    with ui.header().classes('bg-white text-slate-900 shadow-sm border-b items-center h-16 px-6'):
        ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/')).props('flat color=primary')
        ui.label('⭐ 我的评分管理').classes('text-lg font-bold')

    content_div = ui.column().classes('w-full p-6 items-center bg-slate-50 min-h-screen')

    async def load_data():
        content_div.clear()
        data = await interaction_service.get_my_ratings_paginated(
            user_id, page_state['current_page'], page_state['page_size']
        )
        print(data)
        with content_div:
            with ui.card().classes('w-full max-w-4xl p-0 shadow-md'):
                # AgGrid 表格
                grid = ui.aggrid({
                    'columnDefs': [
                        {'headerName': '电影名称', 'field': 'title'},
                        {'headerName': '我的评分', 'field': 'rating'},
                        {'headerName': '评价时间', 'field': 'date'},
                    ],
                    'rowData': [
                        {
                            'title': title,
                            'rating': f"{r.rating} / 10",
                            'date': r.created_at.strftime('%Y-%m-%d %H:%M'),
                            'tconst': r.tconst
                        } for r, title in data
                    ],
                    'rowSelection': 'single',
                }).classes('h-[500px]')

                # 操作按钮
                with ui.row().classes('p-4 gap-2'):
                    async def delete_rate():
                        rows = await grid.get_selected_rows()
                        if not rows: return
                        success, msg = await interaction_service.delete_user_rating(user_id, rows[0]['tconst'])
                        if success:
                            ui.notify(msg, type='positive')
                            await load_data()

                    async def edit_rate():
                        rows = await grid.get_selected_rows()
                        if not rows: return
                        # 复用 home 页的评分弹窗逻辑 (这里简化演示)
                        with ui.dialog() as d, ui.card():
                            ui.label(f"修改 {rows[0]['title']} 的评分")
                            s = ui.slider(min=1, max=10, step=0.5, value=float(rows[0]['rating'].split()[0]))
                            ui.button('保存', on_click=lambda: save(d, rows[0]['tconst'], s.value))
                        d.open()

                    async def save(d, tconst, val):
                        await interaction_service.set_user_rating(user_id, tconst, val)
                        d.close()
                        await load_data()

                    ui.button('修改评分', icon='edit', on_click=edit_rate).props('flat color=blue')
                    ui.button('删除记录', icon='delete', on_click=delete_rate).props('flat color=red')

    ui.timer(0, load_data, once=True)