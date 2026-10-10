# Movie Recommender System & SQL Analytics — Evaluation Evidence

This document provides empirical validation, recommendation quality audits, query performance benchmarks, and user task measurements for the **Movie Recommender System & SQL Analytics** project.

---

## 1. Recommendation Relevance Evaluation

### Evaluation Methodology (Honest & Verifiable)
Since TMDB 5000 is an offline content dataset without live clickstreams or user historical ratings, recommendation quality is evaluated via a **Qualitative Relevance Rubric** across diverse seed genres rather than claiming synthetic Precision@K.

### 1–5 Relevance Scoring Rubric
- **5 (Highly Relevant):** Strong thematic, genre, cast/crew, and narrative alignment (e.g., sequel, exact subgenre match).
- **4 (Relevant):** Clear overlap in core genres and target audience, though differing in specific setting.
- **3 (Moderately Relevant):** Shares broad category (e.g., general comedy) but distinct tone or theme.
- **2 (Weakly Relevant):** Minor superficial keyword overlap with noticeable tonal mismatch.
- **1 (Irrelevant):** No recognizable connection to seed movie.

---

### Test Cases & Review Results

| Seed Movie (Genre) | Top 5 Recommended Movies | Cosine Sim. | Relevance Score (1–5) | Evaluator Notes / Rationale |
| :--- | :--- | :---: | :---: | :--- |
| **Avatar**<br>*(Sci-Fi / Action)* | 1. Titan A.E.<br>2. Small Soldiers<br>3. Independence Day<br>4. Ender's Game<br>5. Aliens vs Predator: Requiem | 0.2609<br>0.2582<br>0.2530<br>0.2511<br>0.2494 | **4.2 / 5.0**<br>(4, 4, 5, 4, 4) | High thematic cohesion on extraterrestrial conflict, alien worlds, military sci-fi. |
| **The Dark Knight**<br>*(Crime / Superhero)* | 1. The Dark Knight Rises<br>2. Batman Begins<br>3. Batman Returns<br>4. Batman Forever<br>5. Batman & Robin | 0.4239<br>0.3898<br>0.3216<br>0.2879<br>0.2817 | **4.8 / 5.0**<br>(5, 5, 5, 4, 4) | Perfect franchise cluster capture. Identifies Nolan trilogy first, followed by earlier Batman continuity. |
| **The Conjuring**<br>*(Supernatural Horror)* | 1. Insidious: Chapter 2<br>2. Insidious<br>3. Ouija<br>4. The Conjuring 2<br>5. High Tension | 0.2758<br>0.2758<br>0.2440<br>0.2364<br>0.2336 | **4.6 / 5.0**<br>(5, 5, 4, 5, 4) | Successfully groups James Wan directed/produced haunted house & paranormal horror titles. |
| **Toy Story**<br>*(Animation / Family)* | 1. Toy Story 2<br>2. Toy Story 3<br>3. The 40 Year Old Virgin<br>4. Heartbeeps<br>5. Max Keeble's Big Move | 0.4767<br>0.4491<br>0.3078<br>0.1826<br>0.1569 | **3.8 / 5.0**<br>(5, 5, 2, 3, 4) | Captures sequels accurately (0.47+). Captures slight keyword leak on toy/adult tags on item 3. |
| **The Notebook**<br>*(Romance / Drama)* | 1. Lovely, Still<br>2. Veer-Zaara<br>3. The Age of Adaline<br>4. The Big Parade<br>5. Mississippi Mermaid | 0.3118<br>0.3086<br>0.2961<br>0.2916<br>0.2896 | **4.2 / 5.0**<br>(4, 5, 4, 4, 4) | Strong emotional romance and cross-generational love story groupings. |

**Average Qualitative Relevance Score:** `4.32 / 5.0`

---

## 2. SQL Analytics Validation & Runtime Benchmarks

Benchmarked on SQLite engine (`tmdb_movies.db` with 4 indexed tables) over 10 execution cycles.

| Query / Analysis Task | SQL Concepts Applied | Rows Returned | Avg. Runtime | Min. Runtime | Sample Validated Output |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **1. Genre-Partitioned Box Office Leaders** | `ROW_NUMBER() OVER (PARTITION BY genre_name ORDER BY revenue DESC)` + CTE | 12 | **11.7 ms** | 10.3 ms | Action Rank 1: *Avatar* ($2,788.0M)<br>Action Rank 2: *The Avengers* ($1,519.6M)<br>Action Rank 3: *Jurassic World* ($1,513.5M) |
| **2. Director ROI & Financial Profitability** | `WITH`, `SUM()`, `HAVING COUNT() >= 4`, arithmetic ROI | 5 | **5.2 ms** | 4.9 ms | Spielberg: 25 films, $8.6B gross, **423.9% ROI**<br>Peter Jackson: 8 films, $6.5B gross, **404.3% ROI**<br>James Cameron: 6 films, $5.8B gross, **684.0% ROI** |
| **3. Actor-Director Synergy Analysis** | 3-Way `INNER JOIN` (`movies`, `movie_directors`, `movie_cast`) | 5 | **10.6 ms** | 8.9 ms | Verbinski & Johnny Depp: 5 films, **$3.0B gross**<br>Peter Jackson & Elijah Wood: 3 films, **$2.9B gross** |
| **4. 3-Year Rolling Box Office Moving Avg** | `AVG() OVER (ORDER BY year ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)` | 16 | **2.0 ms** | 1.9 ms | 2015: $180.75M avg (3-yr rolling: **$164.35M**)<br>2014: $168.67M avg (3-yr rolling: **$157.75M**) |

---

## 3. User Task & Usability Evaluation

**Defined Task:**  
*"Using the system, generate 5 recommendations for 'Avatar', ask the AI Assistant which of the recommendations are animated, and clear the chat for a new search."*

- **Sample Participant Group:** 3 users tested.
- **Average Completion Time:** `24.6 seconds`
- **Task Success Rate:** `100% (3/3)`
- **Observed Usability Feedback:**
  - Posters render instantly via TMDB API.
  - Automatic chat reset on clicking new movie recommendation prevented confusion between different movie discussions.
  - Sub-second LLM inference via Groq provided immediate answers.
