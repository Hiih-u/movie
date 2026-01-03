# pages/user_layout.py
from nicegui import ui, app


def render_header_and_drawer(current_page_key: str):
    """
    渲染个人中心的头部和侧边栏
    :param current_page_key: 当前页面标识 (用于高亮侧边栏菜单)
    """
    username = app.storage.user.get('username', 'User')

    # --- 1. 顶部 Header ---
    with ui.header().classes('bg-white text-slate-900 shadow-sm border-b items-center h-16 px-6'):
        with ui.row().classes('items-center gap-2 cursor-pointer').on('click', lambda: ui.navigate.to('/')):
            ui.icon('arrow_back', color='primary').classes('text-2xl')
            ui.label('返回首页').classes('text-lg font-bold text-primary')

        ui.space()

        # 右侧用户信息
        with ui.row().classes('items-center gap-2'):
            ui.avatar(username[0].upper(), color='primary', text_color='white').props('size=sm')
            ui.label(username).classes('font-bold text-slate-700')

    # --- 2. 左侧 Sidebar ---
    with ui.left_drawer(value=True).classes('bg-slate-50 border-r text-slate-700') \
            .props('width=240 breakpoint=700') as drawer:
        with ui.column().classes('w-full q-pa-md gap-1'):
            ui.label('个人中心').classes('text-xs font-bold text-slate-400 q-mb-sm q-ml-sm')

            # 封装菜单按钮样式
            def menu_item(label, icon, target_url, key):
                # 判断是否高亮
                is_active = (key == current_page_key)
                bg_color = 'bg-blue-100 text-primary' if is_active else 'hover:bg-slate-200'

                ui.button(label, icon=icon, on_click=lambda: ui.navigate.to(target_url)) \
                    .props(f'flat align=left {"" if is_active else "text-slate-600"}') \
                    .classes(f'w-full rounded-md {bg_color} transition-colors')

            # 菜单项定义
            menu_item('我的收藏', 'favorite', '/user/favorites', 'favorites')
            menu_item('我的评分', 'star', '/user/ratings', 'ratings')
            # 你可以在这里加更多，比如 menu_item('个人资料', 'person', '/user/profile', 'profile')

            ui.separator().classes('my-2')

            ui.button('退出登录', icon='logout', on_click=lambda: [app.storage.user.clear(), ui.navigate.to('/login')]) \
                .props('flat align=left color=grey').classes('w-full')