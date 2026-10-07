def authenticate(user):
    if isinstance(user, list):
        if len(user) != 1:
            raise TypeError("List must contain exactly one element")
        user = user[0]
    
    if not isinstance(user, str):
        raise TypeError("Input must be a string or a list containing a single string")
    
    if user == "admin":
        return True
    
    return False
