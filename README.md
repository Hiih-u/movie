

## 1. 推荐管理方案：`venv` (最原生、简单)

这是 Python 自带的工具，不需要额外安装任何东西。

### 第一步：创建虚拟环境

在你的项目文件夹目录下打开终端，输入：

```bash
# Windows
python -m venv venv

# Mac / Linux
python3 -m venv venv

```

执行后，你会发现项目里多了一个 `venv` 文件夹。

### 第二步：激活环境

你需要告诉电脑：“现在开始，请把库装进这个文件夹里”。

* **Windows**: `venv\Scripts\activate`
* **Mac / Linux**: `source venv/bin/activate`

**激活成功后，你的命令行开头会出现 `(venv)` 字样。**

### 第三步：安装库

现在再执行你刚才的命令：

```bash
pip install fastapi uvicorn nicegui

```

---

## 2. 毕设收尾必备：生成依赖清单

当你完成开发，准备写论文或者把代码交给老师时，在**激活了虚拟环境**的状态下运行：

```bash
pip freeze > requirements.txt

```

这会生成一个清单。以后在任何新电脑上，只需运行 `pip install -r requirements.txt`，就能一秒还原你的开发环境。

---

## 5. 电影推荐系统的“快速原型”代码

既然环境快装好了，这是一个**最小可行性框架**（`main.py`），你可以直接复制进去运行测试：

```python
from fastapi import FastAPI
from nicegui import ui

# 1. 初始化 FastAPI
app = FastAPI()

# 模拟电影数据
MOVIES = [
    {"title": "肖申克的救赎", "poster": "https://picsum.photos/id/10/200/300"},
    {"title": "霸王别姬", "poster": "https://picsum.photos/id/11/200/300"},
    {"title": "星际穿越", "poster": "https://picsum.photos/id/12/200/300"},
]

# 2. 编写 NiceGUI 界面
@ui.page('/')
def home():
    ui.label('我的电影推荐系统').classes('text-h4 q-pa-md')
    
    with ui.row().classes('w-full wrap justify-start'):
        for movie in MOVIES:
            with ui.card().classes('q-ma-sm').style('width: 200px'):
                ui.image(movie['poster'])
                with ui.card_section():
                    ui.label(movie['title']).classes('text-bold')
                with ui.card_actions():
                    ui.button('看详情', on_click=lambda m=movie: ui.notify(f"点击了: {m['title']}"))

# 3. 将 NiceGUI 挂载到 FastAPI
ui.run_with_fastapi(app)

```
