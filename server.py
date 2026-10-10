def start_server():
    # BUG: I forgot to import the DB module, and forgot the function name!
    # I think it has something to do with "secure connection" or "enterprise".
    from enterprise_db import establish_secure_connection
    connection = establish_secure_connection()
    return connection
