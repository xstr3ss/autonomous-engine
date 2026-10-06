def authenticate(user):
    if isinstance(user, list):
        user = user[0]
    
    if not isinstance(user, str):
        raise TypeError("Input must be a string or a list containing a string.")
    
    if user == "admin":
        return True
    
    return False
