import mysql.connector
import time

# Retry parameters
MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds

def get_db_connection_server1():
    return mysql.connector.connect(
        host="ccscloud.dlsu.edu.ph",
        user="username",
        password="password",
        database="Complete",
        port=20060
    )

def get_db_connection_server2():
    return mysql.connector.connect(
        host="ccscloud.dlsu.edu.ph",
        user="username",
        password="password",
        database="Be1980",
        port=20070
    )

def get_db_connection_server3():
    return mysql.connector.connect(
        host="ccscloud.dlsu.edu.ph",
        user="username",
        password="password",
        database="Af1980",
        port=20080
    )

def retry_execute_query(query, values=None, connection=None):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            execute_query(query, values, connection)
            return
        except mysql.connector.Error as err:
            retries += 1
            delay = RETRY_DELAY * (2 ** retries)
            print(f"Retrying query due to error: {err}. Attempt {retries} in {delay} seconds.")
            time.sleep(delay)
            if retries >= MAX_RETRIES:
                notify_admin(f"Query failed after {MAX_RETRIES} attempts.")
                raise

def execute_query(query, values=None, connection=None):
    cursor = connection.cursor()
    try:
        if values:
            cursor.execute(query, values)
        else:
            cursor.execute(query)
        connection.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        raise
    finally:
        cursor.close()

def fetch_one(query, values=None, connection=None):
    cursor = connection.cursor(dictionary=True)
    try:
        if values:
            cursor.execute(query, values)
        else:
            cursor.execute(query)
        result = cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        raise
    finally:
        cursor.close()
    return result

def log_transaction(transaction_details):
    with open('transaction_log.txt', 'a') as log_file:
        log_file.write(f"{transaction_details}\n")

def retrieve_logs():
    with open('transaction_log.txt', 'r') as log_file:
        return log_file.readlines()

def notify_admin(message):
    # Implement notification logic here (e.g., send an email or a message)
    print(f"Admin Notification: {message}")

def get_node_logs(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM transaction_log")  # Adjust query to your logs table schema
    logs = cursor.fetchall()
    cursor.close()
    return logs

def retrieve_missing_transactions(node_logs, central_logs):
    # Implement logic to find missing transactions based on logs comparison
    missing_transactions = []
    # Example logic
    central_log_ids = {log['id'] for log in central_logs}
    for log in node_logs:
        if log['id'] not in central_log_ids:
            missing_transactions.append(log)
    return missing_transactions

def apply_transactions_to_node(connection, transactions):
    cursor = connection.cursor()
    for transaction in transactions:
        query = transaction['query']  # Assumes each transaction contains a query string
        values = transaction['values']  # Assumes each transaction contains values to be executed
        execute_query(query, values, connection)
    cursor.close()
