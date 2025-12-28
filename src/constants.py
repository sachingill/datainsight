import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables, with fallback to defaults
# OPENAI_API_KEY should be provided by user in the UI or via environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)  # No default value - must be provided by user
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-4.1-2025-04-14")
DATABASE = os.getenv("DATABASE", "ecommerce")
