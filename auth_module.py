def authenticate(user):
    if isinstance(user, list):
        user = user[0] if user else ""
    if not isinstance(user, str):
        raise TypeError("user must be a string or a list")
    return True