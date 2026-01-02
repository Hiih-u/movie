from nicegui import ui, app
from services import movie_service
import math


def create_movie_page():
    # --- 1. 状态管理 ---
    page_state = {'current_page': 1, 'page_size': 20}  # 改成每页20条，体验更好

    # --- 2. 侧边栏 (导航菜单) ---
    with ui.left_drawer(value=True).classes('bg-blue-grey-1 text-slate-900') \
            .props('width=220 breakpoint=700') as drawer:
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
            ui.button('电影管理', icon='movie').classes('w-full shadow-sm bg-white text-primary').props('flat')
            ui.button('评分管理', icon='star', on_click=lambda: ui.navigate.to('/admin/ratings')).classes(
                'w-full').props('flat')
            ui.button('剧组管理', icon='star', on_click=lambda: ui.navigate.to('/admin/crew')).classes(
                'w-full').props('flat')
            ui.button('剧集管理', icon='subscriptions', on_click=lambda: ui.navigate.to('/admin/episodes')).classes(
                'w-full').props('flat')

    # --- 3. 主内容区 ---
    with ui.column().classes('w-full q-pa-md items-center'):
        # 3.1 标题栏 刷新列表按钮下移
        with ui.row().classes('w-full justify-between items-center q-mb-lg q-mt-md'):
            ui.label('🎬 电影资源管理').classes('text-h4 font-bold')
            with ui.row().classes('gap-2'):
                # 【新增】重建缓存按钮
                async def do_refresh():
                    ui.notify('正在后台重建索引，请稍候...', type='info')
                    success, msg = await movie_service.refresh_movie_summary()
                    if success:
                        ui.notify(msg, type='positive')
                    else:
                        ui.notify(msg, type='negative')

                ui.button('重建缓存', icon='cloud_sync', on_click=do_refresh) \
                    .props('outline rounded color=deep-orange') \
                    .tooltip('点击将重新生成首页的热度排序数据')

                ui.button('刷新列表', icon='refresh', on_click=lambda: load_data()) \
                    .props('unelevated rounded color=primary shadow-sm')

        # 3.2 表格区域
        with ui.card().classes('w-full shadow-lg q-pa-none'):
            # (1) 工具栏
            with ui.row().classes('q-pa-sm gap-2'):
                ui.button('新增电影', icon='add', on_click=lambda: open_add_dialog()).props('unelevated color=green')
                ui.button('编辑', icon='edit', on_click=lambda: edit_selected()).props('flat color=blue')
                ui.button('下架', icon='delete', on_click=lambda: delete_selected()).props('flat color=red')

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

            grid = ui.aggrid({
                'columnDefs': [
                    {'headerName': '编号', 'field': 'tconst', 'checkboxSelection': True},
                    {'headerName': '电影名称', 'field': 'primaryTitle'},
                    {'headerName': '上映年份', 'field': 'startYear'},
                    {'headerName': '类型标签', 'field': 'genres'},
                ],
                'rowData': [],
                'rowSelection': 'single',
                'pagination': False,
            }).classes('w-full shadow-lg').style('height: 70vh')

            # (3) 分页条
            with ui.row().classes('w-full justify-center items-center q-pa-sm bg-gray-50 border-t'):
                ui.button(icon='chevron_left', on_click=lambda: change_page(-1)).props('flat')
                pagination_label = ui.label('加载中...').classes('font-bold text-blue')
                ui.button(icon='chevron_right', on_click=lambda: change_page(1)).props('flat')

    # --- 4. 逻辑处理 ---

    async def change_page(delta):
        page_state['current_page'] += delta
        if page_state['current_page'] < 1: page_state['current_page'] = 1
        await load_data()

    async def load_data():
        # --- UI 交互：开始加载 ---
        loading_spinner.visible = True  # 显示转圈
        search_btn.disable()  # 禁用按钮防止狂点
        search_input.disable()  # 禁用输入框

        try:
            # 获取搜索词
            query = search_input.value

            # 1. 获取带搜索条件的总是 (用于计算页数)
            total_count = await movie_service.get_movie_count(query)

            # 计算总页数 (防止 total_count=0 时报错)
            total_pages = math.ceil(total_count / page_state['page_size']) if total_count > 0 else 1

            # 搜索时，如果当前页码超过了新的总页数，重置为第1页
            if page_state['current_page'] > total_pages:
                page_state['current_page'] = 1

            # 2. 获取带搜索条件的数据
            raw_data = await movie_service.get_movies_paginated(
                page_state['current_page'],
                page_state['page_size'],
                search_query=query  # 传入搜索词
            )

            rows = []
            for m in raw_data:
                rows.append({
                    'tconst': str(m.tconst) if m.tconst else '',
                    'primaryTitle': str(m.primaryTitle) if m.primaryTitle else '',
                    'startYear': str(m.startYear) if m.startYear else '',
                    'genres': str(m.genres) if m.genres else ''
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

    # --- 5. CRUD 弹窗逻辑 (保留原有逻辑) ---
    async def open_add_dialog():
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label('✨ 新增电影').classes('text-h6 font-bold text-green')
            id_input = ui.input('编号 (如 tt9999999)').classes('w-full')
            name_input = ui.input('电影名称').classes('w-full')
            year_input = ui.number('上映年份', format='%.0f').classes('w-full')
            genres_input = ui.input('类型 (逗号分隔)').classes('w-full')

            async def do_create():
                if not id_input.value or not name_input.value:
                    ui.notify('编号和名称必填', type='warning')
                    return
                success, msg = await movie_service.create_movie(
                    id_input.value, name_input.value,
                    int(year_input.value) if year_input.value else None,
                    genres_input.value
                )
                if success:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    await load_data()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end q-mt-md'):
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('确认', on_click=do_create).props('unelevated color=green')
        dialog.open()

    async def edit_selected():
        selected = await grid.get_selected_rows()
        if not selected:
            ui.notify('请先选中一行', type='warning')
            return
        row = selected[0]

        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label(f'编辑: {row["tconst"]}').classes('text-h6')
            name_input = ui.input('电影名称', value=row['primaryTitle']).classes('w-full')
            year_input = ui.number('上映年份', value=row['startYear'], format='%.0f').classes('w-full')
            genres_input = ui.input('类型', value=row['genres']).classes('w-full')

            async def do_save():
                success = await movie_service.update_movie_details(
                    row['tconst'], name_input.value,
                    int(year_input.value) if year_input.value else None,
                    genres_input.value
                )
                if success:
                    ui.notify('已更新', type='positive')
                    dialog.close()
                    await load_data()
                else:
                    ui.notify('更新失败', type='negative')

            with ui.row().classes('w-full justify-end q-mt-md'):
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('保存', on_click=do_save).props('unelevated color=primary')
        dialog.open()

    async def delete_selected():
        selected = await grid.get_selected_rows()
        if not selected: return

        async def do_delete():
            success = await movie_service.delete_movie(selected[0]['tconst'])
            if success:
                ui.notify('已删除', type='positive')
                dialog.close()
                await load_data()
            else:
                ui.notify('删除失败', type='negative')

        with ui.dialog() as dialog, ui.card():
            ui.label('确认删除?').classes('font-bold text-red')
            with ui.row().classes('w-full justify-end'):
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('确认', color='red', on_click=do_delete)
        dialog.open()

    # 初始加载
    ui.timer(0.1, load_data, once=True)