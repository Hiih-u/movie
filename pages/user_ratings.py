# pages/user_ratings.py
from nicegui import ui, app
from services import interaction_service
from pages import user_layout
import math

def create_page():
    # 1. 渲染公共布局 (高亮 'ratings')
    user_layout.render_header_and_drawer('ratings')

    # 2. 页面主体内容
    user_id = app.storage.user.get('user_id')
    page_state = {
        'current_page': 1,
        'page_size': 15,
        'total_pages': 1  # <--- 新增状态
    }

    content_div = ui.column().classes('w-full p-6 items-center')

    async def load_data():
        content_div.clear()

        total_count = await interaction_service.get_my_ratings_count(user_id)
        total_pages = math.ceil(total_count / page_state['page_size']) if total_count > 0 else 1
        page_state['total_pages'] = total_pages  # 更新状态

        if page_state['current_page'] > total_pages:
            page_state['current_page'] = 1

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
            with ui.row().classes('w-full mt-6 relative justify-center items-center'):

                # --- 1. 中间：翻页控制条 ---
                with ui.row().classes('items-center gap-4'):
                    # 上一页
                    ui.button('上一页', on_click=lambda: change_page(-1)) \
                        .props('flat dense icon=chevron_left') \
                        .bind_visibility_from(page_state, 'current_page', backward=lambda p: p > 1)

                    # 页码显示
                    ui.label(f"第 {page_state['current_page']} 页 / 共 {total_pages} 页") \
                        .classes('text-slate-500 font-medium')

                    # 下一页
                    ui.button('下一页', on_click=lambda: change_page(1)) \
                        .props('flat dense icon-right=chevron_right') \
                        .bind_visibility_from(page_state, 'current_page', backward=lambda p: p < total_pages)

                # --- 2. 右侧：删除按钮 (绝对定位) ---
                # absolute right-0: 强制贴在父容器的最右边
                with ui.row().classes('absolute right-0'):
                    async def do_delete():
                        rows = await grid.get_selected_rows()
                        if not rows:
                            ui.notify('请先选择一行评分记录', type='warning')
                            return
                        # 确认框 (可选)
                        # if not await confirm_dialog(...): return

                        await interaction_service.delete_user_rating(user_id, rows[0]['tconst'])
                        ui.notify('删除成功', type='positive')
                        await load_data()

                    ui.button('删除记录', icon='delete', color='red', on_click=do_delete) \
                        .props('flat dense') \
                        .tooltip('删除选中的评分')

        async def change_page(delta):
            new_page = page_state['current_page'] + delta
            # 边界检查
            if new_page < 1 or new_page > page_state['total_pages']:
                return
            page_state['current_page'] = new_page
            await load_data()

    ui.timer(0, load_data, once=True)