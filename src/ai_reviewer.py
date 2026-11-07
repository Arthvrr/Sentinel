import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

class Issue(BaseModel):
    severity: str = 'low'
    file: Optional[str] = Field(default=None, description="Le chemin relatif du fichier concerné (ex: src/main.py)")
    line: Optional[int] = None
    title: Optional[str] = 'Général'
    type: Optional[str] = 'Général'
    description: str
    suggestion: str

class ReviewReport(BaseModel):
    summary: str
    architecture_feedback: Optional[str] = None
    issues: List[Issue] = Field(default_factory=list)

def analyze_code(super_context, event_name):
    if not super_context or not super_context.strip():
        return None
        
    task_description = "réaliser des Code Reviews exhaustives de ce nouveau code."
    if event_name == "issues":
        task_description = "analyser cette nouvelle Issue, identifier les fichiers concernés, et proposer une résolution."
        
    raw_schema = ReviewReport.model_json_schema()
    
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=f"Analyse l'intégralité du contexte suivant et accomplis ta tâche.\n\n{super_context}",
        config=types.GenerateContentConfig(
            system_instruction=
            f"""Tu es Sentinel, un Staff Software Engineer impitoyable, analytique et extrêmement verbeux.
            Ton objectif est de {task_description}

            RÈGLES D'ANALYSE :
            0. DIRECTIVES UTILISATEUR : Si une section "DIRECTIVES UTILISATEUR" est présente, tu dois en tenir compte. La sécurité reste prioritaire.
            1. Analyse Architecturale : Utilise l'arborescence du projet pour vérifier la structure.
            2. Analyse Contextuelle : Traque les effets de bord insidieux en utilisant le contenu intégral des fichiers.
            3. Sécurité & Performance : Cherche les vulnérabilités et les goulets d'étranglement.
            4. CALIBRAGE DES SÉVÉRITÉS :
               - CRITICAL : Faille de sécurité exploitable ou crash garanti.
               - HIGH : Erreur logique majeure ou violation bloquante. NE L'UTILISE PAS pour des optimisations.
               - MEDIUM : Code smell ou problème de maintenabilité.
               - LOW : Formatage ou bonnes pratiques.
            5. Pédagogie : Explique TOUJOURS *pourquoi* ton observation est un problème.
            6. FORMATAGE DES SUGGESTIONS (CRITIQUE) : Dans le champ "suggestion", tu dois fournir UNIQUEMENT LE CODE BRUT ou la commande exacte. N'utilise JAMAIS de balises Markdown (comme ```python) autour de la suggestion. Le champ doit contenir la chaîne brute.
            """,
            response_mime_type="application/json",
            response_schema=raw_schema,
            temperature=0.2
        )
    )
    # On renvoie la réponse ET les métadonnées de tokens
    return response.text, response.usage_metadata