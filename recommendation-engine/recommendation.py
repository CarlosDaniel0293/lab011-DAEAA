from flask import Flask, request, jsonify
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from concurrent.futures import ThreadPoolExecutor, as_completed


app = Flask(__name__)


TMDB_API_KEY = '500aa00a87501f5ab69640c02e5620ca'
TMDB_API_URL = 'https://api.themoviedb.org/3/movie/'


def get_movie_details(movie_ids):
    movies = []
   
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_movie = {executor.submit(fetch_movie_data, movie_id): movie_id for movie_id in movie_ids}
       
        for future in as_completed(future_to_movie):
            try:
                movie_data = future.result()
                if movie_data:
                    movies.append(movie_data)
            except Exception as e:
                print(f"Error al obtener datos de la película: {e}")
               
    return movies


def fetch_movie_data(movie_id):
    try:
        response = requests.get(f'{TMDB_API_URL}{movie_id}?api_key={TMDB_API_KEY}')
        response.raise_for_status()
        movie_data = response.json()
       
        credits_response = requests.get(f'{TMDB_API_URL}{movie_id}/credits?api_key={TMDB_API_KEY}')
        credits_response.raise_for_status()
        credits_data = credits_response.json()
       
        actors = [actor['name'] for actor in credits_data.get('cast', [])[:5]]
        director = next((crew['name'] for crew in credits_data.get('crew', []) if crew['job'] == 'Director'), None)
       
        poster_path = movie_data.get('poster_path')
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://via.placeholder.com/500x750.png?text=No+Poster"
       
        return {
            'id': movie_data['id'],
            'title': movie_data['title'],
            'poster': poster_url,
            'overview': movie_data.get('overview', ''),
            'genres': [genre['name'] for genre in movie_data.get('genres', [])],
            'actors': actors,
            'director': director,
            'release_date': movie_data.get('release_date', ''),
            'vote_average': movie_data.get('vote_average', 0),
            'popularity': movie_data.get('popularity', 0),
            'production_companies': [company['name'] for company in movie_data.get('production_companies', [])],
            'spoken_languages': [language['name'] for language in movie_data.get('spoken_languages', [])]
        }
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos de la película {movie_id}: {e}")
        return None


def get_movie_list(voted_genres):
    movies = []
    try:
        # Recorre 50 páginas
        for page in range(1, 51):
            response = requests.get(f'https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&page={page}')
            response.raise_for_status()
            data = response.json()
           
            # Procesar películas de cada página
            for movie in data.get('results', []):
                movie_id = movie['id']
                movie_details = get_movie_details([movie_id])[0]


                # Filtrar solo por los géneros de las películas votadas
                if any(genre in voted_genres for genre in movie_details['genres']):
                    movies.append(movie_details)


    except requests.exceptions.RequestException as e:
        print(f"Error al obtener lista de películas: {e}")


    return movies




@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    votes = data.get('votes', [])


    if not votes:
        return jsonify({'error': 'No se recibieron votos.'}), 400


    voted_movies = get_movie_details(votes)


    # Obtener los géneros únicos de las películas votadas
    voted_genres = set()
    for movie in voted_movies:
        voted_genres.update(movie['genres'])


    movie_list = get_movie_list(voted_genres)


    if not voted_movies or not movie_list:
        return jsonify({'error': 'No se pudieron obtener suficientes películas para hacer recomendaciones.'}), 500


    # Combina información adicional para cada película en un solo texto
    all_data = [
        f"{movie['overview']} {', '.join(movie['actors'])} {', '.join(movie['genres'])} "
        f"{movie['release_date']} {movie['vote_average']} {movie['popularity']} "
        f"{', '.join(movie['production_companies'])} {movie['spoken_languages']}"
        for movie in voted_movies + movie_list
    ]


    # Crear la matriz TF-IDF
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(all_data)


    # Dividir los vectores en votados y todos
    voted_vectors = tfidf_matrix[:len(voted_movies)]
    all_vectors = tfidf_matrix[len(voted_movies):]


    # Calcular similitud coseno entre votados y lista total
    cosine_similarities = cosine_similarity(voted_vectors, all_vectors)


    # Filtrar y ordenar las películas más similares
    added_movie_ids = set()
    similar_movies = []
    for sim in cosine_similarities:
        similar_indices = sim.argsort()[-5:][::-1]
        for idx in similar_indices:
            if movie_list[idx]['id'] not in added_movie_ids:
                similar_movies.append(movie_list[idx])
                added_movie_ids.add(movie_list[idx]['id'])


    # Asegurar que haya al menos 5 recomendaciones
    if len(similar_movies) < 5:
        for movie in movie_list[:5]:
            if movie['id'] not in added_movie_ids:
                similar_movies.append(movie)
                added_movie_ids.add(movie['id'])


    # Preparar el resultado final con los campos adicionales
    recommendations = [{
        'id': movie['id'],
        'title': movie['title'],
        'poster': movie['poster'],
        'overview': movie['overview'],
        'actors': movie['actors'],
        'director': movie['director'],
        'genres': movie['genres'],
        'release_date': movie['release_date'],
        'vote_average': movie['vote_average'],
        'popularity': movie['popularity'],
        'production_companies': movie['production_companies'],
        'languages': movie['spoken_languages']
    } for movie in similar_movies]


    return jsonify({'recommendations': recommendations})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)