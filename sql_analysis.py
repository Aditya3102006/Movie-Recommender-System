"""
TMDB 5000 Relational Database & SQL Analytics Module
---------------------------------------------------
This script parses the TMDB movie and credit datasets into a normalized 
relational SQLite database and executes advanced SQL analytical queries 
using Joins, CTEs, Aggregations, and Window Functions.
"""

import sqlite3
import pandas as pd
import json
import ast
import os
import sys

# Ensure UTF-8 output encoding for terminals
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB_PATH = "tmdb_movies.db"
MOVIES_CSV = "tmdb_5000_movies.csv"
CREDITS_CSV = "tmdb_5000_credits.csv"

def safe_parse_json(val):
    if pd.isna(val) or not val:
        return []
    try:
        return ast.literal_eval(val)
    except Exception:
        try:
            return json.loads(val)
        except Exception:
            return []

def build_relational_database():
    print("[+] Loading raw CSV data...")
    movies_df = pd.read_csv(MOVIES_CSV)
    credits_df = pd.read_csv(CREDITS_CSV)

    print("[+] Normalizing tables for relational SQLite database...")
    
    # Connect to SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Drop existing tables if re-running
    cursor.executescript("""
        DROP TABLE IF EXISTS movie_genres;
        DROP TABLE IF EXISTS movie_cast;
        DROP TABLE IF EXISTS movie_directors;
        DROP TABLE IF EXISTS movies;
    """)

    # 1. Main Movies Table
    movies_clean = movies_df[[
        'id', 'title', 'budget', 'revenue', 'popularity', 
        'vote_average', 'vote_count', 'release_date', 'runtime', 'original_language'
    ]].copy()
    movies_clean.rename(columns={'id': 'movie_id'}, inplace=True)
    movies_clean['release_year'] = pd.to_datetime(movies_clean['release_date'], errors='coerce').dt.year

    movies_clean.to_sql('movies', conn, if_exists='replace', index=False)

    # 2. Movie Genres Table (Normalized 1-to-many)
    genre_records = []
    for _, row in movies_df.iterrows():
        movie_id = row['id']
        genres = safe_parse_json(row['genres'])
        for g in genres:
            if isinstance(g, dict) and 'name' in g:
                genre_records.append((movie_id, g['name']))

    genre_df = pd.DataFrame(genre_records, columns=['movie_id', 'genre_name'])
    genre_df.to_sql('movie_genres', conn, if_exists='replace', index=False)

    # 3. Movie Cast Table (Top 5 cast members per movie)
    cast_records = []
    for _, row in credits_df.iterrows():
        movie_id = row['movie_id']
        cast_list = safe_parse_json(row['cast'])
        for c in cast_list[:5]: # Top 5 actors
            if isinstance(c, dict):
                cast_records.append((
                    movie_id, 
                    c.get('name', ''), 
                    c.get('character', ''), 
                    c.get('order', 0)
                ))

    cast_table = pd.DataFrame(cast_records, columns=['movie_id', 'actor_name', 'character_name', 'cast_order'])
    cast_table.to_sql('movie_cast', conn, if_exists='replace', index=False)

    # 4. Movie Directors Table
    director_records = []
    for _, row in credits_df.iterrows():
        movie_id = row['movie_id']
        crew_list = safe_parse_json(row['crew'])
        for member in crew_list:
            if isinstance(member, dict) and member.get('job') == 'Director':
                director_records.append((movie_id, member.get('name', '')))

    directors_df = pd.DataFrame(director_records, columns=['movie_id', 'director_name'])
    directors_df.to_sql('movie_directors', conn, if_exists='replace', index=False)

    # Create Indexes for Query Performance
    cursor.executescript("""
        CREATE INDEX IF NOT EXISTS idx_movies_id ON movies(movie_id);
        CREATE INDEX IF NOT EXISTS idx_genres_id ON movie_genres(movie_id);
        CREATE INDEX IF NOT EXISTS idx_cast_id ON movie_cast(movie_id);
        CREATE INDEX IF NOT EXISTS idx_directors_id ON movie_directors(movie_id);
    """)

    conn.commit()
    print("[✓] SQLite database created successfully at:", DB_PATH)
    return conn

def run_sql_queries(conn):
    print("\n" + "="*80)
    print("EXECUTING ADVANCED SQL ANALYTICAL QUERIES (Joins, CTEs, Window Functions)")
    print("="*80)

    # Query 1: Window Functions (ROW_NUMBER & DENSE_RANK partitioned by genre)
    q1 = """
    -- Query 1: Top 3 Highest-Grossing Movies per Genre using Window Functions
    WITH ranked_genre_movies AS (
        SELECT 
            g.genre_name,
            m.title,
            m.budget,
            m.revenue,
            ROUND(m.revenue / 1000000.0, 2) AS revenue_millions,
            ROW_NUMBER() OVER (
                PARTITION BY g.genre_name 
                ORDER BY m.revenue DESC
            ) AS genre_rank
        FROM movies m
        INNER JOIN movie_genres g ON m.movie_id = g.movie_id
        WHERE m.revenue > 0
    )
    SELECT 
        genre_name,
        genre_rank,
        title,
        revenue_millions || ' $M' AS box_office
    FROM ranked_genre_movies
    WHERE genre_rank <= 3 AND genre_name IN ('Action', 'Science Fiction', 'Drama', 'Comedy')
    ORDER BY genre_name, genre_rank;
    """
    print("\n--- [1] WINDOW FUNCTION: Top-3 Box Office Records Partitioned by Genre ---")
    df1 = pd.read_sql_query(q1, conn)
    print(df1.to_string(index=False))

    # Query 2: CTEs + Financial ROI Analysis
    q2 = """
    -- Query 2: Director Profitability & Return on Investment (ROI) via CTE
    WITH director_financials AS (
        SELECT 
            d.director_name,
            COUNT(DISTINCT m.movie_id) AS total_films,
            SUM(m.budget) AS total_budget,
            SUM(m.revenue) AS total_revenue,
            ROUND(AVG(m.vote_average), 2) AS avg_rating
        FROM movie_directors d
        INNER JOIN movies m ON d.movie_id = m.movie_id
        WHERE m.budget > 10000000 AND m.revenue > 0
        GROUP BY d.director_name
        HAVING COUNT(DISTINCT m.movie_id) >= 4
    )
    SELECT 
        director_name,
        total_films,
        ROUND(total_revenue / 1000000.0, 1) || ' $M' AS total_box_office,
        ROUND(((total_revenue - total_budget) * 100.0 / total_budget), 1) || '%' AS net_roi_percentage,
        avg_rating
    FROM director_financials
    ORDER BY (total_revenue - total_budget) DESC
    LIMIT 8;
    """
    print("\n--- [2] CTE & ROI ANALYSIS: Top Directors by Commercial Return & Rating ---")
    df2 = pd.read_sql_query(q2, conn)
    print(df2.to_string(index=False))

    # Query 3: Multi-table Joins (Actor-Director Box Office Collaborations)
    q3 = """
    -- Query 3: High-Performing Actor-Director Partnerships (Multi-Table Joins & Aggregations)
    SELECT 
        d.director_name,
        c.actor_name,
        COUNT(m.movie_id) AS shared_projects,
        ROUND(SUM(m.revenue) / 1000000.0, 1) || ' $M' AS combined_gross_revenue,
        ROUND(AVG(m.vote_average), 2) AS avg_critic_score
    FROM movies m
    INNER JOIN movie_directors d ON m.movie_id = d.movie_id
    INNER JOIN movie_cast c ON m.movie_id = c.movie_id AND c.cast_order = 0  -- Lead actor
    WHERE m.revenue > 0
    GROUP BY d.director_name, c.actor_name
    HAVING COUNT(m.movie_id) >= 3
    ORDER BY SUM(m.revenue) DESC
    LIMIT 8;
    """
    print("\n--- [3] MULTI-TABLE JOINS: Top Actor-Director Duos by Total Box Office ---")
    df3 = pd.read_sql_query(q3, conn)
    print(df3.to_string(index=False))

    # Query 4: Rolling Window Aggregation (3-Year Moving Average)
    q4 = """
    -- Query 4: 3-Year Rolling Average Revenue Trend Analysis
    WITH yearly_stats AS (
        SELECT 
            CAST(release_year AS INT) AS rel_year,
            COUNT(movie_id) AS release_count,
            ROUND(AVG(budget) / 1000000.0, 2) AS avg_budget_m,
            ROUND(AVG(revenue) / 1000000.0, 2) AS avg_revenue_m
        FROM movies
        WHERE release_year BETWEEN 2000 AND 2015 AND revenue > 0
        GROUP BY CAST(release_year AS INT)
    )
    SELECT 
        rel_year,
        release_count,
        avg_revenue_m || ' $M' AS avg_yearly_rev,
        ROUND(
            AVG(avg_revenue_m) OVER (
                ORDER BY rel_year 
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ), 2
        ) || ' $M' AS rolling_3yr_avg_revenue
    FROM yearly_stats
    ORDER BY rel_year DESC;
    """
    print("\n--- [4] ROLLING WINDOW AGGREGATE: 3-Year Moving Average Industry Box Office Trends ---")
    df4 = pd.read_sql_query(q4, conn)
    print(df4.to_string(index=False))

if __name__ == "__main__":
    connection = build_relational_database()
    run_sql_queries(connection)
    connection.close()
