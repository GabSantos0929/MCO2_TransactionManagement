from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from db import execute_query, fetch_one, fetch_all, is_central_node_up, fetch_binlog_from_slave, apply_binlog_to_master, get_last_executed_position

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Ensure you have a secret key for flash messages

def direct_to_central():
    session['db_config'] = {
            'host': "ccscloud.dlsu.edu.ph",
            'user': "username",
            'password': "password",
            'database': "Complete",
            'port': 20060
        }

def central_node_failure(node):
    if node == 'Complete':
        central_node_status = is_central_node_up()
        if not central_node_status:
            return True
    return False

def catch_up_with_transactions():
    master_config = {
        'host': "ccscloud.dlsu.edu.ph",
        'user': "username",
        'password': "password",
        'database': "Complete",
        'port': 20060
    }
    
    last_position = get_last_executed_position(master_config)
    
    bf1980_slave_config = {
        'host': "ccscloud.dlsu.edu.ph",
        'user': "username",
        'password': "password",
        'database': "Be1980",
        'port': 20070
    }
    
    af1980_slave_config = {
        'host': "ccscloud.dlsu.edu.ph",
        'user': "username",
        'password': "password",
        'database': "Af1980",
        'port': 20080
    }
    
    bf1980_events = fetch_binlog_from_slave(bf1980_slave_config, last_position)
    af1980_events = fetch_binlog_from_slave(af1980_slave_config, last_position)
    
    apply_binlog_to_master(bf1980_events, master_config)
    apply_binlog_to_master(af1980_events, master_config)

@app.route('/')
def index():
    node = session.get('current_node')
    central_node_status = central_node_failure(node)
    if central_node_status:
        return render_template('index.html')
    # catch_up_with_transactions()
    movies = fetch_all("SELECT * FROM movie")
    return render_template('index.html', movies=movies)

@app.route('/insert', methods=['POST'])
def insert_movie():
    node = session.get('current_node')
    central_node_status = central_node_failure(node)
    if central_node_status:
        flash('Central node is down. Please connect to a different node')
        return redirect(url_for('index'))
    
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
        direct_to_central()
        execute_query(query, values, session['db_config'])
        flash('Movie added successfully!', 'success')
    except Exception as e:
        flash('An error occurred: {}'.format(str(e)), 'danger')
    
    return redirect(url_for('index'))

@app.route('/search', methods=['GET'])
def search_movie():
    node = session.get('current_node')
    central_node_status = central_node_failure(node)
    if central_node_status:
        flash('Central node is down. Please connect to a different node')
        return redirect(url_for('index'))

    movie_id = request.args.get('search_id')
    query = "SELECT * FROM movie WHERE MovieID = %s"
    movie = fetch_one(query, (movie_id,))
    if not movie:
        flash('Movie not found!', 'danger')
        return redirect(url_for('index'))
    return render_template('index.html', movie=movie)

@app.route('/update', methods=['POST'])
def update_movie():
    node = session.get('current_node')
    central_node_status = central_node_failure(node)
    if central_node_status:
        flash('Central node is down. Please connect to a different node')
        return redirect(url_for('index'))
    
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
        direct_to_central()
        execute_query(query, values, session['db_config'])
        flash('Movie updated successfully!', 'success')
    except Exception as e:
        flash('An error occurred: {}'.format(str(e)), 'danger')
    
    return redirect(url_for('index'))

@app.route('/delete', methods=['POST'])
def delete_movie():
    node = session.get('current_node')
    central_node_status = central_node_failure(node)
    if central_node_status:
        flash('Central node is down. Please connect to a different node')
        return redirect(url_for('index'))
    
    movie_id = request.form['delete_id']
    query = "DELETE FROM movie WHERE MovieID = %s"
    
    try:
        movie = fetch_one("SELECT * FROM movie WHERE MovieID = %s", (movie_id,))
        if not movie:
            flash('Movie not found!', 'danger')
            return redirect(url_for('index'))
        direct_to_central()
        execute_query(query, (movie_id,), session['db_config'])
        flash('Movie deleted successfully!', 'success')
    except Exception as e:
        flash('An error occurred: {}'.format(str(e)), 'danger')
    
    return redirect(url_for('index'))

@app.route('/switch_node', methods=['POST'])
def switch_node():
    node = request.form['node']
    
    if node == 'Complete':
        central_node_status = is_central_node_up()
        if central_node_status:
            session['db_config'] = {
                'host': "ccscloud.dlsu.edu.ph",
                'user': "username",
                'password': "password",
                'database': "Complete",
                'port': 20060
            }
            session['current_node'] = 'Complete'
            flash(f'Connected to {session["current_node"]}.', 'success')
        else:
            flash('Central node is down. Please connect to a different node')
    elif node == 'Be1980':
        session['db_config'] = {
            'host': "ccscloud.dlsu.edu.ph",
            'user': "username",
            'password': "password",
            'database': "Be1980",
            'port': 20070
        }
        session['current_node'] = 'Be1980'
        flash(f'Connected to {session["current_node"]}.', 'success')
    elif node == 'Af1980':
        session['db_config'] = {
            'host': "ccscloud.dlsu.edu.ph",
            'user': "username",
            'password': "password",
            'database': "Af1980",
            'port': 20080
        }
        session['current_node'] = 'Af1980'
        flash(f'Connected to {session["current_node"]}.', 'success')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
