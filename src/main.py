import json #Imports
from git_analyzer import get_latest_commit_diff
from ai_reviewer import analyze_code

def main():
    print("🔍 Sentinel: Récupération du dernier commit...")
    diff = get_latest_commit_diff()
    
    if not diff:
        print("Aucun diff trouvé. As-tu fait au moins un commit dans ce repository ?")
        return

    print("🧠 Sentinel: Analyse du code en cours par Gemini 3.8 Flash...")
    ai_response = analyze_code(diff)
    
    if ai_response:
        # On transforme le texte JSON en dictionnaire Python
        report = json.loads(ai_response)
        print(f"\n✅ Résumé : {report['summary']}")
        
        issues = report.get('issues', [])
        if not issues:
            print("🎉 Aucun problème détecté ! Beau travail.")
        else:
            print(f"⚠️ {len(issues)} problème(s) trouvé(s) :\n")
            for issue in issues:
                print(f"[{issue['severity'].upper()}] Ligne {issue.get('line', 'N/A')} - {issue['type']}")
                print(f"Description : {issue['description']}")
                print(f"Suggestion  : {issue['suggestion']}\n")

if __name__ == "__main__":
    main()