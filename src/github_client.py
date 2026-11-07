import os
import requests
import time
import jwt

def get_auth_token():
    """Détermine dynamiquement la méthode d'authentification à utiliser."""
    
    app_id = os.environ.get("SENTINEL_APP_ID")
    private_key_pem = os.environ.get("SENTINEL_PRIVATE_KEY")
    github_token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY") 

    # MODE 1 : Propriétaire (Avec le logo Sentinel, pour tes propres projets)
    if app_id and private_key_pem and repo:
        now = int(time.time())
        payload = {
            "iat": now - 60,
            "exp": now + (10 * 60),
            "iss": app_id
        }
        try:
            encoded_jwt = jwt.encode(payload, private_key_pem, algorithm="RS256")
            headers = {
                "Authorization": f"Bearer {encoded_jwt}",
                "Accept": "application/vnd.github.v3+json"
            }
            owner, repo_name = repo.split("/")
            install_url = f"https://api.github.com/repos/{owner}/{repo_name}/installation"
            response = requests.get(install_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                installation_id = response.json().get("id")
                token_url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
                token_response = requests.post(token_url, headers=headers, timeout=10)
                if token_response.status_code == 201:
                    return token_response.json().get("token")
        except Exception as e:
            print(f"⚠️ Échec du mode Propriétaire : {e}")

    # MODE 2 : Public / Open-Source (Sécurisé, utilise github-actions[bot])
    if github_token:
        return github_token

    print("❌ Aucune méthode d'authentification trouvée (ni App, ni Token).")
    return None

def post_commit_comment(report: dict) -> bool:
    """Publie l'analyse de Sentinel en tant que commentaire sur le commit."""
    
    repo = os.environ.get("GITHUB_REPOSITORY") 
    commit_sha = os.environ.get("GITHUB_SHA")
    token = get_auth_token()
    
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
            severity = (issue.get('severity') or 'low').lower()
            severity_icon = "🚨" if severity == "critical" else "🔴" if severity == "high" else "🟠" if severity == "medium" else "🔵"
            
            title = issue.get('title') or issue.get('type') or 'Général'
            markdown_body += f"#### {severity_icon} [{severity.upper()}] Ligne {issue.get('line', 'N/A')} - {title}\n"
            
            description = issue.get('description') or ''
            markdown_body += f"- **Description** : {description}\n"
            
            # Correction de l'AttributeError potentiel (NoneType)
            suggestion_text = (issue.get('suggestion') or '').strip()
            
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

    # Tronquer le commentaire si la limite de l'API GitHub est atteinte
    MAX_GITHUB_COMMENT_LENGTH = 65000
    if len(markdown_body) > MAX_GITHUB_COMMENT_LENGTH:
        markdown_body = markdown_body[:MAX_GITHUB_COMMENT_LENGTH] + "\n\n⚠️ *[Commentaire tronqué : volume maximal autorisé par GitHub (65536 octets) atteint]*"

    url = f"https://api.github.com/repos/{repo}/commits/{commit_sha}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": markdown_body}

    # Sécurisation des appels réseau avec try/except
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 201:
            print(f"✅ Commentaire publié avec succès sur le commit {commit_sha[:7]} !")
            return True
        else:
            print(f"❌ Erreur lors de la publication : {response.status_code}\n{response.text}")
            return False
    except requests.RequestException as exc:
        print(f"❌ Échec réseau lors de la publication du commentaire : {exc}")
        return False