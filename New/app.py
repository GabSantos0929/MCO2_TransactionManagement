from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from db import get_db_connection, execute_query, fetch_one, fetch_all, is_central_node_up

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Ensure you have a secret key for flash messages

def set_db_config_with_failover(release_date=None):
    if is_central_node_up():
        session['db_config'] = {
            'host': "ccscloud.dlsu.edu.ph",
            'user': "username",
            'password': "password",
            'database': "Complete",
            'port': 20060
        }
    else:
        if release_date and release_date < '1980-01-01':
            session['db_config'] = {
                'host': "ccscloud.dlsu.edu.ph",
                'user': "username",
                'password': "password",
                'database': "Be1980",
                'port': 20070
            }
        else:
            session['db_config'] = {
                'host': "ccscloud.dlsu.edu.ph",
                'user': "username",
                'password': "password",
                'database': "Af1980",
                'port': 20080
            }

@app.route('/')
def index():
    set_db_config_with_failover()
    movies = fetch_all("SELECT * FROM movie")
    return render_template('index.html', movies=movies)

@app.route('/insert', methods=['POST'])
def insert_movie():
    movie_id = request.form['movie_id']
    title = request.form['title']
    director_name = request.form['director_name']
    actor_name = request.form['actor_name']
    release_date = request.form['release_date']
    production_budget = request.form['production_budget']
    movie_rating = request.form['movie_rating']
    genre = request.form['genre']
    
    query = """INSERT INTO movie 
               (MovieID, Title, DirectorName, ActorName, ReleaseDate, ProductionBudget, MovieRating, Genre) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    values = (movie_id, title, director_name, actor_name, release_date, production_budget, movie_rating, genre)
    
    try:
        set_db_config_with_failover(release_date)
        execute_query(query, values, session['db_config'])
        flash('Movie added successfully!', 'success')
    except Exception as e:
        flash('An error occurred: {}'.format(str(e)), 'danger')
    
    return redirect(url_for('index'))

@app.route('/search', methods=['GET'])
def search_movie():
    movie_id = request.args.get('search_id')
    
    query = "SELECT * FROM movie WHERE MovieID = %s"
    set_db_config_with_failover()
    movie = fetch_one(query, (movie_id,))
    
    if movie:
        return render_template('index.html', movie=movie)
    else:
        flash('Movie not found!', 'danger')
        return redirect(url_for('index'))

@app.route('/update', methods=['POST'])
def update_movie():
    movie_id = request.form['movie_id']
    title = request.form['title']
    director_name = request.form['director_name']
    actor_name = request.form['actor_name']
    release_date = request.form['release_date']
    production_budget = request.form['production_budget']
    movie_rating = request.form['movie_rating']
    genre = request.form['genre']
    
    query = """UPDATE movie 
               SET Title = %s, DirectorName = %s, ActorName = %s, ReleaseDate = %s, 
                   ProductionBudget = %s, MovieRating = %s, Genre = %s 
               WHERE MovieID = %s"""
    values = (title, director_name, actor_name, release_date, production_budget, movie_rating, genre, movie_id)
    
    try:
        set_db_config_with_failover(release_date)
        execute_query(query, values, session['db_config'])
        flash('Movie updated successfully!', 'success')
    except Exception as e:
        flash('An error occurred: {}'.format(str(e)), 'danger')
    
    return redirect(url_for('index'))

@app.route('/delete', methods=['POST'])
def delete_movie():
    movie_id = request.form['delete_id']
    
    query = "DELETE FROM movie WHERE MovieID = %s"
    
    try:
        movie = fetch_one("SELECT * FROM movie WHERE MovieID = %s", (movie_id,))
        if not movie:
            flash('Movie not found!', 'danger')
            return redirect(url_for('index'))

        release_date = movie['ReleaseDate']
        set_db_config_with_failover(release_date)

        execute_query(query, (movie_id,), session['db_config'])
        flash('Movie deleted successfully!', 'success')
    except Exception as e:
        flash('An error occurred: {}'.format(str(e)), 'danger')
    
    return redirect(url_for('index'))

@app.route('/switch_node', methods=['POST'])
def switch_node():
    node = request.form['node']
    
    if node == 'Complete':
        session['db_config'] = {
            'host': "ccscloud.dlsu.edu.ph",
            'user': "username",
            'password': "password",
            'database': "Complete",
            'port': 20060
        }
    elif node == 'Be1980':
        session['db_config'] = {
            'host': "ccscloud.dlsu.edu.ph",
            'user': "username",
            'password': "password",
            'database': "Be1980",
            'port': 20070
        }
    elif node == 'Af1980':
        session['db_config'] = {
            'host': "ccscloud.dlsu.edu.ph",
            'user': "username",
            'password': "password",
            'database': "Af1980",
            'port': 20080
        }
    
    flash(f'Switched to {node} database.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
