# ai_agent.py
import google.generativeai as genai
import requests
from PIL import Image
from io import BytesIO

def analyze_car_with_ai(car_data, intent):
    model = genai.GenerativeModel('gemini-2.5-pro')
    
    prompt = f"""
    Du bist ein technisches Analyse-System für KFZ-Profis. 
    
    RICHTLINIEN:
    - KEINE Einleitungen (z.B. "Hallo", "Gerne gebe ich...").
    - KEIN Geplauder.
    - Starte DIREKT mit dem Rating.
    - Nutze für Fettgedrucktes ausschließlich <b>Text</b> (KEINE Sterne).
    - Nutze für Plus/Minus-Listen ausschließlich das vorgegebene HTML-Format.
    - 1 BIS 2 kurze Sätze MAX pro Plus/Minus!

    FOKUS: "{intent}"
    DATEN: {car_data['title']}, {car_data['text']}
    
    STRUKTUR:
    **Rating:** [X]/10
    
    <ul class="plus-list">
      <li><b>[Thema]:</b> [Fachliche Analyse]</li>
    </ul>
    
    <ul class="minus-list">
      <li><b>[Thema]:</b> [Fachliche Analyse]</li>
    </ul>
    
    **Fazit:** [1-2 Sätze!!]
    """
    
    gemini_inputs = [prompt]
    # Jedes Bild verbraucht 258 Tokens
    for img_url in car_data['image_urls']:
        try:
            img_response = requests.get(img_url, timeout=5)
            img = Image.open(BytesIO(img_response.content))
            gemini_inputs.append(img)
        except Exception:
            pass

    try:
        response = model.generate_content(gemini_inputs)
        return response.text
    except Exception as e:
        return f"Fehler bei der KI-Analyse: {e}"

def get_final_verdict(intent, valid_results):
    model = genai.GenerativeModel('gemini-2.5-pro')
    prompt = f"Vergleiche als KFZ-Berater folgende Inserate (Fokus: {intent}):\n"
    for idx, result in enumerate(valid_results):
        prompt += f"\nAuto {idx + 1}: {result['data']['title']}\n{result['analysis']}\n"
        
    prompt += """
    Vergleiche diese Fahrzeuge. Deine Priorität ist es, den GEWINNER zu küren (das Auto mit der besten Substanz oder dem besten Preis-Leistungs-Verhältnis). 
    Nur wenn alle Fahrzeuge nachweislich gefährlich (Schrottwert) oder nicht zum Suchprofil(FOKUS) passen oder völlig überteuert sind, darfst du von allen abraten. Ansonsten wähle die ehrlichste Basis.   
    Ehrlichkeit gewinnt. bleib kurz mit der Antwort.
    Format:
    ### 🏆 Finales Urteil: [Gewinner]
    [Kurz & Fachlich 2-3 Sätze!!] 
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Fehler: {e}"