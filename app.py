# app.py
import streamlit as st
import google.generativeai as genai
import time

from scraper import scrape_real_willhaben
from ai_agent import analyze_car_with_ai, get_final_verdict

st.set_page_config(page_title="Auto Analyst Pro", layout="wide")

# API KEY SETUP
# Ersetze dies in Produktion durch st.secrets["GEMINI_API_KEY"]!
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# CSS LADEN
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if 'url_count' not in st.session_state:
    st.session_state.url_count = 1

# --- BEREINIGTE PROFI-SUCHPROFILE ---
search_intents = [
    "Standard: Objektive Zustands- & Preis-Leistungs-Analyse",
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
        <h1>Willhaben Fahrzeug Analyse</h1>
        <p>Das Tool für den knallharten Inserat-Vergleich. Füge ein oder mehrere Autos ein, lass die KI Blender herausfiltern und finde die ehrlichste Basis.</p>
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
                base_intent = "Objektive Analyse der harten Fakten, Karosseriesubstanz und Preis-Leistung."
            else:
                base_intent = f"Fokus auf: {intent_selection}"
                
            if custom_intent.strip():
                final_intent = f"{base_intent}\nZusätzliche Prioritäten des Nutzers: {custom_intent.strip()}"
            else:
                final_intent = base_intent
            
        with col_input2:
            st.subheader("2. Willhaben-Link(s) einfügen")
            entered_urls = []
            for i in range(st.session_state.url_count):
                url = st.text_input(f"Link {i+1}", key=f"url_input_{i}", placeholder="https://www.willhaben.at/iad/...")
                entered_urls.append(url)
                
            if st.button("+ Weiteres Auto zum Vergleich hinzufügen"):
                st.session_state.url_count += 1
                st.rerun()

    st.write("")

    # --- HAUPT-LOGIK START ---
    if st.button("Experten-Analyse starten", type="primary"):
        valid_urls = [url.strip() for url in entered_urls if url.strip() != ""]
        invalid_urls = [url for url in valid_urls if not url.startswith("https://www.willhaben.at/iad/gebrauchtwagen")]
        
        if len(valid_urls) == 0:
            st.error("Bitte gib mindestens einen gueltigen Willhaben-Link ein.")
        elif len(invalid_urls) > 0:
            st.error("Fehler: Einer der Links ist kein gueltiges Willhaben-Inserat. Bitte pruefe deine Eingabe.")
        else:
            st.markdown("---")
            
            loader_placeholder = st.empty()
            
            def update_loader(percent, text):
                html = f"""
                <div class="custom-loader-container">
                    <div class="loader-header">
                        <div class="spinner"></div>
                        <div class="custom-loader-text">{text} ({percent}%)</div>
                    </div>
                    <div class="custom-loader-bg">
                        <div class="custom-loader-fill" style="width: {percent}%;"></div>
                    </div>
                </div>
                """
                loader_placeholder.markdown(html, unsafe_allow_html=True)
            
            valid_results = [] 
            total_cars = len(valid_urls)
            
            for idx, current_url in enumerate(valid_urls):
                base_p = (idx / total_cars) * 100
                step = (1 / total_cars) * 100
                
                with st.container():
                    st.markdown(f"### Fahrzeug {idx + 1}")
                    
                    update_loader(int(base_p + (step * 0.1)), f"Fahrzeug {idx+1}/{total_cars}: Verbinde mit Server...")
                    time.sleep(1) 
                    
                    data = scrape_real_willhaben(current_url)
                    
                    is_valid_ad = data['status'] == 'success' and len(data.get('image_urls', [])) > 0 and data.get('title')
                    
                    if is_valid_ad:
                        update_loader(int(base_p + (step * 0.3)), f"Fahrzeug {idx+1}: {len(data['image_urls'])} Bilder geladen...")
                        time.sleep(1.5) 
                        
                        col_img, col_text = st.columns([1, 1.5])
                        
                        with col_img:
                            # --- NATIVE STREAMLIT BILDER-GALERIE (KLICKBAR) ---
                            if data['image_urls']:
                                # Hauptbild gross darstellen
                                st.image(data['image_urls'][0], use_container_width=True)
                                
                                # Bis zu 8 Thumbnails laden
                                thumbnails = data['image_urls'][1:9]
                                
                                if thumbnails:
                                    # Erstellt saubere 4er-Reihen unter dem Hauptbild
                                    for i in range(0, len(thumbnails), 4):
                                        cols = st.columns(4)
                                        chunk = thumbnails[i:i+4]
                                        for j, thumb in enumerate(chunk):
                                            cols[j].image(thumb, use_container_width=True)
                            # --------------------------------------------------
                        
                        with col_text:
                            st.info(f"**{data['title']}**")
                            
                            update_loader(int(base_p + (step * 0.6)), f"Fahrzeug {idx+1}: wird analysiert...")
                            
                            analysis = analyze_car_with_ai(data, final_intent)
                            st.markdown(analysis, unsafe_allow_html=True)
                            
                        valid_results.append({"data": data, "analysis": analysis})
                        
                        update_loader(int(base_p + step), f"Fahrzeug {idx+1} abgeschlossen!")
                        time.sleep(0.5)
                    else:
                        st.error(f"Fehler bei Fahrzeug {idx+1}: Die Anzeige existiert nicht mehr, wurde geloescht oder ist kein KFZ-Inserat.")
                        update_loader(int(base_p + step), f"Fahrzeug {idx+1} uebersprungen (Fehler).")
                        time.sleep(1)

            loader_placeholder.empty() 

            if len(valid_results) == 0:
                st.warning("Keines der eingegebenen Fahrzeuge konnte erfolgreich analysiert werden. Bitte ueberpruefe die Links.")
            elif len(valid_results) == 1:
                st.markdown("---")
                st.success("Einzelanalyse erfolgreich abgeschlossen. Die Details findest du oben.")
            elif len(valid_results) > 1:
                st.markdown("---")
                st.header("Vergleich & Kaufempfehlung")
                with st.spinner("Fahrzeuge werden verglichen..."):
                    verdict = get_final_verdict(final_intent, valid_results)
                st.success(verdict)

# ==========================================
# SEITE 2: KONTAKT                                                                                                                                                                                                     jjjkkjkj                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
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