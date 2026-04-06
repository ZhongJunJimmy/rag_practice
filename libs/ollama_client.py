"""
Central Ollama client instance.
"""
import os
from dotenv import load_dotenv
from ollama import Client
from libs.config import OLLAMA_HOST

load_dotenv()


client = Client(
    host="https://ollama.com",
    headers={'Authorization': 'Bearer ' + os.environ.get('OLLAMA_API_KEY')}
)

embedd_client = Client(host=OLLAMA_HOST)
