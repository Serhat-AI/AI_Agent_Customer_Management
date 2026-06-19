import os
from dotenv import load_dotenv

load_dotenv()

# Gmail
GMAIL_CREDENTIALS_PATH = os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json')
GMAIL_TOKEN_PATH = os.getenv('GMAIL_TOKEN_PATH', 'token.json')
GMAIL_USER_EMAIL = os.getenv('GMAIL_USER_EMAIL')
GMAIL_QUERY = os.getenv('GMAIL_QUERY', 'subject:RSD')

# LLM
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
USE_OLLAMA = os.getenv('USE_OLLAMA', 'false').lower() == 'true'
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral')

# Document Archive
PROJECT_DOCS_PATH = os.getenv('PROJECT_DOCS_PATH', './project_documents')
FILE_EXTENSIONS = os.getenv('FILE_EXTENSIONS', '.pdf,.docx,.txt').split(',')

# RAG
VECTOR_DB_PATH = os.getenv('VECTOR_DB_PATH', './vector_db')
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1000))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 200))
SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.6))

# Email Summary
SUMMARY_RECIPIENT_EMAIL = os.getenv('SUMMARY_RECIPIENT_EMAIL')

# Validate required configs
def validate_config():
    if not GMAIL_USER_EMAIL:
        raise ValueError("GMAIL_USER_EMAIL not configured in .env")
    if not SUMMARY_RECIPIENT_EMAIL:
        raise ValueError("SUMMARY_RECIPIENT_EMAIL not configured in .env")
    if not USE_OLLAMA and not OPENAI_API_KEY:
        raise ValueError("Either USE_OLLAMA=true or OPENAI_API_KEY must be configured")
