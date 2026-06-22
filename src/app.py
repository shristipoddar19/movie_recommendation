from flask import Flask,request,jsonify
import mysql.connector
import pandas as pd

import logging
import time

from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app=Flask(__name__)
@app.before_request
def start_timer():
    request.start_time = time.time()

@app.after_request
def log_request(response):

    duration = time.time() - request.start_time

    logging.info(
        f"{request.method} {request.path} completed in {duration:.4f} sec"
    )

    return response

@app.errorhandler(Exception)
def handle_error(error):

    logging.error(f"Error: {str(error)}")

    return jsonify({
        "error": "Something went wrong"
    }), 500

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

app.config["JWT_SECRET_KEY"] = "super-secret-key-change-this-in-production"
jwt = JWTManager(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

db=mysql.connector.connect(
    host="localhost",
    user="root",
    password="BhoolNaMat@1",
    database="final_project"
)
cursor=db.cursor(dictionary=True)

# --- USER REGISTRATION & LOGIN ENDPOINTS ---

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password') # Production mein isse hash karna chahiye (e.g., Werkzeug)
    email = data.get('email')

    if not username or not password or not email:
        return jsonify({"error": "Missing username or password or email"}), 400

    try:
        query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, email, password))
        db.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error or user exists: {err}"}), 400

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute") # Login endpoint par strict rate limit lagayi hai
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    query = "SELECT * FROM users WHERE name = %s AND password = %s"
    cursor.execute(query, (username, password))
    user = cursor.fetchone()

    if user:
        # JWT Token generate karein
        access_token = create_access_token(identity=str(user['user_id']))
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"message": "Bad username or password"}), 401

@app.route('/movies',methods=['GET'])
@jwt_required() # Ab sirf logged-in users hi movies dekh sakte hain
def get_movies():
    cursor.execute("SELECT * FROM movies")
    movies=cursor.fetchall()
    return jsonify(movies) 



@app.route('/add_movie',methods=['POST'])
def add_movie():
     data=request.json
     title=data['title']
     description=data['description']
     year=data['release_year']


     query="INSERT INTO movies(title,description,release_year)VALUES(%s,%s,%s)"
     cursor.execute(query,(title,description,year))
     db.commit()

     return jsonify({"message":"movie added successfully"})

@app.route('/add_genre', methods=['POST'])
def add_genre():

    data = request.json
    genre_name = data['genre_name']

    query = "INSERT INTO genres (genre_name) VALUES (%s)"
    
    cursor.execute(query, (genre_name,))
    db.commit()

    return jsonify({"message": "Genre added successfully"})

@app.route('/genres', methods=['GET'])
def get_genres():

    query = "SELECT * FROM genres"

    df = pd.read_sql(query, db)

    return df.to_json(orient='records')

@app.route('/add_movie_genre', methods=['POST'])
def add_movie_genre():

    data = request.json

    movie_id = data['movie_id']
    genre_id = data['genre_id']

    query = "INSERT INTO movie_genres (movie_id, genre_id) VALUES (%s, %s)"

    cursor.execute(query, (movie_id, genre_id))
    db.commit()

    return jsonify({"message": "Movie genre added successfully"})

@app.route('/movie_genres', methods=['GET'])
def get_movie_genres():

    query = """
    SELECT movies.title, genres.genre_name
    FROM movie_genres
    JOIN movies ON movie_genres.movie_id = movies.movie_id
    JOIN genres ON movie_genres.genre_id = genres.genre_id
    """

    df = pd.read_sql(query, db)

    return df.to_json(orient='records')

@app.route('/add_rating',methods=['POST'])
def add_rating():
     data=request.json
     user_id=data['user_id']
     movie_id=data['movie_id']
     rating=data['rating']

     query="INSERT INTO ratings(user_id,movie_id,rating)VALUES(%s,%s,%s)"
     cursor.execute(query,(user_id,movie_id,rating))
     db.commit()

     return jsonify({"message":"Rating added"})




@app.route('/ratings',methods=['GET'])
def get_ratings():
    query="SELECT *FROM ratings"
    df=pd.read_sql(query,db)

    return df.to_json(orient='records')


@app.route('/')
def home():
    return "Movie Recommendation API Running"


@app.route('/top_ratings')
def top_ratings():

    query="""
    SELECT movie_id,AVG(rating)as avg_rating
    From ratings
    GROUP BY movie_id
    ORDER BY avg_rating DESC
    """

    df=pd.read_sql(query,db)
    return df.to_json(orient='records')

@app.route('/recommend/<int:movie_id>', methods=['GET'])
def recommend_movies(movie_id):
    # 1. Database se saari movies description ke saath load karein
    query = '''SELECT 
                    movies.movie_id,
                    movies.title,
                    movies.description,
                    GROUP_CONCAT(genres.genre_name SEPARATOR ' ') AS genres
                FROM movies
                LEFT JOIN movie_genres 
                    ON movies.movie_id = movie_genres.movie_id
                LEFT JOIN genres 
                    ON movie_genres.genre_id = genres.genre_id
                GROUP BY movies.movie_id'''
    df_movies = pd.read_sql(query, db)
    
    # Check karein ki di gayi movie database mei hai ya nahi
    if movie_id not in df_movies['movie_id'].values:
        return jsonify({"error": "Movie not found"}), 404
        
    # 2. Text preprocessing aur ML Vectorization
    tfidf = TfidfVectorizer(stop_words='english')
    # Agar description Khali (null) ho toh empty string se replace karein
    df_movies['description'] = df_movies['description'].fillna('')
    df_movies['genres'] = df_movies['genres'].fillna('')
    df_movies['combined_features'] = (
        df_movies['genres'] + ' ' +
        df_movies['genres'] + ' ' +
        df_movies['genres'] + ' ' +
        df_movies['description']
    )    
    tfidf_matrix = tfidf.fit_transform(df_movies['combined_features'])
    
    # Cosine Similarity Matrix calculate karein
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    # 3. Target movie ka index find karein
    idx = df_movies[df_movies['movie_id'] == movie_id].index[0]
    
    # 4. Similar movies ke scores nikaalein aur sort karein
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    
    # Top 5 similar movies select karein (pehli movie ko chhod kar kyunki woh khud wahi movie hogi)
    sim_scores = sim_scores[1:6]
    
    # 5. Movies ke IDs aur titles fetch karke list banayein
    movie_indices = [i[0] for i in sim_scores]
    recommended_data = df_movies.iloc[movie_indices][
        ['movie_id', 'title', 'description', 'genres']
    ].to_dict(orient='records')    
    
    return jsonify({
        "searched_movie": df_movies.loc[idx, 'title'],
        "recommendations": recommended_data
    })


@app.route('/collaborative_recommend/<int:user_id>', methods=['GET'])
def collaborative_recommend(user_id):

    query = """
    SELECT user_id, movie_id, rating
    FROM ratings
    """

    df = pd.read_sql(query, db)

    if df.empty:
        return jsonify({"error": "No ratings data found"}), 404

    # User-Movie Matrix
    user_movie_matrix = df.pivot_table(
        index='user_id',
        columns='movie_id',
        values='rating'
    ).fillna(0)

    # Similarity calculation
    similarity = cosine_similarity(user_movie_matrix)

    similarity_df = pd.DataFrame(
        similarity,
        index=user_movie_matrix.index,
        columns=user_movie_matrix.index
    )

    if user_id not in similarity_df.index:
        return jsonify({"error": "User not found"}), 404

    # Most similar users
    similar_users = similarity_df[user_id].sort_values(ascending=False)

    similar_users = similar_users.drop(user_id)

    if similar_users.empty:
        return jsonify({"message": "No similar users found"})

    top_user = similar_users.index[0]

    # Movies watched by target user
    target_movies = set(
        df[df['user_id'] == user_id]['movie_id']
    )

    # Movies watched by similar user
    recommended_movies = df[
        (df['user_id'] == top_user) &
        (~df['movie_id'].isin(target_movies))
    ]['movie_id'].unique()

    if len(recommended_movies) == 0:
        return jsonify({"message": "No recommendations found"})

    # Fetch movie details
    movie_ids = ','.join(map(str, recommended_movies))

    movie_query = f"""
    SELECT movie_id, title, description
    FROM movies
    WHERE movie_id IN ({movie_ids})
    """

    recommendations = pd.read_sql(movie_query, db)

    return jsonify({
        "recommended_for_user": user_id,
        "similar_user": int(top_user),
        "recommendations": recommendations.to_dict(orient='records')
    })


if __name__=='__main__':
  app.run(debug=True) 