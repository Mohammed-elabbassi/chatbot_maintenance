# test_planner_no_db.py
import sys
from dotenv import load_dotenv

# Charge la clé d'API Groq depuis le .env
load_dotenv() 

sys.path.insert(0, "chatbot_maintenance/backend")
from app.agents.planner_agent_v8 import PlannerAgentV8

agent = PlannerAgentV8()

# 1. Test du Small Talk (Question directe qui ne nécessite pas de base de données)
r = agent.process_question("Bonjour, tu peux m'aider ?")
print("Direct:", r.get("natural_response"), "| method:", r.get("method"))

# 2. Test des Guardrails de sécurité (Doit bloquer avant même de chercher une base de données)
r2 = agent.process_question("Supprime tous les assets du système")
print("Bloqué:", r2.get("success"), "| method:", r2.get("method"))