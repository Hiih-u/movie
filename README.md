# 🎬 MovieRec Sys - 影视推荐系统

**MovieRec Sys** 是一个基于 **Python 3.11** 开发的影视推荐系统。它融合了 **大数据计算 (Spark)**、**自然语言处理 (NLP/Transformers)** 和 **实时协同过滤** 技术，旨在为用户提供精准的个性化电影推荐服务，并为管理员提供强大的数据可视化大屏。

---

## ✨ 核心特性 (Features)

### 🧠 混合推荐引擎

1. **离线推荐 (Spark ALS)**: 使用 PySpark 的交替最小二乘法 (ALS) 处理海量评分数据，挖掘潜在的 User-Item 关联，解决数据稀疏性问题。
2. **实时推荐 (Item-Based CF)**: 基于 Scikit-learn 余弦相似度计算，根据用户的实时收藏和评分行为，毫秒级响应推荐相似电影。
3. **情感语义推荐 (NLP)**: 集成 Hugging Face 的 `chinese_xlm_xnli` 模型，支持自然语言输入（如“今天加班好累”），AI 自动识别情绪并推荐治愈系或解压影片。
4. **冷启动策略**: 针对新用户提供基于热门榜单、分类精选的兜底推荐。

### 📊 数据可视化与管理

* **可视化大屏**: 集成 Plotly 绘制动态图表，包括商业价值气泡图、题材玫瑰图、中西审美对比图等。
* **全功能后台**: 基于 NiceGUI 开发的 SPA (单页应用) 管理后台，支持用户、电影、演职员、评分、剧集的 CRUD 操作。
* **数据爬虫**: 内置多线程爬虫，支持抓取 IMDb 票房数据和豆瓣 Top250 榜单。

### 🛠 技术栈

* **前端/全栈**: [NiceGUI](https://nicegui.io/) (基于 FastAPI + Vue)
* **数据库**: PostgreSQL (异步 asyncpg + 同步 psycopg2)
* **大数据**: Apache Spark (PySpark)
* **AI/NLP**: PyTorch, Transformers (Hugging Face)
* **数据分析**: Pandas, Plotly

---

## 📋 1. 环境准备 (Prerequisites)

在开始之前，请确保服务器或本地环境已安装以下基础软件。

### 1.1 基础软件

* **操作系统**: 推荐 Linux (Ubuntu/Debian) 或 Windows。
* **Python**: 版本 **3.11**。
* **PostgreSQL**: 数据库服务。
* **Java JDK**: **必须安装 JDK 17** (用于 PySpark 运行，JDK 8 已不兼容新版 PySpark)。
* **Git**: 用于克隆代码和模型。

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

## 🛠️ 2. 项目初始化 (Installation)

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

### 3.3 配置数据库连接

修改 `database.py` 和 `spark_runner.py` 中的连接字符串。

* **Web 服务 (`database.py`)**:
```python
# 必须使用 asyncpg
DATABASE_URL = "postgresql+asyncpg://postgresuser:password@localhost:5432/movie_db"

```


* **Spark 任务 (`spark_runner.py`)**:
```python
# 必须使用 psycopg2
DATABASE_URL = "postgresql+psycopg2://postgresuser:password@localhost:5432/movie_db"

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

1. **同步数据库表结构** (创建用户表、收藏表、推荐表等):
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


4. **生成模拟数据** (可选，生成虚拟用户和评分用于测试推荐):
```bash
python init/seed_ratings.py

```


5. **生成图表缓存** (用于后台数据总览展示):
```bash
python init/generate_charts.py

```



---

## ⚡ 6. 运行推荐算法

### 6.1 离线推荐 (Spark ALS)

使用 PySpark 进行大规模矩阵计算。**建议在 Linux 环境下运行此步骤**。

```bash
python spark_runner.py

```

**预期输出：**

* 显示 `🚀 [Step 1] 初始化 Spark...`
* 最终显示 `✅ 成功！已保存 XX 条推荐记录。`

### 6.2 实时推荐模型训练

生成 Item-Based CF 所需的相似度矩阵（基于内存）。

* 登录后台 -> **数据总览** -> 点击 **“立即重新训练”**。
* 或者直接在代码中调用 `services.recommendation_service.train_model()`。

---

## 🚀 7. 启动 Web 服务

一切准备就绪，启动主程序：

```bash
python main.py

```

* **访问地址**: [http://localhost:61081](https://www.google.com/search?q=http://localhost:61081)
* **后台管理**: 登录后点击右上角头像 -> “后台管理”。

---

## 🕷️ 附录：数据爬虫 (Optional)

如果需要补充票房数据或豆瓣评分，可运行爬虫脚本：

1. **爬取票房数据** (Box Office Mojo):
```bash
python crawlers/box_office_crawler.py

```


2. **爬取豆瓣 Top 250**:
*(注意：需在代码中配置 Cookie)*
```bash
python crawlers/top250_crawler.py

```



---

## ❓ 常见问题 (Troubleshooting)

| 问题现象 | 解决方案 |
| --- | --- |
| **Spark 报错 `class file version 61.0**` | Java 版本过低。Spark 新版需要 Java 17。请安装 JDK 17 并通过 `update-alternatives` 切换默认版本。 |
| **Spark 报错 `winutils**` | Windows 环境常见错误。建议在 WSL 或 Linux 虚拟机中运行 `spark_runner.py`。 |
| **NLP 模型加载失败** | 检查 `ml_models` 目录路径是否正确，且已安装 `torch` 库。 |
| **首页图片不显示** | 确保已正确配置 TMDB API Key (`services/tmdb_service.py`)，并点击后台的 **"影视管理" -> "重建缓存"**。 |
| **图表无法加载** | 请运行 `python init/generate_charts.py` 生成静态 HTML 文件。 |