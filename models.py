from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey
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
    hashed_password = Column(String)  # 存加密后的乱码


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