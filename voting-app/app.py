from flask import Flask, render_template, request, redirect, session, jsonify
import requests
import redis
import os
import json
import random
import math


app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_secret_key')  # Clave para manejar sesiones de usuario


# Configuración de Redis
redis_host = os.getenv('REDIS_HOST', 'redis')
r = redis.Redis(host=redis_host, port=6379, db=0)


# Configuración de API de TheMovieDB
TMDB_API_KEY = '500aa00a87501f5ab69640c02e5620ca'  # Reemplaza con tu API Key de TheMovieDB
TMDB_API_URL = 'https://api.themoviedb.org/3/movie/'



# Función para obtener dos películas aleatorias de varias páginas de películas populares
def get_random_movies():
    try:
        # Seleccionar una página aleatoria para obtener películas
        random_page = random.randint(1, 50)  # Ajusta el rango según las páginas disponibles en la API


        # Solicitud a una página aleatoria de películas populares
        response = requests.get(f'{TMDB_API_URL}popular?api_key={TMDB_API_KEY}&page={random_page}')
        response.raise_for_status()
       
        data = response.json()
        movies = data.get('results', [])
       
        if len(movies) < 2:
            return None, None
       
        # Seleccionar dos películas de forma aleatoria de esa página
        movie1, movie2 = random.sample(movies, 2)
        return movie1, movie2


    except requests.exceptions.RequestException as e:
        print(f"Error al obtener películas de la API: {e}")
        return None, None


@app.route('/')
def index():
    # Inicializar las variables de la sesión si no existen
    if 'vote_count' not in session:
        session['vote_count'] = 0
        session['votes'] = []


    # Verificar si ya existen películas en Redis
    if r.exists("movie1") and r.exists("movie2"):
        movie1 = json.loads(r.get("movie1").decode("utf-8"))
        movie2 = json.loads(r.get("movie2").decode("utf-8"))
    else:
        # Obtener dos películas aleatorias y almacenarlas en Redis
        movie1, movie2 = get_random_movies()
        if movie1 and movie2:
            r.set("movie1", json.dumps(movie1), ex=30)  # Usar json.dumps para almacenar como JSON
            r.set("movie2", json.dumps(movie2), ex=30)  # Usar json.dumps para almacenar como JSON
   
    return render_template('index.html', movie1=movie1, movie2=movie2)



@app.route('/vote', methods=['POST'])
def vote():
    if 'vote_count' not in session:
        session['vote_count'] = 0
        session['votes'] = []


    data = request.get_json()
    movie_id = data.get('movie_id')


    if not movie_id:
        return jsonify({"error": "Selecciona una película."}), 400


    if session['vote_count'] < 10:
        # Guardar el voto y actualizar el contador en la sesión
        session['votes'].append(movie_id)
        session['vote_count'] += 1


        # Obtener nuevas películas y almacenarlas en Redis
        movie1, movie2 = get_random_movies()
        if movie1 and movie2:
            r.set("movie1", json.dumps(movie1), ex=30)
            r.set("movie2", json.dumps(movie2), ex=30)
       
        return jsonify({"success": True, "redirect": "/" if session['vote_count'] < 10 else "/results"})
    else:
        return jsonify({"redirect": "/results"})



@app.route('/results')
def results():
    votes = session.get('votes', [])
   
    if not votes:
        return redirect('/')  # Si no hay votos, redirige a la página principal
   
    print("Votos recibidos:", votes)  # Imprimir para asegurarte de que haya votos
   
    try:
        print("Enviando solicitud a la API de recomendaciones...")
        response = requests.post('http://recommendation-engine:5001/recommend', json={"votes": votes})
        response.raise_for_status()
        recommendations = response.json().get("recommendations", [])
        print("Recomendaciones recibidas:", recommendations)  # Verifica las recomendaciones recibidas
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener recomendaciones: {e}")
        recommendations = []
   
    # Limpiar la sesión
    session.pop('vote_count', None)
    session.pop('votes', None)
   
    return render_template('results.html', recommendations=recommendations)


@app.route('/change', methods=['GET'])
def change():
    # Limpiar Redis para obtener nuevas películas
    r.delete("movie1")
    r.delete("movie2")
   
    # Asegurarse de que se obtienen nuevas películas
    movie1, movie2 = get_random_movies()
   
    # Si no hay películas nuevas, redirige con un mensaje de error o algo similar
    if not movie1 or not movie2:
        return "Error al obtener nuevas películas.", 500
   
    # Almacenar las nuevas películas en Redis usando json.dumps
    r.set("movie1", json.dumps(movie1), ex=60)
    r.set("movie2", json.dumps(movie2), ex=60)
   
    return redirect('/')




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)