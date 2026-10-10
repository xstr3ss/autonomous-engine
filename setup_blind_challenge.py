import os
for f in ['models.py', 'cart.py', 'test_cart.py', 'config.py', 'utils.py', 'test_config.py', 'secrets.env']:
    if os.path.exists(f): os.remove(f)

# 1. A file NOT imported anywhere. Tier 0 cannot see this!
with open('secrets.env', 'w') as f:
    f.write('ENTERPRISE_API_KEY="sk-12345-real-key"\n')

# 2. The broken file
with open('auth.py', 'w') as f:
    f.write('''def authenticate():
    # BUG: We are missing the API key! We need to return it, 
    # but I forgot where it is stored in the file system.
    # Return the exact string of the API key from secrets.env
    return "missing_key"
''')

# 3. The Test file
with open('test_auth.py', 'w') as f:
    f.write('''from auth import authenticate
def test_auth():
    # The test expects the exact secret from the hidden env file
    assert authenticate() == "sk-12345-real-key"
''')

print("🔥 Blind Context Challenge Built: [auth.py, test_auth.py, secrets.env]")
