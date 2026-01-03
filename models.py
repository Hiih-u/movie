from datetime import datetime

from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, DateTime
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
    primaryTitle = Column(String)
    startYear = Column(Integer)
    runtimeMinutes = Column(Integer)
    genres = Column(String)

    # 把评分表的数据也搬过来
    averageRating = Column(Float)
    numVotes = Column(Integer, index=True)  # 加索引，排序飞快

# 6. 用户收藏表
class UserFavorite(Base):
    __tablename__ = "user_favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    tconst = Column(String, ForeignKey("title_basics.tconst"), index=True)
    created_at = Column(DateTime, default=datetime.now)

# 7. 用户个人评分表
class UserRating(Base):
    __tablename__ = "user_personal_ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    tconst = Column(String, ForeignKey("title_basics.tconst"), index=True)
    rating = Column(Float)  # 用户打分 (e.g. 1.0 - 10.0)
    created_at = Column(DateTime, default=datetime.now)

