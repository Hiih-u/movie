

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