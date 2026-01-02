from nicegui import ui, app
from services import rating_service
import math


def create_rating_page():
    # --- 1. 状态管理 ---
    page_state = {'current_page': 1, 'page_size': 20}

    # --- 2. 侧边栏 (添加了评分管理的选中状态) ---
    with ui.left_drawer(value=True).classes('bg-blue-grey-1 text-slate-900'):
        ui.button('回首页', icon='home', on_click=lambda: ui.navigate.to('/')) \
            .classes('text-h6 font-bold text-primary w-full') \
            .props('flat align=left no-caps q-pa-md')
        ui.separator()
        with ui.column().classes('w-full q-pa-sm'):
            ui.button('仪表盘', icon='dashboard', on_click=lambda: ui.navigate.to('/admin')).classes('w-full').props(
                'flat')
            ui.button('用户管理', icon='people', on_click=lambda: ui.navigate.to('/admin/users')).classes(
                'w-full').props('flat')
            ui.button('演职人员', icon='badge', on_click=lambda: ui.navigate.to('/admin/people')).classes(
                'w-full').props('flat')
            ui.button('电影管理', icon='movie', on_click=lambda: ui.navigate.to('/admin/movies')).classes(
                'w-full').props('flat')
            # 当前页面高亮
            ui.button('评分管理', icon='star').classes('w-full shadow-sm bg-white text-primary').props('flat')
            ui.button('剧组管理', icon='star', on_click=lambda: ui.navigate.to('/admin/crew')).classes(
                'w-full').props('flat')
            ui.button('剧集管理', icon='subscriptions', on_click=lambda: ui.navigate.to('/admin/episodes')).classes(
                'w-full').props('flat')

    # --- 3. 主内容区 ---
    with ui.column().classes('w-full q-pa-md items-center'):
        # 标题栏
        with ui.row().classes('w-full justify-between items-center q-mb-lg q-mt-md'):
            ui.label('⭐ 电影评分管理').classes('text-h4 font-bold')
            ui.button('刷新列表', icon='refresh', on_click=lambda: load_data()).props(
                'unelevated rounded color=primary')

        # 表格卡片
        with ui.card().classes('w-full shadow-lg q-pa-none'):
            # 工具栏
            with ui.row().classes('q-pa-sm gap-2'):
                ui.button('新增评分', icon='add', on_click=lambda: open_edit_dialog(None)).props(
                    'unelevated color=green')
                ui.button('修改', icon='edit', on_click=lambda: edit_selected()).props('flat color=blue')
                ui.button('删除', icon='delete', on_click=lambda: delete_selected()).props('flat color=red')

                ui.space()  # 把搜索框挤到右边

                with ui.row().classes('items-center no-wrap gap-1'):
                    # 搜索输入框
                    search_input = ui.input(placeholder='请输入编号或名称') \
                        .props('dense outlined clearable') \
                        .classes('w-64') \
                        .on('keydown.enter', lambda: load_data())  # 回车也能搜

                    # 搜索按钮 (点击触发)
                    search_btn = ui.button(icon='search', on_click=lambda: load_data()) \
                        .props('flat round dense color=primary') \
                        .tooltip('点击查询')

                    # 等待提示 (加载圈)
                    # 默认 visible=False (隐藏)，加载时显示
                    loading_spinner = ui.spinner(size='2em').props('color=primary thickness=4')
                    loading_spinner.visible = False

            # 表格定义
            grid = ui.aggrid({
                'columnDefs': [
                    {'headerName': '电影编号 (ID)', 'field': 'tconst', 'checkboxSelection': True},
                    {'headerName': '电影名称', 'field': 'title'},
                    {'headerName': '平均评分', 'field': 'averageRating'},
                    {'headerName': '投票数', 'field': 'numVotes'},
                ],
                'rowData': [],
                'rowSelection': 'single',
                'pagination': False,
            }).classes('w-full shadow-lg').style('height: 70vh')

            # 分页控件
            with ui.row().classes('w-full justify-center items-center q-pa-sm bg-gray-50 border-t'):
                ui.button(icon='chevron_left', on_click=lambda: change_page(-1)).props('flat')
                pagination_label = ui.label('加载中...').classes('font-bold text-blue')
                ui.button(icon='chevron_right', on_click=lambda: change_page(1)).props('flat')

    # --- 4. 逻辑处理 ---
    async def load_data():
        # --- UI 交互：开始加载 ---
        loading_spinner.visible = True  # 显示转圈
        search_btn.disable()  # 禁用按钮防止狂点
        search_input.disable()  # 禁用输入框

        try:
            # 获取搜索词
            query = search_input.value

            # 1. 获取带搜索条件的总是 (用于计算页数)
            total_count = await rating_service.get_rating_count(query)

            # 计算总页数 (防止 total_count=0 时报错)
            total_pages = math.ceil(total_count / page_state['page_size']) if total_count > 0 else 1

            # 搜索时，如果当前页码超过了新的总页数，重置为第1页
            if page_state['current_page'] > total_pages:
                page_state['current_page'] = 1

            # 2. 获取带搜索条件的数据
            data_list = await rating_service.get_ratings_paginated(
                page_state['current_page'],
                page_state['page_size'],
                search_query=query  # 传入搜索词
            )
            rows = []
            for rating_obj, movie_name in data_list:
                rows.append({
                    'tconst': rating_obj.tconst,
                    'title': movie_name,  # 显示查询出来的电影名
                    'averageRating': rating_obj.averageRating,
                    'numVotes': rating_obj.numVotes
                })
            grid.options['rowData'] = rows
            grid.update()
            grid.run_grid_method('setRowData', rows)

            pagination_label.text = f"第 {page_state['current_page']} 页 / 共 {total_pages} 页"

            # 只有在非搜索状态下才提示“更新成功”，避免刷屏
            if not query:
                ui.notify('列表已更新', type='positive', timeout=500)
            else:
                ui.notify(f'查询完成，找到 {total_count} 条结果', type='info', timeout=1000)

        except Exception as e:
            ui.notify(f'加载失败: {e}', type='negative')
        finally:
            # --- UI 交互：结束加载 ---
            loading_spinner.visible = False  # 隐藏转圈
            search_btn.enable()  # 恢复按钮
            search_input.enable()  # 恢复输入框

    async def change_page(delta):
        page_state['current_page'] += delta
        if page_state['current_page'] < 1: page_state['current_page'] = 1
        await load_data()

    # --- 5. 弹窗逻辑 ---
    def open_edit_dialog(data=None):
        is_edit = data is not None
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label('编辑评分' if is_edit else '新增评分').classes('text-h6 font-bold')

            # 只有新增时允许输入 ID，编辑时锁定
            tconst_input = ui.input('电影编号 (tconst)', value=data['tconst'] if is_edit else '').classes('w-full')
            if is_edit: tconst_input.disable()

            # 评分和票数输入
            rating_input = ui.number('平均分 (0-10)', value=data['averageRating'] if is_edit else 0.0, format='%.1f',
                                     min=0, max=10).classes('w-full')
            votes_input = ui.number('投票数', value=data['numVotes'] if is_edit else 0, format='%.0f').classes('w-full')

            async def save():
                if not tconst_input.value:
                    ui.notify('必须填写电影编号', type='warning')
                    return

                if is_edit:
                    success, msg = await rating_service.update_rating(
                        tconst_input.value,
                        float(rating_input.value or 0),
                        int(votes_input.value or 0)
                    )
                else:
                    success, msg = await rating_service.create_rating(
                        tconst_input.value,
                        float(rating_input.value or 0),
                        int(votes_input.value or 0)
                    )

                if success:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    await load_data()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end q-mt-md'):
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('保存', on_click=save).props('unelevated color=primary')
        dialog.open()

    async def edit_selected():
        rows = await grid.get_selected_rows()
        if not rows:
            ui.notify('请先选中一行', type='warning')
            return
        open_edit_dialog(rows[0])

    async def delete_selected():
        rows = await grid.get_selected_rows()
        if not rows: return

        async def confirm():
            success, msg = await rating_service.delete_rating(rows[0]['tconst'])
            if success:
                ui.notify(msg, type='positive')
                await load_data()
            else:
                ui.notify(msg, type='negative')

        with ui.dialog() as dialog, ui.card():
            ui.label(f"确认删除 {rows[0]['tconst']} 的评分数据?").classes('font-bold text-red')
            with ui.row().classes('w-full justify-end'):
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('删除', color='red', on_click=lambda: [confirm(), dialog.close()])
        dialog.open()

    # 初始加载
    ui.timer(0.1, load_data, once=True)