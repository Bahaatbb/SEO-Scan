from llama_index.llms.openai import OpenAI
from ..env import OPENAI_API_KEY

llm = OpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY, temperature=0.3, request_timeout=990)
