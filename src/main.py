import json
import sys
from git_analyzer import get_context_for_gemini
from ai_reviewer import analyze_code
from github_client import post_commit_comment

def main():
    print("🔍 Sentinel: Récupération du contexte et du dernier commit...")
    super_context = get_context_for_gemini()
    
    if not super_context:
        print("Aucun contexte généré. As-tu fait au moins un commit dans ce repository ?")
        return

    print("🧠 Sentinel: Analyse du code en cours par Gemini 3.8 Flash...")
    ai_response = analyze_code(super_context)
    
    if ai_response:
        try:
            # On parse le JSON une seule et unique fois ici
            report = json.loads(ai_response)
            
            print(f"\n✅ Résumé : {report.get('summary', 'Terminé.')}")
            print(f"⚠️ {len(report.get('issues', []))} problème(s) trouvé(s).")
            
            print("\n📡 Tentative de publication sur GitHub...")
            # On transmet le dictionnaire Python directement, pas le texte brut
            post_commit_comment(report)
            
        except json.JSONDecodeError as err:
            # On tue le process proprement pour que GitHub Actions affiche "Failed"
            print(f"❌ Erreur critique : le modèle n'a pas renvoyé un JSON valide.\n{err}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
