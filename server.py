from enterprise_db import establish_secure_connection

def start_server():
    connection = establish_secure_connection()
    return connection
