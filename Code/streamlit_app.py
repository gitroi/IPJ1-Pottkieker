"""
Streamlit Web-App für die EE-Ausbau Simulation
Team Pottkieker - IPJ1
"""

import streamlit as st
import sys
from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt
import os
from io import BytesIO

# Pfad-Setup für Deployment
if Path(__file__).parent.name == "Code":
    # Lokale Entwicklung: streamlit_app.py liegt in Code/
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    CODE_DIR = PROJECT_ROOT / "Code"
else:
    # Deployment: streamlit_app.py liegt im Root
    PROJECT_ROOT = Path(__file__).resolve().parent
    CODE_DIR = PROJECT_ROOT / "Code"

sys.path.insert(0, str(CODE_DIR))
os.chdir(str(PROJECT_ROOT))

try:
    from config import DATA_DIR, PROJECT_ROOT as PR
    from Klassen import Szenario
    from Szenarien_auswahl import load_scenarios, load_verbrauchsprofile, get_scenario_by_name, get_verbrauchsprofil_by_name
    from Histogramme import plot_histogram_gesamtauswertung

except ImportError as e:
    st.error(f"❌ Import-Fehler: {str(e)}")
    st.error(f"PROJECT_ROOT: {PROJECT_ROOT}")
    st.error(f"CODE_DIR: {CODE_DIR}")
    st.error(f"Current dir: {os.getcwd()}")
    st.error(f"sys.path: {sys.path}")
    st.stop()

st.set_page_config(
    page_title="Simulation der Stromversorgung mit Erneuerbaren Energien in Deutschland",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚡ Simulation der Stromversorgung mit Erneuerbaren Energien in Deutschland")
st.markdown("**Simulation des Erneuerbare-Energien-Ausbaus bis 2030/2045**")
st.markdown("---")

def get_file_mtime(filepath):
    """Hilfsfunktion: Gibt die letzte Änderungszeit einer Datei zurück"""
    return filepath.stat().st_mtime

@st.cache_data
def lade_szenarien(_mtime):
    """Lädt Szenarien aus JSON-Datei (cached mit Auto-Reload bei Dateiänderung)"""
    return load_scenarios()

@st.cache_data
def lade_verbrauchsprofile(_mtime):
    """Lädt Verbrauchsprofile aus JSON-Datei (cached mit Auto-Reload bei Dateiänderung)"""
    return load_verbrauchsprofile()

szenarien_pfad = DATA_DIR / "Szenarien.json"
verbrauchsprofile_pfad = DATA_DIR / "Verbrauchsprofile.json"

szenarien = lade_szenarien(get_file_mtime(szenarien_pfad))
verbrauchsprofile = lade_verbrauchsprofile(get_file_mtime(verbrauchsprofile_pfad))

with st.sidebar:
    st.header("📊 Navigation")
    modus = st.radio(
        "Simulationsmodus wählen:",
        ["🎯 Einzelnes Szenario", "📈 Alle Szenarien vergleichen", "ℹ️ Über das Projekt"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### 👥 Team Pottkieker")
    st.markdown("IPJ1 - HAW Hamburg")

# ============================================================================
# MODUS 1: EINZELNES SZENARIO
# ============================================================================
if modus == "🎯 Einzelnes Szenario":
    st.header("🎯 Einzelnes Szenario simulieren")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Szenario wählen")
        szenario_namen = [s["Name"] for s in szenarien]
        ausgewähltes_szenario_name = st.selectbox(
            "Verfügbare Szenarien:",
            szenario_namen,
            help="Wähle ein Szenario für die Simulation"
        )
        
        gewaehltes_szenario = get_scenario_by_name(szenarien, ausgewähltes_szenario_name)
        if gewaehltes_szenario:
            st.info(f"📝 {gewaehltes_szenario['Beschreibung']}")
    
    with col2:
        st.subheader("Verbrauchsprofil wählen")
        profil_namen = [p["Name"] for p in verbrauchsprofile]
        ausgewähltes_profil_name = st.selectbox(
            "Verfügbare Profile:",
            profil_namen,
            help="Wähle ein Verbrauchsprofil"
        )
        
        gewaehltes_profil = get_verbrauchsprofil_by_name(verbrauchsprofile, ausgewähltes_profil_name)
        if gewaehltes_profil:
            st.info(f"📝 {gewaehltes_profil.get('Beschreibung', 'Verbrauchsprofil für die Simulation')}")
    
    st.subheader("⚙️ Simulationsparameter")
    col3, col4 = st.columns(2)
    
    with col3:
        ertragsart = st.selectbox(
            "Ertragsart:",
            ["mittel", "schlecht", "gut"],
            help="Ertragsniveau für erneuerbare Energien"
        )
    
    with col4:
        jahre = range(2026, 2046)
        jahr_optionen = ["Alle Jahre"] + list(map(str, jahre))
        jahr_auswahl = st.selectbox(
            "Abbildungsjahr Diagramm:",
            jahr_optionen,
            help="Jahr für das die Ist-Analyse dargestellt werden soll"
        )
        jahr = None if jahr_auswahl == "Alle Jahre" else int(jahr_auswahl)
    
    st.markdown("---")
    if st.button("🚀 Simulation starten", type="primary", use_container_width=True):
        if gewaehltes_szenario and gewaehltes_profil:
            with st.spinner(f"🔄 Berechne Prognosen für '{ausgewähltes_szenario_name}'..."):
                try:
                    szenario_ergebnis = Szenario(
                        name=ausgewähltes_szenario_name,
                        beschreibung=gewaehltes_szenario["Beschreibung"],
                        szenario=gewaehltes_szenario,
                        ziele_2030=gewaehltes_szenario["Ziele 2030"],
                        ziele_2045=gewaehltes_szenario["Ziele 2045"],
                        ertragsart=ertragsart,
                        verbrauchsprofile=gewaehltes_profil,
                        veränderungsfaktoren=gewaehltes_szenario["Veränderungsfaktoren"]["Erzeugung"]
                    )
                    
                    #szenario_ergebnis.berechne_alle_prognosen()
                    
                    st.success(f"✅ Simulation für '{ausgewähltes_szenario_name}' abgeschlossen!")
                    
                    st.session_state['letztes_szenario'] = szenario_ergebnis
                    st.session_state['jahr'] = jahr
                    
                except Exception as e:
                    st.error(f"❌ Fehler bei der Simulation: {str(e)}")
                    st.exception(e)
    
    if 'letztes_szenario' in st.session_state:
        st.markdown("---")
        st.header("📊 Ergebnisse")
        
        szenario = st.session_state['letztes_szenario']
        jahr = st.session_state.get('jahr')
        
        tab1, tab2 = st.tabs(["📈 Übersicht", "📊 Plots"])
        
        with tab1:
            st.subheader("Zusammenfassung")
            
            col1, col2,col3,col4 = st.columns(4)
            
            ergebnisse = szenario.auswertungsdaten_generieren()
            if ergebnisse is not None:
                try:         
                    stromerzeugung = ergebnisse["Erzeugung Erneuerbare im Jahr [TWh]"].sum()
                    gesamtkosten = ergebnisse["Gesamtkosten_EE_und_Speicher [Mrd. €]"].sum()   
                    st.dataframe(ergebnisse, use_container_width=True)
                    col1.metric("Erzeugung Erneuerbare 2026-2045", f"{stromerzeugung:.1f} TWh")
                    col2.metric("Gesamtkosten 2026-2045", f"{gesamtkosten:.2f} Mrd. €")
                except Exception as e:
                    st.warning(f"Fehler bei Metriken: {str(e)}")


            if szenario.konventionelle:
                try:
                    konv = szenario.konventionelle
                    wert2030 = konv[2030]["Energie"]/1e3
                    wert2045 = konv[2045]["Energie"]/1e3
                    col3.metric("Konv. Energie 2030", f"{wert2030:.1f} GWh")
                    col4.metric("Konv. Energie 2045", f"{wert2045:.1f} GWh")
                except Exception as e:
                    st.warning(f"Fehler bei konventionellen Daten: {str(e)}")
    
        
        with tab2:
            st.subheader("📊 Visualisierungen")
            
            if hasattr(szenario, 'gebe_plots'):
                try:
                    figures = szenario.gebe_plots(jahr)
                    
                    st.markdown("### 🔋 EE-Anteil mit/ohne Speicher")
                    st.pyplot(figures['fig5'])
                    buf5 = BytesIO()
                    figures['fig5'].savefig(buf5, format='png', dpi=300, bbox_inches='tight')
                    buf5.seek(0)
                    st.download_button(
                        label="💾 Plot herunterladen",
                        data=buf5,
                        file_name=f"szenario_{szenario.name}_ertragsart_{szenario.ertragsart}_jahr_{jahr if jahr else 'alle'}.png",
                        mime="image/png",
                        on_click="ignore"
                    )

                    st.markdown("---")
                    st.markdown("### 📊 EE-Anteil & Konventionelle Energie")
                    st.pyplot(figures['fig1'])
                    buf1 = BytesIO()
                    figures['fig1'].savefig(buf1, format='png', dpi=300, bbox_inches='tight')
                    buf1.seek(0)
                    st.download_button(
                        label="💾 Plot herunterladen",
                        data=buf1,
                        file_name=f"szenario_{szenario.name}_ertragsart_{szenario.ertragsart}.png",
                        mime="image/png",
                        on_click="ignore"
                    )
                    
                    st.markdown("---")
                    st.markdown("### 💰 Kosten-Analyse")
                    st.pyplot(figures['fig2'])
                    buf2 = BytesIO()
                    figures['fig2'].savefig(buf2, format='png', dpi=300, bbox_inches='tight')
                    buf2.seek(0)
                    st.download_button(
                        label="💾 Plot herunterladen",
                        data=buf2,
                        file_name=f"szenario_{szenario.name}_kosten_ertragsart_{szenario.ertragsart}.png",
                        mime="image/png",
                        on_click="ignore"
                    )
                    
                    st.markdown("---")
                    st.markdown("### 📈 Ausbauraten Übersicht")
                    st.pyplot(figures['fig3'])
                    buf3 = BytesIO()
                    figures['fig3'].savefig(buf3, format='png', dpi=300, bbox_inches='tight')
                    buf3.seek(0)
                    st.download_button(
                        label="💾 Plot herunterladen",
                        data=buf3,
                        file_name=f"szenario_{szenario.name}_ausbauraten_ertragsart_{szenario.ertragsart}.png",
                        mime="image/png",
                        on_click="ignore"
                    )
                    
                    st.markdown("---")
                    st.markdown("### 📊 Installierte Leistungen/Kapazitäten")
                    st.pyplot(figures['fig4'])
                    buf4 = BytesIO()
                    figures['fig4'].savefig(buf4, format='png', dpi=300, bbox_inches='tight')
                    buf4.seek(0)
                    st.download_button(
                        label="💾 Plot herunterladen",
                        data=buf4,
                        file_name=f"szenario_{szenario.name}_installierte_leistungen_ertragsart_{szenario.ertragsart}.png",
                        mime="image/png",
                        on_click="ignore"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Fehler beim Erstellen der Plots: {str(e)}")
                    st.exception(e)
                
        
        st.markdown("---")
        excel_buffer = BytesIO()
        szenario.auswertungsdaten_generieren().to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        
        st.download_button(
            label="💾 Gesamtergebnis als Excel herunterladen",
            data=excel_buffer,
            file_name=f"szenario_{szenario.name}_ertragsart_{szenario.ertragsart}_ergebnisse.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ============================================================================
# MODUS 2: ALLE SZENARIEN
# ============================================================================
elif modus == "📈 Alle Szenarien vergleichen":
    st.header("📈 Alle Szenarien vergleichen")
    
    st.info("Dieser Modus berechnet alle verfügbaren Szenarien und vergleicht die Ergebnisse.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        profil_namen = [p["Name"] for p in verbrauchsprofile]
        ausgewähltes_profil_name = st.selectbox(
            "Verbrauchsprofil:",
            profil_namen
        )
    
    with col2:
        ertragsart = st.selectbox(
            "Ertragsart für alle Szenarien:",
            ["mittel", "schlecht", "gut"]
        )
    
    
    if st.button("🚀 Alle Szenarien simulieren", type="primary", use_container_width=True):
        gewaehltes_profil = get_verbrauchsprofil_by_name(verbrauchsprofile, ausgewähltes_profil_name)
        
        if gewaehltes_profil:
            alle_ergebnisse = pd.DataFrame()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, szenario_data in enumerate(szenarien):
                status_text.text(f"Berechne {szenario_data['Name']}... ({idx+1}/{len(szenarien)})")
                
                try:
                    szenario_ergebnis = Szenario(
                        name=szenario_data["Name"],
                        beschreibung=szenario_data["Beschreibung"],
                        szenario=szenario_data,
                        ziele_2030=szenario_data["Ziele 2030"],
                        ziele_2045=szenario_data["Ziele 2045"],
                        ertragsart=ertragsart,
                        verbrauchsprofile=gewaehltes_profil,
                        veränderungsfaktoren=szenario_data["Veränderungsfaktoren"]["Erzeugung"]
                    )
                    
                    #szenario_ergebnis.berechne_alle_prognosen()
                    ergebnisse_df = szenario_ergebnis.getErgebnisse()
                    alle_ergebnisse = pd.concat([alle_ergebnisse, ergebnisse_df], ignore_index=True)
                    
                except Exception as e:
                    st.warning(f"Fehler bei {szenario_data['Name']}: {str(e)}")
                
                progress_bar.progress((idx + 1) / len(szenarien))
            
            status_text.text("Erstelle Vergleichsvisualisierungen...")
            
            fig1, ax1 = plt.subplots(1, 2, figsize=(12, 6))
            fig2, ax2 = plt.subplots(1, 2, figsize=(12, 6))
            
            try:
                plot_histogram_gesamtauswertung(alle_ergebnisse, ax1[0], ax1[1], ax2[0], ax2[1])
                plt.tight_layout()
                
                st.success("✅ Alle Szenarien erfolgreich berechnet!")
                
                st.pyplot(fig1)
                buf1 = BytesIO()
                fig1.savefig(buf1, format='png', dpi=300, bbox_inches='tight')
                buf1.seek(0)
                st.download_button(
                    label="💾 Plot herunterladen",
                    data=buf1,
                    file_name=f"vergleich_aller_szenarien_ertragsart_{ertragsart}_plots1.png",
                    mime="image/png",
                    on_click="ignore"
                )
                st.pyplot(fig2)
                buf2 = BytesIO()
                fig2.savefig(buf2, format='png', dpi=300, bbox_inches='tight')
                buf2.seek(0)
                st.download_button(
                    label="💾 Plot herunterladen",
                    data=buf2,
                    file_name=f"vergleich_aller_szenarien_ertragsart_{ertragsart}_plots2.png",
                    mime="image/png",
                    on_click="ignore"
                )
                
                st.subheader("📊 Vergleichstabelle")
                st.dataframe(alle_ergebnisse, use_container_width=True)
                st.markdown("---")
                excel_buffer = BytesIO()
                alle_ergebnisse.to_excel(excel_buffer, index=False, engine='openpyxl')
                excel_buffer.seek(0)
                
                st.download_button(
                    label="💾 Gesamtergebnis als Excel herunterladen",
                    data=excel_buffer,
                    file_name=f"gesamtergebnisse_ertragsart_{ertragsart}_ergebnisse.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:
                st.error(f"Fehler bei der Visualisierung: {str(e)}")
                st.exception(e)
            
            progress_bar.empty()
            status_text.empty()

# ============================================================================
# Modus 3: Szenario hinzufügen
# ============================================================================

elif modus == "➕ Szenario hinzufügen":
    st.header("➕ Szenario hinzufügen")
    st.info("Diese Funktion ist derzeit nicht verfügbar.")
    # Platzhalter für zukünftige Implementierung zum Hinzufügen von Szenarien


# ============================================================================
# MODUS 4: ÜBER DAS PROJEKT
# ============================================================================
elif modus == "ℹ️ Über das Projekt":
    st.header("ℹ️ Über das Projekt")
    
    st.markdown("""
    ## IPJ1 - Team Pottkieker
    
    ### 🎯 Projektbeschreibung
    Diese Simulationssoftware analysiert den Ausbau erneuerbarer Energien in Deutschland 
    bis zu den Zieljahren 2030 und 2045.
    
    ### 🔧 Funktionen
    - **Szenario-Simulation:** Berechnung verschiedener Ausbauszenarien
    - **Erzeugungsprognose:** Vorhersage der EE-Erzeugung nach Technologien
    - **Speicheranalyse:** Bewertung des Speicherbedarfs
    - **Kostenrechnung:** Investitions- und Betriebskosten
    - **Dunkelflaute-Szenarien:** Analyse kritischer Situationen
    
    ### 📊 Verfügbare Szenarien
    """)
    
    for szenario in szenarien:
        with st.expander(f"📁 {szenario['Name']}"):
            st.write(f"**Beschreibung:** {szenario['Beschreibung']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("**Ziele 2030:**")
                st.json(szenario['Ziele 2030'])
            with col2:
                st.write("**Ziele 2045:**")
                st.json(szenario['Ziele 2045'])
            with col3:
                st.write("**Veränderungsfaktoren:**")
                st.json(szenario['Veränderungsfaktoren'])
    
    st.markdown("""
    ### 👥 Softwareteam
    - Joris Bürger
    - Robin Matzke
    
    ### 🏫 Institution
    HAW Hamburg - Integrationsprojekt 1
    """)
    
    st.markdown("---")
    st.markdown("🔧 **Streamlit Version:** " + st.__version__)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>© 2025 Team Pottkieker | HAW Hamburg</div>",
    unsafe_allow_html=True
)
