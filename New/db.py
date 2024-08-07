import mysql.connector
from flask import session, flash

def get_db_connection():
    db_config = session.get('db_config', {
        'host': "ccscloud.dlsu.edu.ph",
        'user': "username",
        'password': "password",
        'database': "Complete",
        'port': 20060
    })
    
    return mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        port=db_config['port']
    )

def execute_query(query, values, db_config):
    connection = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        port=db_config['port']
    )
    
    cursor = connection.cursor()
    cursor.execute(query, values)
    connection.commit()
    cursor.close()
    connection.close()


def fetch_all(query, values=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, values)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def fetch_one(query, values=None):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, values) if values else cursor.execute(query)
        result = cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        raise
    finally:
        cursor.close()
        connection.close()
    return result

def is_central_node_up():
    try:
        connection = mysql.connector.connect(
            host="ccscloud.dlsu.edu.ph",
            user="username",
            password="password",
            database="Complete",
            port=20060
        )
        connection.close()
        return True
    except mysql.connector.Error:
        return False

def is_be1980_node_up():
    try:
        connection = mysql.connector.connect(
            host="ccscloud.dlsu.edu.ph",
            user="username",
            password="password",
            database="Be1980",
            port=20070
        )
        connection.close()
        return True
    except mysql.connector.Error:
        return False

def is_af1980_node_up():
    try:
        connection = mysql.connector.connect(
            host="ccscloud.dlsu.edu.ph",
            user="username",
            password="password",
            database="Af1980",
            port=20080
        )
        connection.close()
        return True
    except mysql.connector.Error:
        return False
