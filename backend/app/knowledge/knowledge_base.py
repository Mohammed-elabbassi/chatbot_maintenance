# knowledge_base.py
"""
Chargeur de la base de connaissances OCP
Permet à l'Agent NLP d'accéder aux informations statiques
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

class KnowledgeBase:
    """Base de connaissances statiques sur OCP"""
    
    def __init__(self, json_path: str = None):
        """
        Initialiser la base de connaissances
        
        Args:
            json_path: Chemin vers le fichier JSON (optionnel)
        """
        if json_path is None:
            # Chemin par défaut
            json_path = Path(__file__).parent / 'ocp_systeme_complet.json'
        
        self.json_path = Path(json_path)
        self.data = self._load_json()
    
    def _load_json(self) -> Dict:
        """Charger le fichier JSON"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Fichier non trouvé: {self.json_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Erreur JSON: {e}")
            return {}
    
    def get_entreprise(self) -> Dict:
        """Récupérer les informations sur l'entreprise"""
        return self.data.get('entreprise', {})
    
    def get_sites(self) -> List[Dict]:
        """Récupérer la liste des sites"""
        return self.data.get('sites', [])
    
    def get_site_by_ville(self, ville: str) -> Optional[Dict]:
        """Rechercher un site par ville"""
        ville_lower = ville.lower()
        for site in self.get_sites():
            if ville_lower in site.get('ville', '').lower():
                return site
        return None
    
    def get_processus(self) -> Dict:
        """Récupérer le processus industriel"""
        return self.data.get('processus_industriel', {})
    
    def get_metiers(self) -> List[str]:
        """Récupérer la liste des métiers"""
        return self.data.get('metiers', [])
    
    def get_technologies(self) -> List[str]:
        """Récupérer la liste des technologies"""
        return self.data.get('technologies', [])
    
    def get_applications_ml(self) -> List[str]:
        """Récupérer les applications ML"""
        return self.data.get('applications_ml', [])
    
    def search_faq(self, question: str) -> Optional[str]:
        """
        Rechercher une réponse dans la FAQ
        
        Args:
            question: Question de l'utilisateur
        
        Returns:
            Réponse ou None
        """
        question_lower = question.lower()
        
        for faq in self.data.get('faq', []):
            # Recherche par mots-clés
            if any(mot in question_lower for mot in faq.get('question', '').lower().split()):
                return faq.get('reponse')
        
        return None
    
    def get_all_faq(self) -> List[Dict]:
        """Récupérer toute la FAQ"""
        return self.data.get('faq', [])
    
    def search(self, keyword: str) -> Dict[str, Any]:
        """
        Recherche globale dans la base de connaissances
        
        Args:
            keyword: Mot-clé à rechercher
        
        Returns:
            Dict avec les résultats
        """
        results = {
            'entreprise': [],
            'sites': [],
            'processus': [],
            'faq': [],
        }
        
        keyword_lower = keyword.lower()
        
        # Recherche dans entreprise
        entreprise = self.get_entreprise()
        for key, value in entreprise.items():
            if keyword_lower in str(value).lower():
                results['entreprise'].append({key: value})
        
        # Recherche dans sites
        for site in self.get_sites():
            if any(keyword_lower in str(v).lower() for v in site.values()):
                results['sites'].append(site)
        
        # Recherche dans FAQ
        for faq in self.get_all_faq():
            if keyword_lower in faq.get('question', '').lower() or \
               keyword_lower in faq.get('reponse', '').lower():
                results['faq'].append(faq)
        
        return results
    
    def get_summary(self) -> str:
        """Récupérer un résumé de l'entreprise"""
        entreprise = self.get_entreprise()
        return (
            f"{entreprise.get('nom', 'OCP')} est une entreprise {entreprise.get('pays', '')} "
            f"créée en {entreprise.get('creation', '')} dans le secteur : "
            f"{entreprise.get('secteur', '')}. "
            f"{entreprise.get('description', '')}"
        )


# ═══════════════════════════════════════════════════════════════
# EXEMPLE D'UTILISATION
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*80)
    print(" " * 25 + " BASE DE CONNAISSANCES OCP")
    print("="*80)
    
    kb = KnowledgeBase()
    
    # Résumé
    print("\n RÉSUMÉ:")
    print(kb.get_summary())
    
    # Sites
    print("\n SITES:")
    for site in kb.get_sites():
        print(f"   • {site['ville']} ({site['type']})")
    
    # Métiers
    print("\n MÉTIERS:")
    for metier in kb.get_metiers()[:5]:
        print(f"   • {metier}")
    
    # Technologies
    print("\n TECHNOLOGIES:")
    for tech in kb.get_technologies():
        print(f"   • {tech}")
    
    # Test de recherche
    print("\n" + "="*80)
    print(" " * 30 + " TESTS DE RECHERCHE")
    print("="*80)
    
    test_keywords = ["OCP", "Khouribga", "phosphate", "IA", "maintenance"]
    
    for keyword in test_keywords:
        results = kb.search(keyword)
        print(f"\n Recherche: '{keyword}'")
        print(f"   Entreprise: {len(results['entreprise'])} résultats")
        print(f"   Sites: {len(results['sites'])} résultats")
        print(f"   FAQ: {len(results['faq'])} résultats")
    
    print("\n" + "="*80 + "\n")