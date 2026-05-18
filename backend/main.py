# backend/main.py
"""
FastAPI Backend — I-Chat Multi-Tenant Chatbot
Endpoints:
  POST /auth/login        ← Authentification utilisateur
  POST /chat/question     ← Poser une question au chatbot
  GET  /health            ← Healthcheck
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
from pathlib import Path

# ── Import path setup ─────────────────────────────────────────────────────
for p in [str(Path(__file__).parent), str(Path(__file__).parent / "app")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.database.connection import DatabaseConnection

# ── Lazy import du planner (évite l'échec si Milvus/Groq absent) ─────────
_planner = None
def get_planner():
    global _planner
    if _planner is None:
        try:
            from app.agents.planner_agent_v8 import PlannerAgentV8
            _planner = PlannerAgentV8()
            print("[API] ✅ PlannerAgentV8 chargé.")
        except Exception as e:
            print(f"[API] ⚠️  PlannerAgentV8 non disponible : {e}")
    return _planner


# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="I-Chat API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # En prod : restreindre aux domaines frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mapping entreprise → tenant DB ────────────────────────────────────────
COMPANY_TENANT_MAP: Dict[str, str] = {
    "jln":                             "v3_tenant_jln",
    "khouribga":                       "v3_tenant_jln",
    "safi":                            "v3_tenant_Site_Safi",
    "site safi":                       "v3_tenant_Site_Safi",
    "ocp safi":                        "v3_tenant_Site_Safi",
    "cmcp":                            "v3_tenant_cmcp_ip",
    "cmcp ip":                         "v3_tenant_cmcp_ip",
    "casablanca chimie":               "v3_tenant_cmcp_ip",
    "cobomi":                          "v3_tenant_cobomi",
    "jfc4":                            "v3_tenant_jfc4",
    "jorf lasfar":                     "v3_tenant_jfc4",
    "jorf":                            "v3_tenant_jfc4",
    "nomac":                           "v3_tenant_nomac",
    "ntn":                             "v3_tenant_ntn",
    "onee":                            "v3_tenant_onee",
    "bouskoura":                       "v3_tenant_lafarge_holcim_bouskoura",
    "lafarge":                         "v3_tenant_lafarge_holcim_bouskoura",
    "lafarge holcim":                  "v3_tenant_lafarge_holcim_bouskoura",
    "lafarge holcim bouskoura":        "v3_tenant_lafarge_holcim_bouskoura",
}

# ─────────────────────────────────────────────────────────────────────────────
# Schémas Pydantic
# ─────────────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str

class QuestionRequest(BaseModel):
    question: str
    tenant_db: str
    response_mode: str = "data"   # "data" | "data_sql" | "data_sql_excel"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_authorized_tenants(companies_string: str) -> List[str]:
    """Retourne la liste des tenant_db autorisés pour un utilisateur."""
    if not companies_string:
        return []
    companies = [c.strip().lower() for c in companies_string.split(",")]
    tenants = set()
    for company in companies:
        for key, tenant_db in COMPANY_TENANT_MAP.items():
            if company == key or key in company or company in key:
                tenants.add(tenant_db)
    return list(tenants)


def fetch_user(email: str) -> Optional[Dict]:
    """Récupère un utilisateur depuis la base de données."""
    sql = """
        SELECT
            u.first_name  AS prenom,
            u.last_name   AS nom,
            u.email       AS email,
            u.password    AS mot_de_passe,
            GROUP_CONCAT(DISTINCT c.name SEPARATOR ', ') AS entreprises
        FROM i_sense_v3_devenv_db.users u
        INNER JOIN i_sense_v3_devenv_db.user_company uc ON u.id = uc.user_id
        INNER JOIN i_sense_v3_devenv_db.companies c     ON uc.company_id = c.id
        WHERE u.deleted_at IS NULL
          AND uc.deleted_at IS NULL
          AND c.deleted_at IS NULL
          AND u.active = 1
          AND u.email = %s
        GROUP BY u.id, u.first_name, u.last_name, u.email, u.password
        LIMIT 1
    """
    db = DatabaseConnection()
    try:
        if not db.connect("i_sense_v3_devenv_db"):
            return None
        rows = db.execute_query(sql, (email,))
        return rows[0] if rows else None
    except Exception as e:
        print(f"[fetch_user] Erreur : {e}")
        return None
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/auth/login")
def auth_login(req: LoginRequest):
    """
    Authentifie un utilisateur.
    - email   : adresse email
    - password: en production, hacher et comparer ; ici on accepte 'admin' comme passe-partout
    """
    if not req.email or not req.password:
        raise HTTPException(400, "Email et mot de passe requis.")

    user = fetch_user(req.email)
    if not user:
        raise HTTPException(401, "Utilisateur introuvable ou inactif.")

    # Vérification du mot de passe
    stored_pass = user.get("mot_de_passe", "") or ""
    if req.password != "admin" and req.password != stored_pass:
        raise HTTPException(401, "Mot de passe incorrect.")

    authorized_tenants = get_authorized_tenants(user.get("entreprises", ""))

    return {
        "prenom":              user.get("prenom", ""),
        "nom":                 user.get("nom", ""),
        "email":               user.get("email", ""),
        "entreprises":         user.get("entreprises", ""),
        "authorized_tenants":  authorized_tenants,
    }


def clean_natural_response(text: str) -> str:
    """
    Supprime les tableaux Markdown de la réponse naturelle.
    Les données sont déjà affichées dans le tableau HTML du frontend.
    """
    if not text:
        return text
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        # Ignorer les lignes qui ressemblent à un tableau Markdown
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            continue
        if stripped.startswith("|--") or stripped.startswith("| --"):
            continue
        cleaned.append(line)
    # Supprimer les lignes vides consécutives
    result = "\n".join(cleaned).strip()
    return result


@app.post("/chat/question")
def chat_question(req: QuestionRequest):
    """
    Traite une question utilisateur sur le tenant sélectionné.
    """
    if not req.question.strip():
        raise HTTPException(400, "La question ne peut pas être vide.")

    planner = get_planner()
    if not planner:
        raise HTTPException(503, "Moteur IA non disponible. Vérifiez Groq/Milvus.")

    try:
        # Passer le tenant forcé directement au planner (méthode V8)
        result = planner.process_question(
            question=req.question,
            forced_tenant_db=req.tenant_db,
        )

        natural = result.get("natural_response", "")
        # Si on a des données tabulaires, supprimer le tableau markdown du texte
        if result.get("rows"):
            natural = clean_natural_response(natural)

        response = {
            "success":          result.get("success", False),
            "natural_response": natural,
            "tenant":           req.tenant_db,
            "method":           result.get("method", "unknown"),
            "processing_time":  result.get("processing_time", 0),
            "category":         result.get("category", "unknown"),
            "row_count":        result.get("row_count", 0),
        }

        # Inclure SQL selon le mode
        if req.response_mode in ("data_sql", "data_sql_excel") and result.get("sql"):
            response["sql"] = result["sql"]

        # Inclure les données tabulaires
        if result.get("rows") is not None:
            response["rows"]    = result["rows"]
            response["columns"] = result.get("columns", [])

        if result.get("error"):
            response["error"] = result["error"]

        return response

    except Exception as e:
        print(f"[chat_question] Erreur : {e}")
        raise HTTPException(500, f"Erreur interne : {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# Démarrage
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


# ----------------------------------------------------------------------------------2-----------------

# # backend/main.py
# """
# FastAPI Backend — I-Chat Multi-Tenant Chatbot
# Endpoints:
#   POST /auth/login        ← Authentification utilisateur
#   POST /chat/question     ← Poser une question au chatbot
#   GET  /health            ← Healthcheck
# """

# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import Optional, List, Dict, Any
# import sys
# from pathlib import Path

# # ── Import path setup ─────────────────────────────────────────────────────
# for p in [str(Path(__file__).parent), str(Path(__file__).parent / "app")]:
#     if p not in sys.path:
#         sys.path.insert(0, p)

# from app.database.connection import DatabaseConnection

# # ── Lazy import du planner (évite l'échec si Milvus/Groq absent) ─────────
# _planner = None
# def get_planner():
#     global _planner
#     if _planner is None:
#         try:
#             from app.agents.planner_agent_v8 import PlannerAgentV8
#             _planner = PlannerAgentV8()
#             print("[API] ✅ PlannerAgentV8 chargé.")
#         except Exception as e:
#             print(f"[API] ⚠️  PlannerAgentV8 non disponible : {e}")
#     return _planner


# # ─────────────────────────────────────────────────────────────────────────────
# app = FastAPI(title="I-Chat API", version="1.0.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],          # En prod : restreindre aux domaines frontend
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ── Mapping entreprise → tenant DB ────────────────────────────────────────
# COMPANY_TENANT_MAP: Dict[str, str] = {
#     "jln":                             "v3_tenant_jln",
#     "khouribga":                       "v3_tenant_jln",
#     "safi":                            "v3_tenant_Site_Safi",
#     "site safi":                       "v3_tenant_Site_Safi",
#     "ocp safi":                        "v3_tenant_Site_Safi",
#     "cmcp":                            "v3_tenant_cmcp_ip",
#     "cmcp ip":                         "v3_tenant_cmcp_ip",
#     "casablanca chimie":               "v3_tenant_cmcp_ip",
#     "cobomi":                          "v3_tenant_cobomi",
#     "jfc4":                            "v3_tenant_jfc4",
#     "jorf lasfar":                     "v3_tenant_jfc4",
#     "jorf":                            "v3_tenant_jfc4",
#     "nomac":                           "v3_tenant_nomac",
#     "ntn":                             "v3_tenant_ntn",
#     "onee":                            "v3_tenant_onee",
#     "bouskoura":                       "v3_tenant_lafarge_holcim_bouskoura",
#     "lafarge":                         "v3_tenant_lafarge_holcim_bouskoura",
#     "lafarge holcim":                  "v3_tenant_lafarge_holcim_bouskoura",
#     "lafarge holcim bouskoura":        "v3_tenant_lafarge_holcim_bouskoura",
# }

# # ─────────────────────────────────────────────────────────────────────────────
# # Schémas Pydantic
# # ─────────────────────────────────────────────────────────────────────────────

# class LoginRequest(BaseModel):
#     email: str
#     password: str

# class QuestionRequest(BaseModel):
#     question: str
#     tenant_db: str
#     response_mode: str = "data"   # "data" | "data_sql" | "data_sql_excel"


# # ─────────────────────────────────────────────────────────────────────────────
# # Helpers
# # ─────────────────────────────────────────────────────────────────────────────

# def get_authorized_tenants(companies_string: str) -> List[str]:
#     """Retourne la liste des tenant_db autorisés pour un utilisateur."""
#     if not companies_string:
#         return []
#     companies = [c.strip().lower() for c in companies_string.split(",")]
#     tenants = set()
#     for company in companies:
#         for key, tenant_db in COMPANY_TENANT_MAP.items():
#             if company == key or key in company or company in key:
#                 tenants.add(tenant_db)
#     return list(tenants)


# def fetch_user(email: str) -> Optional[Dict]:
#     """Récupère un utilisateur depuis la base de données."""
#     sql = """
#         SELECT
#             u.first_name  AS prenom,
#             u.last_name   AS nom,
#             u.email       AS email,
#             u.password    AS mot_de_passe,
#             GROUP_CONCAT(DISTINCT c.name SEPARATOR ', ') AS entreprises
#         FROM i_sense_v3_devenv_db.users u
#         INNER JOIN i_sense_v3_devenv_db.user_company uc ON u.id = uc.user_id
#         INNER JOIN i_sense_v3_devenv_db.companies c     ON uc.company_id = c.id
#         WHERE u.deleted_at IS NULL
#           AND uc.deleted_at IS NULL
#           AND c.deleted_at IS NULL
#           AND u.active = 1
#           AND u.email = %s
#         GROUP BY u.id, u.first_name, u.last_name, u.email, u.password
#         LIMIT 1
#     """
#     db = DatabaseConnection()
#     try:
#         if not db.connect("i_sense_v3_devenv_db"):
#             return None
#         rows = db.execute_query(sql, (email,))
#         return rows[0] if rows else None
#     except Exception as e:
#         print(f"[fetch_user] Erreur : {e}")
#         return None
#     finally:
#         db.close()


# # ─────────────────────────────────────────────────────────────────────────────
# # Routes
# # ─────────────────────────────────────────────────────────────────────────────

# @app.get("/health")
# def health():
#     return {"status": "ok", "version": "1.0.0"}


# @app.post("/auth/login")
# def auth_login(req: LoginRequest):
#     """
#     Authentifie un utilisateur.
#     - email   : adresse email
#     - password: en production, hacher et comparer ; ici on accepte 'admin' comme passe-partout
#     """
#     if not req.email or not req.password:
#         raise HTTPException(400, "Email et mot de passe requis.")

#     user = fetch_user(req.email)
#     if not user:
#         raise HTTPException(401, "Utilisateur introuvable ou inactif.")

#     # Vérification du mot de passe
#     stored_pass = user.get("mot_de_passe", "") or ""
#     if req.password != "admin" and req.password != stored_pass:
#         raise HTTPException(401, "Mot de passe incorrect.")

#     authorized_tenants = get_authorized_tenants(user.get("entreprises", ""))

#     return {
#         "prenom":              user.get("prenom", ""),
#         "nom":                 user.get("nom", ""),
#         "email":               user.get("email", ""),
#         "entreprises":         user.get("entreprises", ""),
#         "authorized_tenants":  authorized_tenants,
#     }


# @app.post("/chat/question")
# def chat_question(req: QuestionRequest):
#     """
#     Traite une question utilisateur sur le tenant sélectionné.
#     """
#     if not req.question.strip():
#         raise HTTPException(400, "La question ne peut pas être vide.")

#     planner = get_planner()
#     if not planner:
#         raise HTTPException(503, "Moteur IA non disponible. Vérifiez Groq/Milvus.")

#     try:
#         # Passer le tenant forcé directement au planner (méthode V8)
#         result = planner.process_question(
#             question=req.question,
#             forced_tenant_db=req.tenant_db,
#         )

#         response = {
#             "success":          result.get("success", False),
#             "natural_response": result.get("natural_response", ""),
#             "tenant":           req.tenant_db,
#             "method":           result.get("method", "unknown"),
#             "processing_time":  result.get("processing_time", 0),
#             "category":         result.get("category", "unknown"),
#             "row_count":        result.get("row_count", 0),
#         }

#         # Inclure SQL selon le mode
#         if req.response_mode in ("data_sql", "data_sql_excel") and result.get("sql"):
#             response["sql"] = result["sql"]

#         # Inclure les données tabulaires
#         if result.get("rows") is not None:
#             response["rows"]    = result["rows"]
#             response["columns"] = result.get("columns", [])

#         if result.get("error"):
#             response["error"] = result["error"]

#         return response

#     except Exception as e:
#         print(f"[chat_question] Erreur : {e}")
#         raise HTTPException(500, f"Erreur interne : {str(e)}")


# # ─────────────────────────────────────────────────────────────────────────────
# # Démarrage
# # ─────────────────────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

















# ---------------------------------------------------------------------------3--------------------------------




# # # backend/main.py
# """
# FastAPI Backend — I-Chat Multi-Tenant Chatbot
# Endpoints:
#   POST /auth/login        ← Authentification utilisateur
#   POST /chat/question     ← Poser une question au chatbot
#   GET  /health            ← Healthcheck
# """

# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import Optional, List, Dict, Any
# import sys
# from pathlib import Path

# # ── Import path setup ─────────────────────────────────────────────────────
# BASE_DIR = Path(__file__).parent
# for p in [str(BASE_DIR), str(BASE_DIR / "app")]:
#     if p not in sys.path:
#         sys.path.insert(0, p)

# from app.database.connection import DatabaseConnection

# # ── Lazy import du planner ────────────────────────────────────────────────
# _planner = None

# def get_planner():
#     global _planner
#     if _planner is None:
#         try:
#             from app.agents.planner_agent_v8 import PlannerAgentV8
#             _planner = PlannerAgentV8()
#             print("[API] ✅ PlannerAgentV8 chargé.")
#         except Exception as e:
#             print(f"[API] ⚠️  PlannerAgentV8 non disponible : {e}")
#     return _planner


# # ─────────────────────────────────────────────────────────────────────────────
# app = FastAPI(title="I-Chat API", version="1.0.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],          # En prod : mettre ["http://localhost:3000"]
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ── Mapping entreprise → tenant DB ────────────────────────────────────────
# COMPANY_TENANT_MAP: Dict[str, str] = {
#     "jln":                              "v3_tenant_jln",
#     "khouribga":                        "v3_tenant_jln",
#     "safi":                             "v3_tenant_Site_Safi",
#     "site safi":                        "v3_tenant_Site_Safi",
#     "ocp safi":                         "v3_tenant_Site_Safi",
#     "cmcp":                             "v3_tenant_cmcp_ip",
#     "cmcp ip":                          "v3_tenant_cmcp_ip",
#     "casablanca chimie":                "v3_tenant_cmcp_ip",
#     "cobomi":                           "v3_tenant_cobomi",
#     "jfc4":                             "v3_tenant_jfc4",
#     "jorf lasfar":                      "v3_tenant_jfc4",
#     "jorf":                             "v3_tenant_jfc4",
#     "nomac":                            "v3_tenant_nomac",
#     "ntn":                              "v3_tenant_ntn",
#     "onee":                             "v3_tenant_onee",
#     "bouskoura":                        "v3_tenant_lafarge_holcim_bouskoura",
#     "lafarge":                          "v3_tenant_lafarge_holcim_bouskoura",
#     "lafarge holcim":                   "v3_tenant_lafarge_holcim_bouskoura",
#     "lafarge holcim bouskoura":         "v3_tenant_lafarge_holcim_bouskoura",
# }


# # ─────────────────────────────────────────────────────────────────────────────
# # Schémas Pydantic
# # ─────────────────────────────────────────────────────────────────────────────

# class LoginRequest(BaseModel):
#     email: str
#     password: str


# class QuestionRequest(BaseModel):
#     question: str
#     tenant_db: str
#     response_mode: str = "data"   # "data" | "data_sql" | "data_sql_excel"


# # ─────────────────────────────────────────────────────────────────────────────
# # Helpers
# # ─────────────────────────────────────────────────────────────────────────────

# def get_authorized_tenants(companies_string: str) -> List[str]:
#     """Retourne la liste des tenant_db autorisés pour un utilisateur."""
#     if not companies_string:
#         return []
#     companies = [c.strip().lower() for c in companies_string.split(",")]
#     tenants = set()
#     for company in companies:
#         for key, tenant_db in COMPANY_TENANT_MAP.items():
#             if company == key or key in company or company in key:
#                 tenants.add(tenant_db)
#     return list(tenants)


# def fetch_user(email: str) -> Optional[Dict]:
#     """Récupère un utilisateur depuis la base de données."""
#     sql = """
#         SELECT
#             u.first_name  AS prenom,
#             u.last_name   AS nom,
#             u.email       AS email,
#             u.password    AS mot_de_passe,
#             GROUP_CONCAT(DISTINCT c.name SEPARATOR ', ') AS entreprises
#         FROM i_sense_v3_devenv_db.users u
#         INNER JOIN i_sense_v3_devenv_db.user_company uc ON u.id = uc.user_id
#         INNER JOIN i_sense_v3_devenv_db.companies c     ON uc.company_id = c.id
#         WHERE u.deleted_at IS NULL
#           AND uc.deleted_at IS NULL
#           AND c.deleted_at IS NULL
#           AND u.active = 1
#           AND u.email = %s
#         GROUP BY u.id, u.first_name, u.last_name, u.email, u.password
#         LIMIT 1
#     """
#     db = DatabaseConnection()
#     try:
#         if not db.connect("i_sense_v3_devenv_db"):
#             return None
#         rows = db.execute_query(sql, (email,))
#         return rows[0] if rows else None
#     except Exception as e:
#         print(f"[fetch_user] Erreur : {e}")
#         return None
#     finally:
#         db.close()


# # ─────────────────────────────────────────────────────────────────────────────
# # Routes
# # ─────────────────────────────────────────────────────────────────────────────

# @app.get("/health")
# def health():
#     return {"status": "ok", "version": "1.0.0"}


# @app.post("/auth/login")
# def auth_login(req: LoginRequest):
#     """Authentifie un utilisateur via email + mot de passe."""
#     if not req.email or not req.password:
#         raise HTTPException(status_code=400, detail="Email et mot de passe requis.")

#     user = fetch_user(req.email)
#     if not user:
#         raise HTTPException(status_code=401, detail="Utilisateur introuvable ou inactif.")

#     # Vérification mot de passe
#     # → Accepte 'admin' comme code universel OU compare en clair
#     stored_pass = user.get("mot_de_passe", "") or ""
#     if req.password != "admin" and req.password != stored_pass:
#         raise HTTPException(status_code=401, detail="Mot de passe incorrect.")

#     authorized_tenants = get_authorized_tenants(user.get("entreprises", ""))

#     return {
#         "prenom":             user.get("prenom", ""),
#         "nom":                user.get("nom", ""),
#         "email":              user.get("email", ""),
#         "entreprises":        user.get("entreprises", ""),
#         "authorized_tenants": authorized_tenants,
#     }


# @app.post("/chat/question")
# def chat_question(req: QuestionRequest):
#     """Traite une question utilisateur sur le tenant sélectionné."""
#     if not req.question.strip():
#         raise HTTPException(status_code=400, detail="La question ne peut pas être vide.")

#     if not req.tenant_db.strip():
#         raise HTTPException(status_code=400, detail="Le tenant_db est requis.")

#     planner = get_planner()
#     if not planner:
#         raise HTTPException(
#             status_code=503,
#             detail="Moteur IA non disponible. Vérifiez Groq API key et Milvus."
#         )

#     try:
#         # ── Appel du planner avec le tenant forcé ─────────────────────
#         result = planner.process_question(
#             question=req.question,
#             forced_tenant_db=req.tenant_db
#         )

#         # ── Construction de la réponse ─────────────────────────────────
#         response = {
#             "success":          result.get("success", False),
#             "natural_response": result.get("natural_response", ""),
#             "tenant":           req.tenant_db,
#             "method":           result.get("method", "unknown"),
#             "processing_time":  result.get("processing_time", 0),
#             "category":         result.get("category", "unknown"),
#             "row_count":        result.get("row_count", 0),
#         }

#         # Inclure SQL selon le mode de réponse
#         if req.response_mode in ("data_sql", "data_sql_excel") and result.get("sql"):
#             response["sql"] = result["sql"]

#         # Inclure les données tabulaires
#         if result.get("rows") is not None:
#             response["rows"]    = result["rows"]
#             response["columns"] = result.get("columns", [])

#         if result.get("error"):
#             response["error"] = result["error"]

#         return response

#     except Exception as e:
#         print(f"[chat_question] Erreur : {e}")
#         raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")


# # ─────────────────────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)