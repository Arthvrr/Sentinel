import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def analyze_code(super_context, event_name):
    """Envoie le contexte global à Gemini en adaptant le prompt selon l'événement."""
    if not super_context or not super_context.strip():
        return None
        
    # Adaptation de la consigne selon l'événement GitHub
    task_description = "réaliser des Code Reviews exhaustives de ce nouveau code."
    if event_name == "issues":
        task_description = "analyser cette nouvelle Issue (Bug report ou Feature request), identifier les fichiers concernés dans l'arborescence, et proposer une piste de résolution architecturale ou de code."
        
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
            6. FORMATAGE DES SUGGESTIONS (CRITIQUE) : Dans le champ "suggestion", tu dois fournir UNIQUEMENT LE CODE BRUT ou la commande exacte. N'utilise JAMAIS de balises Markdown (comme ```python) autour de la suggestion. Le champ doit contenir la chaîne de caractères brute prête à être copiée-collée.

            Tu dois TOUJOURS répondre en JSON strict respectant cette structure exacte (adapte les champs si c'est une Issue) : 
            {{
            "summary": "Résumé analytique pointu (3-4 phrases).",
            "architecture_feedback": "Analyse critique de l'impact architectural ou localisation probable du bug.",
            "issues": [
                {{
                "severity": "critical|high|medium|low",
                "line": 42,
                "type": "Security|Performance|Architecture|Clean Code|Bug",
                "title": "Titre explicite du problème ou de la solution",
                "description": "Explication technique détaillée du problème ou de l'approche de résolution.",
                "suggestion": "Le bloc de code exact, la commande, ou le design pattern recommandé pour résoudre le problème de manière optimale."
                }}
            ]
            }}
            """,
            response_mime_type="application/json",
            temperature=0.2
        )
    )
    return response.text