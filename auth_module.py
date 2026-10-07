def authenticate(user):
    if isinstance(user, list):
        if len(user) != 1:
            raise TypeError("Expected a single user identifier")
        user = user[0]
    
    if not isinstance(user, str):
        raise TypeError("User identifier must be a string or a list containing a single string")
    
    return user == "admin"
