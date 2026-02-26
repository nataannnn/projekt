# app.py
import streamlit as st
import google.generativeai as genai

from scraper import scrape_real_willhaben
from ai_agent import analyze_car_with_ai, get_final_verdict

st.set_page_config(page_title="Auto Analyst Pro", layout="wide")

# API KEY SETUP
# Holt sich den Key sicher aus den Secrets
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# CSS LADEN
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if 'url_count' not in st.session_state:
    st.session_state.url_count = 2

# --- BEREINIGTE PROFI-SUCHPROFILE ---
search_intents = [
    "Standard: Objektiver Best-of-Vergleich",
    "Originalität & Sammlerpotential (Unverbastelt, Historie, Matching Numbers)",
    "Beste Karosseriesubstanz (Rostfrei, Lackbild, Spaltmaße: Prio 1)",
    "Beste technische Historie (Scheckheft, frisches Pickerl, durchrepariert)",
    "Minimalster Wartungsstau (Geringste Sofort-Investitionen nötig)",
    "Tracktool / Motorsport-Basis (Motor/Fahrwerk Top, Optik egal)",
    "Daily Driver / Vernunftkauf (Wirtschaftlichkeit, Zuverlässigkeit)",
    "Höchstes Wertsteigerungspotenzial (Seltenheit, Ausstattung, wenig km)",
    "Restaurationsobjekt (Beste Preis-Leistung für Bastler)",
    "Export / Weiterverkauf (Fokus auf größte Gewinnmarge)",
    "Winterauto / Schlechtwege (Rostschutz, Antrieb, Rest-Pickerl)",
    "Langstrecken-Fahrzeug (Komfort, Automatik, gepflegter Innenraum)",
    "Schönwetter-Cruiser (Lackbild, Verdeck, makellose Optik)",
    "Motorumbau-Basis (Karosserie top, Motorzustand egal)"
]

# --- ROUTING ---
page = st.query_params.get("page", "analyse")
active_analyse = "active" if page == "analyse" else ""
active_contact = "active" if page == "contact" else ""

# --- NAVBAR ---
navbar_html = f"""
<div class="custom-navbar">
    <div class="nav-logo">Auto Analyst Pro</div>
    <div class="nav-links">
        <a href="?page=analyse" target="_self" class="{active_analyse}">Analyse</a>
        <a href="?page=contact" target="_self" class="{active_contact}">Kontakt</a>
    </div>
</div>
"""
st.markdown(navbar_html, unsafe_allow_html=True)

# ==========================================
# SEITE 1: ANALYSE
# ==========================================
if page == "analyse":
    
    st.markdown("""
    <div class="hero-banner">
        <h1>KI Gebrauchtwagen Analyse</h1>
        <p>Vergleiche identische Modelle knallhart miteinander. Die KI filtert Blender heraus und findet die beste Basis.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        col_input1, col_input2 = st.columns(2)
        
        with col_input1:
            st.subheader("1. Analyse-Fokus")
            intent_selection = st.selectbox("Profil-Vorlage (Optional)", search_intents)
            
            custom_intent = st.text_area(
                "Eigene Kriterien hinzufügen (Optional)", 
                placeholder="z.B. Achte besonders auf Rost am Radlauf hinten links...", 
                height=100
            )
            
            # --- LOGIK: KOMBINATION ---
            if intent_selection == search_intents[0]:
                base_intent = "Objektiver Vergleich der harten Fakten, Karosseriesubstanz und Preis-Leistung."
            else:
                base_intent = f"Fokus auf: {intent_selection}"
                
            if custom_intent.strip():
                final_intent = f"{base_intent}\nZusätzliche Prioritäten des Nutzers: {custom_intent.strip()}"
            else:
                final_intent = base_intent
            
        with col_input2:
            st.subheader("2. Links einfügen")
            entered_urls = []
            for i in range(st.session_state.url_count):
                url = st.text_input(f"Link {i+1}", key=f"url_input_{i}", placeholder="https://www.willhaben.at/iad/...")
                entered_urls.append(url)
                
            if st.button("+ Weiteres Auto hinzufügen"):
                st.session_state.url_count += 1
                st.rerun()

    st.write("")

    
# app.py - Ausschnitt der Analyse-Logik

if st.button("Analyse starten", type="primary"):
    valid_urls = [url for url in entered_urls if url.strip() != ""]
    
    if len(valid_urls) == 0:
        st.error("Bitte gib mindestens eine gültige URL ein.")
    else:
        st.markdown("---")
        
        # --- DAS SCHWEBENDE POPUP (FIXED UNTEN RECHTS) ---
        # Wir nutzen eine leere Div-Klasse für das CSS-Targeting
        st.markdown('<div class="floating-progress">', unsafe_allow_html=True)
        
        # Der Expander dient als "minimierbares" Fenster
        with st.expander("⏳ Analyse-Fortschritt", expanded=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            sub_step_text = st.empty()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        valid_results = [] 
        total_cars = len(valid_urls)
        
        for idx, current_url in enumerate(valid_urls):
            base_p = idx / total_cars
            step = 1 / total_cars
            
            with st.container():
                st.markdown(f"### Fahrzeug {idx + 1}")
                
                # Schritt 1: Start & Scraping
                progress_bar.progress(int(base_p * 100), text=f"Auto {idx+1}/{total_cars}")
                sub_step_text.write(f"🌐 Rufe Daten von Willhaben ab...")
                data = scrape_real_willhaben(current_url)
                
                if data['status'] == 'success':
                    # Schritt 2: Bildverarbeitung
                    progress_bar.progress(int((base_p + step * 0.3) * 100))
                    sub_step_text.write(f"📸 {len(data['image_urls'])} Bilder geladen. Vorbereitung für KI...")
                    
                    col_img, col_text = st.columns([1, 1.5])
                    with col_img:
                        if data['image_urls']:
                            st.image(data['image_urls'][0], use_container_width=True)
                            if len(data['image_urls']) > 1:
                                st.image(data['image_urls'][1:], width=80)
                    
                    with col_text:
                        st.info(f"**{data['title']}**")
                        
                        # Schritt 3: Die schwere Arbeit mit Gemini 2.5 Pro
                        sub_step_text.write(f"🧠 **Gemini 2.5 Pro** analysiert technische Details...")
                        progress_bar.progress(int((base_p + step * 0.6) * 100))
                        
                        analysis = analyze_car_with_ai(data, final_intent)
                        st.markdown(analysis, unsafe_allow_html=True)
                        
                    valid_results.append({"data": data, "analysis": analysis})
                    progress_bar.progress(int((base_p + step) * 100))
                else:
                    st.error(f"Fehler bei Fahrzeug {idx+1}: {data['message']}")

        # Abschluss
        progress_bar.progress(100)
        sub_step_text.success("Alle Fahrzeuge erfolgreich geprüft!")
        
        if len(valid_results) > 0:
            st.markdown("---")
            st.header("Kaufempfehlung")
            with st.status("Erstelle finales Experten-Urteil...", expanded=False):
                verdict = get_final_verdict(final_intent, valid_results)
            st.success(verdict)
# ==========================================
# SEITE 2: KONTAKT
# ==========================================
elif page == "contact":
    st.markdown("""
    <div class="hero-banner">
        <h1>Kontakt & Support</h1>
        <p>Hast du Fragen oder Feedback zum Auto Analyst Pro Tool?</p>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Name")
        with col2:
            st.text_input("E-Mail")
        st.text_area("Nachricht", height=150)
        if st.button("Absenden", type="primary"):
            st.success("Nachricht gesendet.")