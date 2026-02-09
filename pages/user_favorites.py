# pages/user_favorites.py
from nicegui import ui, app
from services import interaction_service
from pages import user_layout, movie_detail  # 【修改 1】引入 movie_detail
import math

BG_COLORS = ['bg-blue-600', 'bg-rose-600', 'bg-emerald-600', 'bg-violet-600', 'bg-amber-600', 'bg-cyan-600']
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w200"  # 【修改 2】定义图片路径前缀


def create_page():
    # 1. 渲染公共布局 (高亮 'favorites')
    user_layout.render_header_and_drawer('favorites')

    # 2. 页面主体内容
    user_id = app.storage.user.get('user_id')
    page_state = {
        'current_page': 1,
        'page_size': 12,
        'total_pages': 1
    }

    content_div = ui.column().classes('w-full p-6 items-center')

    async def load_data():
        content_div.clear()

        # 获取总数并计算页数
        total_count = await interaction_service.get_my_favorites_count(user_id)
        total_pages = math.ceil(total_count / page_state['page_size']) if total_count > 0 else 1
        page_state['total_pages'] = total_pages

        if page_state['current_page'] > total_pages:
            page_state['current_page'] = 1

        movies = await interaction_service.get_my_favorites_paginated(
            user_id, page_state['current_page'], page_state['page_size']
        )

        with content_div:
            # 标题
            ui.label('❤️ 我的收藏夹').classes('text-2xl font-bold text-rose-500 mb-6 self-start')

            if not movies:
                with ui.column().classes('w-full items-center py-20'):
                    ui.icon('favorite_border', size='4em', color='grey-4')
                    ui.label('暂无收藏数据').classes('text-slate-400 text-lg mt-4')
                return

            # 网格列表
            with ui.grid(columns=None).classes('w-full gap-6 grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6'):
                for index, m in enumerate(movies):
                    bg = BG_COLORS[index % len(BG_COLORS)]

                    # 【修改 3】卡片升级：增加点击事件、鼠标手势、溢出隐藏
                    with ui.card().classes(
                            'w-full h-[340px] p-0 gap-0 shadow hover:shadow-xl transition-all relative cursor-pointer group overflow-hidden') \
                            .on('click', lambda _, mid=m.tconst: movie_detail.open_movie_detail_dialog(mid)):

                        # 【修改 4】删除按钮：使用 click.stop 阻止冒泡
                        with ui.button(icon='delete', color='white') as del_btn:
                            del_btn.props('flat round dense') \
                                .classes(
                                'absolute top-2 right-2 z-20 bg-black/30 backdrop-blur-md hover:bg-red-500 transition-colors') \
                                .on('click.stop', lambda _, mid=m.tconst: remove_fav(mid))

                        # 【修改 5】封面区域：支持显示图片
                        with ui.column().classes(
                                f'w-full h-[75%] {bg} items-center justify-center relative overflow-hidden'):
                            # 如果有海报路径，显示图片
                            if hasattr(m, 'poster_path') and m.poster_path:
                                ui.image(f"{IMAGE_BASE_URL}{m.poster_path}") \
                                    .classes(
                                    'w-full h-full object-cover transition-transform duration-700 group-hover:scale-110')
                            # 否则显示首字母兜底
                            else:
                                ui.label(m.primaryTitle[:1]).classes(
                                    'text-6xl text-white opacity-30 font-black select-none')
                                # 显示年份标签
                                if hasattr(m, 'startYear') and m.startYear:
                                    ui.label(str(m.startYear)).classes(
                                        'absolute bottom-2 left-2 text-xs bg-black/20 text-white px-2 rounded')

                        # 信息区域
                        with ui.column().classes('w-full h-[25%] p-3 justify-between bg-white'):
                            ui.label(m.primaryTitle).classes(
                                'font-bold text-sm leading-tight line-clamp-2 text-slate-700 group-hover:text-primary transition-colors')

                            with ui.row().classes('w-full justify-between items-center'):
                                # 显示类型
                                genres = (m.genres or '').split(',')[0]
                                ui.label(genres).classes('text-xs text-slate-400')
                                # 显示评分
                                ui.label(f'★ {m.averageRating or "N/A"}').classes('text-xs font-bold text-orange-500')

            # 简易翻页
            with ui.row().classes('mt-8 justify-center items-center gap-4'):
                ui.button('上一页', on_click=lambda: change_page(-1)) \
                    .props('flat dense icon=chevron_left') \
                    .bind_visibility_from(page_state, 'current_page', backward=lambda p: p > 1)

                ui.label(f"第 {page_state['current_page']} 页 / 共 {total_pages} 页") \
                    .classes('text-slate-500 font-medium')

                ui.button('下一页', on_click=lambda: change_page(1)) \
                    .props('flat dense icon-right=chevron_right') \
                    .bind_visibility_from(page_state, 'current_page', backward=lambda p: p < total_pages)

    async def change_page(delta):
        new_page = page_state['current_page'] + delta
        if new_page < 1 or new_page > page_state['total_pages']:
            return
        page_state['current_page'] = new_page
        await load_data()

    async def remove_fav(tconst):
        # 1. 后台删除
        await interaction_service.toggle_favorite(user_id, tconst)
        # 2. 前端提示
        ui.notify('已从收藏移除', type='info')
        # 3. 刷新列表 (删除操作必须刷新，因为该条目不应再显示)
        await load_data()

    ui.timer(0, load_data, once=True)