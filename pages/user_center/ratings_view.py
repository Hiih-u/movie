from nicegui import ui
from services import interaction_service


async def show(container: ui.column, user_id: int):
    """渲染我的评分页面"""
    container.clear()
    page_state = {'current_page': 1, 'page_size': 15}

    with container:
        ui.label('⭐ 我的评分历史').classes('text-2xl font-bold text-orange-500 mb-6 self-start')
        table_container = ui.column().classes('w-full')

        async def render_table():
            table_container.clear()
            data = await interaction_service.get_my_ratings_paginated(
                user_id, page_state['current_page'], page_state['page_size']
            )

            with table_container:
                if not data:
                    ui.label('暂无评分记录').classes('text-slate-400 italic')
                    return

                # 数据转换
                rows = [{
                    'tconst': r.tconst,
                    'title': title,
                    'rating': str(r.rating),
                    'date': r.created_at.strftime('%Y-%m-%d %H:%M') if r.created_at else ''
                } for r, title in data]

                grid = ui.aggrid({
                    'columnDefs': [
                        {'headerName': '电影名称', 'field': 'title'},
                        {'headerName': '我的打分', 'field': 'rating',
                         'cellStyle': {'color': 'orange', 'fontWeight': 'bold'}},
                        {'headerName': '时间', 'field': 'date'},
                    ],
                    'rowData': rows,
                    'rowSelection': 'single',
                }).classes('w-full h-[500px] shadow-sm border')

                # 底部操作栏 (翻页与操作)
                with ui.row().classes('w-full justify-between mt-4'):
                    with ui.row():
                        ui.button('上一页', on_click=lambda: change_page(-1)).props('flat dense')
                        ui.label(f"第 {page_state['current_page']} 页").classes('self-center mx-2')
                        ui.button('下一页', on_click=lambda: change_page(1)).props('flat dense')

                    with ui.row().classes('gap-2'):
                        ui.button('修改', icon='edit', on_click=lambda: edit_rate(grid)).props('flat color=primary')
                        ui.button('删除', icon='delete', on_click=lambda: delete_rate(grid)).props('flat color=red')

        # --- 辅助逻辑函数 ---
        async def change_page(delta):
            if page_state['current_page'] + delta < 1: return
            page_state['current_page'] += delta
            await render_table()

        async def delete_rate(grid):
            rows = await grid.get_selected_rows()
            if not rows:
                ui.notify('请先选择一行', type='warning')
                return
            success, msg = await interaction_service.delete_user_rating(user_id, rows[0]['tconst'])
            if success:
                ui.notify(msg, type='positive')
                await render_table()

        async def edit_rate(grid):
            rows = await grid.get_selected_rows()
            if not rows: return
            row = rows[0]
            with ui.dialog() as d, ui.card().classes('w-80'):
                ui.label(f"修改: {row['title']}")
                slider = ui.slider(min=1, max=10, step=0.5, value=float(row['rating'])).props(
                    'label-always color=orange')
                ui.button('保存',
                          on_click=lambda: [interaction_service.set_user_rating(user_id, row['tconst'], slider.value),
                                            d.close(), render_table(), ui.notify('保存成功')])
            d.open()

        await render_table()