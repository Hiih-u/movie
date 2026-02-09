from datetime import datetime

from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


# 1. 电影基本信息表 (title_basics)
class TitleBasics(Base):
    __tablename__ = "title_basics"

    # Column("数据库里的列名", 类型, ...)
    tconst = Column("tconst", String, primary_key=True, index=True)
    titleType = Column("titletype", String)
    primaryTitle = Column("primarytitle", String)
    originalTitle = Column("originaltitle", String)

    # 之前修正的 isAdult
    isAdult = Column("isadult", Integer)

    startYear = Column("startyear", Integer)

    # 【本次修正】将 String 改为 Integer
    endYear = Column("endyear", Integer)

    runtimeMinutes = Column("runtimeminutes", Integer)
    genres = Column("genres", String)

    # 【新增】TMDB 相关字段
    poster_path = Column(String, nullable=True)  # 海报路径 (如 /example.jpg)
    backdrop_path = Column(String, nullable=True)  # 背景大图
    overview = Column(String, nullable=True)  # 剧情简介 (存中文)
    tmdb_id = Column(String, nullable=True)  # TMDB ID

    # 关联配置
    rating = relationship("TitleRatings", back_populates="movie", uselist=False)
    crew = relationship("TitleCrew", back_populates="movie", uselist=False)

# 2. 电影评分表 (title_ratings)
class TitleRatings(Base):
    __tablename__ = "title_ratings"

    tconst = Column("tconst", String, ForeignKey("title_basics.tconst"), primary_key=True)
    averageRating = Column("averagerating", Float)
    numVotes = Column("numvotes", Integer)

    movie = relationship("TitleBasics", back_populates="rating")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    # 身份角色
    role = Column(String, default="user")

    # 【新增】推荐算法所需的用户画像字段
    gender = Column(String, nullable=True)  # 性别: 'M', 'F'
    age = Column(Integer, nullable=True)  # 年龄
    occupation = Column(String, nullable=True)  # 职业

# 3. 演职人员表 (name_basics)
class NameBasics(Base):
    __tablename__ = "name_basics"

    # 对应数据库字段
    nconst = Column("nconst", String, primary_key=True, index=True)
    primaryName = Column("primaryname", String)
    birthYear = Column("birthyear", Integer)
    deathYear = Column("deathyear", Integer)
    primaryProfession = Column("primaryprofession", String)
    knownForTitles = Column("knownfortitles", String)


# 【新增】3. 剧组信息表 (title_crew)
class TitleCrew(Base):
    __tablename__ = "title_crew"

    # tconst 作为主键，同时也是外键指向 title_basics
    tconst = Column("tconst", String, ForeignKey("title_basics.tconst"), primary_key=True)

    # 导演和编剧通常是逗号分隔的字符串 (如 "nm00001,nm00002")
    directors = Column("directors", String)
    writers = Column("writers", String)

    # 关联回电影主表
    movie = relationship("TitleBasics", back_populates="crew")


# 【新增】4. 剧集信息表 (title_episode)
class TitleEpisode(Base):
    __tablename__ = "title_episode"

    # 根据你提供的表结构
    tconst = Column("tconst", String, primary_key=True)  # 这一集本身的编号
    parentTconst = Column("parenttconst", String, index=True) # 父级(剧集)编号
    seasonNumber = Column("seasonnumber", Integer)
    episodeNumber = Column("episodenumber", Integer)

    # 建立关联，方便查询时获取 剧集(Series) 的名称
    # 注意：这里假设 parentTconst 关联到 TitleBasics 的 tconst
    parent_series = relationship("TitleBasics", foreign_keys=[parentTconst], primaryjoin="TitleEpisode.parentTconst==TitleBasics.tconst", uselist=False)


# 【新增】首页高性能缓存表 (把电影信息和评分合二为一)
class MovieSummary(Base):
    __tablename__ = "movie_summary"

    tconst = Column(String, primary_key=True, index=True)
    titleType = Column(String, index=True)
    primaryTitle = Column(String)
    startYear = Column(Integer)
    runtimeMinutes = Column(Integer)
    genres = Column(String)

    # 把评分表的数据也搬过来
    averageRating = Column(Float)
    numVotes = Column(Integer, index=True)  # 加索引，排序飞快

    # 【新增】缓存海报，提高首页加载速度
    poster_path = Column(String, nullable=True)

# 6. 用户收藏表
class UserFavorite(Base):
    __tablename__ = "user_favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    tconst = Column(String, ForeignKey("title_basics.tconst"), index=True)
    created_at = Column(DateTime, default=datetime.now)

    # 【优化】添加联合唯一约束，物理层面防止重复收藏，且自动创建联合索引加速查询
    __table_args__ = (
        UniqueConstraint('user_id', 'tconst', name='uix_user_favorite'),
    )

# 7. 用户个人评分表
class UserRating(Base):
    __tablename__ = "user_personal_ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    tconst = Column(String, ForeignKey("title_basics.tconst"), index=True)
    rating = Column(Float)  # 用户打分 (e.g. 1.0 - 10.0)
    created_at = Column(DateTime, default=datetime.now)


class SparkRecommendation(Base):
    """
    存储 Spark 离线计算好的推荐结果
    """
    __tablename__ = "spark_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)  # 给谁推荐
    tconst = Column(String, index=True)    # 推荐了哪部电影
    score = Column(Float)                  # 推荐分数 (预测评分)
    algorithm = Column(String, default="ALS") # 算法名称，方便以后对比


class DoubanTop250(Base):
    """
    存储豆瓣 Top 250 榜单数据
    """
    __tablename__ = "douban_top250"

    id = Column(Integer, primary_key=True, index=True)
    rank = Column(Integer, index=True)  # 排名 (1-250)
    title = Column(String)  # 中文电影名
    douban_id = Column(String, unique=True, index=True)  # 豆瓣 ID (如 1292052)
    imdb_id = Column(String, index=True)  # IMDb ID (如 tt0111161)

    douban_score = Column(Float)

    created_at = Column(DateTime, default=datetime.now)