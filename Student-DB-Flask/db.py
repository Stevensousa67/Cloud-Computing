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
        result = cursor.execute('SELECT * FROM classTable;')
        students = cursor.fetchall()
        if result > 0:
            got_students = jsonify(students)
        else:
            got_students = 'No students in DB'
    conn.close()
    return got_students

def create(student):
    conn = open_connection()
    with conn.cursor(cursor=pymysql.cursors.DictCursor) as cursor:
        cursor.execute('INSERT INTO classTable (id, Name) VALUES (%s, %s)', (student['id'], student['name']))
    conn.commit()
    conn.close()