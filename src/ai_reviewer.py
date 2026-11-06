import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def analyze_code(diff_text):
    """Envoie le diff à Gemini et retourne le JSON brut"""
    if not diff_text or not diff_text.strip():
        return None
        
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=f"Analyse ce git diff et identifie les problèmes potentiels.\n\nDiff:\n{diff_text}",
        config=types.GenerateContentConfig(
            system_instruction="""Tu es Sentinel, un AI Code Reviewer impitoyable mais constructif. 
            Ton but est d'analyser les git diffs pour trouver des bugs, failles et mauvaises pratiques. 
            Tu dois TOUJOURS répondre en JSON strict : 
            {"summary": "...", "issues": [{"severity": "high|medium|low", "line": int, "type": "...", "description": "...", "suggestion": "..."}]}""",
            response_mime_type="application/json",
            temperature=0.2
        )
    )
    return response.text