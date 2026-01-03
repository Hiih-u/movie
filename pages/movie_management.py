# pages/movie_management.py
from nicegui import ui, app
from services import movie_service
import math

# 定义支持的影视类型 (IMDb 标准)
TITLE_TYPES = {
    'movie': '电影 (Movie)',
    'tvSeries': '连续剧 (TV Series)',
    'tvMiniSeries': '迷你剧 (Mini Series)',
    'tvMovie': '电视电影 (TV Movie)',
    'short': '短片 (Short)',
    'video': '视频 (Video)'
}


def create_movie_page():
    # --- 1. 状态管理 ---
    page_state = {'current_page': 1, 'page_size': 20}

    # --- 2. 侧边栏 (保持不变) ---
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
            # 高亮当前页
            ui.button('影视管理', icon='movie').classes('w-full shadow-sm bg-white text-primary').props('flat')
            ui.button('评分管理', icon='star', on_click=lambda: ui.navigate.to('/admin/ratings')).classes(
                'w-full').props('flat')
            ui.button('剧组管理', icon='groups', on_click=lambda: ui.navigate.to('/admin/crew')).classes(
                'w-full').props('flat')
            ui.button('剧集管理', icon='subscriptions', on_click=lambda: ui.navigate.to('/admin/episodes')).classes(
                'w-full').props('flat')

    # --- 3. 主内容区 ---
    with ui.column().classes('w-full q-pa-md items-center'):
        # 3.1 标题栏
        with ui.row().classes('w-full justify-between items-center q-mb-lg q-mt-md'):
            ui.label('🎬 影视内容库管理').classes('text-h4 font-bold')
            with ui.row().classes('gap-2'):
                # 重建缓存按钮
                async def do_refresh():
                    ui.notify('正在后台重建索引，请稍候...', type='info')
                    success, msg = await movie_service.refresh_movie_summary()
                    if success:
                        ui.notify(msg, type='positive')
                    else:
                        ui.notify(msg, type='negative')

                ui.button('重建缓存', icon='cloud_sync', on_click=do_refresh) \
                    .props('outline rounded color=deep-orange') \
                    .tooltip('修改数据后，点击此按钮同步到首页')

                ui.button('刷新列表', icon='refresh', on_click=lambda: load_data()) \
                    .props('unelevated rounded color=primary shadow-sm')

        # 3.2 表格区域
        with ui.card().classes('w-full shadow-lg q-pa-none'):
            # (1) 工具栏
            with ui.row().classes('q-pa-sm gap-2'):
                ui.button('新增作品', icon='add', on_click=lambda: open_edit_dialog(None)).props(
                    'unelevated color=green')
                ui.button('编辑', icon='edit', on_click=lambda: edit_selected()).props('flat color=blue')
                ui.button('下架', icon='delete', on_click=lambda: delete_selected()).props('flat color=red')

                ui.space()

                with ui.row().classes('items-center no-wrap gap-1'):
                    search_input = ui.input(placeholder='请输入编号或名称') \
                        .props('dense outlined clearable') \
                        .classes('w-64') \
                        .on('keydown.enter', lambda: load_data())

                    search_btn = ui.button(icon='search', on_click=lambda: load_data()) \
                        .props('flat round dense color=primary') \
                        .tooltip('点击查询')

                    loading_spinner = ui.spinner(size='2em').props('color=primary thickness=4')
                    loading_spinner.visible = False

            # (2) 表格定义 (增加 Type 列)
            grid = ui.aggrid({
                'columnDefs': [
                    {'headerName': '编号 (ID)', 'field': 'tconst', 'checkboxSelection': True},
                    {'headerName': '类型', 'field': 'titleType', 'cellStyle': {'color': 'gray'}},  # 新增
                    {'headerName': '影视名称', 'field': 'primaryTitle'},
                    {'headerName': '年份', 'field': 'startYear'},
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
        loading_spinner.visible = True
        search_btn.disable()
        search_input.disable()

        try:
            query = search_input.value
            total_count = await movie_service.get_movie_count(query)
            total_pages = math.ceil(total_count / page_state['page_size']) if total_count > 0 else 1

            if page_state['current_page'] > total_pages:
                page_state['current_page'] = 1

            raw_data = await movie_service.get_movies_paginated(
                page_state['current_page'],
                page_state['page_size'],
                search_query=query
            )

            rows = []
            for m in raw_data:
                # 转换类型显示 (把 movie 显示为 电影)
                type_display = TITLE_TYPES.get(m.titleType, m.titleType)

                rows.append({
                    'tconst': str(m.tconst),
                    'titleType': type_display,  # 显示友好名称
                    'titleTypeRaw': m.titleType,  # 保留原始值用于编辑回显
                    'primaryTitle': str(m.primaryTitle or ''),
                    'startYear': str(m.startYear or ''),
                    'genres': str(m.genres or '')
                })

            pagination_label.text = f"第 {page_state['current_page']} 页 / 共 {total_pages} 页"

            grid.options['rowData'] = rows
            await grid.run_grid_method('setRowData', rows, timeout=5.0)


            if not query:
                ui.notify('列表已更新', type='positive', timeout=500)
            else:
                ui.notify(f'查询完成，找到 {total_count} 条结果', type='info', timeout=1000)


        except Exception as e:
            error_msg = str(e)
            if "JavaScript did not respond" in error_msg:
                print(f"⚠️ 忽略前端超时警告: {error_msg}")  # 控制台留个底
            else:
                ui.notify(f'加载失败: {error_msg}', type='negative')
        finally:
            loading_spinner.visible = False
            search_btn.enable()
            search_input.enable()

    # --- 5. 弹窗逻辑 (合并新增和编辑) ---
    def open_edit_dialog(data=None):
        is_edit = data is not None

        with ui.dialog() as dialog, ui.card().classes('w-96'):
            title_text = '编辑作品信息' if is_edit else '✨ 新增影视作品'
            ui.label(title_text).classes('text-h6 font-bold text-primary')

            # ID 输入框 (新增必填，编辑锁定)
            id_input = ui.input('编号 (如 tt1234567)', value=data['tconst'] if is_edit else '') \
                .classes('w-full').props('outlined dense')
            if is_edit: id_input.disable()

            # 类型选择框 (新增可选，编辑通常锁定或仅展示)
            # 这里的 options 使用我们定义的字典的 keys
            type_options = list(TITLE_TYPES.keys())
            # 如果是编辑，尝试获取原始类型，否则默认为 movie
            default_type = data['titleTypeRaw'] if is_edit else 'movie'

            type_select = ui.select(
                options=TITLE_TYPES,  # 使用字典作为选项，会自动显示 value
                value=default_type,
                label='作品类型'
            ).classes('w-full').props('outlined dense')

            # 如果是编辑模式，为了数据一致性，通常不建议随意修改类型（除非你知道你在做什么）
            # 这里暂时允许修改，或者你可以 .disable()
            if is_edit: type_select.disable()

            name_input = ui.input('名称', value=data['primaryTitle'] if is_edit else '') \
                .classes('w-full').props('outlined dense')

            year_input = ui.number('上映年份', value=data['startYear'] if is_edit else None, format='%.0f') \
                .classes('w-full').props('outlined dense')

            genres_input = ui.input('类型标签 (如 Drama,Action)', value=data['genres'] if is_edit else '') \
                .classes('w-full').props('outlined dense')

            async def save():
                if not id_input.value or not name_input.value:
                    ui.notify('编号和名称必填', type='warning')
                    return

                if is_edit:
                    # 编辑逻辑 (目前 service 里的 update_movie_details 只更新 title, year, genres)
                    success = await movie_service.update_movie_details(
                        id_input.value,
                        name_input.value,
                        int(year_input.value) if year_input.value else None,
                        genres_input.value
                    )
                    msg = "更新成功" if success else "更新失败"
                else:
                    # 新增逻辑 (需要传递 type)
                    success, msg = await movie_service.create_movie(
                        tconst=id_input.value,
                        title=name_input.value,
                        year=int(year_input.value) if year_input.value else None,
                        genres=genres_input.value,
                        type_str=type_select.value  # 传入选择的类型
                    )

                if success:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    await load_data()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end q-mt-md gap-2'):
                ui.button('取消', on_click=dialog.close).props('flat color=grey')
                ui.button('保存', on_click=save).props('unelevated color=primary')

        dialog.open()

    async def edit_selected():
        selected = await grid.get_selected_rows()
        if not selected:
            ui.notify('请先选中一行', type='warning')
            return
        open_edit_dialog(selected[0])

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
            ui.label('⚠️ 危险操作').classes('font-bold text-red text-lg')
            ui.label(f"确定要永久删除 {selected[0]['primaryTitle']} 吗？").classes('text-slate-600')
            with ui.row().classes('w-full justify-end q-mt-md'):
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('确认删除', color='red', on_click=do_delete).props('unelevated')
        dialog.open()

    # 初始加载
    ui.timer(0.1, load_data, once=True)