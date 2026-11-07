import subprocess
import os
import json

def generate_project_tree(startpath='.', exclude_dirs={'.git', '__pycache__', 'venv', '.venv', 'node_modules', 'build', '.build'}):
    """Dessine l'arborescence du projet pour que Gemini comprenne la structure."""
    tree_str = "Architecture du répertoire :\n"
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * level
        folder_name = os.path.basename(root) if os.path.basename(root) else '.'
        
        tree_str += f"{indent}📁 {folder_name}/\n"
        subindent = ' ' * 4 * (level + 1)
        
        for f in files:
            if not f.endswith(('.pyc', '.png', '.jpg', '.xcf', '.DS_Store')):
                tree_str += f"{subindent}📄 {f}\n"
                
    return tree_str

def get_context_for_gemini():
    """Récupère le contexte adapté : Diff de Commit, Diff de PR, ou Texte de l'Issue."""
    
    event_name = os.environ.get("GITHUB_EVENT_NAME", "push")
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    
    # 1. Charger le payload JSON de l'événement GitHub
    event_data = {}
    if event_path and os.path.exists(event_path):
        with open(event_path, 'r', encoding='utf-8') as f:
            event_data = json.load(f)

    project_tree = generate_project_tree()

    # 2. Chercher les instructions personnalisées de l'utilisateur
    custom_rules = ""
    sentinel_file = "SENTINEL.md"
    if os.path.exists(sentinel_file):
        with open(sentinel_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                custom_rules = f"\n## DIRECTIVES UTILISATEUR (PRIORITÉ ABSOLUE)\n{content}\n"

    # ---------------------------------------------------------
    # SCÉNARIO 1 : C'EST UNE ISSUE (Pas de code modifié)
    # ---------------------------------------------------------
    if event_name == "issues":
        issue_title = event_data.get("issue", {}).get("title", "Titre inconnu")
        issue_body = event_data.get("issue", {}).get("body", "Aucune description.")
        
        super_context = f"""
{custom_rules}
## ARCHITECTURE GLOBALE DU PROJET
{project_tree}

## NOUVELLE ISSUE SIGNALÉE
Titre : {issue_title}
Description : {issue_body}
"""
        # On retourne le contexte, le type d'événement, et les données brutes
        return super_context, event_name, event_data

    # ---------------------------------------------------------
    # SCÉNARIO 2 : PULL REQUEST OU PUSH (Code modifié)
    # ---------------------------------------------------------
    diff = ""
    files_changed = []
    
    if event_name == "pull_request":
        # Extraire les SHAs de la branche source et cible de la PR
        base_sha = event_data.get("pull_request", {}).get("base", {}).get("sha")
        head_sha = event_data.get("pull_request", {}).get("head", {}).get("sha")
        
        if base_sha and head_sha:
            try:
                diff = subprocess.run(['git', 'diff', base_sha, head_sha], capture_output=True, text=True, check=True).stdout
                files_changed_raw = subprocess.run(['git', 'diff', '--name-only', base_sha, head_sha], capture_output=True, text=True, check=True).stdout
                files_changed = files_changed_raw.strip().split('\n')
            except subprocess.CalledProcessError:
                pass
    else:
        # Mode Push classique
        try:
            diff = subprocess.run(['git', 'diff', 'HEAD~1', 'HEAD'], capture_output=True, text=True, check=True).stdout
            files_changed_raw = subprocess.run(['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'], capture_output=True, text=True, check=True).stdout
            files_changed = files_changed_raw.strip().split('\n')
        except subprocess.CalledProcessError:
            pass

    full_files_content = ""
    for filepath in files_changed:
        if filepath and os.path.exists(filepath) and not filepath.endswith(('.xcf', '.png', '.jpg', '.pyc', '.DS_Store')):
            with open(filepath, 'r', encoding='utf-8') as f:
                full_files_content += f"\n--- CONTENU COMPLET DE : {filepath} ---\n"
                full_files_content += f.read()
                full_files_content += "\n----------------------------------------\n"

    super_context = f"""
{custom_rules}
## ARCHITECTURE GLOBALE DU PROJET
{project_tree}

## FICHIERS MODIFIÉS (Contexte complet)
{full_files_content}

## GIT DIFF (Changements introduits)
{diff}
"""
    return super_context, event_name, event_data