from nicegui import ui, app
from services import person_service
import math


def create_person_page():
    # --- 1. 状态管理 ---
    page_state = {'current_page': 1, 'page_size': 20}

    # --- 2. 侧边栏 (包含新模块入口) ---
    with ui.left_drawer(value=True).classes('bg-blue-grey-1 text-slate-900'):
        ui.label('IMDB 后台管理').classes('text-h6 q-pa-md font-bold text-primary')
        ui.separator()
        with ui.column().classes('w-full q-pa-sm'):
            ui.button('仪表盘', icon='dashboard', on_click=lambda: ui.navigate.to('/admin')).classes('w-full').props(
                'flat')
            ui.button('用户管理', icon='people', on_click=lambda: ui.navigate.to('/admin/users')).classes(
                'w-full').props('flat')
            ui.button('演职人员', icon='badge').classes('w-full shadow-sm bg-white text-primary').props('flat')
            ui.button('电影管理', icon='movie', on_click=lambda: ui.navigate.to('/admin/movies')).classes(
                'w-full').props('flat')


    # --- 3. 主内容区 ---
    with ui.column().classes('w-full q-pa-md items-center'):
        # 标题栏
        with ui.row().classes('w-full justify-between items-center q-mb-lg'):
            ui.label('🎭 演职人员管理').classes('text-h4 font-bold')
            ui.button('刷新列表', icon='refresh', on_click=lambda: load_data()).props('unelevated rounded color=primary')

        # 表格区域
        with ui.card().classes('w-full shadow-lg q-pa-none'):
            # 工具栏
            with ui.row().classes('q-pa-sm gap-2'):
                ui.button('新增人员', icon='person_add', on_click=lambda: open_edit_dialog(None)).props(
                    'unelevated color=green')
                ui.button('编辑', icon='edit', on_click=lambda: edit_selected()).props('flat color=blue')
                ui.button('删除', icon='delete', on_click=lambda: delete_selected()).props('flat color=red')

            # 表格定义
            grid = ui.aggrid({
                'columnDefs': [
                    {'headerName': '编号', 'field': 'nconst', 'checkboxSelection': True},
                    {'headerName': '姓名', 'field': 'primaryName'},
                    {'headerName': '出生年', 'field': 'birthYear'},
                    {'headerName': '去世年', 'field': 'deathYear'},
                    {'headerName': '职业', 'field': 'primaryProfession'},
                    {'headerName': '代表作', 'field': 'knownForTitles'},
                ],
                'rowData': [],
                'rowSelection': 'single',
                'pagination': True,
            }).classes('w-full shadow-lg').style('height: 70vh')

            # 分页控件
            with ui.row().classes('w-full justify-center items-center q-pa-sm bg-gray-50 border-t'):
                ui.button(icon='chevron_left', on_click=lambda: change_page(-1)).props('flat')
                pagination_label = ui.label('第 1 页').classes('font-bold text-blue')
                ui.button(icon='chevron_right', on_click=lambda: change_page(1)).props('flat')

    # --- 4. 逻辑处理 ---
    async def load_data():
        try:
            total = await person_service.get_person_count() or 0
            total_pages = math.ceil(total / page_state['page_size']) if total > 0 else 1
            if page_state['current_page'] > total_pages: page_state['current_page'] = total_pages

            people = await person_service.get_people_paginated(page_state['current_page'], page_state['page_size'])

            rows = [{
                'nconst': p.nconst,
                'primaryName': p.primaryName,
                'birthYear': p.birthYear,
                'deathYear': p.deathYear,
                'primaryProfession': p.primaryProfession,
                'knownForTitles': p.knownForTitles
            } for p in people]

            print(rows)
            await grid.run_grid_method('setGridOption', 'rowData', rows)
            pagination_label.text = f"第 {page_state['current_page']} 页 / 共 {total_pages} 页 (总数: {total})"
            ui.notify('数据已更新', type='positive', timeout=1000)
        except Exception as e:
            ui.notify(f'加载失败: {e}', type='negative')

    async def change_page(delta):
        page_state['current_page'] += delta
        if page_state['current_page'] < 1: page_state['current_page'] = 1
        await load_data()

    # --- 5. 弹窗功能 ---
    def open_edit_dialog(data=None):
        is_edit = data is not None
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label('编辑人员' if is_edit else '新增人员').classes('text-h6 font-bold')

            nconst_input = ui.input('编号 (如 nm0000001)', value=data['nconst'] if is_edit else '').classes('w-full')
            if is_edit: nconst_input.disable()  # 编辑时不可改ID

            name_input = ui.input('姓名', value=data['primaryName'] if is_edit else '').classes('w-full')
            birth_input = ui.number('出生年份', value=data['birthYear'] if is_edit else None, format='%.0f').classes(
                'w-full')
            death_input = ui.number('去世年份', value=data['deathYear'] if is_edit else None, format='%.0f').classes(
                'w-full')
            prof_input = ui.input('主要职业', value=data['primaryProfession'] if is_edit else '').classes('w-full')
            titles_input = ui.input('代表作 (逗号分隔)', value=data['knownForTitles'] if is_edit else '').classes(
                'w-full')

            async def save():
                if not nconst_input.value or not name_input.value:
                    ui.notify('编号和姓名必填', type='warning')
                    return

                kwargs = {
                    'nconst': nconst_input.value,
                    'name': name_input.value,
                    'birth_year': int(birth_input.value) if birth_input.value else None,
                    'death_year': int(death_input.value) if death_input.value else None,
                    'profession': prof_input.value,
                    'titles': titles_input.value
                }

                if is_edit:
                    success, msg = await person_service.update_person(**kwargs)
                else:
                    success, msg = await person_service.create_person(**kwargs)

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
            ui.notify('请先选择一行', type='warning')
            return
        open_edit_dialog(rows[0])

    async def delete_selected():
        rows = await grid.get_selected_rows()
        if not rows: return

        async def confirm():
            success, msg = await person_service.delete_person(rows[0]['nconst'])
            if success:
                ui.notify(msg, type='positive')
                await load_data()
            else:
                ui.notify(msg, type='negative')

        with ui.dialog() as dialog, ui.card():
            ui.label(f"确认删除 {rows[0]['primaryName']}?").classes('font-bold')
            with ui.row().classes('w-full justify-end'):
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('删除', color='red', on_click=lambda: [confirm(), dialog.close()])
        dialog.open()

    # 初始加载
    ui.timer(0.1, load_data, once=True)