# Movie Recommendation System API Documentation

## Base URL

```txt
http://127.0.0.1:5000
```

## Authentication

This API uses JWT Authentication.

Protected endpoints require:

Authorization: Bearer <your_jwt_token>

---

# 1. Register User

## Endpoint

POST /register

## Request Body

```json
{
  "username": "shristi",
  "email": "shristi@gmail.com",
  "password": "1234"
}
```

## Response

```json
{
  "message": "User registered successfully"
}
```

---

# 2. Login User

## Endpoint

POST /login

## Request Body

```json
{
  "username": "shristi",
  "password": "1234"
}
```

## Response

```json
{
  "access_token": "your_jwt_token"
}
```

---

# 3. Get All Movies

## Endpoint

GET /movies

## Authentication

Required

## Headers

```txt
Authorization: Bearer <your_jwt_token>
```

## Response

```json
[
  {
    "movie_id": 1,
    "title": "conjuring",
    "description": "Paranormal investigators fight evil supernatural forces in a haunted house",
    "release_year": 2014
  }
]
```

---

# 4. Add Movie

## Endpoint

POST /add_movie

## Request Body

```json
{
  "title": "Annabelle",
  "description": "Possessed doll causes supernatural horror",
  "release_year": 2014
}
```

## Response

```json
{
  "message": "movie added successfully"
}
```

---

# 5. Add Rating

## Endpoint

POST /add_rating

## Request Body

```json
{
  "user_id": 1,
  "movie_id": 2,
  "rating": 5
}
```

## Response

```json
{
  "message": "Rating added"
}
```

---

# 6. Get Ratings

## Endpoint

GET /ratings

## Response

```json
[
  {
    "user_id": 1,
    "movie_id": 2,
    "rating": 5
  }
]
```

---

# 7. Top Ratings

## Endpoint

GET /top_ratings

## Response

```json
[
  {
    "movie_id": 2,
    "avg_rating": 4.8
  }
]
```

---

# 8. Add Genre

## Endpoint

POST /add_genre

## Request Body

```json
{
  "genre_name": "Horror"
}
```

## Response

```json
{
  "message": "Genre added successfully"
}
```

---

# 9. Get Genres

## Endpoint

GET /genres

## Response

```json
[
  {
    "genre_id": 1,
    "genre_name": "Horror"
  }
]
```

---

# 10. Add Movie Genre

## Endpoint

POST /add_movie_genre

## Request Body

```json
{
  "movie_id": 1,
  "genre_id": 1
}
```

## Response

```json
{
  "message": "Movie genre added successfully"
}
```

---

# 11. Get Movie Genres

## Endpoint

GET /movie_genres

## Response

```json
[
  {
    "title": "conjuring",
    "genre_name": "Horror"
  }
]
```

---

# 12. Movie Recommendation

## Endpoint

GET /recommend/<movie_id>

## Example

```txt
/recommend/1
```

## Response

```json
{
  "searched_movie": "conjuring",
  "recommendations": [
    {
      "movie_id": 33,
      "title": "Annabelle",
      "description": "Possessed doll causes supernatural horror",
      "genres": "Horror"
    }
  ]
}
```

---

# 13. Collaborative Recommendation

## Endpoint

GET /collaborative_recommend/<user_id>

## Example

```txt
/collaborative_recommend/1
```

## Response

```json
{
  "recommended_for_user": 1,
  "similar_user": 2,
  "recommendations": [
    {
      "movie_id": 5,
      "title": "Titanic",
      "description": "Romance aboard a doomed ship"
    }
  ]
}
```

---

# AI Recommendation Workflow

1. Movies and genres are fetched from the database.
2. Genres and descriptions are combined into a single text feature.
3. TF-IDF Vectorizer converts text into numerical vectors.
4. Cosine similarity is calculated between movies.
5. Top similar movies are returned as recommendations.

---

# Technologies Used

- Python
- Flask
- MySQL
- Pandas
- Scikit-learn
- JWT Authentication
- Flask Limiter

---

# Machine Learning Model

This project uses a Content-Based Recommendation System using:

- TF-IDF Vectorization
- Cosine Similarity