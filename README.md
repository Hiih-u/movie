# 🎬 MovieRec Sys 电影推荐系统部署手册

本手册将指导您在 **Windows** 或 **Linux** 环境下部署 MovieRec Sys。
系统架构：**Python 3.11 (FastAPI + NiceGUI)** + **PostgreSQL** + **Spark (离线推荐)** + **Hugging Face (NLP)**。

---

## 📋 1. 环境准备 (Prerequisites)

在开始之前，请确保服务器或本地环境已安装以下基础软件。

### 1.1 基础软件

* **操作系统**: 推荐 Linux (Ubuntu/Debian) 或 Windows。
* **Python**: 版本 **3.11**。
* **PostgreSQL**: 数据库服务（支持 Docker 部署）。
* **Git**: 用于克隆代码和模型。
* **Java JDK**: **必须安装 JDK 17** (用于 PySpark 运行，JDK 8 已不兼容新版 PySpark)。

### 1.2 Linux 环境特别说明 (推荐)

如果您使用 Linux 虚拟机跑 Spark 任务，需安装以下系统级依赖：

```bash
# 更新源并安装 JDK 17 和 Python pip
sudo apt update
sudo apt install openjdk-17-jdk python3-pip -y

# 验证 Java 版本 (必须输出 17.x)
java -version

```

---

## 🛠️ 2. 项目初始化

### 2.1 获取代码与创建环境

将项目代码下载到本地目录（假设根目录为 `movie/`）。

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

### 2.2 安装 Python 依赖

在激活的虚拟环境中安装所需库。

```bash
# 核心依赖包括 nicegui, sqlalchemy, pyspark, pandas, transformers 等
pip install -r requirements.txt

# Linux 环境额外建议：确保安装 pyspark 和 psycopg2 依赖
# pip install pyspark pandas sqlalchemy psycopg2-binary

```

---

## 🗄️ 3. 数据库部署 (PostgreSQL)

本系统强依赖 PostgreSQL，需完成**数据导入**和**连接配置**。

### 3.1 准备数据库

登录 PostgreSQL 并创建数据库：

* **数据库名**: `movie_db`
* **用户名**: `postgresuser`
* **密码**: `password`

### 3.2 导入 IMDb 原始数据

请参考项目根目录下的 `movie_import.md` 下载并导入数据。

1. **下载**: 从 IMDb 官网下载 `name.basics.tsv.gz`, `title.basics.tsv.gz` 等文件。
2. **解压**: 使用 `gunzip *.tsv.gz`。
3. **导入**: 使用 SQL 执行建表和数据导入。
```sql
-- 示例：导入 title_basics
\COPY title_basics FROM '/path/to/title.basics.tsv' WITH (FORMAT csv, DELIMITER E'\t', NULL '\N', HEADER true, QUOTE E'\b');

```



### 3.3 配置 Web 服务连接 (`database.py`)

修改 `database.py`，配置 Web 服务使用的异步连接：

```python
# ⚠️ 注意：此处必须使用 asyncpg 驱动
DATABASE_URL = "postgresql+asyncpg://postgresuser:password@localhost:5432/movie_db"

```

---

## 🤖 4. NLP 模型配置

系统使用 Hugging Face 的 `chinese_xlm_xnli` 模型进行情感分析，需下载到本地。

1. 在项目根目录下创建文件夹 `ml_models`。
2. 进入文件夹并克隆模型（需安装 Git LFS）：
```bash
cd ml_models
git clone https://huggingface.co/morit/chinese_xlm_xnli

```


*> 检查点：确保 `ml_models/chinese_xlm_xnli/` 目录下包含 `pytorch_model.bin` 等文件。*

---

## ⚙️ 5. 系统初始化 (Initialization)

在启动服务前，必须按顺序运行以下脚本以同步表结构并生成初始数据。

1. **同步数据库表结构** (创建用户表、收藏表等):
```bash
python init/init_db.py

```


2. **添加数据库索引** (提高查询性能，耗时较长):
```bash
python init/add_index.py

```


3. **创建管理员账户** (按提示输入账号信息):
```bash
python init/create_admin.py

```


4. **生成模拟数据** (可选，生成虚拟评分用于测试推荐):
```bash
python init/seed_ratings.py

```



---

## ⚡ 6. 运行 Spark 推荐算法

推荐算法通过 `spark_runner.py` 离线运行。**建议在 Linux 环境下运行此步骤**以避免 Windows 的环境问题。

### 6.1 配置 Spark 数据库连接 (`spark_runner.py`)

Spark 不支持异步驱动，**必须**修改代码中的连接字符串使用 `psycopg2`。

```python
# 打开 spark_runner.py 修改 DATABASE_URL
# ⚠️ 注意：此处必须使用 psycopg2 驱动
# 如果 Postgres 在 Docker 中运行，Linux 宿主机访问通常使用 localhost:5432
DATABASE_URL = "postgresql+psycopg2://postgresuser:password@localhost:5432/movie_db"

```

### 6.2 运行计算任务
linux 虚拟机中运行
```bash
python spark_runner.py

```

**预期输出：**

* 看到 Spark 启动日志。
* 显示 `🚀 [Step 1] 初始化 Spark...`
* 最终显示 `✅ 成功！已保存 XX 条推荐记录。`

---

## 🚀 7. 启动 Web 服务

一切准备就绪，启动主程序：

```bash
python main.py

```

* **访问地址**: [http://localhost:61081](https://www.google.com/search?q=http://localhost:61081)
* **后台管理**: 使用步骤 5.3 创建的账号登录。

---

## ❓ 常见问题 (Troubleshooting)

| 问题现象 | 解决方案 |
| --- | --- |
| **Spark 报错 `class file version 61.0**` | Java 版本过低。Spark 新版需要 Java 17。请安装 JDK 17 并通过 `update-alternatives` 切换默认版本。 |
| **Spark 报错 `socketserver` / `winutils**` | Windows 环境常见错误。建议在 WSL 或 Linux 虚拟机中运行 `spark_runner.py`。 |
| **NLP 模型加载失败** | 检查 `ml_models` 目录路径是否正确，且已安装 `torch` 库。 |
| **首页无数据 / 图片加载失败** | 登录后台 (`/admin`) -> **"影视管理"** -> 点击 **"重建缓存"**，同步 IMDb 数据到业务表。 |
| **bcrypt / passlib 报错** | 可能是版本冲突。尝试锁定版本：`pip install bcrypt==3.2.2 passlib==1.7.4`。 |