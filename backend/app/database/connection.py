# connection.py
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
from pathlib import Path

# Charger les variables d'environnement
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class DatabaseConnection:
    """Gestion des connexions aux bases de données MySQL"""
    
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', '52.143.131.9'),
            'user': os.getenv('DB_USER', 'interns_read_user'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': int(os.getenv('DB_PORT', '3306'))
        }
        self.connection = None
    
    def connect(self, database: str) -> bool:
        """
        Se connecter à une base de données spécifique
        
        Args:
            database: Nom de la base de données
            
        Returns:
            bool: True si connexion réussie, False sinon
        """
        try:
            self.config['database'] = database
            self.connection = mysql.connector.connect(**self.config)
            print(f" Connecté à {database}")
            return True
        except Error as e:
            print(f" Erreur de connexion à {database}: {e}")
            return False
    
    def execute_query(self, query: str, params: tuple = None) -> list:
        """
        Exécuter une requête SQL et retourner les résultats
        
        Args:
            query: Requête SQL
            params: Paramètres pour la requête
            
        Returns:
            list: Résultats de la requête
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            print(f" Erreur requête: {e}")
            return []
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """
        Exécuter une requête UPDATE/INSERT/DELETE
        
        Args:
            query: Requête SQL
            params: Paramètres pour la requête
            
        Returns:
            int: Nombre de lignes affectées
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows
        except Error as e:
            print(f" Erreur mise à jour: {e}")
            self.connection.rollback()
            return 0
    
    def close(self):
        """Fermer la connexion"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print(" Connexion fermée")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()



# # connection.py
# import mysql.connector
# from mysql.connector import Error
# import os
# from dotenv import load_dotenv
# from pathlib import Path

# # Charger les variables d'environnement
# env_path = Path(__file__).parent.parent.parent / '.env'
# load_dotenv(dotenv_path=env_path)

# class DatabaseConnection:
#     """Gestion des connexions aux bases de données MySQL"""
    
#     def __init__(self):
#         self.config = {
#             'host': os.getenv('DB_HOST', 'isense-v3-dev-db.i-sense.io'),
#             'user': os.getenv('DB_USER', 'interns_user'),
#             'password': os.getenv('DB_PASSWORD', ''),
#             'port': int(os.getenv('DB_PORT', '3306'))
#         }
#         self.connection = None
    
#     def connect(self, database: str) -> bool:
#         """
#         Se connecter à une base de données spécifique
        
#         Args:
#             database: Nom de la base de données
            
#         Returns:
#             bool: True si connexion réussie, False sinon
#         """
#         try:
#             self.config['database'] = database
#             self.connection = mysql.connector.connect(**self.config)
#             print(f" Connecté à {database}")
#             return True
#         except Error as e:
#             print(f" Erreur de connexion à {database}: {e}")
#             return False
    
#     def execute_query(self, query: str, params: tuple = None) -> list:
#         """
#         Exécuter une requête SQL et retourner les résultats
        
#         Args:
#             query: Requête SQL
#             params: Paramètres pour la requête
            
#         Returns:
#             list: Résultats de la requête
#         """
#         try:
#             cursor = self.connection.cursor(dictionary=True)
#             cursor.execute(query, params or ())
#             results = cursor.fetchall()
#             cursor.close()
#             return results
#         except Error as e:
#             print(f" Erreur requête: {e}")
#             return []
    
#     def execute_update(self, query: str, params: tuple = None) -> int:
#         """
#         Exécuter une requête UPDATE/INSERT/DELETE
        
#         Args:
#             query: Requête SQL
#             params: Paramètres pour la requête
            
#         Returns:
#             int: Nombre de lignes affectées
#         """
#         try:
#             cursor = self.connection.cursor()
#             cursor.execute(query, params or ())
#             self.connection.commit()
#             affected_rows = cursor.rowcount
#             cursor.close()
#             return affected_rows
#         except Error as e:
#             print(f" Erreur mise à jour: {e}")
#             self.connection.rollback()
#             return 0
    
#     def close(self):
#         """Fermer la connexion"""
#         if self.connection and self.connection.is_connected():
#             self.connection.close()
#             print(" Connexion fermée")
    
#     def __enter__(self):
#         return self
    
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self.close()

