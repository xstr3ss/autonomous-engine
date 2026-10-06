def authenticate(user):
    if isinstance(user, list):
        if len(user) == 0:
            raise TypeError("List must contain at least one element")
        user = user[0]
    
    if not isinstance(user, str):
        raise TypeError("User must be a string or a list containing a string")
    
    return True
