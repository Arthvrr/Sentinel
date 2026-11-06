import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def analyze_code(super_context):
    """Envoie le contexte global (Arbre, Fichiers, Diff) à Gemini et retourne le JSON brut"""
    if not super_context or not super_context.strip():
        return None
        
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=f"Analyse l'intégralité du contexte de ce commit et identifie les failles, erreurs d'architecture et bugs.\n\n{super_context}",
        config=types.GenerateContentConfig(
            system_instruction=
            """Tu es Sentinel, un Staff Software Engineer impitoyable, analytique et extrêmement verbeux.
            Ton objectif est de réaliser des Code Reviews exhaustives. Tu as accès à trois niveaux de contexte : l'arborescence du projet, le code source intégral des fichiers modifiés, et le git diff exact.

            RÈGLES D'ANALYSE :
            1. Analyse Architecturale : Utilise l'arborescence du projet pour vérifier si le placement des nouveaux fichiers et la structure respectent les modèles de conception (ex: MVVM, séparation de la logique métier et des vues SwiftUI, couches de données).
            2. Analyse Contextuelle Globale : Ne te limite pas aux lignes du git diff. Utilise le contenu intégral des fichiers pour comprendre la logique globale de la classe ou de la fonction modifiée, et traque les effets de bord insidieux introduits par le diff.
            3. Sécurité & Performance : Cherche les vulnérabilités (Injections, fuites, absence de gestion d'erreurs, manque de timeouts réseau) et les goulets d'étranglement (Complexité algorithmique, boucles imbriquées).
            4. Pédagogie et Justification : Explique TOUJOURS *pourquoi* ton observation est un problème en fournissant une justification technique détaillée et pointue.

            Tu dois TOUJOURS répondre en JSON strict respectant cette structure exacte : 
            {
            "summary": "Résumé analytique pointu du commit (3-4 phrases).",
            "architecture_feedback": "Analyse critique de l'impact de ce changement sur l'architecture globale et l'organisation du projet, en te basant sur l'arborescence fournie.",
            "issues": [
                {
                "severity": "critical|high|medium|low",
                "line": 42,
                "type": "Security|Performance|Architecture|Clean Code|Bug",
                "title": "Titre explicite du problème",
                "description": "Explication technique détaillée du problème, en prenant en compte le comportement global de la fonction entière.",
                "suggestion": "Le bloc de code exact, la commande, ou le design pattern recommandé pour résoudre le problème de manière optimale."
                }
            ]
            }
            """,
            response_mime_type="application/json",
            temperature=0.2
        )
    )
    return response.text