"""
Configuration file for OpenAI model names and other settings
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Model Names
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
