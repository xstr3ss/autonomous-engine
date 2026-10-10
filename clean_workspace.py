import os

# Clean UTF-8 writes to fix the null byte corruption
with open('enterprise_db.py', 'w', encoding='utf-8') as f:
    f.write('def establish_secure_connection():\n    return "Connected to Enterprise DB!"\n')

with open('server.py', 'w', encoding='utf-8') as f:
    f.write('def start_server():\n    # BUG: I forgot to import the DB module, and forgot the function name!\n    # I think it has something to do with "secure connection" or "enterprise".\n    connection = connect_to_db()\n    return connection\n')

with open('test_server.py', 'w', encoding='utf-8') as f:
    f.write('from server import start_server\n\ndef test_start_server():\n    assert start_server() == "Connected to Enterprise DB!"\n')

print("✅ Workspace cleaned and encoded in pure UTF-8!")
