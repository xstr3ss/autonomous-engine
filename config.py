from utils import deep_merge

# This should NEVER change during runtime.
DEFAULT_CONFIG = {
    "host": "localhost",
    "port": 8080,
    "db": {"name": "production", "user": "admin"}
}

def load_config(user_overrides):
    # Merges user settings with defaults
    # We must pass a deep copy of DEFAULT_CONFIG to deep_merge to prevent
    # the default configuration from being mutated by the merge operation.
    import copy
    safe_defaults = copy.deepcopy(DEFAULT_CONFIG)
    return deep_merge(safe_defaults, user_overrides)