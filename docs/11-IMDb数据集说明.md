# IMDb 数据集说明

## 1. 概述

本项目以 **IMDb Non-Commercial Datasets** 作为核心数据底座。IMDb 数据集是由互联网电影数据库（Internet Movie Database）官方发布的、免费供非商业用途使用的影视行业权威数据，覆盖电影、电视剧、综艺、动画等全球范围内的影视作品及其评分、演职人员信息。

项目中直接使用了 IMDb 原始数据集中的 **5 张核心表**，并在此基础上叠加了项目自建的扩展表，共同构成完整的数据架构。

---

## 2. IMDb 原始数据集

### 2.1 title.basics（电影基本信息）

对应项目模型：`TitleBasics` → 表名 `title_basics`

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `tconst` | String (PK) | IMDb 唯一标识符，如 `tt0111161`（《肖申克的救赎》） |
| `titleType` | String | 作品类型：`movie`、`tvSeries`、`tvEpisode`、`tvMiniSeries`、`tvMovie`、`short` 等 |
| `primaryTitle` | String | 作品最常用名称（通常是英文） |
| `originalTitle` | String | 作品原始语言名称 |
| `isAdult` | Integer | 是否为成人内容（0 = 否，1 = 是） |
| `startYear` | Integer | 首映年份（电影）或首播年份（剧集） |
| `endYear` | Integer | 剧集结束年份（电影通常为 NULL） |
| `runtimeMinutes` | Integer | 片长（分钟） |
| `genres` | String | 类型标签，逗号分隔，如 `Drama,Crime`（最多 3 个） |

**项目扩展字段**：
- `poster_path`：TMDB 海报路径（如 `/example.jpg`）
- `backdrop_path`：TMDB 背景大图路径
- `overview`：中文剧情简介（由 TMDB API 回填）
- `tmdb_id`：TMDB 平台对应的 ID

**数据特点**：
- 全量数据可达 **1000 万+** 条记录，涵盖电影短片、电视剧集、真人秀等
- `genres` 字段为逗号分隔的复合类型，查询时需使用 `ILIKE` 模糊匹配
- `titleType` 决定作品的呈现形态，是分类过滤的核心依据

---

### 2.2 title.ratings（评分数据）

对应项目模型：`TitleRatings` → 表名 `title_ratings`

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `tconst` | String (PK, FK) | 关联 `title_basics.tconst` |
| `averageRating` | Float | 加权平均分（1.0 ~ 10.0） |
| `numVotes` | Integer | 参与评分的用户投票数 |

**数据特点**：
- 仅包含**至少有 1 票投票**的作品，远少于 `title_basics` 全量
- `averageRating` 为 IMDb 官方加权算法计算，非简单算术平均
- `numVotes` 是判断影片**知名度与可信度**的关键指标，项目中多处以此为质量门槛（如 `> 5000` 或 `> 10000`）

---

### 2.3 name.basics（演职人员信息）

对应项目模型：`NameBasics` → 表名 `name_basics`

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `nconst` | String (PK) | 人员唯一标识符，如 `nm0000206`（凯拉·奈特莉） |
| `primaryName` | String | 常用姓名 |
| `birthYear` | Integer | 出生年份 |
| `deathYear` | Integer | 去世年份（NULL 表示在世） |
| `primaryProfession` | String | 主要职业，逗号分隔，如 `actress,soundtrack,producer` |
| `knownForTitles` | String | 其最知名的 4 部作品 `tconst`，逗号分隔 |

**数据特点**：
- 覆盖演员、导演、编剧、制片人、配乐师等全影视行业从业者
- `knownForTitles` 可用于快速构建"明星代表作"列表
- 与 `title_crew`、`title_principals` 配合使用可还原完整的主创关系网络

---

### 2.4 title.crew（剧组信息）

对应项目模型：`TitleCrew` → 表名 `title_crew`

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `tconst` | String (PK, FK) | 关联 `title_basics.tconst` |
| `directors` | String | 导演 `nconst` 列表，逗号分隔 |
| `writers` | String | 编剧 `nconst` 列表，逗号分隔 |

**数据特点**：
- 每部电影/剧集仅有 **一条记录**，导演和编剧以逗号分隔存储
- 项目内通过 `split(',')` 拆解后关联 `NameBasics` 表解析为真实人名
- 部分作品（尤其老片或纪录片）可能导演/编剧字段为空

---

### 2.5 title.episode（剧集分集信息）

对应项目模型：`TitleEpisode` → 表名 `title_episode`

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `tconst` | String (PK) | 单集自身的唯一标识 |
| `parentTconst` | String (FK) | 所属剧集（Series）的 `tconst` |
| `seasonNumber` | Integer | 季数 |
| `episodeNumber` | Integer | 集数 |

**数据特点**：
- 仅适用于 `titleType = tvEpisode` 的条目
- `parentTconst` 关联到 `TitleBasics` 中 `titleType` 为 `tvSeries` 或 `tvMiniSeries` 的记录
- 可用于构建剧集的**季-集层级结构**，支持"按季浏览"或"追剧进度"功能

---

## 3. 项目扩展数据表

在 IMDb 原始数据基础上，项目自建了以下扩展表，用于支撑业务功能：

### 3.1 movie_summary（首页缓存表）

**设计目的**：解决首页高频查询下多表 JOIN 的性能瓶颈。

**字段组成**：
- 合并了 `title_basics` 的核心字段（`titleType`、`primaryTitle`、`startYear`、`runtimeMinutes`、`genres`）
- 合并了 `title_ratings` 的评分字段（`averageRating`、`numVotes`）
- 附加 `poster_path` 海报缓存

**特点**：
- 单表查询即可支撑首页卡片列表，避免 `title_basics` + `title_ratings` 的跨表 JOIN
- `numVotes` 加索引，支持按热度快速排序
- 由后台 ETL 任务或爬虫回填更新

---

### 3.2 user_favorites（用户收藏表）

记录用户的收藏行为，`tconst` 外键关联 `title_basics`。

**约束**：联合唯一索引 `(user_id, tconst)`，物理层面防止重复收藏。

---

### 3.3 user_personal_ratings（用户评分表）

用户自主评分记录，评分范围通常为 1.0 ~ 10.0。

是 **ALS 离线模型**和 **Item-Based 协同过滤模型**的核心输入数据源。

---

### 3.4 spark_recommendations（ALS 离线推荐结果）

存储 `spark_runner.py` 离线计算的全局 Top-10 推荐结果。

| 字段 | 说明 |
|------|------|
| `user_id` | 目标用户 |
| `tconst` | 推荐的电影 |
| `score` | ALS 模型预测的评分 |
| `algorithm` | 算法标识（默认 `ALS`，便于后续 A/B 测试扩展） |

---

### 3.5 douban_top250（豆瓣 Top 250 榜单）

由爬虫从豆瓣电影 Top 250 页面抓取，用于**中外评分对比**可视化。

| 字段 | 说明 |
|------|------|
| `rank` | 豆瓣排名（1-250） |
| `title` | 中文片名 |
| `douban_id` | 豆瓣 ID |
| `imdb_id` | 关联 IMDb 的 `tconst`（爬虫回填，用于精确关联对比） |
| `douban_score` | 豆瓣评分 |

---

### 3.6 movie_box_office（票房数据）

由爬虫抓取的商业票房数据，支撑"票房 vs 口碑"气泡图分析。

| 字段 | 说明 |
|------|------|
| `tconst` | 关联 IMDb |
| `box_office` | 票房金额（美元），`BigInteger` 防溢出 |
| `rank` | 票房排名 |
| `updated_at` | 数据更新时间 |

---

## 4. 数据关系总览

```
┌─────────────────┐
│   title_basics  │◄─────────┐
│  (IMDb 核心)     │          │
└────────┬────────┘          │
         │                    │
         │ tconst (PK/FK)     │
         │                    │
    ┌────┴────┬─────────┐    │
    │         │         │    │
    ▼         ▼         ▼    │
┌───────┐ ┌───────┐ ┌──────────────┐
│ratings│ │ crew  │ │   episode    │
└───────┘ └───────┘ └──────────────┘
    │                           │
    │              parentTconst │
    │                           ▼
┌─────────────────┐    ┌──────────────┐
│ name_basics     │    │ title_basics │
│ (人员信息)       │    │ (剧集母表)   │
└─────────────────┘    └──────────────┘

扩展表（业务层）
    │
    ├── movie_summary ──── 首页缓存（聚合 basics + ratings）
    ├── user_favorites ─── 用户收藏
    ├── user_personal_ratings ── 用户评分（推荐算法输入）
    ├── spark_recommendations ── ALS 离线推荐结果
    ├── douban_top250 ── 豆瓣榜单（爬虫）
    └── movie_box_office ── 票房数据（爬虫）
```

---

## 5. 数据来源与更新

### 5.1 官方数据源

- **来源**：IMDb Datasets（https://datasets.imdbws.com/）
- **更新频率**：每日更新（Daily Refresh）
- **格式**： gzip 压缩的 TSV（Tab-Separated Values）文件
- **授权**：非商业用途免费使用（Non-Commercial Licensing）

### 5.2 项目数据更新策略

| 数据类型 | 更新方式 | 频率建议 |
|----------|----------|----------|
| IMDb 原始数据集 | ETL 脚本下载 → 清洗 → 批量导入 PostgreSQL | 每月/每季度 |
| TMDB 海报/简介 | 实时 API 调用（`tmdb_service.py`），本地缓存 | 按需 |
| 豆瓣 Top 250 | 爬虫定时抓取 | 每周 |
| 票房数据 | 爬虫定时抓取 | 每日 |
| 用户评分/收藏 | 用户实时操作写入 | 实时 |
| ALS 离线推荐 | `spark_runner.py` 定时调度 | 每天/每 6 小时 |
| Item-Based 模型 | `train_model()` 后台触发 | 用户活跃后触发或定时 |

---

## 6. 使用建议

1. **索引优化**：`title_basics.tconst`、`title_ratings.numVotes`、`title_episode.parentTconst` 是高频查询字段，确保已建立索引
2. **genre 查询技巧**：由于 `genres` 是逗号分隔字符串，模糊匹配（`ILIKE '%Action%'`）无法利用 B-Tree 索引；若 genre 查询成为瓶颈，建议拆分为独立的 `title_genres` 多对多关联表
3. **冷数据归档**：IMDb 数据集包含大量短片、试验性作品、低投票作品，可根据 `numVotes` 阈值（如 > 100）建立视图或物化视图，减少前端无关数据
4. **TMDB 回填**：`poster_path`、`overview` 等字段依赖 TMDB API，注意 API 调用频率限制（通常 40 requests / 10 seconds），建议本地缓存+异步队列
5. **数据一致性**：`movie_summary` 为聚合缓存表，当 IMDb 原始数据更新后，需同步重建该表，避免缓存与源数据不一致
