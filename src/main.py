import json
from git_analyzer import get_context_for_gemini
from ai_reviewer import analyze_code
from github_client import post_commit_comment

def main():
    print("🔍 Sentinel: Récupération du dernier commit...")
    super_context = get_context_for_gemini()
    
    if not super_context:
        print("Aucun contexte généré. As-tu fait au moins un commit dans ce repository ?")
        return

    print("🧠 Sentinel: Analyse du code en cours par Gemini 3.8 Flash...")
    ai_response = analyze_code(super_context)
    
    if ai_response:
        # On affiche dans le terminal pour le debug local
        try:
            report = json.loads(ai_response)
            print(f"\n✅ Résumé : {report['summary']}")
            print(f"⚠️ {len(report.get('issues', []))} problème(s) trouvé(s).")
            
            # On tente de publier sur GitHub
            print("\n📡 Tentative de publication sur GitHub...")
            post_commit_comment(ai_response)
        except json.JSONDecodeError:
             print("Erreur de décodage JSON de la réponse de l'IA")

if __name__ == "__main__":
    main()