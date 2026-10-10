import os
for f in ['auth.py', 'test_auth.py', 'secrets.env']:
    if os.path.exists(f): os.remove(f)

# 1. The hidden database module (Tier 0 doesn't know it exists because it's not imported yet)
with open('enterprise_db.py', 'w') as f:
    f.write('''def establish_secure_connection():
    return "Connected to Enterprise DB!"
''')

# 2. The broken server file
with open('server.py', 'w') as f:
    f.write('''def start_server():
    # BUG: I forgot to import the DB module, and I forgot the function name!
    # I think it has something to do with "secure connection" or "enterprise".
    connection = connect_to_db() 
    return connection
''')

# 3. The Test
with open('test_server.py', 'w') as f:
    f.write('''from server import start_server
def test_start_server():
    assert start_server() == "Connected to Enterprise DB!"
''')

print("🔥 RAG Challenge Built: [enterprise_db.py, server.py, test_server.py]")
