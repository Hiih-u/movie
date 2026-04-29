import sys
import os
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- 1. 路径配置 ---
# 确保能导入项目根目录的模块
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from services import analysis_service

# 定义静态文件存储路径: movie-main/static/charts
STATIC_DIR = os.path.join(PROJECT_ROOT, "static", "charts")


async def generate_all_charts():
    print(f"🚀 [Init] 开始生成静态图表...")
    print(f"📂 目标目录: {STATIC_DIR}")

    # 1. 自动创建目录
    if not os.path.exists(STATIC_DIR):
        os.makedirs(STATIC_DIR)
        print("✅ 已自动创建 static/charts 目录")

    # --- 图表 1: 题材玫瑰图 ---
    print("🎨 正在生成: 题材偏好 (genre_rose.html)...")
    try:
        rose_data = await analysis_service.get_genre_distribution()
        if rose_data:
            # 优化 1: direction="clockwise" 顺时针，start_angle=90 从12点方向开始
            # 优化 2: 使用 Twilight 周期性配色，视觉更高级
            fig = px.bar_polar(
                rose_data, r="count", theta="genre", color="genre",
                template="plotly_white",
                color_discrete_sequence=px.colors.qualitative.Safe,  # 或者 px.colors.cyclical.Twilight
                direction="clockwise", start_angle=90
            )

            # 优化 3: 自定义悬停信息，更简洁
            fig.update_traces(hovertemplate='<b>%{theta}</b><br>收录: %{r}部<extra></extra>')

            # 优化 4: 隐藏径向轴的刻度数值(showticklabels=False)，只看比例，界面更清爽
            fig.update_layout(
                margin=dict(t=30, b=30, l=30, r=30),
                paper_bgcolor='rgba(0,0,0,0)',
                polar=dict(
                    radialaxis=dict(visible=True, showticklabels=False, ticks=''),
                    angularaxis=dict(rotation=90, direction="clockwise")
                ),
                legend=dict(orientation="h", y=-0.1)  # 图例放到底部
            )
            fig.write_html(os.path.join(STATIC_DIR, "genre_rose.html"))
    except Exception as e:
        print(f"❌ 玫瑰图生成失败: {e}")

    # --- 图表 2: 评分箱线图 (优化版) ---
    print("🎨 正在生成: 评分分布 (rating_box.html)...")
    try:
        violin_data = await analysis_service.get_rating_distribution_by_genre()
        if violin_data:
            df = pd.DataFrame(violin_data)

            # 【核心优化】按“评分中位数”降序排列
            # 这样用户一眼就能看出哪类电影整体质量最高（通常是 Documentary 或 Biography）
            median_order = df.groupby('genre')['rating'].median().sort_values(ascending=False).index

            fig = px.box(
                df, x="genre", y="rating", color="genre",
                # 强制指定排序顺序
                category_orders={"genre": median_order},
                template="plotly_white",
                color_discrete_sequence=px.colors.qualitative.Bold  # 颜色更鲜艳
            )

            # 优化: 调整边距，加上 Y 轴标题
            fig.update_layout(
                showlegend=False,  # 既然X轴已经写了类型，就不需要图例了，省空间
                margin=dict(t=20, b=40, l=50, r=20),
                yaxis_title="IMDb 评分",
                xaxis_title=None,
                yaxis=dict(range=[0, 10.2])  # 固定 0-10 分的显示范围
            )
            fig.write_html(os.path.join(STATIC_DIR, "rating_box.html"))
    except Exception as e:
        print(f"❌ 箱线图生成失败: {e}")


    # --- 图表 3: 时代变迁热力图---
    print("🎨 正在生成: 时代变迁 (evolution_heatmap.html)...")
    try:
        years, genres, z_matrix = await analysis_service.get_genre_evolution()
        if years:
            # 优化 1: 使用更直观的暖色调 (Yellow-Orange-Red)
            # 优化 2: xgap/ygap 增加格子间距，看起来更精致
            fig = go.Figure(data=go.Heatmap(
                z=z_matrix, x=years, y=genres,
                colorscale='YlOrRd',
                xgap=1, ygap=1,
                hovertemplate='<b>%{y}</b><br>%{x}年代<br>产量: %{z}部<extra></extra>',  # 自定义悬停文字
                colorbar=dict(title='产量', title_side='right')
            ))
            fig.update_layout(
                template="plotly_white",
                # 优化 3: 增加左侧边距 (l=100) 防止 Documentary 等长单词被切
                margin=dict(t=10, b=40, l=100, r=20),
                xaxis_title="年代 (Decade)",
                yaxis_title=None,  # Y轴标题多余，直接看文字就知道是类型
                font=dict(family="Arial, sans-serif")
            )
            fig.write_html(os.path.join(STATIC_DIR, "evolution_heatmap.html"))
    except Exception as e:
        print(f"❌ 热力图生成失败: {e}")


    # --- 图表 4: 评分与热度散点图---
    print("🎨 正在生成: 评分与热度 (quality_scatter.html)...")
    try:
        scatter_data = await analysis_service.get_scatter_data()
        if scatter_data:
            df = pd.DataFrame(scatter_data)

            # 优化 1: opacity=0.6 让重叠的点能透出来，看出密度
            # 优化 2: hover_data 增加维度显示
            fig = px.scatter(
                df, x="votes", y="rating", color="genre",
                hover_name="title",
                hover_data={"votes": True, "rating": True, "genre": False},  # 悬停显示详情
                log_x=True,  # 保持对数坐标
                opacity=0.65,  # 透明度，关键！
                template="plotly_white",
                size_max=12
            )

            # 优化 3: 添加一条 8.0 分的参考线 (神作分界线)
            fig.add_hline(y=8.0, line_dash="dash", line_color="rgba(255,0,0,0.5)",
                          annotation_text="8.0分 (神作线)", annotation_position="top left")

            # 优化 4: 去掉内部 Title (因为外部 UI 已经有了)，增加边距利用率
            fig.update_layout(
                margin=dict(t=10, b=30, l=40, r=20),
                xaxis_title="投票数 (热度/对数坐标)",
                yaxis_title="IMDb 评分",
                legend=dict(
                    orientation="h",  # 图例横排，放在顶部，节省垂直空间
                    yanchor="bottom", y=1.02,
                    xanchor="right", x=1
                )
            )
            fig.write_html(os.path.join(STATIC_DIR, "quality_scatter.html"))
    except Exception as e:
        print(f"❌ 散点图生成失败: {e}")

    # --- 图表 5: 中西审美对比 ---
    print("🎨 正在生成: 中西对比 (culture_compare.html)...")
    try:
        comp_data = await analysis_service.get_cultural_comparison()
        if comp_data:
            # 1. 数据倒序：让 Top 1 (Rank 1) 显示在图表的最顶部
            # (Plotly 的 Y 轴默认是从下往上绘制的，所以我们需要把列表反转)
            comp_data.reverse()

            titles = [x['title'] for x in comp_data]
            douban = [x['douban'] for x in comp_data]
            imdb = [x['imdb'] for x in comp_data]

            fig = go.Figure()

            # 左侧：豆瓣 (负值实现方向向左)
            fig.add_trace(go.Bar(
                y=titles, x=[-s for s in douban],
                orientation='h', name='豆瓣评分',
                marker_color='#00B51D',  # 更鲜亮的豆瓣绿
                text=douban,  # 标签显示正数
                textposition='inside',  # 数字显示在条形内部
                insidetextanchor='end',  # 数字紧贴中间轴
                hovertemplate='<b>%{y}</b><br>豆瓣评分: %{text}<extra></extra>'
            ))

            # 右侧：IMDb (正值实现方向向右)
            fig.add_trace(go.Bar(
                y=titles, x=imdb,
                orientation='h', name='IMDb评分',
                marker_color='#F5C518',  # 经典的 IMDb 黄
                text=imdb,
                textposition='inside',
                insidetextanchor='start',  # 数字紧贴中间轴
                hovertemplate='<b>%{y}</b><br>IMDb评分: %{text}<extra></extra>'
            ))

            fig.update_layout(
                barmode='relative',  # 相对模式，实现背对背生长
                template="plotly_white",

                # 优化 1: 增加左侧边距，防止长电影名被切掉
                margin=dict(t=10, b=30, l=140, r=20),

                # 优化 2: 自定义 X 轴刻度，隐藏负号，范围固定
                xaxis=dict(
                    tickvals=[-10, -5, 0, 5, 10],
                    ticktext=['10', '5', '0', '5', '10'],  # 显示文本全是正数
                    range=[-11, 11],  # 留一点白边
                    showgrid=False,  # 去掉网格线，画面更干净
                    zeroline=True, zerolinewidth=1, zerolinecolor='black'  # 强化中间的 0 轴
                ),

                # 优化 3: Y 轴字体
                yaxis=dict(tickfont=dict(size=12)),

                # 优化 4: 图例横排放在顶部居中
                legend=dict(
                    orientation="h",
                    yanchor="bottom", y=1.02,
                    xanchor="center", x=0.5
                ),
                font=dict(family="Arial, sans-serif")
            )

            fig.write_html(os.path.join(STATIC_DIR, "culture_compare.html"))
        else:
            print("⚠️ 未检测到豆瓣/IMDb关联数据，跳过对比图。")
    except Exception as e:
        print(f"❌ 对比图生成失败: {e}")


    # --- 图表 6: 商业价值 vs 口碑 (ROI Bubble Chart) ---
    print("🎨 正在生成: 商业价值 vs 口碑气泡图 (roi_bubble.html)...")
    try:
        roi_data = await analysis_service.get_roi_scatter_data()

        if roi_data:
            df = pd.DataFrame(roi_data)

            # 使用 Plotly Express 绘制气泡图
            # log_x=True 是关键，因为票房差距巨大（几百万到几十亿），必须用对数坐标才能看清
            fig = px.scatter(
                df,
                x="box_office",
                y="rating",
                size="votes",  # 气泡大小代表热度 (投票数)
                color="genre",  # 颜色代表类型
                hover_name="title",  # 鼠标悬停显示电影名
                log_x=True,  # X轴使用对数坐标
                size_max=35,  # 气泡最大尺寸限制，防止太挡视线
                template="plotly_white",
                color_discrete_sequence=px.colors.qualitative.Bold,  # 鲜艳配色
                labels={"box_office": "全球票房 (美元)", "rating": "IMDb 评分", "votes": "投票热度"}
            )

            # --- 深度优化：标注“叫好又叫座”的神作区 ---
            # 我们定义：票房 > 1亿美元 且 评分 > 8.5 的区域为“神作区”

            # 1. 画一个红色虚线框 (Rectangle)
            fig.add_shape(type="rect",
                          x0=100_000_000, y0=8.5,  # 左下角 (1亿, 8.5分)
                          x1=3_000_000_000, y1=10,  # 右上角 (30亿, 10分)
                          line=dict(color="Red", width=2, dash="dot"),
                          fillcolor="rgba(255, 0, 0, 0.05)",  # 极淡的红色背景
                          )

            # 2. 加文字标注
            # 注意：在对数坐标轴上，位置需要 careful。Plotly 的 add_annotation 会自动处理 log 坐标
            fig.add_annotation(
                x=500_000_000,
                y=9.6,
                text="🏆 叫好又叫座 (神作区)",
                showarrow=False,
                font=dict(color="red", size=14, weight="bold")
            )

            # 3. 布局微调
            fig.update_layout(
                margin=dict(t=20, b=40, l=60, r=20),
                legend=dict(
                    title="电影类型",
                    orientation="h",  # 图例横排
                    yanchor="bottom", y=1.02,  # 放在图表上方
                    xanchor="right", x=1
                ),
                height=600  # 高度设高一点，更有气势
            )

            fig.write_html(os.path.join(STATIC_DIR, "roi_bubble.html"))
            print("✅ 气泡图生成成功！")

    except Exception as e:
        print(f"❌ ROI 气泡图生成失败: {e}")

    print("🎉 所有任务执行完毕！")


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(generate_all_charts())