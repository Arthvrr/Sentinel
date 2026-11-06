import os
import requests
import json

def post_commit_comment(report_json):
    """Publie l'analyse de Sentinel en tant que commentaire sur le commit."""
    
    # GitHub Actions fournit automatiquement ces variables d'environnement
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")  # ex: Arthvrr/Sentinel
    commit_sha = os.environ.get("GITHUB_SHA")   # Le hash du commit actuel
    
    if not all([token, repo, commit_sha]):
        print("⚠️ Variables d'environnement GitHub manquantes. Mode local détecté.")
        return False

    # Transformer le JSON de Gemini en un beau message Markdown
    try:
        report = json.loads(report_json)
    except json.JSONDecodeError:
        print("⚠️ Erreur : Le rapport de Gemini n'est pas un JSON valide.")
        return False

    markdown_body = f"## 🦅 Sentinel AI Review\n\n**Résumé** : {report.get('summary', 'Analyse terminée.')}\n\n"
    
    issues = report.get('issues', [])
    if not issues:
        markdown_body += "✅ **Aucun problème détecté ! Beau travail.**"
    else:
        markdown_body += f"⚠️ **{len(issues)} problème(s) trouvé(s)** :\n\n"
        for issue in issues:
            severity_icon = "🔴" if issue.get('severity') == "high" else "🟠" if issue.get('severity') == "medium" else "🔵"
            markdown_body += f"### {severity_icon} [{issue.get('severity', 'N/A').upper()}] Ligne {issue.get('line', 'N/A')} - {issue.get('type', 'Général')}\n"
            markdown_body += f"- **Description** : {issue.get('description', '')}\n"
            markdown_body += f"- **Suggestion** : `{issue.get('suggestion', '')}`\n\n"

    # Préparation de la requête vers l'API GitHub
    url = f"https://api.github.com/repos/{repo}/commits/{commit_sha}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": markdown_body}

    # Envoi du commentaire
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print(f"✅ Commentaire publié avec succès sur le commit {commit_sha[:7]} !")
        return True
    else:
        print(f"❌ Erreur lors de la publication : {response.status_code}")
        print(response.text)
        return False