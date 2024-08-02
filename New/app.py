from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from db import (
    get_db_connection_server1, 
    get_db_connection_server2, 
    get_db_connection_server3, 
    retry_execute_query, 
    fetch_one, 
    log_transaction, 
    retrieve_logs, 
    apply_transactions_to_node, 
    retrieve_missing_transactions, 
    get_node_logs
)
import threading
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Global variables for node status simulation
server1_online = True
node2_online = True
node3_online = True

# Global variables for node tracking
current_central_node = 'server1'

def set_isolation_level(connection, level):
    cursor = connection.cursor()
    cursor.execute(f"SET SESSION TRANSACTION ISOLATION LEVEL {level}")
    cursor.close()

def promote_slave_to_central():
    global server1_online
    global node2_online
    global node3_online
    global current_central_node
    
    if not server1_online:
        print("Server 1 is down. Promoting one of the slave nodes to central.")
        if not node2_online:
            node2_online = True
            current_central_node = 'server2'
        else:
            node3_online = True
            current_central_node = 'server3'
    else:
        print("Server 1 is back online. Replicating data from temporary central node.")
        replicate_data_from_temp_central()

def replicate_data_from_temp_central():
    global current_central_node
    if current_central_node == 'server2':
        central_connection = get_db_connection_server2()
    elif current_central_node == 'server3':
        central_connection = get_db_connection_server3()
    else:
        central_connection = get_db_connection_server1()
    
    # Retrieve transaction logs from the central node
    central_logs = retrieve_logs()
    
    # Replay missing transactions on Node 2 and Node 3
    if node2_online:
        node2_connection = get_db_connection_server2()
        node2_logs = get_node_logs(node2_connection)
        missing_transactions = retrieve_missing_transactions(node2_logs, central_logs)
        apply_transactions_to_node(node2_connection, missing_transactions)
        node2_connection.close()

    if node3_online:
        node3_connection = get_db_connection_server3()
        node3_logs = get_node_logs(node3_connection)
        missing_transactions = retrieve_missing_transactions(node3_logs, central_logs)
        apply_transactions_to_node(node3_connection, missing_transactions)
        node3_connection.close()

def check_server1_status_and_replicate():
    global server1_online
    while not server1_online:
        time.sleep(10)  # Wait before checking again
        server1_online = True
        print("Server 1 is back online.")
        promote_slave_to_central()

threading.Thread(target=check_server1_status_and_replicate, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/insert', methods=['POST'])
def insert_movie():
    connection = get_db_connection_server1()
    set_isolation_level(connection, 'REPEATABLE READ')
    
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
        retry_execute_query(query, values, connection)
        log_transaction(f"INSERT: {values}")
        flash('Movie added successfully!', 'success')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
    finally:
        connection.close()
    
    return redirect(url_for('index'))

@app.route('/search', methods=['GET'])
def search_movie():
    connection = get_db_connection_server1()
    set_isolation_level(connection, 'READ COMMITTED')
    
    movie_id = request.args.get('search_id')
    
    query = "SELECT * FROM movie WHERE MovieID = %s"
    movie = fetch_one(query, (movie_id,), connection)
    
    if movie:
        return render_template('index.html', movie=movie)
    else:
        flash('Movie not found!', 'danger')
        return redirect(url_for('index'))

@app.route('/update', methods=['POST'])
def update_movie():
    connection = get_db_connection_server1()
    set_isolation_level(connection, 'REPEATABLE READ')
    
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
        retry_execute_query(query, values, connection)
        log_transaction(f"UPDATE: {values}")
        flash('Movie updated successfully!', 'success')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
    finally:
        connection.close()
    
    return redirect(url_for('index'))

@app.route('/delete', methods=['POST'])
def delete_movie():
    connection = get_db_connection_server1()
    set_isolation_level(connection, 'REPEATABLE READ')
    
    movie_id = request.form['delete_id']
    
    query = "DELETE FROM movie WHERE MovieID = %s"
    
    try:
        retry_execute_query(query, (movie_id,), connection)
        log_transaction(f"DELETE: {movie_id}")
        flash('Movie deleted successfully!', 'success')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
    finally:
        connection.close()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
