import pickle
import streamlit as st
import requests
import pandas as pd

# --- Configuration & Styles ---
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for that Netflix feel
st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
    }
    .stHeader {
        background-color: rgba(0,0,0,0);
    }
    .css-1d391kg {
        padding-top: 1rem;
    }
    h1 {
        color: #E50914;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 700;
        text-align: center;
        padding-bottom: 2rem;
    }
    h2, h3 {
        color: #FFFFFF;
    }
    .movie-title {
        color: #FFFFFF;
        text-align: center;
        font-size: 1rem;
        margin-top: 0.5rem;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data
def load_data():
    try:
        movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
        movies = pd.DataFrame(movies_dict)
        similarity = pickle.load(open('similarity.pkl', 'rb'))
        return movies, similarity
    except FileNotFoundError:
        st.error("Error: Pickle files not found. Please ensure 'movies_dict.pkl' and 'similarity.pkl' are in the directory.")
        return None, None

movies, similarity = load_data()

# --- Helper Functions ---
def fetch_poster(movie_id):
    try:
        api_key = st.secrets["tmdb_api_key"]
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
        data = requests.get(url, timeout=5)
        data.raise_for_status() # Check for HTTP errors
        data = data.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return "https://image.tmdb.org/t/p/w500/" + poster_path
        return "https://via.placeholder.com/500x750?text=No+Image"
    except Exception as e:
        # Fallback image on error
        return "https://via.placeholder.com/500x750?text=Error"

def recommend(movie):
    if movies is None or similarity is None:
        return [], []
        
    try:
        index = movies[movies['title'] == movie].index[0]
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
        
        recommended_movies = []
        recommended_posters = []
        
        # Taking top 5 recommendations
        for i in distances[1:6]:
            movie_id = movies.iloc[i[0]].movie_id
            recommended_movies.append(movies.iloc[i[0]].title)
            recommended_posters.append(fetch_poster(movie_id))
            
        return recommended_movies, recommended_posters
    except Exception as e:
        st.error(f"Error generating recommendations: {e}")
        return [], []

# --- Main Layout ---
if movies is not None:
    st.title("🎬 Movie Recommender System")

    # Sidebar for controls
    with st.sidebar:
        st.header("Search Parameters")
        st.markdown("Select a movie you like to get personalized recommendations.")
        
        movie_list = movies['title'].values
        selected_movie = st.selectbox(
            "Type or select a movie",
            movie_list
        )
        
        if st.button('Show Recommendations', use_container_width=True):
            st.session_state.show_recommendations = True
            st.session_state.selected_movie = selected_movie

    # Main content area
    if 'show_recommendations' in st.session_state and st.session_state.show_recommendations:
        with st.spinner('Curating your watchlist...'):
            names, posters = recommend(st.session_state.selected_movie)
            
            if names:
                st.subheader(f"Because you watched *{st.session_state.selected_movie}*:")
                st.markdown("---")
                
                cols = st.columns(5)
                for idx, col in enumerate(cols):
                    with col:
                        st.image(posters[idx], use_container_width=True)
                        st.markdown(f"<div class='movie-title'>{names[idx]}</div>", unsafe_allow_html=True)
            else:
                st.warning("No recommendations found. Try another movie!")
    else:
        # Welcome / Empty state
        st.markdown("""
        ### Welcome to your personal movie guide!
        Navigate to the sidebar to start exploring similar movies.
        """)

else:
    st.stop()
