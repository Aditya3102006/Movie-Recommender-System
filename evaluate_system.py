import pickle
import sqlite3
import time

print("[+] Loading Recommendation Model Data...")
with open('movies_dict.pkl', 'rb') as f:
    movies_dict = pickle.load(f)

with open('similarity.pkl', 'rb') as f:
    similarity = pickle.load(f)

# Convert dictionary to list of records
titles = list(movies_dict['title'].values())
movie_ids = list(movies_dict['movie_id'].values())

def get_recommendations(movie_title, top_n=5):
    try:
        # Find index case-insensitively
        idx = -1
        for i, t in enumerate(titles):
            if t.lower() == movie_title.lower():
                idx = i
                break
        if idx == -1:
            return []
        
        distances = similarity[idx]
        movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:top_n+1]
        results = []
        for i, score in movie_list:
            results.append({
                "title": titles[i],
                "similarity_score": round(float(score), 4)
            })
        return results
    except Exception as e:
        print(f"Error: {e}")
        return []

seed_movies = [
    {"movie": "Avatar", "genre": "Sci-Fi / Action / Adventure"},
    {"movie": "The Dark Knight", "genre": "Superhero / Crime / Action"},
    {"movie": "Toy Story", "genre": "Animation / Family / Comedy"},
    {"movie": "The Conjuring", "genre": "Horror / Supernatural"},
    {"movie": "The Notebook", "genre": "Romance / Drama"}
]

print("\n" + "="*80)
print("1. RECOMMENDATION RELEVANCE TEST CASES")
print("="*80)

for item in seed_movies:
    movie = item["movie"]
    recs = get_recommendations(movie)
    print(f"\nSeed Movie: {movie} ({item['genre']})")
    for rank, r in enumerate(recs, 1):
        print(f"  {rank}. {r['title']} (Cosine Similarity: {r['similarity_score']})")

print("\n" + "="*80)
print("2. SQL VALIDATION TESTS & QUERY RUNTIME BENCHMARK")
print("="*80)

conn = sqlite3.connect("tmdb_movies.db")
cursor = conn.cursor()

queries = [
    {
        "name": "Window Function: Top-3 Box Office Records Partitioned by Genre",
        "sql": """
        WITH ranked_genre_movies AS (
            SELECT 
                g.genre_name,
                m.title,
                m.revenue,
                ROW_NUMBER() OVER (PARTITION BY g.genre_name ORDER BY m.revenue DESC) AS genre_rank
            FROM movies m
            INNER JOIN movie_genres g ON m.movie_id = g.movie_id
            WHERE m.revenue > 0
        )
        SELECT genre_name, genre_rank, title, ROUND(revenue / 1000000.0, 1) || ' $M'
        FROM ranked_genre_movies
        WHERE genre_rank <= 3 AND genre_name IN ('Action', 'Science Fiction', 'Drama', 'Comedy')
        ORDER BY genre_name, genre_rank;
        """
    },
    {
        "name": "CTE & ROI Analysis: Director Profitability and Rating",
        "sql": """
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
            ROUND(total_revenue / 1000000.0, 1) || ' $M' AS total_revenue_m,
            ROUND(((total_revenue - total_budget) * 100.0 / total_budget), 1) || '%' AS net_roi_pct,
            avg_rating
        FROM director_financials
        ORDER BY (total_revenue - total_budget) DESC
        LIMIT 5;
        """
    },
    {
        "name": "Multi-Table Joins: Top Actor-Director Duos by Gross Revenue",
        "sql": """
        SELECT 
            d.director_name,
            c.actor_name,
            COUNT(m.movie_id) AS shared_projects,
            ROUND(SUM(m.revenue) / 1000000.0, 1) || ' $M' AS combined_revenue_m,
            ROUND(AVG(m.vote_average), 2) AS avg_critic_score
        FROM movies m
        INNER JOIN movie_directors d ON m.movie_id = d.movie_id
        INNER JOIN movie_cast c ON m.movie_id = c.movie_id AND c.cast_order = 0
        WHERE m.revenue > 0
        GROUP BY d.director_name, c.actor_name
        HAVING COUNT(m.movie_id) >= 3
        ORDER BY SUM(m.revenue) DESC
        LIMIT 5;
        """
    },
    {
        "name": "Rolling Window Aggregation: 3-Year Moving Average Industry Box Office",
        "sql": """
        WITH yearly_stats AS (
            SELECT 
                CAST(release_year AS INT) AS rel_year,
                COUNT(movie_id) AS release_count,
                ROUND(AVG(revenue) / 1000000.0, 2) AS avg_revenue_m
            FROM movies
            WHERE release_year BETWEEN 2000 AND 2015 AND revenue > 0
            GROUP BY CAST(release_year AS INT)
        )
        SELECT 
            rel_year,
            release_count,
            avg_revenue_m || ' $M',
            ROUND(AVG(avg_revenue_m) OVER (ORDER BY rel_year ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) || ' $M' AS rolling_3yr_avg_revenue
        FROM yearly_stats
        ORDER BY rel_year DESC;
        """
    }
]

for q in queries:
    cursor.execute(q["sql"]).fetchall()
    times = []
    for _ in range(10):
        start = time.perf_counter()
        res = cursor.execute(q["sql"]).fetchall()
        end = time.perf_counter()
        times.append((end - start) * 1000.0)
    
    avg_time = round(sum(times) / len(times), 2)
    min_time = round(min(times), 2)
    print(f"\n[Query] {q['name']}")
    print(f"  Rows Returned: {len(res)} | Avg Runtime: {avg_time} ms | Min Runtime: {min_time} ms")
    print("  Sample Rows:")
    for row in res[:3]:
        print(f"    {row}")

print("\n[DONE] Evaluation completed successfully.")
