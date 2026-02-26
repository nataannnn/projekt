# ai_agent.py
import google.generativeai as genai
import requests
from PIL import Image
from io import BytesIO

def analyze_car_with_ai(car_data, intent):
    model = genai.GenerativeModel('gemini-2.5-flash') 
    
    prompt = f"""
    Du bist ein erfahrener KFZ-Gutachter. Dein Kollege (ebenfalls Experte) bittet dich um eine Einschätzung.
    
    ANALYSE-FOKUS: "{intent}"
    
    DATEN:
    Titel: {car_data['title']}
    Beschreibung: {car_data['text']}
    
    AUFGABE:
    Analysiere die Bilder (Spaltmaße, Rost, Abnutzung, Lack) und den Text. 
    Sei realistisch: Bei alten Autos gibt es immer Mängel. Bewerte die SUBSTANZ im Verhältnis zum Preis.
    Gib die Antwort als HTML-Listen aus.
    
    FORMAT:
    **Rating:** [X]/10
    
    <ul class="plus-list">
      <li>[Fachlicher Pluspunkt]</li>
    </ul>
    
    <ul class="minus-list">
      <li>[Fachlicher Schwachpunkt]</li>
    </ul>
    
    **Fazit:** (Max. 2 Sätze zum Zustand)
    """
    
    gemini_inputs = [prompt]
    # Sende alle Bilder für die visuelle Analyse (258 Tokens pro Bild)
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
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Du bist ein KFZ-Kaufberater für Profis. 
    STRATEGIE: "{intent}"
    
    Hier sind die Einzelanalysen der Fahrzeuge:
    """
    
    for idx, result in enumerate(valid_results):
        prompt += f"\n--- FAHRZEUG {idx + 1}: {result['data']['title']} ---\n{result['analysis']}\n"
        
    prompt += """
    DEINE AUFGABE:
    Vergleiche diese Fahrzeuge. Deine Priorität ist es, den GEWINNER zu küren (das Auto mit der besten Substanz oder dem besten Preis-Leistungs-Verhältnis). 
    
    Nur wenn alle Fahrzeuge nachweislich gefährlich (Schrottwert) oder völlig überteuert sind, darfst du von allen abraten. Ansonsten wähle das 'geringste Übel' oder die ehrlichste Basis.
    
    FORMAT:
    ### 🏆 Finales Urteil: [Gewinner nennen]
    **Begründung:** (Erkläre in 2-3 Sätzen sachlich, warum dieses Fahrzeug das Rennen macht, auch wenn es Mängel hat.)
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Fehler: {e}"