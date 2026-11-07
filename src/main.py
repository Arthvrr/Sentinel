import sys
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
from git_analyzer import get_context_for_gemini
from ai_reviewer import analyze_code
from github_client import post_github_comment

# --- Modèles de validation Pydantic ---
class Issue(BaseModel):
    severity: str = 'low'
    line: Optional[int] = None
    title: Optional[str] = 'Général'
    type: Optional[str] = 'Général'
    description: str
    suggestion: str

class ReviewReport(BaseModel):
    summary: str
    architecture_feedback: Optional[str] = None
    issues: List[Issue] = Field(default_factory=list)
# --------------------------------------

def main():
    print("🔍 Sentinel: Analyse de l'événement GitHub...")
    # On récupère les 3 éléments du nouveau git_analyzer
    context_data = get_context_for_gemini()
    
    if not context_data:
        print("❌ Erreur : Impossible de générer le contexte d'analyse.", file=sys.stderr)
        sys.exit(1)
        
    super_context, event_name, event_data = context_data

    print(f"🧠 Sentinel: Analyse du contexte ({event_name}) par Gemini 3.8 Flash...")
    # On passe le type d'événement à l'IA pour qu'elle adapte son prompt
    ai_response = analyze_code(super_context, event_name)
    
    if ai_response:
        try:
            report = ReviewReport.model_validate_json(ai_response)
            
            print(f"\n✅ Résumé : {report.summary}")
            print(f"⚠️ {len(report.issues)} point(s) d'attention trouvé(s).")
            
            print("\n📡 Tentative de publication sur GitHub...")
            # On passe event_name et event_data au client pour qu'il construise la bonne URL
            success = post_github_comment(report.model_dump(), event_name, event_data)
            
            if not success:
                print("❌ Échec de la publication du rapport sur GitHub.", file=sys.stderr)
                sys.exit(1)
                
        except ValidationError as err:
            print(f"❌ Erreur critique : le modèle n'a pas respecté la structure JSON requise.\n{err}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()