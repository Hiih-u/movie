from nicegui import ui, app
from services import user_service
import math  # 用于计算总页数


def create_user_page():
    # --- 1. 状态管理 ---
    # 分页状态：默认第1页，每页10条
    page_state = {
        'current_page': 1,
        'page_size': 10
    }

    # --- 2. 侧边栏 (保持原样) ---
    with ui.left_drawer(value=True).classes('bg-blue-grey-1 text-slate-900'):
        ui.label('IMDB 后台管理').classes('text-h6 q-pa-md font-bold text-primary')
        ui.separator()
        with ui.column().classes('w-full q-pa-sm'):
            ui.button('仪表盘', icon='dashboard', on_click=lambda: ui.navigate.to('/admin')).classes('w-full').props(
                'flat')
            ui.button('用户管理', icon='people').classes('w-full shadow-sm bg-white text-primary').props('flat')
            ui.button('演职人员', icon='badge', on_click=lambda: ui.navigate.to('/admin/people')).classes(
                'w-full').props('flat')
            ui.button('电影管理', icon='movie', on_click=lambda: ui.navigate.to('/admin/movies')).classes(
                'w-full').props('flat')
            ui.button('评分管理', icon='star', on_click=lambda: ui.navigate.to('/admin/ratings')).classes(
                'w-full').props('flat')
            ui.button('剧组管理', icon='star', on_click=lambda: ui.navigate.to('/admin/crew')).classes(
                'w-full').props('flat')
            ui.button('剧集管理', icon='subscriptions', on_click=lambda: ui.navigate.to('/admin/episodes')).classes(
                'w-full').props('flat')

    # --- 3. 主内容区 ---
    with ui.column().classes('w-full q-pa-md items-center'):

        # 3.1 标题栏
        with ui.row().classes('w-full justify-between items-center q-mb-lg q-mt-md'):
            ui.label('👥 系统用户管理').classes('text-h4 font-bold')
            # 点击刷新，重置到当前页加载
            ui.button('刷新列表', icon='refresh', on_click=lambda: load_users()).props(
                'unelevated rounded color=primary')

        # 3.2 表格卡片容器
        with ui.card().classes('w-full shadow-lg q-pa-none'):
            # (1) 顶部工具栏
            with ui.row().classes('q-pa-sm gap-2'):
                ui.button('新增管理员', icon='person_add', on_click=lambda: open_add_dialog()).props(
                    'unelevated color=green')
                ui.button('修改密码', icon='lock_reset', on_click=lambda: open_pwd_dialog()).props('flat color=orange')
                ui.button('删除用户', icon='person_remove', on_click=lambda: delete_selected()).props('flat color=red')

            # (2) AgGrid 表格配置
            # 注意：pagination=False，因为我们手动接管分页
            grid = ui.aggrid({
                'columnDefs': [
                    {'headerName': 'ID', 'field': 'id', 'checkboxSelection': True},  # 对应 Integer 类型
                    {'headerName': '用户名', 'field': 'username'},  # 对应 String 类型
                ],
                'rowData': [],
                'rowSelection': 'single',
                'pagination': False,
            }).classes('w-full shadow-lg').style('height: 70vh')

            # (3) 底部翻页控制条
            with ui.row().classes('w-full justify-center items-center q-pa-sm gap-4 bg-gray-50 border-t'):
                # 翻页函数
                def change_page(delta):
                    new_page = page_state['current_page'] + delta
                    if new_page < 1:
                        return
                    page_state['current_page'] = new_page
                    load_users()

                btn_prev = ui.button('上一页', on_click=lambda: change_page(-1)).props('flat dense icon=chevron_left')
                pagination_label = ui.label('正在加载...').classes('text-gray-700 font-medium')
                btn_next = ui.button('下一页', on_click=lambda: change_page(1)).props(
                    'flat dense icon-right=chevron_right')

    # --- 4. 逻辑处理函数 ---

    async def load_users():
        """加载数据核心逻辑"""
        try:
            # 1. 获取总记录数
            total_count = await user_service.get_user_count()

            # 2. 计算总页数
            # 如果 total_count 是 0，total_pages 至少应为 1
            total_pages = math.ceil(total_count / page_state['page_size']) if total_count > 0 else 1

            # 3. 页码越界修正 (比如删除了最后一页的数据)
            if page_state['current_page'] > total_pages:
                page_state['current_page'] = total_pages

            print(f"加载第 {page_state['current_page']} 页，共 {total_pages} 页")

            # 4. 获取分页数据
            users = await user_service.get_users_paginated(
                page_state['current_page'],
                page_state['page_size']
            )

            # 5. 格式化数据
            rows = [
                {'id': u.id, 'username': str(u.username)}
                for u in users
            ]

            # 6. 更新表格
            await grid.run_grid_method('setGridOption', 'rowData', rows)


            # 7. 更新底部状态
            pagination_label.text = f"第 {page_state['current_page']} 页 / 共 {total_pages} 页 (总数: {total_count})"

            # 控制按钮状态
            if page_state['current_page'] <= 1:
                btn_prev.disable()
            else:
                btn_prev.enable()

            if page_state['current_page'] >= total_pages:
                btn_next.disable()
            else:
                btn_next.enable()

            ui.notify('列表已更新', type='positive', timeout=1000)

        except Exception as e:
            print(f"加载出错: {e}")
            ui.notify(f'加载失败: {e}', type='negative')

    # --- 功能函数 ---

    def open_add_dialog():
        """打开新增窗口"""
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label('新增管理员').classes('text-h6 font-bold')
            username = ui.input('用户名').classes('w-full')
            password = ui.input('密码', password=True, password_toggle_button=True).classes('w-full')

            async def save():
                if not username.value or not password.value:
                    ui.notify('请填写完整', type='warning')
                    return
                # 调用后端
                success, msg = await user_service.create_user(username.value, password.value)
                if success:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    await load_users()  # 刷新列表
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end q-mt-md'):
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('创建', on_click=save).props('unelevated color=green')
        dialog.open()

    async def delete_selected():
        """删除选中用户"""
        rows = await grid.get_selected_rows()
        if not rows:
            ui.notify('请先选择一个用户', type='warning')
            return

        user_data = rows[0]
        # 安全检查：防止自删
        current_user_name = app.storage.user.get('username', '')
        if user_data['username'] == current_user_name:
            ui.notify('操作禁止：不能删除当前登录的账户！', type='negative')
            return

        with ui.dialog() as dialog, ui.card():
            ui.label('⚠️ 危险操作').classes('text-red font-bold text-lg')
            ui.label(f'确定要删除用户 "{user_data["username"]}" 吗？').classes('text-gray-600')

            async def confirm():
                success, msg = await user_service.delete_user(user_data['id'])
                if success:
                    ui.notify(msg, type='positive')
                    dialog.close()
                    # 删除后重新加载当前页
                    await load_users()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end'):
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('确认删除', color='red', on_click=confirm)
        dialog.open()

    async def open_pwd_dialog():
        """打开修改密码窗口"""
        rows = await grid.get_selected_rows()
        if not rows:
            ui.notify('请先选择一个用户', type='warning')
            return
        user_data = rows[0]

        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label(f'重置密码: {user_data["username"]}').classes('text-h6')
            new_pwd = ui.input('新密码', password=True, password_toggle_button=True).classes('w-full')

            async def save_pwd():
                if not new_pwd.value:
                    ui.notify('密码不能为空', type='warning')
                    return
                success, msg = await user_service.change_password(user_data['id'], new_pwd.value)
                if success:
                    ui.notify(msg, type='positive')
                    dialog.close()
                else:
                    ui.notify(msg, type='negative')

            with ui.row().classes('w-full justify-end q-mt-md'):
                ui.button('取消', on_click=dialog.close).props('flat')
                ui.button('保存', on_click=save_pwd).props('unelevated color=orange')
        dialog.open()

    # --- 5. 初始加载 ---
    # 稍微延迟以确保前端 UI 准备就绪
    ui.timer(0.1, load_users, once=True)