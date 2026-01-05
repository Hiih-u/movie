from nicegui import ui, app
import plotly.graph_objects as go
from services import analysis_service, recommendation_service


def create_admin_page():
    # 1. 侧边栏 (需同步更新)
    with ui.left_drawer(value=True).classes('bg-blue-grey-1 text-slate-900') \
            .props('width=220 breakpoint=700') as drawer:
        ui.button('回首页', icon='home', on_click=lambda: ui.navigate.to('/')) \
            .classes('text-h6 font-bold text-primary w-full') \
            .props('flat align=left no-caps q-pa-md')
        ui.separator()
        with ui.column().classes('w-full q-pa-sm'):
            ui.button('仪表盘', icon='dashboard').classes('w-full shadow-sm bg-white text-primary').props('flat')
            ui.button('用户管理', icon='people', on_click=lambda: ui.navigate.to('/admin/users')).classes(
                'w-full').props('flat')
            ui.button('演职人员', icon='badge', on_click=lambda: ui.navigate.to('/admin/people')).classes(
                'w-full').props('flat')
            ui.button('影视管理', icon='movie', on_click=lambda: ui.navigate.to('/admin/movies')).classes(
                'w-full').props('flat')
            ui.button('评分管理', icon='star', on_click=lambda: ui.navigate.to('/admin/ratings')).classes(
                'w-full').props('flat')
            ui.button('剧组管理', icon='star', on_click=lambda: ui.navigate.to('/admin/crew')).classes(
                'w-full').props('flat')
            ui.button('剧集管理', icon='subscriptions', on_click=lambda: ui.navigate.to('/admin/episodes')).classes(
                'w-full').props('flat')

    # 2. 主内容区 (纯可视化)
    with ui.column().classes('w-full q-pa-md items-center'):
        # 顶部标题栏
        with ui.row().classes('w-full justify-between items-center q-mb-lg q-mt-md'):
            ui.label('📊 影视大数据分析终端').classes('text-h4 font-bold')
            ui.button('刷新数据', icon='refresh', on_click=lambda: load_stats()).props(
                'unelevated rounded color=primary')

        # --- 统计指标卡片 ---
        with ui.row().classes('w-full q-mb-md'):
            with ui.card().classes('col q-pa-sm items-center border'):
                ui.label('总影视条目').classes('text-grey-7 text-xs')
                total_label = ui.label('Loading...').classes('text-h5 font-bold')
            with ui.card().classes('col q-pa-sm items-center border'):
                ui.label('全网平均分').classes('text-grey-7 text-xs')
                avg_label = ui.label('Loading...').classes('text-h5 font-bold text-orange')

        with ui.card().classes('w-full q-mb-md shadow-sm border-t-4 border-purple-500'):
            with ui.row().classes('w-full items-center justify-between'):
                with ui.column().classes('gap-0'):
                    ui.label('🧠 协同过滤推荐引擎').classes('text-h6 font-bold')
                    # 显示模型当前状态
                    model_status_label = ui.label('正在检测模型状态...').classes('text-xs text-grey-6')

                # 训练按钮
                train_btn = ui.button('立即重新训练', icon='psychology', on_click=lambda: run_training()) \
                    .props('unelevated color=purple')

            # 训练逻辑
            async def run_training():
                train_btn.disable()
                train_btn.text = '训练中(约需几秒)...'
                model_status_label.text = '⏳ 正在计算相似度矩阵...'

                # 调用后台服务
                success, msg = await recommendation_service.train_model()

                if success:
                    ui.notify(msg, type='positive')
                    refresh_status()  # 刷新显示的文字
                else:
                    ui.notify(msg, type='negative')
                    model_status_label.text = '❌ 上次训练失败'

                train_btn.text = '立即重新训练'
                train_btn.enable()

            # 刷新状态文字的辅助函数
            def refresh_status():
                if recommendation_service._similarity_df is not None:
                    model_status_label.text = f"✅ 模型已加载 | 算法: Item-Based CF"
                    model_status_label.classes('text-green-600', remove='text-grey-6 text-red-600')
                else:
                    model_status_label.text = "⚠️ 模型未加载 (当前使用热门榜单降级策略)"
                    model_status_label.classes('text-red-600', remove='text-grey-6 text-green-600')

            # 进入页面时自动检测一次
            refresh_status()

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
                    ui.label('📈 影视产量年度趋势').classes('font-bold q-pa-sm')
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