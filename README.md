# 🎬 Movie Recommender System & SQL Analytics Engine

A dual-capability Data Science & Machine Learning project featuring a **Content-Based Movie Recommendation Engine** (Streamlit, NLP, Cosine Similarity) and an **Advanced SQL Analytics Module** (SQLite, CTEs, Window Functions, Multi-Table Joins) built on the TMDB 5000 dataset.

---

## 🌟 Key Features

### 1. 🤖 Content-Based Recommendation Engine
- **Data Preprocessing & NLP Pipeline**: Extracted structured attributes from nested JSON metadata (genres, keywords, cast, and directors). Applied text normalization, entity binding, **Porter Stemming** (`NLTK`), and **CountVectorizer** (`max_features=5000`).
- **Vector Space & Similarity**: Constructed a 5,000-dimensional bag-of-words representation and computed a pairwise **Cosine Similarity matrix ($4,806 \times 4,806$)**.
- **Memory Optimization**: Reduced the serialized similarity matrix memory overhead by **50%** via `float32` precision downcasting.
- **Interactive UI**: Sleek dark glassmorphic **Streamlit** dashboard with real-time poster retrieval via the **TMDB REST API**.

### 2. 📊 Relational SQL Analytics Suite
- **Normalized Schema**: Converted semi-structured movie records into relational tables (`movies`, `movie_genres`, `movie_cast`, `movie_directors`) with indexed foreign keys in SQLite (`tmdb_movies.db`).
- **Advanced SQL Techniques**:
  - **Window Functions (`ROW_NUMBER()` / `DENSE_RANK()`)**: Partitioned box-office rankings across individual genres.
  - **Common Table Expressions (CTEs)**: Analyzed director Return on Investment (ROI) and commercial profitability thresholds.
  - **Multi-Table Relational Joins**: Identified highest-grossing lead actor & director partnerships.
  - **Rolling Window Aggregations**: Evaluated 3-year moving averages for industry budget and box office trends.

---

## 🏗️ Architecture & Workflow

```
       ┌────────────────────────────────────────────────────────┐
       │             TMDB 5000 Movies & Credits Data            │
       └───────────────────────────┬────────────────────────────┘
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ▼                                                   ▼
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│       NLP & ML Pipeline         │       │     Relational SQL Analytics    │
│  - JSON Extraction & Tokenizing │       │  - Relational Schema Mapping    │
│  - Porter Stemming (NLTK)       │       │  - SQLite Database Generation   │
│  - CountVectorizer (5,000 dims) │       │  - CTEs & ROI Aggregations      │
│  - Cosine Similarity Matrix     │       │  - Window Functions & Trends    │
└────────────────┬────────────────┘       └────────────────┬────────────────┘
                 ▼                                         ▼
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│     Streamlit Interactive App   │       │   Insightful Business Reports   │
│  - Real-time TMDB API Posters   │       │   (sql_analysis.py / .sql)      │
└─────────────────────────────────┘       └─────────────────────────────────┘
```

---

## 💻 SQL Query Highlights

### Top 3 Highest-Grossing Movies per Genre (Window Functions)
```sql
WITH ranked_genre_movies AS (
    SELECT 
        g.genre_name,
        m.title,
        m.revenue,
        ROW_NUMBER() OVER (
            PARTITION BY g.genre_name 
            ORDER BY m.revenue DESC
        ) AS genre_rank
    FROM movies m
    INNER JOIN movie_genres g ON m.movie_id = g.movie_id
    WHERE m.revenue > 0
)
SELECT genre_name, genre_rank, title, ROUND(revenue / 1000000.0, 2) || ' $M' AS box_office
FROM ranked_genre_movies
WHERE genre_rank <= 3;
```

### Director Commercial ROI Analysis (CTEs & Multi-Table Joins)
```sql
WITH director_financials AS (
    SELECT 
        d.director_name,
        COUNT(DISTINCT m.movie_id) AS total_films,
        SUM(m.budget) AS total_budget,
        SUM(m.revenue) AS total_revenue
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
    ROUND(((total_revenue - total_budget) * 100.0 / total_budget), 1) || '%' AS net_roi
FROM director_financials
ORDER BY (total_revenue - total_budget) DESC
LIMIT 10;
```

---

## 🛠️ Installation & Quickstart

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/movie-recommender-system.git
cd movie-recommender-system
```

### 2. Set Up Virtual Environment & Dependencies
```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate    # macOS / Linux
pip install -r requirements.txt
```

### 3. Run the SQL Analytics Suite
```bash
python sql_analysis.py
```

### 4. Launch the Streamlit Recommender Web App
```bash
streamlit run app.py
```

---

## 🚀 Deployment (Streamlit Community Cloud)

1. Push this repository to GitHub.
2. Log in to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Connect your repository and select `app.py` as the entry point.
4. Add your TMDB API Key under **Advanced Settings > Secrets**:
   ```toml
   tmdb_api_key = "your_tmdb_api_key_here"
   ```
5. Click **Deploy!**
