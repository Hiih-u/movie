from nicegui import ui
import plotly.graph_objects as go
# 引入后端服务模块
from services import movie_service

# --- 页面状态管理 ---
page_state = {'current_page': 1, 'page_size': 100}


# --- 页面布局 ---
def create_admin_page():
    # 1. 侧边栏
    with ui.left_drawer(value=True).classes('bg-blue-grey-1 text-slate-900') as drawer:
        ui.label('IMDB 后台管理').classes('text-h6 q-pa-md font-bold text-primary')
        ui.separator()
        with ui.column().classes('w-full q-pa-sm'):
            ui.button('仪表盘', icon='dashboard').classes('w-full shadow-sm').props('flat')
            ui.button('算法管理', icon='auto_awesome').classes('w-full').props('flat')
            ui.button('系统日志', icon='assignment').classes('w-full').props('flat')

    # 2. 主内容区
    with ui.column().classes('w-full q-pa-md items-center'):
        # 顶部标题栏
        with ui.row().classes('w-full justify-between items-center q-mb-lg'):
            ui.label('📊 电影大数据分析终端').classes('text-h4 font-bold')
            ui.button('同步数据库', icon='refresh', on_click=lambda: load_dashboard_data()).props(
                'unelevated rounded color=primary')

        # --- 统计指标卡片 ---
        with ui.row().classes('w-full q-mb-md'):
            with ui.card().classes('col q-pa-sm items-center border'):
                ui.label('总电影条目').classes('text-grey-7 text-xs')
                total_label = ui.label('0').classes('text-h5 font-bold')
            with ui.card().classes('col q-pa-sm items-center border'):
                ui.label('全网平均分').classes('text-grey-7 text-xs')
                avg_label = ui.label('0.0').classes('text-h5 font-bold text-orange')

        # --- 第一部分：图表区域 ---
        with ui.row().classes('w-full gap-4'):
            chart_container_1 = ui.card().classes('flex-1 h-80 shadow-md border-t-4 border-blue-400')
            chart_container_2 = ui.card().classes('flex-1 h-80 shadow-md border-t-4 border-red-400')

        # --- 第二部分：数据管理表格 ---
        ui.label('📋 电影资源管理').classes('text-h5 q-mt-xl q-mb-sm self-start font-bold')

        with ui.card().classes('w-full q-pa-none shadow-lg'):
            with ui.row().classes('q-pa-sm gap-2'):
                ui.button('编辑', icon='edit', on_click=lambda: edit_selected()).props('flat color=blue')
                ui.button('下架电影', icon='delete_forever', on_click=lambda: delete_selected()).props('flat color=red')

            grid = ui.aggrid({
                'columnDefs': [
                    {'headerName': '编号', 'field': 'tconst', 'checkboxSelection': True},
                    {'headerName': '电影名称', 'field': 'primaryTitle'},
                    {'headerName': '上映年份', 'field': 'startYear'},
                    {'headerName': '类型标签', 'field': 'genres'},
                ],
                'rowData': [],
                'rowSelection': 'single',
                'pagination': True,
            }).classes('h-96 w-full shadow-lg')

            with ui.row().classes('w-full justify-center items-center q-pa-sm bg-grey-1'):
                ui.button(icon='chevron_left', on_click=lambda: change_page(-1)).props('flat')
                pagination_label = ui.label('第 1 页').classes('font-bold text-blue')
                ui.button(icon='chevron_right', on_click=lambda: change_page(1)).props('flat')

        # --- 交互函数实现 ---
        async def change_page(delta):
            page_state['current_page'] += delta
            if page_state['current_page'] < 1: page_state['current_page'] = 1
            await load_dashboard_data()

        async def edit_selected():
            selected = await grid.get_selected_rows()
            if not selected:
                ui.notify('请先在表格中选中一行', type='warning', position='center')
                return

            row = selected[0]

            with ui.dialog() as dialog, ui.card().classes('w-96'):
                ui.label(f'📝 编辑: {row["tconst"]}').classes('text-h6 font-bold')

                name_input = ui.input('电影名称', value=row['primaryTitle']).classes('w-full')

                # 处理年份显示
                default_year = row['startYear'] if row['startYear'] and row['startYear'] != 'None' else None
                year_input = ui.number('上映年份', value=default_year, format='%.0f').classes('w-full')
                genres_input = ui.input('类型 (逗号分隔)', value=row['genres']).classes('w-full')

                with ui.row().classes('w-full justify-end q-mt-md'):
                    ui.button('取消', on_click=dialog.close).props('flat text-color=grey')
                    ui.button('保存修改', on_click=lambda: do_save(dialog)).props('unelevated color=primary')

            async def do_save(dlg):
                try:
                    new_year = int(year_input.value) if year_input.value else None
                except ValueError:
                    ui.notify('年份必须是数字', type='negative')
                    return

                # 调用后端 Service
                success = await movie_service.update_movie_details(
                    row['tconst'],
                    name_input.value,
                    new_year,
                    genres_input.value
                )

                if success:
                    dlg.close()
                    ui.notify('修改成功！数据已更新', type='positive')
                    await load_dashboard_data()
                else:
                    ui.notify('保存失败，请检查系统日志', type='negative')

            dialog.open()

        async def delete_selected():
            selected = await grid.get_selected_rows()
            if not selected:
                ui.notify('请先选中要删除的电影', type='warning', position='center')
                return

            row = selected[0]

            with ui.dialog() as dialog, ui.card().classes('q-pa-md'):
                ui.label('⚠️ 危险操作').classes('text-h6 text-red font-bold')
                ui.label(f'确定要永久下架电影 "{row["primaryTitle"]}" 吗？').classes('q-py-md text-lg')

                with ui.row().classes('w-full justify-end'):
                    ui.button('手滑了', on_click=dialog.close).props('flat')
                    # 调用后端 Service
                    ui.button('确定下架', color='red', on_click=lambda: do_delete(row['tconst'], dialog))

            dialog.open()

        async def do_delete(tconst, dlg):
            success = await movie_service.delete_movie(tconst)
            dlg.close()
            if success:
                ui.notify(f'电影 {tconst} 已成功下架', type='positive')
                await load_dashboard_data()
            else:
                ui.notify('删除失败', type='negative')

        # --- 异步加载数据 (Frontend 调用 Backend) ---
        async def load_dashboard_data():
            n = ui.notification('正在从 PostgreSQL 同步数据...', spinner=True, duration=None)
            try:
                # 1. 获取统计概览
                count, avg = await movie_service.get_stats_summary()
                total_label.text = f"{count:,}"
                avg_label.text = f"{avg}"

                # 2. 获取图表数据
                top_movies = await movie_service.get_top_movies()
                chart_container_1.clear()
                with chart_container_1:
                    ui.label('🏆 评分最高榜单 (Top 10)').classes('font-bold q-pa-sm')
                    if top_movies:
                        fig1 = go.Figure(data=[
                            go.Bar(x=[str(m[0])[:15] for m in top_movies], y=[m[1] for m in top_movies],
                                   marker_color='#3b82f6')])
                        fig1.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=220)
                        ui.plotly(fig1).classes('w-full')

                year_stats = await movie_service.get_year_stats()
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

                # 3. 获取表格分页数据
                print(f"正在加载第 {page_state['current_page']} 页数据...")

                # 调用后端获取分页数据
                raw_data = await movie_service.get_movies_paginated(
                    page_state['current_page'],
                    page_state['page_size']
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

                pagination_label.text = f"第 {page_state['current_page']} 页 / 共 {count // 100 + 1} 页"

                n.dismiss()
                ui.notify('数据看板已更新', type='positive')
            except Exception as e:
                n.dismiss()
                print(f"加载报错: {e}")
                ui.notify(f'加载失败: {e}', type='negative')

        # 启动时自动加载一次
        ui.timer(0.1, load_dashboard_data, once=True)