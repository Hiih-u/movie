import time
import importlib
from nicegui import ui

def render_sidebar():
    with ui.left_drawer(value=True).classes('bg-blue-grey-1 text-slate-900') \
            .props('width=220 breakpoint=700'):
        ui.button('回首页', icon='home', on_click=lambda: ui.navigate.to('/')) \
            .classes('text-h6 font-bold text-primary w-full') \
            .props('flat align=left no-caps q-pa-md')
        ui.separator()
        with ui.column().classes('w-full q-pa-sm'):
            ui.button('数据总览', icon='dashboard', on_click=lambda: ui.navigate.to('/admin')).classes('w-full').props(
                'flat')
            # --- 高亮当前页 ---
            ui.button('数据可视化', icon='analytics').classes('w-full shadow-sm bg-white text-primary').props('flat')
            ui.button('用户管理', icon='people', on_click=lambda: ui.navigate.to('/admin/users')).classes(
                'w-full').props('flat')
            ui.button('演职人员', icon='badge', on_click=lambda: ui.navigate.to('/admin/people')).classes(
                'w-full').props('flat')
            ui.button('影视管理', icon='movie', on_click=lambda: ui.navigate.to('/admin/movies')).classes(
                'w-full').props('flat')
            ui.button('评分管理', icon='star', on_click=lambda: ui.navigate.to('/admin/ratings')).classes(
                'w-full').props('flat')
            ui.button('剧组管理', icon='groups', on_click=lambda: ui.navigate.to('/admin/crew')).classes(
                'w-full').props('flat')
            ui.button('剧集管理', icon='subscriptions', on_click=lambda: ui.navigate.to('/admin/episodes')).classes(
                'w-full').props('flat')


def create_analytics_page():
    # 渲染侧边栏
    render_sidebar()

    with ui.column().classes('w-full q-pa-md items-center bg-slate-50 min-h-screen'):
        # 顶部标题栏
        with ui.row().classes('w-full justify-between items-center q-mb-lg'):
            with ui.column().classes('gap-0'):
                ui.label('📈 影视全域数据分析').classes('text-h4 font-bold text-slate-800')
                ui.label('基于千万级 IMDb 离线数据的静态可视化大屏').classes('text-slate-500')

            # 手动触发更新按钮
            async def run_update():
                ui.notify('正在后台运行 generate_charts.py ...', type='info')

                from init import generate_charts
                importlib.reload(generate_charts)

                await generate_charts.generate_all_charts()

                await ui.run_javascript("""
                    document.querySelectorAll('iframe').forEach(i => {
                        let url = i.src.split('?')[0]; 
                        i.src = url + '?v=' + Date.now();
                    });
                """)
                ui.notify('图表缓存已更新！', type='positive')

            ui.button('更新图表缓存', icon='update', on_click=run_update).props('unelevated color=deep-orange')

        # 辅助函数：创建图表容器
        def chart_card(title, filename, height='450px', color='blue'):
            # 生成带时间戳的 URL
            timestamp = int(time.time())
            src_url = f"/static/charts/{filename}?v={timestamp}"

            with ui.card().classes(f'w-full h-[{height}] shadow-sm p-0 overflow-hidden flex flex-col'):
                # 标题栏
                with ui.row().classes('w-full items-center px-4 py-2 bg-slate-50 border-b gap-2'):
                    ui.element('div').classes(f'w-1 h-4 bg-{color}-500 rounded')
                    ui.label(title).classes(f'font-bold text-{color}-700 text-sm')

                # iframe
                ui.element('iframe').props(f'src="{src_url}" frameborder="0"') \
                    .classes('w-full flex-1')

        with ui.row().classes('w-full q-mb-lg'):
            # height='600px' 给足空间
            chart_card(
                title='💰 票房与评分气泡图',
                filename='roi_bubble.html',
                height='710px',
                color='indigo'
            )

        # --- 第一行：题材与评分 (左右布局) ---
        with ui.row().classes('w-full gap-6 q-mb-md'):
            with ui.column().classes('flex-1'):
                chart_card('🌸 题材占比玫瑰图', 'genre_rose.html', color='pink')
            with ui.column().classes('flex-1'):
                chart_card('🎻 评分分布箱型图', 'rating_box.html', color='purple')

        # --- 第二行：时代演变 (通栏) ---
        with ui.row().classes('w-full q-mb-md'):
            chart_card('🔥 题材变迁热力图', 'evolution_heatmap.html', height='500px', color='orange')

        # --- 第三行：质量与热度 (通栏) ---
        with ui.row().classes('w-full q-mb-md'):
            chart_card('✨ 评分与热度散点图', 'quality_scatter.html', height='600px', color='blue')

        # --- 第四行：中西对比 (通栏) ---
        with ui.row().classes('w-full q-mb-md'):
            chart_card('🌏 不同平台评分对比图', 'culture_compare.html', height='600px', color='teal')

        ui.label('注：图表数据来自本地 /static/charts 缓存，请定期点击右上角更新。').classes(
            'text-xs text-slate-400 q-mt-xl')