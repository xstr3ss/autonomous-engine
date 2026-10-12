def is_palindrome(word: str) -> bool:
    """
    Check if a word is a palindrome, ignoring spaces and case.
    
    Args:
        word: The string to check
        
    Returns:
        True if the word is a palindrome, False otherwise
    """
    cleaned = word.replace(" ", "").lower()
    return cleaned == cleaned[::-1]
