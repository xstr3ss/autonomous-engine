import os

# Clean up previous challenge files
for f in ['models.py', 'cart.py', 'test_cart.py']:
    if os.path.exists(f): os.remove(f)

# 1. Core Logic (The Bug is hidden here)
utils_code = """import copy

def deep_merge(dict1, dict2):
    # BUG: Mutates dict1 directly instead of creating a safe copy!
    # In Python, dictionaries are passed by reference.
    result = dict1
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
"""

# 2. Business Logic 
config_code = """from utils import deep_merge

# This should NEVER change during runtime.
DEFAULT_CONFIG = {
    "host": "localhost",
    "port": 8080,
    "db": {"name": "production", "user": "admin"}
}

def load_config(user_overrides):
    # Merges user settings with defaults
    return deep_merge(DEFAULT_CONFIG, user_overrides)
"""

# 3. The Test Suite
test_config_code = """from config import load_config, DEFAULT_CONFIG

def test_load_config_isolation():
    # User 1 loads config and changes the port and user
    user1_overrides = {"port": 9000, "db": {"user": "shyam"}}
    config1 = load_config(user1_overrides)
    
    assert config1["port"] == 9000
    assert config1["db"]["user"] == "shyam"
    
    # User 2 loads config with just a host change.
    # Because of the bug in utils.py, DEFAULT_CONFIG was permanently mutated by User 1!
    user2_overrides = {"host": "0.0.0.0"}
    config2 = load_config(user2_overrides)
    
    # This will fail because User 1's settings leaked into User 2's session!
    assert config2["port"] == 8080, f"Memory Leak! Expected port 8080, got {config2['port']}"
    assert config2["db"]["user"] == "admin", f"Memory Leak! Expected user admin, got {config2['db']['user']}"
"""

with open('utils.py', 'w') as f: f.write(utils_code)
with open('config.py', 'w') as f: f.write(config_code)
with open('test_config.py', 'w') as f: f.write(test_config_code)

print("🔥 SWE-bench Challenge Environment Built: [utils.py, config.py, test_config.py]")
