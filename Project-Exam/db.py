import pymysql, os
from flask import jsonify

db_user = os.environ.get("CLOUD_SQL_USERNAME")
db_password = os.environ.get("CLOUD_SQL_PASSWORD")
db_name = os.environ.get("CLOUD_SQL_DATABASE_NAME")
db_connection_name = os.environ.get("CLOUD_SQL_CONNECTION_NAME")

def open_connection():
    conn = None
    try:
        if os.environ.get('GAE_ENV') == 'standard':
            unix_socket = f'/cloudsql/{db_connection_name}'

            # Create the connection parameters dictionary
            conn_params = {
                'user': db_user,
                'db': db_name,
                'unix_socket': unix_socket,
            }
            
            # Only add password if it's provided
            if db_password:
                conn_params['password'] = db_password

            conn = pymysql.connect(**conn_params)

    except pymysql.MySQLError as e:
        print(f"Error connecting to the database: {e}")
        raise
    return conn

def get():
    conn = open_connection()
    with conn.cursor(cursor=pymysql.cursors.DictCursor) as cursor:
        result = cursor.execute('SELECT * FROM todoTable;')
        ToDos = cursor.fetchall()
    conn.close()

    # Return the raw list of ToDos
    if result > 0:
        return ToDos
    else:
        return []

def create(toDo):
    conn = open_connection()
    with conn.cursor(cursor=pymysql.cursors.DictCursor) as cursor:
        cursor.execute('INSERT INTO todoTable (todo) VALUES (%s)', (toDo['todo']))
    conn.commit()
    conn.close()