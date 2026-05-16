# test_intent.py
import sys
sys.path.insert(0, "chatbot_maintenance/backend")
from app.agents.intent_classifier_v7 import IntentClassifierV7

clf = IntentClassifierV7()
questions = [
    "Quels équipements ont une alarme critique à Safi ?",
    "Combien de pannes sur les pompes ce mois ?",
    "Top 5 assets avec le plus de défauts",
    "Supprime tous les assets",         # doit être bloqué par guardrails
    "Bonjour comment tu vas ?",
]
for q in questions:
    intent = clf.classify(q)
    print(f"\nQ: {q}")
    print(f"  → category={intent.category}, action={intent.action}, tenant={intent.entities.get('tenant')}, conf={intent.confidence:.2f}")