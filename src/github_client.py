import os
import requests
import time
import jwt

def get_app_installation_token():
    # ... (Garde la fonction get_app_installation_token exactement comme elle est) ...
    app_id = os.environ.get("SENTINEL_APP_ID")
    private_key_pem = os.environ.get("SENTINEL_PRIVATE_KEY")
    repo = os.environ.get("GITHUB_REPOSITORY") 
    
    if not all([app_id, private_key_pem, repo]):
        print("⚠️ Variables d'environnement de la GitHub App manquantes.")
        return None

    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + (10 * 60),
        "iss": app_id
    }
    
    try:
        encoded_jwt = jwt.encode(payload, private_key_pem, algorithm="RS256")
    except Exception as e:
        print(f"❌ Erreur lors de la signature du JWT : {e}")
        return None

    headers = {
        "Authorization": f"Bearer {encoded_jwt}",
        "Accept": "application/vnd.github.v3+json"
    }
    owner, repo_name = repo.split("/")
    
    install_url = f"https://api.github.com/repos/{owner}/{repo_name}/installation"
    response = requests.get(install_url, headers=headers, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Erreur lors de la récupération de l'installation : {response.text}")
        return None
        
    installation_id = response.json().get("id")

    token_url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    token_response = requests.post(token_url, headers=headers, timeout=10)
    
    if token_response.status_code != 201:
         print(f"❌ Erreur lors de la création du token d'accès : {token_response.text}")
         return None
         
    return token_response.json().get("token")


def post_commit_comment(report: dict) -> bool:
    """Publie l'analyse de Sentinel en tant que commentaire sur le commit."""
    
    repo = os.environ.get("GITHUB_REPOSITORY") 
    commit_sha = os.environ.get("GITHUB_SHA")
    token = get_app_installation_token()
    
    if not all([token, repo, commit_sha]):
        print("⚠️ Impossible de poster : informations ou token manquants.")
        return False

    markdown_body = f"""## 🦅 Sentinel AI Code Review\n\n> **Résumé :** {report.get('summary', 'Analyse terminée.')}\n\n"""
    
    if 'architecture_feedback' in report and report['architecture_feedback']:
        markdown_body += f"### 🏛️ Feedback Architecture\n{report['architecture_feedback']}\n\n"
    
    issues = report.get('issues', [])
    if not issues:
        markdown_body += "✅ **Aucun problème détecté ! Beau travail.**\n"
    else:
        markdown_body += f"### ⚠️ {len(issues)} point(s) d'attention\n\n"
        for issue in issues:
            severity = issue.get('severity', 'low').lower()
            severity_icon = "🚨" if severity == "critical" else "🔴" if severity == "high" else "🟠" if severity == "medium" else "🔵"
            
            markdown_body += f"#### {severity_icon} [{severity.upper()}] Ligne {issue.get('line', 'N/A')} - {issue.get('title', issue.get('type', 'Général'))}\n"
            markdown_body += f"- **Description** : {issue.get('description', '')}\n"
            
            # Nettoyage anti-bug Markdown : suppression des backticks hallucinés par le LLM
            suggestion_text = issue.get('suggestion', '').strip()
            if suggestion_text.startswith('```'):
                lines = suggestion_text.split('\n')
                if lines[0].startswith('```'): lines = lines[1:]
                if lines and lines[-1].startswith('```'): lines = lines[:-1]
                suggestion_text = '\n'.join(lines).strip()
            
            if '\n' in suggestion_text:
                markdown_body += f"- **Suggestion** :\n```text\n{suggestion_text}\n```\n\n"
            else:
                markdown_body += f"- **Suggestion** : `{suggestion_text}`\n\n"
            
    markdown_body += "---\n*🤖 Code review générée automatiquement par **Sentinel** (Gemini 3.8 Flash).*"

    url = f"https://api.github.com/repos/{repo}/commits/{commit_sha}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": markdown_body}

    response = requests.post(url, headers=headers, json=data, timeout=10)
    
    if response.status_code == 201:
        print(f"✅ Commentaire publié avec succès sur le commit {commit_sha[:7]} en tant que GitHub App !")
        return True
    else:
        print(f"❌ Erreur lors de la publication : {response.status_code}")
        print(response.text)
        return False