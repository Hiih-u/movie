# pages/movie_detail.py
from nicegui import ui
from services import tmdb_service


async def open_movie_detail_dialog(tconst: str, on_close=None):
    """
    打开电影详情弹窗 (Modal)
    """
    # 创建一个宽大的 Dialog，内部是一个 Card
    # w-[90vw] max-w-5xl: 保证在大屏上够宽，但不过宽
    # h-[85vh]: 保证高度，内部滚动
    with ui.dialog() as dialog, ui.card().classes(
            'w-[90vw] max-w-5xl h-[85vh] p-0 gap-0 overflow-hidden shadow-2xl bg-slate-50'):

        # --- 1. 加载状态覆盖层 (骨架屏) ---
        # 使用 absolute covering 覆盖整个卡片，数据加载完后隐藏
        with ui.column().classes('absolute inset-0 z-50 bg-white items-center justify-center') as loading_overlay:
            ui.spinner('dots', size='3rem', color='primary')
            ui.label('正在从 TMDB 获取资料...').classes('text-slate-500 mt-2 animate-pulse')

        # --- 2. 关闭按钮 ---
        # 放在最顶层，白色带半透明背景，确保在深色海报上也能看见
        ui.button(icon='close', on_click=dialog.close) \
            .props('flat round dense text-color=white') \
            .classes('absolute top-4 right-4 z-40 bg-black/30 hover:bg-black/50 backdrop-blur-sm transition-all')

        if on_close:
            dialog.on('close', on_close)

        dialog.open()

        # --- 3. 异步获取数据 ---
        # 调用 tmdb_service (如果有缓存直接读库，没有则调API)
        info = await tmdb_service.get_movie_info(tconst)

        # 隐藏加载层
        loading_overlay.set_visibility(False)

        if not info:
            with ui.column().classes('w-full h-full items-center justify-center'):
                ui.icon('sentiment_dissatisfied', size='4rem', color='grey')
                ui.label('抱歉，未找到该影片的详细信息').classes('text-lg text-slate-400 mt-2')
            return

        # --- 4. 渲染内容 (内部滚动区域) ---
        with ui.scroll_area().classes('w-full h-full'):

            # (A) 顶部大背景图区域 (Header)
            # 如果没有 backdrop，用占位图
            backdrop_url = info['backdrop_url'] or 'https://via.placeholder.com/1920x600?text=No+Backdrop'

            with ui.row().classes('w-full h-[40vh] relative'):
                ui.image(backdrop_url).classes('w-full h-full object-cover')

                # 渐变遮罩：底部黑色渐变，让白色文字清晰
                ui.element('div').classes(
                    'absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/30 to-transparent')

                # 标题信息 (悬浮在背景图左下角)
                with ui.column().classes('absolute bottom-6 left-6 md:left-10 gap-2 max-w-3xl pr-16'):
                    # 标题
                    ui.label(info['title']).classes(
                        'text-3xl md:text-5xl font-black text-white leading-tight drop-shadow-lg')

                    # 元数据行
                    with ui.row().classes('items-center gap-3 text-white/90'):
                        # 年份胶囊
                        ui.label(str(info['year'])).classes(
                            'px-2 py-0.5 bg-white/20 backdrop-blur-md rounded text-sm font-bold border border-white/10')
                        # 评分
                        if info['rating'] and info['rating'] != 'N/A':
                            with ui.row().classes('items-center gap-1'):
                                ui.icon('star', color='orange').classes('text-lg')
                                ui.label(f"{info['rating']}").classes('text-lg font-bold text-orange-400')
                        # 类型
                        ui.label(str(info['genres']).replace(',', ' · ')).classes('text-sm opacity-80')

            # (B) 下半部分：详情内容
            with ui.row().classes('w-full p-6 md:p-10 gap-8 items-start relative'):
                # 左侧：竖版海报 (负 margin 向上重叠背景图，营造层次感)
                # 仅在平板/桌面端显示，移动端隐藏(因为屏幕太窄)
                poster_url = info['poster_url'] or 'https://via.placeholder.com/300x450?text=No+Poster'
                with ui.card().classes(
                        'hidden md:block w-[220px] shrink-0 -mt-24 z-10 p-1 bg-white shadow-2xl rounded-lg'):
                    ui.image(poster_url).classes('w-full aspect-[2/3] object-cover rounded')

                # 右侧：文本介绍
                with ui.column().classes('flex-1 gap-6'):
                    # 剧情简介
                    with ui.column().classes('gap-2 w-full'):
                        with ui.row().classes('items-center gap-2 mb-1'):
                            ui.icon('format_quote', color='primary').classes('text-2xl opacity-50')
                            ui.label('剧情简介').classes('text-xl font-bold text-slate-800')

                        overview_text = info['overview'] if info['overview'] else "暂无剧情简介。"
                        ui.label(overview_text).classes('text-slate-600 leading-relaxed text-justify text-base')

                    ui.separator()

                    # 底部信息占位 (演职员表等)
                    with ui.row().classes('gap-8 w-full'):
                        directors_str = " / ".join(info.get('directors', [])) or "未知"
                        writers_str = " / ".join(info.get('writers', [])) or "未知"

                        _info_item('导演', directors_str)
                        _info_item('编剧', writers_str)
                        _info_item('语言', 'English / Chinese')


# 辅助小组件
def _info_item(label, value):
    with ui.column().classes('gap-1'):
        ui.label(label).classes('text-xs font-bold text-slate-400 uppercase tracking-wider')
        ui.label(value).classes('text-sm text-slate-700 font-medium')