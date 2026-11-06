import subprocess
import os

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
    """Récupère l'arbre du projet, les règles utilisateur, le diff, et le code source."""
    
    # 1. Obtenir l'arborescence du projet
    project_tree = generate_project_tree()

    # 2. Chercher les instructions personnalisées de l'utilisateur
    custom_rules = ""
    sentinel_file = "SENTINEL.md"
    if os.path.exists(sentinel_file):
        with open(sentinel_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                custom_rules = f"\n## DIRECTIVES UTILISATEUR (PRIORITÉ ABSOLUE)\n{content}\n"

    # 3. Obtenir le Git Diff
    try:
        diff = subprocess.run(['git', 'diff', 'HEAD~1', 'HEAD'], capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
         return None

    # 4. Trouver les fichiers modifiés
    try:
        files_changed_raw = subprocess.run(['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'], capture_output=True, text=True, check=True).stdout
        files_changed = files_changed_raw.strip().split('\n')
    except subprocess.CalledProcessError:
        files_changed = []

    # 5. Lire le contenu complet de ces fichiers modifiés
    full_files_content = ""
    for filepath in files_changed:
        if filepath and os.path.exists(filepath) and not filepath.endswith(('.xcf', '.png', '.jpg', '.pyc', '.DS_Store')):
            with open(filepath, 'r', encoding='utf-8') as f:
                full_files_content += f"\n--- CONTENU COMPLET DE : {filepath} ---\n"
                full_files_content += f.read()
                full_files_content += "\n----------------------------------------\n"

    # 6. Le Super Prompt (Contexte ultime avec les règles utilisateur en premier)
    super_context = f"""
{custom_rules}
## ARCHITECTURE GLOBALE DU PROJET
{project_tree}

## FICHIERS MODIFIÉS (Contexte complet)
{full_files_content}

## GIT DIFF (Les changements exacts de ce commit)
{diff}
"""
    return super_context