import json
from git_analyzer import get_latest_commit_diff
from ai_reviewer import analyze_code
from github_client import post_commit_comment

def main():
    print("🔍 Sentinel: Récupération du dernier commit...")
    diff = get_latest_commit_diff()
    
    if not diff:
        print("Aucun diff trouvé. As-tu fait au moins un commit dans ce repository ?")
        return

    print("🧠 Sentinel: Analyse du code en cours par Gemini 3.8 Flash...")
    ai_response = analyze_code(diff)
    
    if ai_response:
        # On affiche dans le terminal pour le debug local
        report = json.loads(ai_response)
        print(f"\n✅ Résumé : {report['summary']}")
        print(f"⚠️ {len(report.get('issues', []))} problème(s) trouvé(s).")
        
        # On tente de publier sur GitHub
        print("\n📡 Tentative de publication sur GitHub...")
        post_commit_comment(ai_response)

if __name__ == "__main__":
    main()