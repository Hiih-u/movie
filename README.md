

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

ml_models 导入文本模型
git clone https://huggingface.co/morit/chinese_xlm_xnli

https://huggingface.co/morit/chinese_xlm_xnli


既然你的目标很明确：**只是为了在 Linux 虚拟机里跑 Spark，把算好的数据存进 Docker 里的 Postgres**。

那么在 Linux 虚拟机里操作其实比 Windows 简单得多，**不需要任何补丁**。

你现在的环境是：

* **OS**: Linux (Ubuntu/Debian)
* **DB**: Docker 容器运行的 Postgres (端口映射 5432)
* **代码**: 还没上传/配置好

请按以下 **3 步** 极简操作即可跑通：

---

### 第一步：安装必要的环境 (Java + Python库)

Spark 必须依赖 Java，而连接数据库需要 `psycopg2`。
在你的终端（已经是 root 用户）依次执行：

1. **安装 Java (JDK 8)**：
```bash
apt update
apt install openjdk-8-jdk -y

```


*验证：输入 `java -version` 应该能看到输出。*
2. **安装 Python 依赖库**：
```bash
apt install python3-pip
pip install pyspark pandas sqlalchemy psycopg2-binary

```


*(注意：Linux 下 `psycopg2-binary` 是开箱即用的，不需要像 Windows 那样担心编译问题 )*

---

### 第二步：确认代码文件

你需要把 Windows 写的 `spark_runner.py` 上传到虚拟机当前目录 (`~/movie_project/`)。

如果你还没上传，可以在虚拟机里直接新建一个文件把代码粘贴进去：

1. **新建文件**：
```bash
nano spark_runner.py

```


2. **粘贴代码**：
把你在 Windows 上写好的 `spark_runner.py` 内容复制，在 Linux 终端里右键粘贴。
*(**注意**：确保代码里的 `DATABASE_URL` 用户名密码是对的，且使用的是 `psycopg2` 而不是 `asyncpg`)*
3. **保存退出**：
按 `Ctrl + O` (回车保存)，然后 `Ctrl + X` (退出)。

**关键检查点：数据库连接**
因为你的 Postgres 是 Docker 跑的，且映射到了宿主机的 5432 端口。
所以在 `spark_runner.py` 里，`host` 写 **`localhost`** 即可。

```python
# 确保 spark_runner.py 里是这样的（或者代码里有自动替换逻辑）
DATABASE_URL = "postgresql+psycopg2://postgres:你的密码@localhost:5432/你的数据库名"

```

---

### 第三步：直接运行

一切准备就绪，直接运行 Python 脚本：

```bash
python3 spark_runner.py

```

### 预期结果

你不会再看到 Windows 上那些 `socketserver`、`winutils.exe`、`Time out` 的报错。
你会看到：

1. Spark 启动日志（一大堆 INFO/WARN，属于正常）。
2. `🚀 [Step 1] 初始化 Spark...`
3. `✅ 成功！已保存 XX 条推荐记录。`

**这就完事了！** 数据已经由 Spark 算好并存进你的 Postgres 容器里了。


这是一个非常明确的 **Java 版本不匹配** 错误。

**错误解读：**

* `class file version 61.0`: 代表 **Java 17**。
* `this version ... up to 52.0`: 代表 **Java 8**。
* **含义**：你安装的最新版 PySpark（可能是 3.5 或 4.0）是用 **Java 17** 编译的，但你的系统里现在运行的是 **Java 8**。老版本 Java 跑不动新版本代码。

之前我让你装 Java 8 是因为旧版 Spark 的标准配置，但现在 `pip install pyspark` 默认下载了最新版，它强制要求更高版本的 Java。

**解决方法：升级到 Java 17。**

请在终端中依次执行以下 3 步：

### 第一步：安装 OpenJDK 17

```bash
apt update
apt install openjdk-17-jdk -y

```

### 第二步：切换默认 Java 版本 (关键)

安装完后，系统可能默认还是用 Java 8。你需要手动切一下。

输入以下命令：

```bash
update-alternatives --config java

```

**操作指南：**

1. 输入命令后，屏幕会列出已安装的 Java 版本（比如 0, 1, 2...）。
2. 找到路径里包含 **`java-17-openjdk`** 的那一项。
3. 输入那一项对应的 **数字编号**，然后按回车。

*(例如：如果 Java 17 是选项 2，你就输 2 回车)*

### 第三步：验证并重新运行

1. **验证版本**：
```bash
java -version

```


*确保输出里包含 `openjdk version "17..."*`
2. **再次运行脚本**：
```bash
python3 spark_runner.py

```



这次应该就能完美启动了！🚀