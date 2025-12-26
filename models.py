from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from database import Base


# 1. 电影基本信息表 (title_basics)
class TitleBasics(Base):
    __tablename__ = "title_basics"  # 确保表名和数据库一致

    # Column("数据库里的列名", 类型, ...)
    # 这里的第一个参数必须完全匹配你刚才发的表结构截图
    tconst = Column("tconst", String, primary_key=True, index=True)
    titleType = Column("titletype", String)  # 假设数据库里是小写
    primaryTitle = Column("primarytitle", String)  # 假设数据库里是小写
    originalTitle = Column("originaltitle", String)
    isAdult = Column("isadult", Boolean)
    startYear = Column("startyear", Integer)
    endYear = Column("endyear", String)
    runtimeMinutes = Column("runtimeminutes", Integer)
    genres = Column("genres", String)

    # 关联配置
    rating = relationship("TitleRatings", back_populates="movie", uselist=False)


# 2. 电影评分表 (title_ratings)
class TitleRatings(Base):
    __tablename__ = "title_ratings"

    # 注意：你的截图显示 averagerating 是 numeric 类型，numvotes 是 int4
    tconst = Column("tconst", String, ForeignKey("title_basics.tconst"), primary_key=True)

    # 关键修改：显式指定数据库列名为全小写的 "averagerating"
    averageRating = Column("averagerating", Float)

    # 关键修改：显式指定数据库列名为全小写的 "numvotes"
    numVotes = Column("numvotes", Integer)

    movie = relationship("TitleBasics", back_populates="rating")