# test_groq.py
import sys
import os
from dotenv import load_dotenv

# 1. Charger le fichier .env en mémoire avant tout le reste
load_dotenv() 

sys.path.insert(0, "chatbot_maintenance/backend")
from app.agents.llm_agent_v8 import LLMAgentV8

# 2. Maintenant, l'agent trouvera GROQ_API_KEY grâce à load_dotenv()
llm = LLMAgentV8()
print("Disponible:", llm.is_available())

r = llm.generate("vous etes qui ?")
print("Réponse:", r)

r2 = llm.generate_json('Réponds uniquement en JSON: {"test": "ok", "valeur": 42}')
print("JSON:", r2)