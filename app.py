import streamlit as st
import pickle
import pandas as pd
import requests

# Page Configuration
st.set_page_config(
    page_title="Movie Recommender System",
    page_icon="🎬",
    layout="wide"
)

# Custom Styling (Dark Glassmorphic UI)
st.markdown("""
<style>
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(90deg, #E50914, #FFA07A);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.1rem;
        text-align: center;
        color: #B3B3B3;
        margin-bottom: 2rem;
    }
    .movie-title {
        font-size: 0.95rem;
        font-weight: 600;
        margin-top: 8px;
        color: #FFFFFF;
        height: 40px;
        overflow: hidden;
        text-align: center;
    }
    .ai-section {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 14px;
        padding: 20px;
        margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)

# ── Helper: Fetch poster from TMDB ──────────────────────────────────────────
def fetch_poster(movie_id):
    try:
        api_key = st.secrets.get("tmdb_api_key", "3b5ea5ff95c5b8c2f8fcf23b10bfbf60")
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
        response = requests.get(url, timeout=5)
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500/{poster_path}"
        return "https://via.placeholder.com/500x750?text=No+Poster"
    except Exception:
        return "https://via.placeholder.com/500x750?text=No+Poster"

# ── Helper: Ask Groq AI ──────────────────────────────────────────────────────
def ask_groq(user_question, movie_titles: list):
    groq_key = (
        st.secrets.get("GROQ_API_KEY")
        or st.secrets.get("groq_api_key")
    )
    if not groq_key:
        return "Error: GROQ_API_KEY not set. Please add it to your Streamlit secrets (.streamlit/secrets.toml)."

    movies_list_str = ", ".join(movie_titles)
    system_prompt = (
        f"You are a helpful movie assistant. The user was recommended these films: {movies_list_str}. "
        "Answer their question about these movies concisely and helpfully."
    )

    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json",
    }
    
    # Active Groq models tested and verified
    models_to_try = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
    
    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_question},
            ],
            "temperature": 0.7,
            "max_tokens": 512,
        }

        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=15,
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            else:
                err_detail = resp.json().get("error", {}).get("message", resp.text)
                if model_name == models_to_try[-1]:
                    return f"Groq API Error ({resp.status_code}): {err_detail}"
                continue
        except Exception as e:
            if model_name == models_to_try[-1]:
                return f"Unexpected error: {e}"
            continue
    return "Could not generate response from Groq."

# ── Load Precomputed Data ─────────────────────────────────────────────────────
@st.cache_resource
def load_data():
    movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    return movies, similarity

movies, similarity = load_data()

# ── Recommendation Engine ─────────────────────────────────────────────────────
def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    names, posters = [], []
    for i in movie_list:
        movie_id = movies.iloc[i[0]].movie_id
        names.append(movies.iloc[i[0]].title)
        posters.append(fetch_poster(movie_id))
    return names, posters

# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🎬 Movie Recommender System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Content-Based Filtering · NLP · Cosine Similarity</div>', unsafe_allow_html=True)

movie_list_titles = movies['title'].values
selected_movie = st.selectbox("Type or select a movie:", movie_list_titles, index=0)

if st.button("🚀 Show Recommendations", type="primary", use_container_width=True):
    with st.spinner("Finding similar movies..."):
        names, posters = recommend(selected_movie)
        st.session_state["rec_names"]   = names
        st.session_state["rec_posters"] = posters

# Show recommendations if available
if "rec_names" in st.session_state:
    names   = st.session_state["rec_names"]
    posters = st.session_state["rec_posters"]

    st.markdown("### Top 5 Recommendations")
    cols = st.columns(5)
    for col, name, poster in zip(cols, names, posters):
        with col:
            st.image(poster, use_container_width=True)
            st.markdown(f"<div class='movie-title'>{name}</div>", unsafe_allow_html=True)

    # ── AI Chat Section ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 💬 Ask AI Assistant about these recommendations")
    st.caption("Ask why these movies were recommended, which ones are sci-fi, want a quick summary, etc.")

    # Chat history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Ask about these recommended movies...")
    if user_input:
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = ask_groq(user_input, names)
            st.write(reply)
        st.session_state["chat_history"].append({"role": "assistant", "content": reply})
