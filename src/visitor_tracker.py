"""
Visitor tracking module for Streamlit application.
Tracks and stores the number of unique visitors/sessions.
"""

import json
import os
from datetime import datetime
from pathlib import Path


VISITOR_LOG_FILE = "visitor_log.json"


def get_visitor_log_path():
    """Get the path to the visitor log file."""
    # Store in the project root directory
    current_dir = Path(__file__).parent.parent
    return current_dir / VISITOR_LOG_FILE


def load_visitor_data():
    """Load visitor data from file."""
    log_path = get_visitor_log_path()
    
    if log_path.exists():
        try:
            with open(log_path, 'r') as f:
                data = json.load(f)
                # If total_visitors is less than 10000, initialize it
                if data.get("total_visitors", 0) < 10000:
                    data["total_visitors"] = 10000
                    # Adjust unique_sessions to match
                    if isinstance(data.get("unique_sessions"), list):
                        # Create enough session IDs to match the count
                        existing_sessions = set(data.get("unique_sessions", []))
                        # Add dummy sessions to reach 10000
                        for i in range(10000 - len(existing_sessions)):
                            existing_sessions.add(f"initial_session_{i}")
                        data["unique_sessions"] = list(existing_sessions)
                    save_visitor_data(data)
                return data
        except (json.JSONDecodeError, IOError):
            # If file is corrupted, return default with 10000
            default_data = {
                "total_visitors": 10000,
                "unique_sessions": [f"initial_session_{i}" for i in range(10000)],
                "last_updated": datetime.now().isoformat()
            }
            save_visitor_data(default_data)
            return default_data
    
    # First time - initialize with 10000
    default_data = {
        "total_visitors": 10000,
        "unique_sessions": [f"initial_session_{i}" for i in range(10000)],
        "last_updated": datetime.now().isoformat()
    }
    save_visitor_data(default_data)
    return default_data


def save_visitor_data(data):
    """Save visitor data to file."""
    log_path = get_visitor_log_path()
    
    # Convert set to list for JSON serialization
    data_to_save = {
        "total_visitors": data["total_visitors"],
        "unique_sessions": list(data["unique_sessions"]),
        "last_updated": data.get("last_updated", datetime.now().isoformat())
    }
    
    try:
        with open(log_path, 'w') as f:
            json.dump(data_to_save, f, indent=2)
    except IOError as e:
        print(f"Error saving visitor data: {e}")


def track_visitor(session_id: str):
    """
    Track a visitor session and update the count.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        dict: Updated visitor statistics
    """
    data = load_visitor_data()
    
    # Convert list back to set for easier manipulation
    if isinstance(data.get("unique_sessions"), list):
        data["unique_sessions"] = set(data["unique_sessions"])
    elif "unique_sessions" not in data:
        data["unique_sessions"] = set()
    
    # Ensure minimum count of 10000
    if len(data["unique_sessions"]) < 10000:
        # Add initial sessions if needed
        for i in range(10000 - len(data["unique_sessions"])):
            data["unique_sessions"].add(f"initial_session_{i}")
        data["total_visitors"] = len(data["unique_sessions"])
        save_visitor_data(data)
    
    # Check if this is a new session (excluding initial sessions)
    # Convert session_id to string if it's not already
    session_id_str = str(session_id)
    is_new_visitor = session_id_str not in data["unique_sessions"] and not session_id_str.startswith("initial_session_")
    
    if is_new_visitor:
        data["unique_sessions"].add(session_id_str)
        data["total_visitors"] = len(data["unique_sessions"])
        data["last_updated"] = datetime.now().isoformat()
        save_visitor_data(data)
    
    return {
        "total_visitors": data["total_visitors"],
        "is_new_visitor": is_new_visitor,
        "last_updated": data.get("last_updated")
    }


def get_visitor_count():
    """Get the current visitor count without tracking."""
    data = load_visitor_data()
    
    # Convert list to set if needed
    if isinstance(data.get("unique_sessions"), list):
        unique_sessions = set(data["unique_sessions"])
    else:
        unique_sessions = data.get("unique_sessions", set())
    
    # Ensure minimum count of 10000
    if len(unique_sessions) < 10000:
        # Add initial sessions if needed
        for i in range(10000 - len(unique_sessions)):
            unique_sessions.add(f"initial_session_{i}")
        # Update and save
        data["unique_sessions"] = list(unique_sessions)
        data["total_visitors"] = len(unique_sessions)
        save_visitor_data(data)
    
    return {
        "total_visitors": len(unique_sessions),
        "last_updated": data.get("last_updated")
    }

