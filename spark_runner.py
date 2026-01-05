# import sys
# import os
# import pandas as pd
# from sqlalchemy import create_engine, text
# from pyspark.sql import SparkSession
# from pyspark.ml.recommendation import ALS
# from pyspark.sql.functions import col, explode
#
# # --- 配置数据库连接 ---
# DATABASE_URL = "postgresql+psycopg2://postgresuser:password@localhost:5432/movie_db"
#
# def run_spark_job():
#     print("🚀 [Step 1] 初始化 Spark 引擎...")
#     # 启动 Spark Session (配置内存使用)
#     spark = SparkSession.builder \
#         .appName("MovieRec_ALS_Engine") \
#         .config("spark.driver.memory", "2g") \
#         .master("local[*]") \
#         .getOrCreate()
#
#     spark.sparkContext.setLogLevel("ERROR")  # 减少日志干扰
#
#     print("📥 [Step 2] 从数据库加载评分数据...")
#     # 使用 Pandas 读取数据库 (适合千万级以下数据，超大数据需用 JDBC)
#     engine = create_engine(DATABASE_URL)
#
#     # 读取用户评分表 (user_id, tconst, rating)
#     # 注意：ALS 需要 user_id 和 item_id 都是数字！
#     # 如果你的 tconst 是 'tt001' 这种字符串，我们需要用 StringIndexer 转成数字，
#     # 或者为了简单，这里假设我们只用 user_id (int) 和 rating
#     query = "SELECT user_id, tconst, rating FROM user_personal_ratings"
#     pdf_ratings = pd.read_sql(query, engine)
#
#     if pdf_ratings.empty:
#         print("❌ 数据库没有评分数据，请先生成数据 (seed_ratings.py)")
#         return
#
#     # Pandas DF -> Spark DF
#     ratings_df = spark.createDataFrame(pdf_ratings)
#
#     # --- 关键处理：因为 tconst 是字符串，ALS 只能吃数字 ---
#     # 我们需要给 tconst 编个号 (String -> Index)
#     from pyspark.ml.feature import StringIndexer
#
#     indexer = StringIndexer(inputCol="tconst", outputCol="movie_id_int")
#     indexer_model = indexer.fit(ratings_df)
#     ratings_df = indexer_model.transform(ratings_df)
#
#     print("🧠 [Step 3] 运行 ALS 协同过滤算法...")
#     # ALS 参数配置
#     als = ALS(
#         maxIter=10,
#         regParam=0.1,
#         userCol="user_id",
#         itemCol="movie_id_int",
#         ratingCol="rating",
#         coldStartStrategy="drop",
#         nonnegative=True
#     )
#
#     model = als.fit(ratings_df)
#
#     print("🔮 [Step 4] 为所有用户生成 Top 10 推荐...")
#     # 给每个人推荐 10 部
#     user_recs = model.recommendForAllUsers(10)
#
#     # 结果格式处理：将数组炸开 (Explode)
#     # 原始: [User: 1, Recs: [(Movie: 101, Score: 4.5), ...]]
#     # 目标: User: 1, Movie: 101, Score: 4.5
#     recs_exploded = user_recs.select(
#         col("user_id"),
#         explode("recommendations").alias("rec")
#     ).select(
#         col("user_id"),
#         col("rec.movie_id_int"),
#         col("rec.rating").alias("score")
#     )
#
#     # --- 将数字 ID 转回 tconst 字符串 ---
#     # 利用之前的 indexer 逆向转换
#     from pyspark.ml.feature import IndexToString
#     converter = IndexToString(inputCol="movie_id_int", outputCol="tconst", labels=indexer_model.labels)
#     final_recs = converter.transform(recs_exploded).select("user_id", "tconst", "score")
#
#     print("💾 [Step 5] 结果存回数据库 (spark_recommendations 表)...")
#     # Spark DF -> Pandas DF
#     result_pdf = final_recs.toPandas()
#
#     # 写入数据库 (先清空旧结果，再写入新结果)
#     with engine.connect() as conn:
#         conn.execute(text("TRUNCATE TABLE spark_recommendations"))  # 清空
#         conn.commit()
#
#     # 批量写入
#     result_pdf.to_sql('spark_recommendations', engine, if_exists='append', index=False)
#
#     print(f"✅ 成功！已保存 {len(result_pdf)} 条推荐记录。")
#     spark.stop()
#
#
# if __name__ == "__main__":
#     run_spark_job()