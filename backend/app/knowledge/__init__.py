# chatbot_maintenance/backend/app/knowledge/__init__.py
"""
Module de connaissances sur l'entreprise OCP
Contient des informations statiques (sans requêtes SQL)
"""

from .knowledge_base import KnowledgeBase

__all__ = ['KnowledgeBase']