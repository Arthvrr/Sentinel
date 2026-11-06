import sys
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
from git_analyzer import get_context_for_gemini
from ai_reviewer import analyze_code
from github_client import post_commit_comment

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
    print("🔍 Sentinel: Récupération du contexte et du dernier commit...")
    super_context = get_context_for_gemini()
    
    if not super_context:
        print("Aucun contexte généré. As-tu fait au moins un commit dans ce repository ?")
        sys.exit(0)
        return

    print("🧠 Sentinel: Analyse du code en cours par Gemini 3.8 Flash...")
    ai_response = analyze_code(super_context)
    
    if ai_response:
        try:
            # 1. Validation stricte : Si l'IA hallucine, Pydantic lève une erreur
            report = ReviewReport.model_validate_json(ai_response)
            
            print(f"\n✅ Résumé : {report.summary}")
            print(f"⚠️ {len(report.issues)} problème(s) trouvé(s).")
            
            print("\n📡 Tentative de publication sur GitHub...")
            # On passe le dictionnaire validé
            success = post_commit_comment(report.model_dump())
            
            # 2. Gestion de l'échec silencieux
            if not success:
                print("❌ Échec de la publication du rapport sur GitHub.", file=sys.stderr)
                sys.exit(1)
                
        except ValidationError as err:
            print(f"❌ Erreur critique : le modèle n'a pas respecté la structure JSON requise.\n{err}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()