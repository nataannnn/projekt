# ai_agent.py
import google.generativeai as genai
import requests
from PIL import Image
from io import BytesIO

def analyze_car_with_ai(car_data, intent):
    model = genai.GenerativeModel('gemini-2-flash')
    prompt = f"""
    Du bist ein extrem kritischer KFZ-Gutachter und sprichst mit einem anderen Auto-Experten. 
    Lass sämtliche Laien-Erklärungen weg (z.B. erkläre nicht, was ein Pickerl ist). Fokussiere dich auf harte Fakten, bekannte Schwachstellen des Modells auf den Bildern und ehrliche Einschätzungen der Substanz.
    
    Analyse-Fokus / Filter-Linse: "{intent}"
    
    Titel des Inserats: {car_data['title']}
    Beschreibungstext: {car_data['text']}
    
    Du erhältst auch die Bilder. Prüfe Spaltmaße, Lackunterschiede, Abnutzung im Innenraum und offensichtlichen Rost/Mängel extrem genau.
    Du MUSST zwingend die Plus- und Minuspunkte als reines HTML ausgeben.
    
    Nutze EXAKT diese Struktur:
    
    **Rating:** [X]/10
    
    <ul class="plus-list">
      <li>[Knappes, fachliches Plusargument]</li>
    </ul>
    
    <ul class="minus-list">
      <li>[Knappes, fachliches Minusargument]</li>
    </ul>
    
    **Fazit:** (1-2 Sätze, knallhart auf den Punkt)
    """
    
    gemini_inputs = [prompt]
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
    model = genai.GenerativeModel('gemini-2-flash')
    prompt = f"""Du bist ein strenger KFZ-Berater, der mit einem Experten spricht. 
    Kunden-Fokus: "{intent}"
    """
    
    for idx, result in enumerate(valid_results):
        prompt += f"\nAuto {idx + 1}: {result['data']['title']}\n{result['analysis']}\n"
        
    prompt += """
    Vergleiche alle Autos. Welches ist für den geforderten Fokus die objektiv beste Basis? 
    Wenn es z.B. 4 identische BMW E46 sind, sage klar, welcher am ehrlisten wirkt und warum. 
    Wenn alle Schrott sind, rate von allen ab.
    
    Format:
    ### 🏆 Finales Urteil: [Gewinner / "Kauf KEINES"]
    **Begründung:** (2-3 Sätze, fachlich fundiert, warum dieses Auto die anderen schlägt)
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Fehler: {e}"
