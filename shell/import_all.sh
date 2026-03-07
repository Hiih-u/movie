#!/bin/bash

# 设置变量
DB_USER="postgresuser"
DB_NAME="movie_db"
CONTAINER_NAME="postgres"
export PGPASSWORD="password"

# 定义按顺序排列的文件列表
FILES=(
    "users.sql"
    "title_basics.sql"
    "name_basics.sql"
    "title_ratings.sql"
    "title_crew.sql"
    "title_episode.sql"
    "movie_box_office.sql"
    "user_favorites.sql"
    "user_personal_ratings.sql"
    "movie_summary.sql"
    "douban_top250.sql"
    "spark_recommendations.sql"
)

echo "开始按顺序导入数据库..."

for FILE in "${FILES[@]}"; do
    if [ -f "$FILE" ]; then
        echo "-----------------------------------------------"
        echo "正在导入: $FILE ..."
        # 使用 -i (interactive) 模式通过管道传输 SQL
        cat "$FILE" | docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME
        if [ $? -eq 0 ]; then
            echo "成功: $FILE"
        else
            echo "错误: $FILE 导入失败，请检查数据或格式。"
        fi
    else
        echo "跳过: 未找到文件 $FILE"
    fi
done

echo "所有导入任务已完成！"
