```bash
gunzip *.tsv.gz
```

```sql
-- ============================================
-- IMDb Dataset Full PostgreSQL Schema
-- ============================================

-- 1. name.basics.tsv
DROP TABLE IF EXISTS name_basics;
CREATE TABLE name_basics (
    nconst TEXT PRIMARY KEY,
    primaryName TEXT,
    birthYear INT,
    deathYear INT,
    primaryProfession TEXT,   -- comma-separated list
    knownForTitles TEXT       -- comma-separated list
);

-- 2. title.basics.tsv
DROP TABLE IF EXISTS title_basics;
CREATE TABLE title_basics (
    tconst TEXT PRIMARY KEY,
    titleType TEXT,
    primaryTitle TEXT,
    originalTitle TEXT,
    isAdult INT,
    startYear INT,
    endYear INT,
    runtimeMinutes INT,
    genres TEXT                -- comma-separated list
);

-- -- 3. title.akas.tsv
-- DROP TABLE IF EXISTS title_akas;
-- CREATE TABLE title_akas (
--     titleId TEXT,
--     ordering INT,
--     title TEXT,
--     region TEXT,
--     language TEXT,
--     types TEXT,                -- comma-separated list
--     attributes TEXT,           -- comma-separated list
--     isOriginalTitle INT
-- );

-- 4. title.crew.tsv
DROP TABLE IF EXISTS title_crew;
CREATE TABLE title_crew (
    tconst TEXT PRIMARY KEY,
    directors TEXT,            -- comma-separated list (nconst)
    writers TEXT               -- comma-separated list (nconst)
);

-- 5. title.episode.tsv
DROP TABLE IF EXISTS title_episode;
CREATE TABLE title_episode (
    tconst TEXT PRIMARY KEY,
    parentTconst TEXT,
    seasonNumber INT,
    episodeNumber INT
);

-- -- 6. title.principals.tsv
-- DROP TABLE IF EXISTS title_principals;
-- CREATE TABLE title_principals (
--     tconst TEXT,
--     ordering INT,
--     nconst TEXT,
--     category TEXT,
--     job TEXT,
--     characters TEXT
-- );

-- 7. title.ratings.tsv
DROP TABLE IF EXISTS title_ratings;
CREATE TABLE title_ratings (
    tconst TEXT PRIMARY KEY,
    averageRating NUMERIC(3,1),
    numVotes INT
);

-- ======================
-- 可选：加索引（导完数据后执行）
-- ======================

-- CREATE INDEX idx_episode_parent ON title_episode(parentTconst);
-- CREATE INDEX idx_basics_genres_gin ON title_basics USING GIN (genres gin_trgm_ops);
-- CREATE INDEX idx_ratings_votes ON title_ratings(numVotes);
```

```sql
PGPASSWORD=password psql -U postgresuser -h localhost -d movie_db

\COPY name_basics FROM '/home/wly/movie_data/name.basics.tsv'
WITH (FORMAT csv, DELIMITER E'\t', NULL '\N', HEADER true, QUOTE E'\b');

\COPY title_basics FROM '/home/wly/movie_data/title.basics.tsv'
WITH (FORMAT csv, DELIMITER E'\t', NULL '\N', HEADER true, QUOTE E'\b');

\COPY title_akas FROM '/home/wly/movie_data/title.akas.tsv'
WITH (FORMAT csv, DELIMITER E'\t', NULL '\N', HEADER true, QUOTE E'\b');

\COPY title_crew FROM '/home/wly/movie_data/title.crew.tsv'
WITH (FORMAT csv, DELIMITER E'\t', NULL '\N', HEADER true, QUOTE E'\b');

\COPY title_episode FROM '/home/wly/movie_data/title.episode.tsv'
WITH (FORMAT csv, DELIMITER E'\t', NULL '\N', HEADER true, QUOTE E'\b');

\COPY title_ratings FROM '/home/wly/movie_data/title.ratings.tsv'
WITH (FORMAT csv, DELIMITER E'\t', NULL '\N', HEADER true, QUOTE E'\b');
``