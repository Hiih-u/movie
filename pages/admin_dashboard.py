from nicegui import ui, app
import plotly.graph_objects as go
from services import analysis_service


def create_admin_page():
    # 1. 侧边栏 (需同步更新)
    with ui.left_drawer(value=True).classes('bg-blue-grey-1 text-slate-900'):
        ui.label('IMDB 后台管理').classes('text-h6 q-pa-md font-bold text-primary')
        ui.separator()
        with ui.column().classes('w-full q-pa-sm'):
            ui.button('仪表盘', icon='dashboard').classes('w-full shadow-sm bg-white text-primary').props('flat')
            ui.button('用户管理', icon='people', on_click=lambda: ui.navigate.to('/admin/users')).classes(
                'w-full').props('flat')
            ui.button('演职人员', icon='badge', on_click=lambda: ui.navigate.to('/admin/people')).classes(
                'w-full').props('flat')
            ui.button('电影管理', icon='movie', on_click=lambda: ui.navigate.to('/admin/movies')).classes(
                'w-full').props('flat')

    # 2. 主内容区 (纯可视化)
    with ui.column().classes('w-full q-pa-md items-center'):
        # 顶部标题栏
        with ui.row().classes('w-full justify-between items-center q-mb-lg q-mt-md'):
            ui.label('📊 电影大数据分析终端').classes('text-h4 font-bold')
            ui.button('刷新数据', icon='refresh', on_click=lambda: load_stats()).props(
                'unelevated rounded color=primary')

        # --- 统计指标卡片 ---
        with ui.row().classes('w-full q-mb-md'):
            with ui.card().classes('col q-pa-sm items-center border'):
                ui.label('总电影条目').classes('text-grey-7 text-xs')
                total_label = ui.label('Loading...').classes('text-h5 font-bold')
            with ui.card().classes('col q-pa-sm items-center border'):
                ui.label('全网平均分').classes('text-grey-7 text-xs')
                avg_label = ui.label('Loading...').classes('text-h5 font-bold text-orange')

        # --- 图表区域 ---
        with ui.row().classes('w-full gap-4'):
            chart_container_1 = ui.card().classes('flex-1 h-80 shadow-md border-t-4 border-blue-400')
            chart_container_2 = ui.card().classes('flex-1 h-80 shadow-md border-t-4 border-red-400')

        # --- 异步加载数据 ---
        async def load_stats():
            try:
                # 1. 统计概览
                count, avg = await analysis_service.get_stats_summary()
                total_label.text = f"{count:,}"
                avg_label.text = f"{avg}"

                # 2. Top 10 图表
                top_movies = await analysis_service.get_top_movies()
                chart_container_1.clear()
                with chart_container_1:
                    ui.label('🏆 评分最高榜单 (Top 10)').classes('font-bold q-pa-sm')
                    if top_movies:
                        fig1 = go.Figure(data=[
                            go.Bar(x=[str(m[0])[:15] for m in top_movies], y=[m[1] for m in top_movies],
                                   marker_color='#3b82f6')])
                        fig1.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=220)
                        ui.plotly(fig1).classes('w-full')

                # 3. 年度趋势图表
                year_stats = await analysis_service.get_year_stats()
                chart_container_2.clear()
                with chart_container_2:
                    ui.label('📈 电影产量年度趋势').classes('font-bold q-pa-sm')
                    if year_stats:
                        sorted_stats = sorted(year_stats, key=lambda x: x[0])
                        fig2 = go.Figure(data=[
                            go.Scatter(x=[str(y[0]) for y in sorted_stats], y=[y[1] for y in sorted_stats],
                                       mode='lines+markers', line=dict(color='#ef4444', width=2))])
                        fig2.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=220)
                        ui.plotly(fig2).classes('w-full')

                ui.notify('仪表盘已更新', type='positive')

            except Exception as e:
                ui.notify(f'加载失败: {e}', type='negative')

        ui.timer(0.1, load_stats, once=True)