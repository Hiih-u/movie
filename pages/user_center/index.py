from nicegui import ui, app
# 导入我们拆分出去的子页面
from pages.user_center import favorites_view, ratings_view


def create_page():
    # 1. 权限与用户信息
    user_id = app.storage.user.get('user_id')
    username = app.storage.user.get('username', '用户')

    if not app.storage.user.get('authenticated', False) or not user_id:
        ui.notify('请先登录', type='warning')
        ui.navigate.to('/login')
        return

    # 2. 页面 Header
    with ui.header().classes('bg-white text-slate-900 shadow-sm border-b items-center h-16 px-6'):
        with ui.row().classes('items-center gap-2 cursor-pointer').on('click', lambda: ui.navigate.to('/')):
            ui.icon('arrow_back', color='primary').classes('text-2xl')
            ui.label('返回首页').classes('text-lg font-bold text-primary')
        ui.space()
        ui.label(f'{username} 的个人中心').classes('text-lg font-bold text-slate-700')

    # 3. 主内容容器 (核心：所有子页面都渲染在这里)
    # 我们把它定义在外面，方便传递给侧边栏按钮的点击事件
    content_container = ui.column().classes('w-full p-6 min-h-screen items-center bg-white')

    # 4. 侧边栏 (控制 content_container 显示什么)
    with ui.left_drawer(value=True).classes('bg-slate-50 border-r') as drawer:
        with ui.column().classes('w-full q-pa-md gap-2'):
            ui.label('功能菜单').classes('text-xs font-bold text-slate-400 q-mb-sm')

            # 封装一个生成菜单按钮的辅助函数
            def menu_item(label, icon, view_module):
                # 点击时，调用 view_module.show，并传入容器和 ID
                ui.button(label, icon=icon,
                          on_click=lambda: view_module.show(content_container, user_id)) \
                    .props('flat align=left').classes('w-full text-slate-700')

            menu_item('我的收藏', 'favorite', favorites_view)
            menu_item('我的评分', 'star', ratings_view)

            ui.separator().classes('my-2')
            ui.button('退出登录', icon='logout', on_click=lambda: [app.storage.user.clear(), ui.navigate.to('/login')]) \
                .props('flat align=left color=grey').classes('w-full')

    # 5. 默认显示收藏页
    # 使用 timer(0) 确保页面加载完成后立即执行
    ui.timer(0, lambda: favorites_view.show(content_container, user_id), once=True)