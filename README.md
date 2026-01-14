

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

这份部署手册基于您提供的 `README.md`、`movie_import.md` 以及项目代码结构编写。手册涵盖了从环境准备、数据库导入、模型配置、初始化到最终启动的全过程。

---

# 🎬 MovieRec Sys 电影推荐系统部署手册

本手册将指导您在 **Windows** 或 **Linux** 环境下部署该电影推荐系统。系统基于 Python (FastAPI + NiceGUI) 开发，使用 PostgreSQL 存储数据，并集成 Spark 进行离线推荐计算。

## 1. 环境准备 (Prerequisites)

在开始之前，请确保服务器或本地电脑已安装以下基础软件：

* **操作系统**: Windows / Linux (推荐 Ubuntu/Debian)
* **Python**: 版本 **3.11** (推荐)
* **PostgreSQL**: 数据库服务
* **Java JDK**: 版本 **17** (用于运行 Spark 推荐算法)
* **Git**: 用于克隆代码和模型

---

## 2. 项目代码与 Python 环境配置

### 2.1 克隆项目

将项目代码下载到本地目录（假设项目根目录为 `movie/`）。

### 2.2 创建虚拟环境

建议使用 `venv` 进行依赖隔离。

**Windows:**

```bash
cd movie
python -m venv venv
venv\Scripts\activate

```

**Linux / Mac:**

```bash
cd movie
python3 -m venv venv
source venv/bin/activate

```

*(激活成功后，命令行前会出现 `(venv)` 字样)*

### 2.3 安装依赖库

在激活的虚拟环境中安装项目所需的 Python 库。

```bash
pip install -r requirements.txt

```

*注意：`requirements.txt` 中包含了 `nicegui`, `sqlalchemy`, `pyspark`, `pandas`, `transformers` 等关键库。*

---

## 3. 数据库部署 (PostgreSQL)

本系统强依赖 PostgreSQL，需分两步操作：导入 IMDb 原始数据 和 初始化系统表。

### 3.1 创建数据库与用户

登录 PostgreSQL 并创建数据库（建议使用以下配置，或后续修改代码配置）：

* **数据库名**: `movie_db`
* **用户名**: `postgresuser`
* **密码**: `password`

### 3.2 导入 IMDb 原始数据集

系统依赖 IMDb 的公开数据集 (`.tsv` 格式)。请参考 `movie_import.md` 进行操作：

1. **下载数据**: 从 IMDb 官网下载 `name.basics.tsv.gz`, `title.basics.tsv.gz` 等文件。
2. **解压文件**: 使用 `gunzip *.tsv.gz` 解压。
3. **创建表结构并导入**:
使用 SQL 工具或命令行执行建表和导入语句。确保路径指向您解压的 `.tsv` 文件路径。
```sql
-- 示例：导入 title_basics 表 (更多表结构请查看 movie_import.md)
DROP TABLE IF EXISTS title_basics;
CREATE TABLE title_basics ( ... ); -- 完整建表语句见 movie_import.md

-- 导入数据 (注意修改文件路径)
\COPY title_basics FROM '/path/to/title.basics.tsv' WITH (FORMAT csv, DELIMITER E'\t', NULL '\N', HEADER true, QUOTE E'\b');

```


*需导入的表包括：`name_basics`, `title_basics`, `title_crew`, `title_episode`, `title_ratings`。*

### 3.3 配置数据库连接

打开 `database.py`，修改 `DATABASE_URL` 为您的实际配置：

```python
# 格式: postgresql+asyncpg://用户名:密码@IP地址:端口/数据库名
DATABASE_URL = "postgresql+asyncpg://postgresuser:password@localhost:5432/movie_db"

```

---

## 4. 机器学习模型配置 (NLP)

系统使用 Hugging Face 的模型进行情感分析，需下载模型文件到本地。

1. 在项目根目录下创建文件夹 `ml_models`。
2. 进入文件夹并克隆模型（需安装 Git LFS）：
```bash
cd ml_models
git clone https://huggingface.co/morit/chinese_xlm_xnli

```


*确保 `ml_models/chinese_xlm_xnli/` 目录下包含 `pytorch_model.bin` 等文件。*

---

## 5. 系统初始化 (Initialization)

在启动 Web 服务前，需要运行一系列初始化脚本来创建应用表、管理员账户和索引。确保在 `venv` 环境下运行。

### 5.1 同步数据库表结构

创建用户表、收藏表、推荐表等应用层表结构。

```bash
python init/init_db.py

```

### 5.2 添加数据库索引

为提高查询速度，为 IMDb 原始数据表添加索引。

```bash
python init/add_index.py

```

*(注：此步骤耗时较长，请耐心等待)*

### 5.3 创建管理员账户

按照提示输入用户名、密码及画像信息。

```bash
python init/create_admin.py

```

### 5.4 生成模拟评分数据 (可选)

如果数据库中没有用户互动数据，可运行此脚本生成虚拟用户和评分，用于测试推荐算法。

```bash
python init/seed_ratings.py

```

---

## 6. 运行推荐算法 (Spark Engine)

Spark 推荐算法通过 `spark_runner.py` 离线运行。建议设置定时任务（如 Crontab）定期执行。

### 6.1 Java 环境检查

Spark 依赖 Java。请确保安装了 **JDK 17**。

```bash
java -version
# 输出应包含 openjdk version "17..."

```

*如果遇到 `class file version 61.0` 错误，说明 Java 版本过低，请升级到 Java 17。*

### 6.2 运行 Spark 任务

```bash
python spark_runner.py

```

* 该脚本会读取数据库中的评分数据，运行 ALS 协同过滤算法。
* 计算结果将存回数据库的 `spark_recommendations` 表。
* **注意**: 脚本中的 `DATABASE_URL` 可能需要单独配置（使用 `psycopg2` 驱动而非 `asyncpg`）。

---

## 7. 启动 Web 服务 (Run Application)

完成上述所有步骤后，启动主程序。

```bash
python main.py

```

* **访问地址**: 打开浏览器访问 `http://localhost:61081`
* **登录**: 使用步骤 5.3 中创建的管理员账号登录后台，或注册新用户进入前台。

---

## 8. 常见问题排查 (Troubleshooting)

1. **Spark 运行报错 `socketserver` 或 `Time out` (Windows)**:
* Spark 在 Windows 上运行通常需要配置 `Hadoop` 环境 (`winutils.exe`)。
* **建议**: 如 `README.md` 所述，建议在 **Linux** (或 WSL) 环境下运行 `spark_runner.py`，配置会简单得多。


2. **图片加载失败 / 首页无数据**:
* 请登录后台 (`/admin`) 点击 **"影视管理" -> "重建缓存"** 按钮，将 IMDb 原始数据同步到 `movie_summary` 表。


3. **模型加载失败**:
* 检查 `ml_models/chinese_xlm_xnli` 路径是否正确，且文件完整。


4. **数据库连接错误**:
* 检查 `database.py` (Web用) 和 `spark_runner.py` (Spark用) 里的 `DATABASE_URL` 是否都已修改为正确的数据库地址和密码。