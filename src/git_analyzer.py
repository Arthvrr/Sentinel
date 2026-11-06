import subprocess
import os

def generate_project_tree(startpath='.', exclude_dirs={'.git', '__pycache__', 'venv', '.venv', 'node_modules', 'build', '.build'}):
    """Dessine l'arborescence du projet pour que Gemini comprenne la structure."""
    tree_str = "Architecture du répertoire :\n"
    for root, dirs, files in os.walk(startpath):
        # On modifie la liste des dossiers "en place" pour ne pas scanner les dossiers inutiles
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
    """Récupère l'arbre du projet, le diff, et le code source des fichiers modifiés."""
    
    # 1. Obtenir l'arborescence du projet
    project_tree = generate_project_tree()

    # 2. Obtenir le Git Diff
    try:
        diff = subprocess.run(['git', 'diff', 'HEAD~1', 'HEAD'], capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
         return None

    # 3. Trouver les fichiers modifiés
    try:
        files_changed_raw = subprocess.run(['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'], capture_output=True, text=True, check=True).stdout
        files_changed = files_changed_raw.strip().split('\n')
    except subprocess.CalledProcessError:
        files_changed = []

    # 4. Lire le contenu complet de ces fichiers modifiés
    full_files_content = ""
    for filepath in files_changed:
        if filepath and os.path.exists(filepath) and not filepath.endswith(('.xcf', '.png', '.jpg', '.pyc', '.DS_Store')):
            with open(filepath, 'r', encoding='utf-8') as f:
                full_files_content += f"\n--- CONTENU COMPLET DE : {filepath} ---\n"
                full_files_content += f.read()
                full_files_content += "\n----------------------------------------\n"

    # 5. Le Super Prompt (Contexte ultime)
    super_context = f"""
## ARCHITECTURE GLOBALE DU PROJET
{project_tree}

## FICHIERS MODIFIÉS (Contexte complet)
{full_files_content}

## GIT DIFF (Les changements exacts de ce commit)
{diff}
"""
    return super_context