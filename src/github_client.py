import os
import requests
import time
import jwt
import re

def get_auth_token():
    """Détermine dynamiquement la méthode d'authentification à utiliser."""
    
    app_id = os.environ.get("SENTINEL_APP_ID")
    private_key_pem = os.environ.get("SENTINEL_PRIVATE_KEY")
    github_token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY") 

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

    if github_token:
        return github_token

    print("❌ Aucune méthode d'authentification trouvée (ni App, ni Token).")
    return None

def post_github_comment(report: dict, event_name: str, event_data: dict) -> bool:
    """Publie l'analyse de Sentinel sur l'Endpoint approprié (Commit, PR ou Issue)."""
    
    repo = os.environ.get("GITHUB_REPOSITORY") 
    token = get_auth_token()
    
    if not all([token, repo]):
        print("⚠️ Impossible de poster : informations système manquantes.")
        return False

    # Détermination de l'URL cible selon l'événement
    url = ""
    if event_name in ("issues", "pull_request", "pull_request_target"):
        # Pour les Issues et les PR, on poste sur l'endpoint des commentaires d'Issue (ID global)
        issue_number = event_data.get("issue", {}).get("number") or event_data.get("pull_request", {}).get("number") or event_data.get("number")
        
        if not issue_number:
            print("❌ Numéro d'Issue ou de PR introuvable.")
            return False
        url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    else:
        # Mode Push classique (Commits)
        commit_sha = os.environ.get("GITHUB_SHA")
        if not commit_sha:
            print("❌ SHA du commit introuvable.")
            return False
        url = f"https://api.github.com/repos/{repo}/commits/{commit_sha}/comments"

    # Construction du Markdown
    title = "🦅 Sentinel AI Code Review" if event_name != "issues" else "🦅 Sentinel AI Issue Triage"
    markdown_body = f"""## {title}\n\n> **Résumé :** {report.get('summary', 'Analyse terminée.')}\n\n"""
    
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
            
            issue_title = issue.get('title') or issue.get('type') or 'Général'
            
            # Formatage adapté si c'est une ligne de code ou juste une remarque globale (Issue)
            line_info = f" Ligne {issue.get('line')} -" if issue.get('line') else ""
            markdown_body += f"#### {severity_icon} [{severity.upper()}]{line_info} {issue_title}\n"
            
            description = issue.get('description') or ''
            markdown_body += f"- **Description** : {description}\n"
            
            suggestion_text = (issue.get('suggestion') or '').strip()
            
            # Nettoyage robuste : supprime l'ouverture (ex: ```python) et la fermeture (```) en périphérie
            suggestion_text = re.sub(r'^```[a-zA-Z0-9_-]*\n?', '', suggestion_text)
            suggestion_text = re.sub(r'\n?```$', '', suggestion_text).strip()
            
            if '\n' in suggestion_text:
                # On utilise un bloc vide pour éviter de forcer 'python' sur du YAML ou HTML
                markdown_body += f"- **Suggestion** :\n```\n{suggestion_text}\n```\n\n"
            else:
                markdown_body += f"- **Suggestion** : `{suggestion_text}`\n\n"
            
    markdown_body += "---\n*🤖 Support généré automatiquement par **Sentinel** (Gemini 3.8 Flash).*"

    MAX_GITHUB_COMMENT_LENGTH = 65000
    if len(markdown_body) > MAX_GITHUB_COMMENT_LENGTH:
        truncated = markdown_body[:MAX_GITHUB_COMMENT_LENGTH]
        if truncated.count('```') % 2 != 0:
            truncated += '\n```'
        markdown_body = truncated + '\n\n⚠️ *[Commentaire tronqué : volume maximal autorisé par GitHub atteint]*'

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": markdown_body}

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 201:
            print(f"✅ Commentaire publié avec succès ({event_name}) !")
            return True
        else:
            print(f"❌ Erreur lors de la publication : {response.status_code}\n{response.text}")
            return False
    except requests.RequestException as exc:
        print(f"❌ Échec réseau lors de la publication du commentaire : {exc}")
        return False