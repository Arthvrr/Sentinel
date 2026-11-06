import subprocess

def get_latest_commit_diff():
    """Récupère le diff du dernier commit local"""
    try:
        # Exécute la commande git et capture la sortie
        result = subprocess.run(
            ['git', 'diff', 'HEAD~1', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de Git : {e}")
        return None
    except FileNotFoundError:
        print("L'outil 'git' n'est pas installé ou introuvable.")
        return None