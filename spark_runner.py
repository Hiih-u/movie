import os
import time
import pandas as pd
from sqlalchemy import create_engine, text
from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.feature import StringIndexer, IndexToString
from pyspark.sql.functions import col, explode

# --- 配置区 ---
DATABASE_URL = "postgresql+psycopg2://postgresuser:password@localhost:5432/movie_db"


def log(message):
    """自定义带时间戳的日志输出"""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")


def run_recommendation_pipeline():
    # 1. 初始化 Spark
    log("🚀 正在启动 Spark Session...")
    spark = SparkSession.builder \
        .appName("Movie_Recommendation_ALS_Offline") \
        .config("spark.driver.memory", "4g") \
        .master("local[*]") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    # 2. 数据摄取
    log("📥 从 PostgreSQL 提取评分数据...")
    engine = create_engine(DATABASE_URL)
    query = "SELECT user_id, tconst, rating FROM user_personal_ratings"
    pdf_ratings = pd.read_sql(query, engine)

    if pdf_ratings.empty:
        log("⚠️ 警告：评分数据集为空，流程终止。")
        return

    ratings_df = spark.createDataFrame(pdf_ratings)
    log(f"✅ 成功加载 {ratings_df.count()} 条评分记录。")

    # 3. 特征工程 (StringIndexer)
    log("正在进行特征编码 (tconst -> index)...")
    string_indexer = StringIndexer(inputCol="tconst", outputCol="movie_idx")
    indexer_model = string_indexer.fit(ratings_df)
    indexed_ratings = indexer_model.transform(ratings_df)

    # 4. 划分训练集与测试集 (80/20)
    # 这是计算 RMSE 的核心环节
    (training, test) = indexed_ratings.randomSplit([0.8, 0.2], seed=42)
    log(f"数据划分完成：训练集 {training.count()} 条，测试集 {test.count()} 条。")

    # 5. 模型训练
    log("正在训练 ALS 协同过滤模型...")
    als = ALS(
        rank=4,  # 增加一点维度提升拟合能力
        maxIter=15,
        regParam=0.5,
        userCol="user_id",
        itemCol="movie_idx",
        ratingCol="rating",
        coldStartStrategy="drop",
        nonnegative=True
    )
    model = als.fit(training)
    log("模型拟合完成。")

    # 6. 模型评估 (RMSE)
    log("正在计算模型评估指标 (RMSE)...")
    predictions = model.transform(test)
    evaluator = RegressionEvaluator(
        metricName="rmse",
        labelCol="rating",
        predictionCol="prediction"
    )
    rmse = evaluator.evaluate(predictions)

    # 均方根误差公式：$RMSE = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2}$
    log(f"当前模型 RMSE = {rmse:.4f}")

    if rmse > 1.2:
        log("注意：RMSE 指标偏高，建议调整 rank 或 regParam 参数，或检查原始数据噪声。")
    else:
        log("提示：模型性能表现良好。")

    # 7. 生成全局推荐
    log("🎯 正在为所有用户生成 Top-10 推荐清单...")
    user_recs = model.recommendForAllUsers(10)

    # 8. 逆向还原索引与数据平铺
    log("🔄 正在还原影视 ID 并格式化结果...")
    recs_exploded = user_recs.select(
        col("user_id"),
        explode("recommendations").alias("rec")
    ).select(
        col("user_id"),
        col("rec.movie_idx").alias("movie_idx"),
        col("rec.rating").alias("score")
    )

    id_converter = IndexToString(
        inputCol="movie_idx",
        outputCol="tconst",
        labels=indexer_model.labels
    )
    final_recommendations = id_converter.transform(recs_exploded).select("user_id", "tconst", "score")

    # 9. 结果入库
    log("💾 正在同步结果至数据库 (spark_recommendations)...")
    result_pdf = final_recommendations.toPandas()

    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE spark_recommendations"))
        conn.commit()

    result_pdf.to_sql('spark_recommendations', engine, if_exists='append', index=False)

    log(f"🏁 离线任务全部完成！已更新 {len(result_pdf)} 条个性化推荐记录。")
    spark.stop()


if __name__ == "__main__":
    run_recommendation_pipeline()