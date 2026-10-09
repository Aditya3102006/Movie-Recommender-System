-- ==============================================================================
-- TMDB 5000 Relational SQL Analytics Script
-- Database Engine: SQLite / PostgreSQL compatible
-- Author: Aditya Yadav
-- Key Techniques: Multi-table Joins, CTEs, Window Functions, Aggregate Framing
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. WINDOW FUNCTION: Top 3 Highest-Grossing Movies per Genre
-- Concepts: ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)
-- ------------------------------------------------------------------------------
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
WHERE genre_rank <= 3
ORDER BY genre_name, genre_rank;


-- ------------------------------------------------------------------------------
-- 2. CTE & FINANCIAL ROI: Director Profitability & Commercial Return
-- Concepts: Common Table Expressions (WITH), GROUP BY, HAVING, Multi-table JOIN
-- ------------------------------------------------------------------------------
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
LIMIT 10;


-- ------------------------------------------------------------------------------
-- 3. MULTI-TABLE RELATIONAL JOINS: Actor-Director Partnerships Box Office
-- Concepts: Multi-table INNER JOINs, Filter on Lead Actors (cast_order = 0), Aggregations
-- ------------------------------------------------------------------------------
SELECT 
    d.director_name,
    c.actor_name,
    COUNT(m.movie_id) AS shared_projects,
    ROUND(SUM(m.revenue) / 1000000.0, 1) || ' $M' AS combined_gross_revenue,
    ROUND(AVG(m.vote_average), 2) AS avg_critic_score
FROM movies m
INNER JOIN movie_directors d ON m.movie_id = d.movie_id
INNER JOIN movie_cast c ON m.movie_id = c.movie_id AND c.cast_order = 0
WHERE m.revenue > 0
GROUP BY d.director_name, c.actor_name
HAVING COUNT(m.movie_id) >= 3
ORDER BY SUM(m.revenue) DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- 4. ROLLING WINDOW AGGREGATE: 3-Year Moving Average Box Office Trend
-- Concepts: Window Functions with Frame Specification (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
-- ------------------------------------------------------------------------------
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
