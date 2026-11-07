import sys
from pydantic import ValidationError
from git_analyzer import get_context_for_gemini
from ai_reviewer import analyze_code, ReviewReport
from github_client import post_github_comment

def main():
    print("🔍 Sentinel: Analyse de l'événement GitHub...")
    context_data = get_context_for_gemini()
    
    if not context_data:
        print("❌ Erreur : Impossible de générer le contexte d'analyse.", file=sys.stderr)
        sys.exit(1)
        
    super_context, event_name, event_data = context_data

    print(f"🧠 Sentinel: Analyse du contexte ({event_name}) par Gemini 3.8 Flash...")
    result = analyze_code(super_context, event_name)
    
    if not result:
        print("❌ Erreur : Aucune réponse générée par l'IA.", file=sys.stderr)
        sys.exit(1)
        
    # On déballe le tuple renvoyé par l'IA
    ai_response, usage_metadata = result
        
    try:
        report = ReviewReport.model_validate_json(ai_response)
        
        print(f"\n✅ Résumé : {report.summary}")
        print(f"⚠️ {len(report.issues)} point(s) d'attention trouvé(s).")
        
        print("\n📡 Tentative de publication sur GitHub...")
        # On passe les métadonnées au client GitHub
        success = post_github_comment(report.model_dump(), event_name, event_data, usage_metadata)
        
        if not success:
            print("❌ Échec de la publication du rapport sur GitHub.", file=sys.stderr)
            sys.exit(1)
            
    except ValidationError as err:
        print(f"❌ Erreur critique : Le JSON validé par l'API ne correspond pas au schéma Pydantic.\n{err}", file=sys.stderr)
        sys.exit(1)
    except Exception as err:
        print(f"❌ Erreur inattendue :\n{err}\n--- Payload ---\n{ai_response}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()