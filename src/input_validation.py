"""
Input validation module for Text2SQL application.
Prevents SQL injection and validates user input.
"""

import re
from typing import Tuple, Optional


def validate_query_input(user_input: str) -> Tuple[bool, Optional[str]]:
    """
    Validate user input before processing.
    
    Args:
        user_input: The user's natural language query
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if input is valid, False otherwise
        - error_message: Error message if invalid, None if valid
    """
    if not user_input or not isinstance(user_input, str):
        return False, "Input must be a non-empty string"
    
    # Check input length
    if len(user_input) > 2000:
        return False, "Query too long. Maximum 2000 characters allowed."
    
    if len(user_input.strip()) < 3:
        return False, "Query too short. Please provide more details."
    
    # Check for SQL injection patterns
    dangerous_patterns = [
        (r';\s*(drop|delete|truncate|alter|create|insert|update)\s+', 'SQL injection attempt detected'),
        (r'union\s+select', 'SQL injection attempt detected'),
        (r'exec\s*\(', 'SQL injection attempt detected'),
        (r'xp_\w+', 'SQL injection attempt detected'),
        (r'sp_\w+', 'SQL injection attempt detected'),
        (r'--\s*$', 'SQL comment injection attempt'),
        (r'/\*.*\*/', 'SQL comment injection attempt'),
        (r';\s*--', 'SQL injection attempt detected'),
        (r'waitfor\s+delay', 'SQL injection attempt detected'),
        (r'shutdown', 'Dangerous SQL command detected'),
    ]
    
    user_input_lower = user_input.lower()
    for pattern, error_msg in dangerous_patterns:
        if re.search(pattern, user_input_lower, re.IGNORECASE):
            return False, error_msg
    
    # Check for excessive special characters (potential obfuscation)
    special_char_count = len(re.findall(r'[;\\\'\"`]', user_input))
    if special_char_count > 10:
        return False, "Input contains too many special characters. Please rephrase your query."
    
    return True, None


def sanitize_input(user_input: str) -> str:
    """
    Sanitize user input by removing potentially dangerous characters.
    
    Args:
        user_input: The user's natural language query
        
    Returns:
        Sanitized input string
    """
    # Remove null bytes
    sanitized = user_input.replace('\x00', '')
    
    # Remove control characters except newlines and tabs
    sanitized = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', sanitized)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    return sanitized

