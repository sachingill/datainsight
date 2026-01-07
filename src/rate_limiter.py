"""
Rate limiting module for Text2SQL application.
Prevents abuse and protects API costs.
"""

import time
from collections import defaultdict
from typing import Dict, Tuple, Optional
import streamlit as st


class RateLimiter:
    """
    Simple in-memory rate limiter.
    For production, consider using Redis-based rate limiting.
    """
    
    def __init__(self):
        # Store request timestamps per user/session
        self.requests: Dict[str, list] = defaultdict(list)
        # Cleanup old entries periodically
        self.last_cleanup = time.time()
    
    def _cleanup_old_entries(self):
        """Remove entries older than 1 hour."""
        current_time = time.time()
        if current_time - self.last_cleanup > 3600:  # Cleanup every hour
            cutoff_time = current_time - 3600
            for key in list(self.requests.keys()):
                self.requests[key] = [
                    ts for ts in self.requests[key] 
                    if ts > cutoff_time
                ]
                if not self.requests[key]:
                    del self.requests[key]
            self.last_cleanup = current_time
    
    def _get_user_key(self) -> str:
        """Get unique identifier for the current user/session."""
        # Use session ID if available, otherwise use a default
        session_id = st.session_state.get('_session_id', id(st.session_state))
        return str(session_id)
    
    def check_rate_limit(
        self, 
        max_requests: int = 20, 
        time_window: int = 60
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user has exceeded rate limit.
        
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, error_message)
            - is_allowed: True if request is allowed, False if rate limited
            - error_message: Error message if rate limited, None if allowed
        """
        self._cleanup_old_entries()
        
        user_key = self._get_user_key()
        current_time = time.time()
        
        # Get requests in the current time window
        window_start = current_time - time_window
        recent_requests = [
            ts for ts in self.requests[user_key] 
            if ts > window_start
        ]
        
        # Check if limit exceeded
        if len(recent_requests) >= max_requests:
            oldest_request = min(recent_requests)
            wait_time = int(time_window - (current_time - oldest_request))
            return False, f"Rate limit exceeded. Please wait {wait_time} seconds before making another request. (Limit: {max_requests} requests per {time_window} seconds)"
        
        # Record this request
        self.requests[user_key].append(current_time)
        
        return True, None
    
    def get_remaining_requests(
        self, 
        max_requests: int = 20, 
        time_window: int = 60
    ) -> int:
        """
        Get remaining requests for current user.
        
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
            
        Returns:
            Number of remaining requests
        """
        self._cleanup_old_entries()
        
        user_key = self._get_user_key()
        current_time = time.time()
        window_start = current_time - time_window
        
        recent_requests = [
            ts for ts in self.requests[user_key] 
            if ts > window_start
        ]
        
        return max(0, max_requests - len(recent_requests))


# Global rate limiter instance
rate_limiter = RateLimiter()

