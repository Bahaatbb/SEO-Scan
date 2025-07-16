import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env file

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
GOOGLE_PSI_API_KEY = os.getenv("GOOGLE_PSI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")