from nicegui import ui
import plotly.graph_objects as go
from sqlalchemy import select, func, desc, update, delete
from database import AsyncSessionLocal
from models import TitleBasics, TitleRatings


# --- 数据库操作逻辑 ---
async def update_movie_details(tconst, new_title, new_year, new_genres):
    """同时更新电影的标题、年份和类型"""
    async with AsyncSessionLocal() as db:
        try:
            # 构建更新语句
            stmt = (
                update(TitleBasics)
                .where(TitleBasics.tconst == tconst)
                .values(
                    primaryTitle=new_title,
                    startYear=new_year,
                    genres=new_genres
                )
            )
            await db.execute(stmt)
            await db.commit()
            return True
        except Exception as e:
            print(f"更新失败: {e}")
            await db.rollback()
            return False


async def delete_movie(tconst):
    """物理删除电影记录"""
    async with AsyncSessionLocal() as db:
        try:
            await db.execute(delete(TitleBasics).where(TitleBasics.tconst == tconst))
            await db.commit()
            return True
        except Exception as e:
            print(f"删除失败: {e}")
            await db.rollback()
            return False

async def get_top_movies(limit=10):
    """查询评分最高的10部电影 (需有评分数据)"""
    async with AsyncSessionLocal() as db:
        # 使用 Join 关联两张表：title_basics 和 title_ratings
        query = (
            select(TitleBasics.primaryTitle, TitleRatings.averageRating)
            .join(TitleRatings, TitleBasics.tconst == TitleRatings.tconst)
            .where(TitleRatings.numVotes > 10000)  # 过滤掉评价人数太少的，保证质量
            .order_by(desc(TitleRatings.averageRating))
            .limit(limit)
        )
        result = await db.execute(query)
        return result.all()

async def get_year_stats():
    """统计近 20 年的电影产量分布"""
    async with AsyncSessionLocal() as db:
        query = (
            select(TitleBasics.startYear, func.count(TitleBasics.tconst))
            .where(TitleBasics.titleType == 'movie')
            .where(TitleBasics.startYear.is_not(None))
            .group_by(TitleBasics.startYear)
            .order_by(desc(TitleBasics.startYear))
            .limit(20)
        )
        result = await db.execute(query)
        return result.all()

# --- 封装的数据获取函数 ---
async def get_stats_summary():
    async with AsyncSessionLocal() as db:
        movie_count = await db.execute(select(func.count(TitleBasics.tconst)))
        avg_rating = await db.execute(select(func.avg(TitleRatings.averageRating)))
        return movie_count.scalar(), round(avg_rating.scalar() or 0, 2)


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

        # --- 优化：统计指标卡片 (毕设亮点) ---

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
                    {'headerName': '电影名称', 'field': 'primaryTitle'},  # 必须是 primaryTitle
                    {'headerName': '上映年份', 'field': 'startYear'},  # 必须是 startYear
                    {'headerName': '类型标签', 'field': 'genres'},  # 必须是 genres
                ],
                'rowData': [],
                'rowSelection': 'single',
                'pagination': True,
            }).classes('h-96 w-full shadow-lg')  # 👈 确保这里有高度 h-96

            with ui.row().classes('w-full justify-center items-center q-pa-sm bg-grey-1'):
                ui.button(icon='chevron_left', on_click=lambda: change_page(-1)).props('flat')
                pagination_label = ui.label('第 1 页').classes('font-bold text-blue')
                ui.button(icon='chevron_right', on_click=lambda: change_page(1)).props('flat')

        # --- 交互函数实现 ---
        async def change_page(delta):
            page_state['current_page'] += delta
            if page_state['current_page'] < 1: page_state['current_page'] = 1
            await load_dashboard_data()

        # --- 交互函数实现 ---
        async def edit_selected():
            # 获取当前选中的行
            selected = await grid.get_selected_rows()
            if not selected:
                ui.notify('请先在表格中选中一行', type='warning', position='center')
                return

            row = selected[0]  # 获取行数据字典

            # 创建弹窗
            with ui.dialog() as dialog, ui.card().classes('w-96'):
                ui.label(f'📝 编辑: {row["tconst"]}').classes('text-h6 font-bold')

                # 表单输入框 (绑定默认值为当前行的数据)
                name_input = ui.input('电影名称', value=row['primaryTitle']).classes('w-full')

                # 年份需要处理空值，防止报错
                default_year = row['startYear'] if row['startYear'] and row['startYear'] != 'None' else None
                year_input = ui.number('上映年份', value=default_year, format='%.0f').classes('w-full')

                genres_input = ui.input('类型 (逗号分隔)', value=row['genres']).classes('w-full')

                # 底部按钮栏
                with ui.row().classes('w-full justify-end q-mt-md'):
                    ui.button('取消', on_click=dialog.close).props('flat text-color=grey')
                    ui.button('保存修改', on_click=lambda: do_save(dialog)).props('unelevated color=primary')

            # 定义保存动作
            async def do_save(dlg):
                # 数据清洗：年份必须转为整数
                try:
                    new_year = int(year_input.value) if year_input.value else None
                except ValueError:
                    ui.notify('年份必须是数字', type='negative')
                    return

                # 调用后端更新
                success = await update_movie_details(
                    row['tconst'],
                    name_input.value,
                    new_year,
                    genres_input.value
                )

                if success:
                    dlg.close()
                    ui.notify('修改成功！数据已更新', type='positive')
                    await load_dashboard_data()  # 刷新表格显示最新数据
                else:
                    ui.notify('保存失败，请检查系统日志', type='negative')

            dialog.open()  # 💡 必须调用 open() 才能显示弹窗

        async def delete_selected():
            selected = await grid.get_selected_rows()
            if not selected:
                ui.notify('请先选中要删除的电影', type='warning', position='center')
                return

            row = selected[0]

            # 创建确认弹窗
            with ui.dialog() as dialog, ui.card().classes('q-pa-md'):
                ui.label('⚠️ 危险操作').classes('text-h6 text-red font-bold')
                ui.label(f'确定要永久下架电影 "{row["primaryTitle"]}" 吗？').classes('q-py-md text-lg')

                with ui.row().classes('w-full justify-end'):
                    ui.button('手滑了', on_click=dialog.close).props('flat')
                    ui.button('确定下架', color='red', on_click=lambda: do_delete(row['tconst'], dialog))

            dialog.open()

            # 执行删除
        async def do_delete(tconst, dlg):
            success = await delete_movie(tconst)
            dlg.close()
            if success:
                ui.notify(f'电影 {tconst} 已成功下架', type='positive')
                await load_dashboard_data()  # 刷新数据
            else:
                ui.notify('删除失败', type='negative')

        # --- 异步加载数据 ---
        async def load_dashboard_data():
            n = ui.notification('正在从 PostgreSQL 同步数据...', spinner=True, duration=None)
            try:
                # 计算偏移量
                offset = (page_state['current_page'] - 1) * page_state['page_size']

                # 1. 刷新统计指标
                count, avg = await get_stats_summary()
                total_label.text = f"{count:,}"
                avg_label.text = f"{avg}"

                # 2. & 3. 渲染图表 (代码保持不变，只需在里面加上 check 数据是否为空)
                top_movies = await get_top_movies()
                chart_container_1.clear()
                with chart_container_1:
                    ui.label('🏆 评分最高榜单 (Top 10)').classes('font-bold q-pa-sm')
                    if top_movies:
                        fig1 = go.Figure(data=[
                            go.Bar(x=[str(m[0])[:15] for m in top_movies], y=[m[1] for m in top_movies],
                                   marker_color='#3b82f6')])
                        fig1.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=220)
                        ui.plotly(fig1).classes('w-full')

                year_stats = await get_year_stats()
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

                # 4. 刷新表格 (增加翻页和强制重绘)
                print(f"正在加载第 {page_state['current_page']} 页数据...")
                async with AsyncSessionLocal() as db:
                    # 使用 offset 和 limit 进行真分页
                    result = await db.execute(select(TitleBasics).offset(offset).limit(page_state['page_size']))
                    raw_data = result.scalars().all()

                    rows = []
                    for m in raw_data:
                        # 核心修改：确保所有数据都是字符串，防止 AG Grid 无法识别特殊类型
                        rows.append({
                            'tconst': str(m.tconst) if m.tconst else '',
                            'primaryTitle': str(m.primaryTitle) if m.primaryTitle else '',
                            'startYear': str(m.startYear) if m.startYear else '',
                            'genres': str(m.genres) if m.genres else ''
                        })

                    # 双重更新保险
                    grid.options['rowData'] = rows
                    grid.update()
                    # 强制使用 AG Grid 内部方法刷新数据
                    grid.run_grid_method('setRowData', rows)

                    pagination_label.text = f"第 {page_state['current_page']} 页 / 共 {count // 100 + 1} 页"

                n.dismiss()
                ui.notify('数据看板已更新', type='positive')
            except Exception as e:
                n.dismiss()
                print(f"加载报错: {e}")
                ui.notify(f'加载失败: {e}', type='negative')

        ui.timer(0.1, load_dashboard_data, once=True)