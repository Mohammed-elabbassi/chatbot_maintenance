# I-Chat Frontend — Guide d'installation

## Architecture

```
ichat-frontend/           ← React App
├── src/
│   ├── App.js            ← Router principal
│   ├── index.css         ← Variables CSS globales + animations
│   ├── context/
│   │   └── AuthContext.js  ← Gestion auth + mapping entreprise→tenant
│   ├── services/
│   │   └── api.js          ← Appels HTTP vers le backend + export Excel
│   └── pages/
│       ├── LoginPage.js/css    ← Page de connexion (style I-Chat)
│       └── DashboardPage.js/css ← Dashboard multi-tenant
backend_main.py           ← À copier dans votre backend FastAPI
```

## 1. Installation Frontend

```bash
cd ichat-frontend
npm install
npm start       # → http://localhost:3000
```

## 2. Backend FastAPI

Copiez `backend_main.py` dans votre dossier `backend/` et renommez-le en `main.py`.

```bash
pip install fastapi uvicorn python-multipart
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 3. Variable d'environnement

Créez `ichat-frontend/.env` :

```
REACT_APP_API_URL=http://localhost:8000
```

## 4. Authentification

- Email : celui de la base `i_sense_v3_devenv_db.users`
- Mot de passe : `admin` (universel) ou le mot de passe stocké en clair

## 5. Fonctionnement

| Option réponse           | Résultat                        |
|--------------------------|----------------------------------|
| LES DONNÉES              | Texte + tableau des données     |
| DONNÉES AVEC REQUÊTES    | Texte + tableau + SQL généré    |
| DONNÉES/REQUÊTES/TÉLÉCHARGER | Tout + bouton export Excel  |

## 6. Sécurité production

- Remplacer la vérification `password == "admin"` par bcrypt
- Ajouter JWT tokens
- Restreindre CORS aux domaines frontend uniquement
- Utiliser HTTPS

## Logique tenants

Le tenant actif est sélectionné dans la liste de gauche.
Toutes les questions envoyées utilisent ce tenant — sans besoin de le mentionner dans la question.
Les tenants non autorisés apparaissent avec 🔒 et sont non-cliquables.
