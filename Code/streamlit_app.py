"""
Streamlit Web-App für die EE-Ausbau Simulation
Team Pottkieker - IPJ1
Programmiert von Joris Bürger, Robin Matzke 
"""

import streamlit as st
import sys
from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt
import os
from io import BytesIO
import subprocess

script_path = Path(__file__).resolve()

if script_path.parent.name == "Code":
    PROJECT_ROOT = script_path.parent.parent
    CODE_DIR = PROJECT_ROOT / "Code"
else:
    PROJECT_ROOT = script_path.parent
    CODE_DIR = PROJECT_ROOT / "Code"

code_dir_str = str(CODE_DIR)
if code_dir_str not in sys.path:
    sys.path.insert(0, code_dir_str)

os.chdir(str(PROJECT_ROOT))

try:
    from config import DATA_DIR, PROJECT_ROOT as PR
    from Klassen import Szenario
    from Szenarien_auswahl import load_scenarios, load_verbrauchsprofile, get_scenario_by_name, get_verbrauchsprofil_by_name
    from Diagramme import plot_histogram_gesamtauswertung,verbrauch_jahr,zweiwochendiagramm_stunden,plot_liniendiagramm_ladestand,plot_liniendiagramm_ladestand_dunkelflaute

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

def git_commit_and_push(filepath, commit_message):
    """Führt Git Add, Commit und Push für eine Datei aus"""
    try:
        # Prüfen ob Git verfügbar ist
        result = subprocess.run(["git", "--version"], 
                              capture_output=True, 
                              text=True, 
                              cwd=str(PROJECT_ROOT))
        if result.returncode != 0:
            return False, "Git ist nicht verfügbar"
        
        # Git Add
        result = subprocess.run(["git", "add", str(filepath)], 
                              capture_output=True, 
                              text=True, 
                              cwd=str(PROJECT_ROOT))
        if result.returncode != 0:
            return False, f"Git Add fehlgeschlagen: {result.stderr}"
        
        # Git Commit
        result = subprocess.run(["git", "commit", "-m", commit_message], 
                              capture_output=True, 
                              text=True, 
                              cwd=str(PROJECT_ROOT))
        if result.returncode != 0:
            # Kein Fehler wenn nichts zu committen ist
            if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                return True, "Keine Änderungen zu committen"
            return False, f"Git Commit fehlgeschlagen: {result.stderr}"
        
        # Git Push
        result = subprocess.run(["git", "push"], 
                              capture_output=True, 
                              text=True, 
                              cwd=str(PROJECT_ROOT))
        if result.returncode != 0:
            return False, f"Git Push fehlgeschlagen: {result.stderr}"
        
        return True, "Erfolgreich ins Repository gespeichert"
        
    except Exception as e:
        return False, f"Git-Operation fehlgeschlagen: {str(e)}"

szenarien_pfad = DATA_DIR / "Szenarien.json"
verbrauchsprofile_pfad = DATA_DIR / "Verbrauchsprofile.json"

szenarien = lade_szenarien(get_file_mtime(szenarien_pfad))
verbrauchsprofile = lade_verbrauchsprofile(get_file_mtime(verbrauchsprofile_pfad))

with st.sidebar:
    st.header("📊 Navigation")
    modus = st.radio(
        "Simulationsmodus wählen:",
        ["🎯 Einzelnes Szenario", "📈 Szenarien vergleichen", "➕ Szenario hinzufügen/Verändern","ℹ️ Über das Projekt"],
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
    col3 = st.columns(1)[0]
    
    with col3:
        ertragsart = st.selectbox(
            "Ertragsart:",
            ["mittel", "schlecht", "gut"],
            help="Ertragsniveau für erneuerbare Energien"
        )
    
    st.markdown("### ⚡ Konventionelle Anteile")
    st.info("Verteilung der konventionellen Stromerzeugung auf verschiedene Technologien (Summe sollte 1.0 ergeben)")
    
    with st.expander("Anteile 2030 konfigurieren", expanded=False):
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            braun_2030 = st.number_input("Braunkohle", min_value=0.0, max_value=1.0, value=0.25, step=0.05, key="sim_braun_2030")
        with col2:
            erdgas_2030 = st.number_input("Erdgas", min_value=0.0, max_value=1.0, value=0.4, step=0.05, key="sim_erdgas_2030")
        with col3:
            stein_2030 = st.number_input("Steinkohle", min_value=0.0, max_value=1.0, value=0.15, step=0.05, key="sim_stein_2030")
        with col4:
            sonstige_konv_2030 = st.number_input("Sonstige", min_value=0.0, max_value=1.0, value=0.1, step=0.05, key="sim_sonst_konv_2030")
        with col5:
            importe_2030 = st.number_input("Importe", min_value=0.0, max_value=1.0, value=0.1, step=0.05, key="sim_importe_2030")
        
        summe_2030 = braun_2030 + erdgas_2030 + stein_2030 + sonstige_konv_2030 + importe_2030
        if abs(summe_2030 - 1.0) > 0.01:
            st.warning(f"⚠️ Summe 2030: {summe_2030:.2f} (sollte 1.0 sein)")
        else:
            st.success(f"✓ Summe 2030: {summe_2030:.2f}")
    
    with st.expander("Anteile 2045 konfigurieren", expanded=False):
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            braun_2045 = st.number_input("Braunkohle", min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="sim_braun_2045")
        with col2:
            erdgas_2045 = st.number_input("Erdgas", min_value=0.0, max_value=1.0, value=0.6, step=0.05, key="sim_erdgas_2045")
        with col3:
            stein_2045 = st.number_input("Steinkohle", min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="sim_stein_2045")
        with col4:
            sonstige_konv_2045 = st.number_input("Sonstige", min_value=0.0, max_value=1.0, value=0.2, step=0.05, key="sim_sonst_konv_2045")
        with col5:
            importe_2045 = st.number_input("Importe", min_value=0.0, max_value=1.0, value=0.2, step=0.05, key="sim_importe_2045")
        
        summe_2045 = braun_2045 + erdgas_2045 + stein_2045 + sonstige_konv_2045 + importe_2045
        if abs(summe_2045 - 1.0) > 0.01:
            st.warning(f"⚠️ Summe 2045: {summe_2045:.2f} (sollte 1.0 sein)")
        else:
            st.success(f"✓ Summe 2045: {summe_2045:.2f}")
    
    st.markdown("### 📊 Lastprofile")
    lastprofile_einzel = st.checkbox(
        "Lastprofile berücksichtigen",
        value=True,
        help="Aktivieren, um E-Auto- und Wärmepumpen-Lastprofile in die Simulation einzubeziehen",
        key="lastprofile_einzel"
    )
    
    st.markdown("---")
    if st.button("🚀 Simulation starten", type="primary", width='stretch'):
        if gewaehltes_szenario and gewaehltes_profil:
            with st.spinner(f"Berechne Prognosen für '{ausgewähltes_szenario_name}'..."):
                try:
                    # Konventionelle Anteile aus den UI-Inputs verwenden
                    konven_anteile = {
                        "2030": {
                            "braun": braun_2030,
                            "erdgas": erdgas_2030,
                            "stein": stein_2030,
                            "sonstige": sonstige_konv_2030,
                            "importe": importe_2030
                        },
                        "2045": {
                            "braun": braun_2045,
                            "erdgas": erdgas_2045,
                            "stein": stein_2045,
                            "sonstige": sonstige_konv_2045,
                            "importe": importe_2045
                        }
                    }
                    
                    szenario_key = f"{ausgewähltes_szenario_name}_{ertragsart}_{lastprofile_einzel}_{ausgewähltes_profil_name}"
                    
                    if 'szenario_key' not in st.session_state or st.session_state['szenario_key'] != szenario_key:
                        szenario_ergebnis = Szenario(
                            name=ausgewähltes_szenario_name,
                            beschreibung=gewaehltes_szenario["Beschreibung"],
                            szenario=gewaehltes_szenario,
                            ziele_2030=gewaehltes_szenario["Ziele 2030"],
                            ziele_2045=gewaehltes_szenario["Ziele 2045"],
                            ertragsart=ertragsart,
                            verbrauchsprofile=gewaehltes_profil,
                            veränderungsfaktoren=gewaehltes_szenario["Veränderungsfaktoren"]["Erzeugung"],
                            konven_anteile=konven_anteile,
                            lastprofile=lastprofile_einzel
                        )
                        
                        st.session_state['letztes_szenario'] = szenario_ergebnis
                        st.session_state['szenario_key'] = szenario_key
                        st.session_state['jahr'] = 2045
                        st.success(f"✅ Simulation für '{ausgewähltes_szenario_name}' abgeschlossen!")
                    else:
                        st.info("ℹ️ Verwende gecachte Simulation (keine Parameter geändert)")
                    
                except Exception as e:
                    st.error(f"❌ Fehler bei der Simulation: {str(e)}")
                    st.exception(e)
    
    if 'letztes_szenario' in st.session_state:
        st.markdown("---")
        st.header("📊 Ergebnisse")
        
        szenario = st.session_state['letztes_szenario']
        jahr = st.session_state.get('jahr')
        
        tab1, tab2, tab3 = st.tabs(["ℹ️ Übersicht", "📊 Plots","📈 Verlaufsdarstellung"])
        
        with tab1:
            st.subheader("Zusammenfassung")
            
            col1, col2,col3,col4 = st.columns(4)
            
            ergebnisse = szenario.auswertungsdaten_generieren()
            top10_fehlenergie = szenario.getFehlenergieDF()
            if ergebnisse is not None and top10_fehlenergie is not None:
                try:         
                    stromerzeugung = ergebnisse["Erzeugung Erneuerbare im Jahr [TWh]"].sum()
                    gesamtkosten = ergebnisse["Gesamtkosten_EE_und_Speicher [Mrd. €]"].sum()   
                    st.header("Jahresübersicht")
                    st.dataframe(ergebnisse, width='stretch')
                    st.header("10 Viertelstunden mit größtem Energie-Defizit")
                    st.dataframe(top10_fehlenergie, width='stretch')
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
            
        with tab3:

            st.subheader("📈 Verlaufsdarstellung")
            st.markdown("### Verbrauch & Erzeugung im Jahr")
            jahr_auswertung = st.slider(
                "Jahr auswählen:", min_value=2026, max_value=2045, value=2045, step=1
            )

            try:
                fig1, ax1 = plt.subplots(figsize=(12, 6))
                verbrauch_jahr(szenario.getGesamtDF(), jahr_auswertung if jahr_auswertung else 2045, ax1)
                st.pyplot(fig1)
                buf_auswertung = BytesIO()
                fig1.savefig(buf_auswertung, format='png', dpi=300, bbox_inches='tight')
                buf_auswertung.seek(0)
                st.download_button(
                    label="💾 Plot herunterladen",
                    data=buf_auswertung,
                    file_name=f"szenario_{szenario.name}_zweierwochendiagramm_ertragsart_{szenario.ertragsart}_jahr_{jahr if jahr else 'alle'}.png",
                    mime="image/png",
                    on_click="ignore"
                )
            except Exception as e:
                st.error(f"❌ Fehler beim Erstellen der Auswertungskurven: {str(e)}")
                st.exception(e)    

            st.markdown("---")
            st.markdown("### Zwei-Wochen-Diagramm Stundenwerte")
            
            @st.fragment
            def render_zweiwochen_diagramm():
                startdatum = st.text_input(
                    "Startdatum im Format TT-MM-JJJJ (z.B., 15-12-2045):",
                    value="15-12-2045",
                    help="Geben Sie das Startdatum für das Zwei-Wochen-Diagramm ein.",
                    key="startdatum_zweiwochen"
                )
                try:
                    fig2, ax2 = plt.subplots(figsize=(12, 6))
                    zweiwochendiagramm_stunden(szenario.getGesamtDF(), startdatum, ax2)
                    st.pyplot(fig2)
                    buf_zweiwochen = BytesIO()
                    fig2.savefig(buf_zweiwochen, format='png', dpi=300, bbox_inches='tight')
                    buf_zweiwochen.seek(0)
                    st.download_button(
                        label="💾 Plot herunterladen",
                        data=buf_zweiwochen,
                        file_name=f"szenario_{szenario.name}_zweierwochendiagramm_stunden_ertragsart_{szenario.ertragsart}_start_{startdatum}.png",
                        mime="image/png",
                        key="download_zweiwochen"
                    )
                except Exception as e:
                    st.error(f"❌ Fehler beim Erstellen des Zwei-Wochen-Diagramms: {str(e)}")
                    st.exception(e)
            
            render_zweiwochen_diagramm()

            @st.fragment
            def render_ladestand_diagramm():
                startdatum_ladestand = st.text_input(
                    "Startdatum für Ladestand (TT-MM-JJJJ):",
                    value="15-12-2045",
                    key="startdatum_ladestand"
                )
                try:
                    st.markdown("---")
                    st.markdown("### Ladestand der Speicher")
                    fig3, ax3 = plt.subplots(figsize=(12, 6))
                    plot_liniendiagramm_ladestand(szenario.getGesamtDF(), startdatum_ladestand, ax3)
                    st.pyplot(fig3)
                    buf_ladestand = BytesIO()
                    fig3.savefig(buf_ladestand, format='png', dpi=300, bbox_inches='tight')
                    buf_ladestand.seek(0)
                    st.download_button(
                        label="💾 Plot herunterladen",
                        data=buf_ladestand,
                        file_name=f"szenario_{szenario.name}_ladestand_batteriespeicher_ertragsart_{szenario.ertragsart}_start_{startdatum_ladestand}.png",
                        mime="image/png",
                        key="download_ladestand"
                    )
                except Exception as e:
                    st.error(f"❌ Fehler beim Erstellen des Ladestand-Diagramms: {str(e)}")
                    st.exception(e)
            
            render_ladestand_diagramm()
            
            try:
                    st.markdown("---")
                    st.markdown("### Ladestand der Speicher während der Dunkelflaute 2030")
                    fig4, ax4 = plt.subplots(figsize=(12, 6))
                    plot_liniendiagramm_ladestand_dunkelflaute(szenario.getDunkelflauteDF(2030), ax4)
                    st.pyplot(fig4)
                    buf_dunkel2030 = BytesIO()
                    fig4.savefig(buf_dunkel2030, format='png', dpi=300, bbox_inches='tight')
                    buf_dunkel2030.seek(0)
                    st.download_button(
                        label="💾 Plot herunterladen",
                        data=buf_dunkel2030,
                        file_name=f"szenario_{szenario.name}_ladestand_dunkelflaute2030_ertragsart_{szenario.ertragsart}.png",
                        mime="image/png",
                        key="download_dunkel2030"
                    )
            except Exception as e:
                    st.error(f"❌ Fehler beim Erstellen des Dunkelflaute-2030-Diagramms: {str(e)}")
                    st.exception(e)

            try:
                    st.markdown("---")
                    st.markdown("### Ladestand der Speicher während der Dunkelflaute 2045")
                    fig5, ax5 = plt.subplots(figsize=(12, 6))
                    plot_liniendiagramm_ladestand_dunkelflaute(szenario.getDunkelflauteDF(2045), ax5)
                    st.pyplot(fig5)
                    buf_dunkel2045 = BytesIO()
                    fig5.savefig(buf_dunkel2045, format='png', dpi=300, bbox_inches='tight')
                    buf_dunkel2045.seek(0)
                    st.download_button(
                        label="💾 Plot herunterladen",
                        data=buf_dunkel2045,
                        file_name=f"szenario_{szenario.name}_ladestand_dunkelflaute2045_ertragsart_{szenario.ertragsart}.png",
                        mime="image/png",
                        key="download_dunkel2045"
                    )
            except Exception as e:
                    st.error(f"❌ Fehler beim Erstellen des Dunkelflaute-2045-Diagramms: {str(e)}")
                    st.exception(e)


        st.markdown("---")
        try:
            excel_buffer2 = BytesIO()
            gesamt = szenario.getGesamtDF().copy()
            
            # Timezone entfernen falls vorhanden
            if "Datum von" in gesamt.columns:
                if hasattr(gesamt["Datum von"].dtype, 'tz') and gesamt["Datum von"].dt.tz is not None:
                    gesamt["Datum von"] = gesamt["Datum von"].dt.tz_localize(None)
            
            gesamt.to_csv(excel_buffer2, index=False, decimal='.', sep=';')
            excel_buffer2.seek(0)
            
            st.download_button(
                label="💾 Simulationsdaten als csv herunterladen",
                data=excel_buffer2,
                file_name=f"szenario_{szenario.name}_ertragsart_{szenario.ertragsart}_simulationsdaten.csv",
                mime="text/csv",
                on_click="ignore"
            )
        except Exception as e:
            st.error(f"❌ Fehler beim Erstellen der Simulationsdaten-Excel: {str(e)}")
            st.exception(e)

        st.markdown("---")
        excel_buffer = BytesIO()
        szenario.auswertungsdaten_generieren().to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        
        st.download_button(
            label="💾 Gesamtergebnis als Excel herunterladen",
            data=excel_buffer,
            file_name=f"szenario_{szenario.name}_ertragsart_{szenario.ertragsart}_ergebnisse.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            on_click="ignore"
        )

# ============================================================================
# MODUS 2: ALLE SZENARIEN
# ============================================================================
elif modus == "📈 Szenarien vergleichen":
    st.header("📈 Szenarien vergleichen")
    
    st.info("Dieser Modus berechnet alle verfügbaren Szenarien und vergleicht die Ergebnisse.")
    
    szenarien_dict = {}
    for szen in szenarien:
        szenarien_dict[szen["Name"]] = szen

    ausgewählte_szenarien = st.multiselect(
        "Szenario auswählen",
        options=szenarien_dict.keys()
    )

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
    
    st.markdown("### ⚡ Konventionelle Anteile")
    st.info("Verteilung der konventionellen Stromerzeugung auf verschiedene Technologien (Summe sollte 1.0 ergeben)")
    
    with st.expander("Anteile bis 2030 konfigurieren", expanded=False):
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            braun_2030_vgl = st.number_input("Braunkohle", min_value=0.0, max_value=1.0, value=0.25, step=0.05, key="vgl_braun_2030")
        with col2:
            erdgas_2030_vgl = st.number_input("Erdgas", min_value=0.0, max_value=1.0, value=0.4, step=0.05, key="vgl_erdgas_2030")
        with col3:
            stein_2030_vgl = st.number_input("Steinkohle", min_value=0.0, max_value=1.0, value=0.15, step=0.05, key="vgl_stein_2030")
        with col4:
            sonstige_konv_2030_vgl = st.number_input("Sonstige", min_value=0.0, max_value=1.0, value=0.1, step=0.05, key="vgl_sonst_konv_2030")
        with col5:
            importe_2030_vgl = st.number_input("Importe", min_value=0.0, max_value=1.0, value=0.1, step=0.05, key="vgl_importe_2030")
        
        summe_2030_vgl = braun_2030_vgl + erdgas_2030_vgl + stein_2030_vgl + sonstige_konv_2030_vgl + importe_2030_vgl
        if abs(summe_2030_vgl - 1.0) > 0.01:
            st.warning(f"⚠️ Summe 2030: {summe_2030_vgl:.2f} (sollte 1.0 sein)")
        else:
            st.success(f"✓ Summe 2030: {summe_2030_vgl:.2f}")
    
    with st.expander("Anteile bis 2045 konfigurieren", expanded=False):
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            braun_2045_vgl = st.number_input("Braunkohle", min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="vgl_braun_2045")
        with col2:
            erdgas_2045_vgl = st.number_input("Erdgas", min_value=0.0, max_value=1.0, value=0.6, step=0.05, key="vgl_erdgas_2045")
        with col3:
            stein_2045_vgl = st.number_input("Steinkohle", min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="vgl_stein_2045")
        with col4:
            sonstige_konv_2045_vgl = st.number_input("Sonstige", min_value=0.0, max_value=1.0, value=0.2, step=0.05, key="vgl_sonst_konv_2045")
        with col5:
            importe_2045_vgl = st.number_input("Importe", min_value=0.0, max_value=1.0, value=0.2, step=0.05, key="vgl_importe_2045")
        
        summe_2045_vgl = braun_2045_vgl + erdgas_2045_vgl + stein_2045_vgl + sonstige_konv_2045_vgl + importe_2045_vgl
        if abs(summe_2045_vgl - 1.0) > 0.01:
            st.warning(f"⚠️ Summe 2045: {summe_2045_vgl:.2f} (sollte 1.0 sein)")
        else:
            st.success(f"✓ Summe 2045: {summe_2045_vgl:.2f}")
    
    st.markdown("### 📊 Lastprofile")
    lastprofile_vergleich = st.checkbox(
        "Lastprofile berücksichtigen",
        value=True,
        help="Aktivieren, um E-Auto- und Wärmepumpen-Lastprofile in die Simulation einzubeziehen",
        key="lastprofile_vergleich"
    )
    
    ausgewählte = []
    for key in ausgewählte_szenarien:
        ausgewählte.append(szenarien_dict[key])
    
    if st.button("🚀 Ausgewählte Szenarien simulieren", type="primary", width='stretch'):
        gewaehltes_profil = get_verbrauchsprofil_by_name(verbrauchsprofile, ausgewähltes_profil_name)
        
        if gewaehltes_profil:
            alle_ergebnisse = pd.DataFrame()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, szenario_data in enumerate(ausgewählte):
                status_text.text(f"Berechne {szenario_data['Name']}... ({idx+1}/{len(ausgewählte)})")
                
                try:
                    # Konventionelle Anteile aus den UI-Inputs verwenden
                    konven_anteile = {
                        "2030": {
                            "braun": braun_2030_vgl,
                            "erdgas": erdgas_2030_vgl,
                            "stein": stein_2030_vgl,
                            "sonstige": sonstige_konv_2030_vgl,
                            "importe": importe_2030_vgl
                        },
                        "2045": {
                            "braun": braun_2045_vgl,
                            "erdgas": erdgas_2045_vgl,
                            "stein": stein_2045_vgl,
                            "sonstige": sonstige_konv_2045_vgl,
                            "importe": importe_2045_vgl
                        }
                    }
                    
                    szenario_ergebnis = Szenario(
                        name=szenario_data["Name"],
                        beschreibung=szenario_data["Beschreibung"],
                        szenario=szenario_data,
                        ziele_2030=szenario_data["Ziele 2030"],
                        ziele_2045=szenario_data["Ziele 2045"],
                        ertragsart=ertragsart,
                        verbrauchsprofile=gewaehltes_profil,
                        veränderungsfaktoren=szenario_data["Veränderungsfaktoren"]["Erzeugung"],
                        konven_anteile=konven_anteile,
                        lastprofile=lastprofile_vergleich
                    )
                    
                    #szenario_ergebnis.berechne_alle_prognosen()
                    ergebnisse_df = szenario_ergebnis.getErgebnisse()
                    alle_ergebnisse = pd.concat([alle_ergebnisse, ergebnisse_df], ignore_index=True)
                    
                except Exception as e:
                    st.warning(f"Fehler bei {szenario_data['Name']}: {str(e)}")
                
                progress_bar.progress((idx + 1) / len(ausgewählte))
            
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
                    mime="image/png"
                )
                st.pyplot(fig2)
                buf2 = BytesIO()
                fig2.savefig(buf2, format='png', dpi=300, bbox_inches='tight')
                buf2.seek(0)
                st.download_button(
                    label="💾 Plot herunterladen",
                    data=buf2,
                    file_name=f"vergleich_aller_szenarien_ertragsart_{ertragsart}_plots2.png",
                    mime="image/png"
                )
                
                st.subheader("📊 Vergleichstabelle")
                st.dataframe(alle_ergebnisse, width='stretch')
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

elif modus == "➕ Szenario hinzufügen/Verändern":
    st.header("➕ Szenario hinzufügen/Verändern")
    st.info("Hier können Sie neue Szenarien und Verbrauchsprofile zur Simulation hinzufügen oder verändern. Wird Online nur Lokal gespeichert.")
    
    tab1, tab2, tab3 = st.tabs(["🎯 Neues Szenario", "📊 Neues Verbrauchsprofil", "✏️ Szenario verändern"])
    
    # ========================================================================
    # TAB 1: NEUES SZENARIO HINZUFÜGEN
    # ========================================================================
    with tab1:
        st.subheader("🎯 Neues Szenario erstellen")
        
        with st.form("neues_szenario_form"):
            st.markdown("### Grunddaten")
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Szenario-Name*", placeholder="z.B. Optimistisches Szenario")
            with col2:
                beschreibung = st.text_area("Beschreibung*", placeholder="Kurze Beschreibung des Szenarios")
            
            st.markdown("---")
            st.markdown("### 🎯 Ziele 2030")
            st.markdown("#### Ausbau Erneuerbare Energien (in GW)")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                pv_dach_2030 = st.number_input("PV Dach", min_value=0.0, value=125.0, step=1.0, key="pv_dach_2030")
                pv_frei_2030 = st.number_input("PV Frei", min_value=0.0, value=90.0, step=1.0, key="pv_frei_2030")
            with col2:
                wind_onshore_2030 = st.number_input("Wind Onshore", min_value=0.0, value=115.0, step=1.0, key="wind_onshore_2030")
                wind_offshore_2030 = st.number_input("Wind Offshore", min_value=0.0, value=30.0, step=1.0, key="wind_offshore_2030")
            with col3:
                biomasse_2030 = st.number_input("Biomasse", min_value=0.0, value=10.0, step=0.1, key="biomasse_2030")
                wasser_2030 = st.number_input("Wasser", min_value=0.0, value=6.0, step=0.1, key="wasser_2030")
            with col4:
                sonstige_2030 = st.number_input("Sonstige", min_value=0.0, value=0.1, step=0.1, key="sonstige_2030")
            
            st.markdown("#### Ausbau Speicher 2030 (in GWh)")
            col1, col2, col3 = st.columns(3)
            with col1:
                batteriespeicher_2030 = st.number_input("Batteriespeicher", min_value=0.0, value=120.0, step=1.0, key="batt_2030")
            with col2:
                wasserstoff_2030 = st.number_input("Wasserstoff", min_value=0.0, value=70.0, step=1.0, key="h2_2030")
            with col3:
                pumpspeicher_2030 = st.number_input("Pumpspeicher", min_value=0.0, value=50.0, step=1.0, key="pump_2030")
            
            st.markdown("---")
            st.markdown("### 🎯 Ziele 2045")
            st.markdown("#### Ausbau Erneuerbare Energien (in GW)")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                pv_dach_2045 = st.number_input("PV Dach", min_value=0.0, value=450.0, step=1.0, key="pv_dach_2045")
                pv_frei_2045 = st.number_input("PV Frei", min_value=0.0, value=250.0, step=1.0, key="pv_frei_2045")
            with col2:
                wind_onshore_2045 = st.number_input("Wind Onshore", min_value=0.0, value=300.0, step=1.0, key="wind_onshore_2045")
                wind_offshore_2045 = st.number_input("Wind Offshore", min_value=0.0, value=150.0, step=1.0, key="wind_offshore_2045")
            with col3:
                biomasse_2045 = st.number_input("Biomasse", min_value=0.0, value=40.0, step=0.1, key="biomasse_2045")
                wasser_2045 = st.number_input("Wasser", min_value=0.0, value=6.0, step=0.1, key="wasser_2045")
            with col4:
                sonstige_2045 = st.number_input("Sonstige", min_value=0.0, value=0.1, step=0.1, key="sonstige_2045")
            
            st.markdown("#### Ausbau Speicher 2045 (in GWh)")
            col1, col2, col3 = st.columns(3)
            with col1:
                batteriespeicher_2045 = st.number_input("Batteriespeicher", min_value=0.0, value=2500.0, step=10.0, key="batt_2045")
            with col2:
                wasserstoff_2045 = st.number_input("Wasserstoff", min_value=0.0, value=1000.0, step=10.0, key="h2_2045")
            with col3:
                pumpspeicher_2045 = st.number_input("Pumpspeicher", min_value=0.0, value=300.0, step=10.0, key="pump_2045")
            
            st.markdown("---")
            st.markdown("### 🔧 Veränderungsfaktoren")
            st.markdown("#### Erzeugung")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                v_pv_dach = st.number_input("PV Dach", min_value=0.0, value=1.0, step=0.1, key="v_pv_dach")
                v_pv_frei = st.number_input("PV Frei", min_value=0.0, value=1.0, step=0.1, key="v_pv_frei")
            with col2:
                v_wind_onshore = st.number_input("Wind Onshore", min_value=0.0, value=1.0, step=0.1, key="v_wind_on")
                v_wind_offshore = st.number_input("Wind Offshore", min_value=0.0, value=1.0, step=0.1, key="v_wind_off")
            with col3:
                v_biomasse = st.number_input("Biomasse", min_value=0.0, value=1.0, step=0.1, key="v_biomasse")
                v_wasser = st.number_input("Wasser", min_value=0.0, value=1.0, step=0.1, key="v_wasser")
            with col4:
                v_sonstige = st.number_input("Sonstige", min_value=0.0, value=1.0, step=0.1, key="v_sonstige")
            
            st.markdown("#### CAPEX EE")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                c_pv_dach = st.number_input("PV Dach", min_value=0.0, value=1.0, step=0.1, key="c_pv_dach")
                c_pv_frei = st.number_input("PV Frei", min_value=0.0, value=1.0, step=0.1, key="c_pv_frei")
            with col2:
                c_wind_onshore = st.number_input("Wind Onshore", min_value=0.0, value=1.0, step=0.1, key="c_wind_on")
                c_wind_offshore = st.number_input("Wind Offshore", min_value=0.0, value=1.0, step=0.1, key="c_wind_off")
            with col3:
                c_biomasse = st.number_input("Biomasse", min_value=0.0, value=1.0, step=0.1, key="c_biomasse")
                c_wasser = st.number_input("Wasser", min_value=0.0, value=1.0, step=0.1, key="c_wasser")
            with col4:
                c_sonstige = st.number_input("Sonstige", min_value=0.0, value=1.0, step=0.1, key="c_sonstige")
            
            st.markdown("#### OPEX EE")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                o_pv_dach = st.number_input("PV Dach", min_value=0.0, value=1.0, step=0.1, key="o_pv_dach")
                o_pv_frei = st.number_input("PV Frei", min_value=0.0, value=1.0, step=0.1, key="o_pv_frei")
            with col2:
                o_wind_onshore = st.number_input("Wind Onshore", min_value=0.0, value=1.0, step=0.1, key="o_wind_on")
                o_wind_offshore = st.number_input("Wind Offshore", min_value=0.0, value=1.0, step=0.1, key="o_wind_off")
            with col3:
                o_biomasse = st.number_input("Biomasse", min_value=0.0, value=1.0, step=0.1, key="o_biomasse")
                o_wasser = st.number_input("Wasser", min_value=0.0, value=1.0, step=0.1, key="o_wasser")
            with col4:
                o_sonstige = st.number_input("Sonstige", min_value=0.0, value=1.0, step=0.1, key="o_sonstige")
            
            st.markdown("#### CAPEX Speicher")
            col1, col2, col3 = st.columns(3)
            with col1:
                cs_batt = st.number_input("Batteriespeicher", min_value=0.0, value=1.0, step=0.1, key="cs_batt")
            with col2:
                cs_h2 = st.number_input("Wasserstoff", min_value=0.0, value=1.0, step=0.1, key="cs_h2")
            with col3:
                cs_pump = st.number_input("Pumpspeicher", min_value=0.0, value=1.0, step=0.1, key="cs_pump")
            
            st.markdown("#### OPEX Speicher")
            col1, col2, col3 = st.columns(3)
            with col1:
                os_batt = st.number_input("Batteriespeicher", min_value=0.0, value=1.0, step=0.1, key="os_batt")
            with col2:
                os_h2 = st.number_input("Wasserstoff", min_value=0.0, value=1.0, step=0.1, key="os_h2")
            with col3:
                os_pump = st.number_input("Pumpspeicher", min_value=0.0, value=1.0, step=0.1, key="os_pump")
            
            st.markdown("---")
            submitted = st.form_submit_button("💾 Szenario speichern", type="primary", width='stretch')
            
            if submitted:
                if not name or not beschreibung:
                    st.error("❌ Bitte füllen Sie Name und Beschreibung aus!")
                else:
                    # Neues Szenario erstellen
                    neues_szenario = {
                        "Name": name,
                        "Beschreibung": beschreibung,
                        "Ziele 2030": {
                            "Ausbau EE": {
                                "pv_dach": pv_dach_2030,
                                "pv_frei": pv_frei_2030,
                                "wind_onshore": wind_onshore_2030,
                                "wind_offshore": wind_offshore_2030,
                                "biomasse": biomasse_2030,
                                "wasser": wasser_2030,
                                "sonstige": sonstige_2030
                            },
                            "Ausbau Speicher": {
                                "batteriespeicher": batteriespeicher_2030,
                                "wasserstoff": wasserstoff_2030,
                                "pumpspeicher": pumpspeicher_2030
                            }
                        },
                        "Ziele 2045": {
                            "Ausbau EE": {
                                "pv_dach": pv_dach_2045,
                                "pv_frei": pv_frei_2045,
                                "wind_onshore": wind_onshore_2045,
                                "wind_offshore": wind_offshore_2045,
                                "biomasse": biomasse_2045,
                                "wasser": wasser_2045,
                                "sonstige": sonstige_2045
                            },
                            "Ausbau Speicher": {
                                "batteriespeicher": batteriespeicher_2045,
                                "wasserstoff": wasserstoff_2045,
                                "pumpspeicher": pumpspeicher_2045
                            }
                        },
                        "Veränderungsfaktoren": {
                            "Erzeugung": {
                                "pv_dach": v_pv_dach,
                                "pv_frei": v_pv_frei,
                                "wind_onshore": v_wind_onshore,
                                "wind_offshore": v_wind_offshore,
                                "biomasse": v_biomasse,
                                "wasser": v_wasser,
                                "sonstige": v_sonstige
                            },
                            "Capex_EE": {
                                "pv_dach": c_pv_dach,
                                "pv_frei": c_pv_frei,
                                "wind_onshore": c_wind_onshore,
                                "wind_offshore": c_wind_offshore,
                                "biomasse": c_biomasse,
                                "wasser": c_wasser,
                                "sonstige": c_sonstige
                            },
                            "Opex_EE": {
                                "pv_dach": o_pv_dach,
                                "pv_frei": o_pv_frei,
                                "wind_onshore": o_wind_onshore,
                                "wind_offshore": o_wind_offshore,
                                "biomasse": o_biomasse,
                                "wasser": o_wasser,
                                "sonstige": o_sonstige
                            },
                            "Capex_Speicher": {
                                "batteriespeicher": cs_batt,
                                "wasserstoff": cs_h2,
                                "pumpspeicher": cs_pump
                            },
                            "Opex_Speicher": {
                                "batteriespeicher": os_batt,
                                "wasserstoff": os_h2,
                                "pumpspeicher": os_pump
                            }
                        }
                    }
                    
                    try:
                        # JSON-Datei laden
                        with open(szenarien_pfad, 'r', encoding='utf-8') as f:
                            alle_szenarien = json.load(f)
                        
                        # Prüfen ob Name bereits existiert
                        if any(s["Name"] == name for s in alle_szenarien):
                            st.error(f"❌ Ein Szenario mit dem Namen '{name}' existiert bereits!")
                        else:
                            # Neues Szenario hinzufügen
                            alle_szenarien.append(neues_szenario)
                            
                            # JSON-Datei speichern
                            with open(szenarien_pfad, 'w', encoding='utf-8') as f:
                                json.dump(alle_szenarien, f, indent=4, ensure_ascii=False)
                            
                            # Cache invalidieren
                            st.cache_data.clear()
                            
                            st.success(f"✅ Szenario '{name}' erfolgreich gespeichert!")
                            
                            # Git-Automatisierung
                            with st.spinner("📤 Speichere ins Repository..."):
                                success, message = git_commit_and_push(
                                    szenarien_pfad.relative_to(PROJECT_ROOT),
                                    f"Neues Szenario hinzugefügt: {name}"
                                )
                                if success:
                                    st.success(f"✅ {message}")
                                else:
                                    st.warning(f"⚠️ Lokal gespeichert, aber Git-Operation fehlgeschlagen: {message}")
                            
                            st.balloons()
                            st.info("🔄 Seite wird neu geladen, um das neue Szenario anzuzeigen...")
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"❌ Fehler beim Speichern: {str(e)}")
                        st.exception(e)
    
    # ========================================================================
    # TAB 2: NEUES VERBRAUCHSPROFIL HINZUFÜGEN
    # ========================================================================
    with tab2:
        st.subheader("📊 Neues Verbrauchsprofil erstellen")
        
        with st.form("neues_profil_form"):
            st.markdown("### Grunddaten")
            
            profil_name = st.text_input("Profil-Name*", placeholder="z.B. 3")
            
            col1, col2 = st.columns(2)
            with col1:
                verbrauch_2030 = st.number_input(
                    "Verbrauch 2030 (TWh)*", 
                    min_value=0.0, 
                    value=628.0, 
                    step=1.0,
                    help="Gesamtverbrauch im Jahr 2030 in Terawattstunden"
                )
            with col2:
                verbrauch_2045 = st.number_input(
                    "Verbrauch 2045 (TWh)*", 
                    min_value=0.0, 
                    value=890.0, 
                    step=1.0,
                    help="Gesamtverbrauch im Jahr 2045 in Terawattstunden"
                )
            
            st.markdown("### E-Auto Annahmen")
            col3, col4 = st.columns(2)
            with col3:
                e_autos_2030 = st.number_input(
                    "E-Autos 2030 (Anzahl)*", 
                    min_value=0, 
                    value=15000000, 
                    step=1000000,
                    help="Anzahl der E-Autos im Jahr 2030"
                )
            with col4:
                e_autos_2045 = st.number_input(
                    "E-Autos 2045 (Anzahl)*", 
                    min_value=0, 
                    value=40000000, 
                    step=1000000,
                    help="Anzahl der E-Autos im Jahr 2045"
                )
            
            st.markdown("### Wärmepumpen Annahmen")
            col5, col6 = st.columns(2)
            with col5:
                wp_2030 = st.number_input(
                    "Wärmepumpen 2030 (Anzahl)*", 
                    min_value=0, 
                    value=6000000, 
                    step=500000,
                    help="Anzahl der Wärmepumpen im Jahr 2030"
                )
            with col6:
                wp_2045 = st.number_input(
                    "Wärmepumpen 2045 (Anzahl)*", 
                    min_value=0, 
                    value=12000000, 
                    step=500000,
                    help="Anzahl der Wärmepumpen im Jahr 2045"
                )
            
            st.markdown("---")
            profil_submitted = st.form_submit_button("💾 Verbrauchsprofil speichern", type="primary", width='stretch')
            
            if profil_submitted:
                if not profil_name:
                    st.error("❌ Bitte geben Sie einen Namen ein!")
                else:
                    # Neues Verbrauchsprofil erstellen
                    neues_profil = {
                        "Name": profil_name,
                        "Verbrauch_2030": verbrauch_2030,
                        "Verbrauch_2045": verbrauch_2045,
                        "E_Autos_2030": e_autos_2030,
                        "E_Autos_2045": e_autos_2045,
                        "WP_2030": wp_2030,
                        "WP_2045": wp_2045
                    }
                    
                    try:
                        with open(verbrauchsprofile_pfad, 'r', encoding='utf-8') as f:
                            alle_profile = json.load(f)
                        
                        if any(p["Name"] == profil_name for p in alle_profile):
                            st.error(f"❌ Ein Verbrauchsprofil mit dem Namen '{profil_name}' existiert bereits!")
                        else:
                            alle_profile.append(neues_profil)
                            
                            with open(verbrauchsprofile_pfad, 'w', encoding='utf-8') as f:
                                json.dump(alle_profile, f, indent=4, ensure_ascii=False)
                            
                            st.cache_data.clear()
                            
                            st.success(f"✅ Verbrauchsprofil '{profil_name}' erfolgreich gespeichert!")
                            
                            with st.spinner("📤 Speichere ins Repository..."):
                                success, message = git_commit_and_push(
                                    verbrauchsprofile_pfad.relative_to(PROJECT_ROOT),
                                    f"Neues Verbrauchsprofil hinzugefügt: {profil_name}"
                                )
                                if success:
                                    st.success(f"✅ {message}")
                                else:
                                    st.warning(f"⚠️ Lokal gespeichert, aber Git-Operation fehlgeschlagen: {message}")
                            
                            st.balloons()
                            st.info("🔄 Seite wird neu geladen, um das neue Profil anzuzeigen...")
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"❌ Fehler beim Speichern: {str(e)}")
                        st.exception(e)
    # ========================================================================
    # TAB 3: SZENARIO VERÄNDERN
    # ========================================================================
    with tab3:
        st.subheader("✏️ Szenario verändern")
        st.info("Wählen Sie ein Szenario aus, um dessen Daten zu bearbeiten.")
        
        szenario_namen = [szen["Name"] for szen in szenarien]
        ausgewähltes_szenario_name = st.selectbox(
            "Szenario auswählen",
            szenario_namen
        )
        
        if ausgewähltes_szenario_name:
            szenario_to_edit = get_scenario_by_name(szenarien, ausgewähltes_szenario_name)
            
            if szenario_to_edit:
                st.markdown("### Aktuelle Beschreibung")
                st.write(szenario_to_edit["Beschreibung"])
                
                neue_beschreibung = st.text_area(
                    "Neue Beschreibung eingeben",
                    value=szenario_to_edit["Beschreibung"]
                )

                st.markdown("---")
                st.markdown("### 🎯 Ziele 2030")
                st.markdown("#### Ausbaustand Erneuerbare Energien (in GW)")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    pv_dach_2030 = st.number_input("PV Dach", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2030"]["Ausbau EE"]["pv_dach"]), 2), step=1.0, key="pv_dach_2030_edit")
                    pv_frei_2030 = st.number_input("PV Frei", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2030"]["Ausbau EE"]["pv_frei"]), 2), step=1.0, key="pv_frei_2030_edit")
                with col2:
                    wind_onshore_2030 = st.number_input("Wind Onshore", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2030"]["Ausbau EE"]["wind_onshore"]), 2), step=1.0, key="wind_onshore_2030_edit")
                    wind_offshore_2030 = st.number_input("Wind Offshore", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2030"]["Ausbau EE"]["wind_offshore"]), 2), step=1.0, key="wind_offshore_2030_edit")
                with col3:
                    biomasse_2030 = st.number_input("Biomasse", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2030"]["Ausbau EE"]["biomasse"]), 2), step=0.1, key="biomasse_2030_edit")
                    wasser_2030 = st.number_input("Wasser", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2030"]["Ausbau EE"]["wasser"]), 2), step=0.1, key="wasser_2030_edit")
                with col4:
                    sonstige_2030 = st.number_input("Sonstige", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2030"]["Ausbau EE"]["sonstige"]), 2), step=0.1, key="sonstige_2030_edit")
                
                st.markdown("#### Ausbau Speicher 2030 (in GWh)")
                col1, col2, col3 = st.columns(3)
                with col1:
                    batteriespeicher_2030 = st.number_input("Batteriespeicher", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2030"]["Ausbau Speicher"]["batteriespeicher"]), 2), step=1.0, key="batt_2030_edit")
                with col2:
                    wasserstoff_2030 = st.number_input("Wasserstoff", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2030"]["Ausbau Speicher"]["wasserstoff"]), 2), step=1.0, key="h2_2030_edit")
                with col3:
                    pumpspeicher_2030 = st.number_input("Pumpspeicher", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2030"]["Ausbau Speicher"]["pumpspeicher"]), 2), step=1.0, key="pump_2030_edit")
                
                st.markdown("---")
                st.markdown("### 🎯 Ziele 2045")
                st.markdown("#### Ausbaustand Erneuerbare Energien (in GW)")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    pv_dach_2045 = st.number_input("PV Dach", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2045"]["Ausbau EE"]["pv_dach"]), 2), step=1.0, key="pv_dach_2045_edit")
                    pv_frei_2045 = st.number_input("PV Frei", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2045"]["Ausbau EE"]["pv_frei"]), 2), step=1.0, key="pv_frei_2045_edit")
                with col2:
                    wind_onshore_2045 = st.number_input("Wind Onshore", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2045"]["Ausbau EE"]["wind_onshore"]), 2), step=1.0, key="wind_onshore_2045_edit")
                    wind_offshore_2045 = st.number_input("Wind Offshore", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2045"]["Ausbau EE"]["wind_offshore"]), 2), step=1.0, key="wind_offshore_2045_edit")
                with col3:
                    biomasse_2045 = st.number_input("Biomasse", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2045"]["Ausbau EE"]["biomasse"]), 2), step=0.1, key="biomasse_2045_edit")
                    wasser_2045 = st.number_input("Wasser", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2045"]["Ausbau EE"]["wasser"]), 2), step=0.1, key="wasser_2045_edit")
                with col4:
                    sonstige_2045 = st.number_input("Sonstige", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2045"]["Ausbau EE"]["sonstige"]), 2), step=0.1, key="sonstige_2045_edit")
                
                st.markdown("#### Ausbau Speicher 2045 (in GWh)")
                col1, col2, col3 = st.columns(3)
                with col1:
                    batteriespeicher_2045 = st.number_input("Batteriespeicher", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2045"]["Ausbau Speicher"]["batteriespeicher"]), 2), step=10.0, key="batt_2045_edit")
                with col2:
                    wasserstoff_2045 = st.number_input("Wasserstoff", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2045"]["Ausbau Speicher"]["wasserstoff"]), 2), step=10.0, key="h2_2045_edit")
                with col3:
                    pumpspeicher_2045 = st.number_input("Pumpspeicher", min_value=0.0, value=round(float(szenario_to_edit["Ziele 2045"]["Ausbau Speicher"]["pumpspeicher"]), 2), step=10.0, key="pump_2045_edit")
                
                st.markdown("---")
                st.markdown("### 🔧 Veränderungsfaktoren")
                st.markdown("#### Erzeugung")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    v_pv_dach = st.number_input("PV Dach", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Erzeugung"]["pv_dach"]), 2), step=0.1, key="v_pv_dach_edit")
                    v_pv_frei = st.number_input("PV Frei", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Erzeugung"]["pv_frei"]), 2), step=0.1, key="v_pv_frei_edit")
                with col2:
                    v_wind_onshore = st.number_input("Wind Onshore", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Erzeugung"]["wind_onshore"]), 2), step=0.1, key="v_wind_on_edit")
                    v_wind_offshore = st.number_input("Wind Offshore", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Erzeugung"]["wind_offshore"]), 2), step=0.1, key="v_wind_off_edit")
                with col3:
                    v_biomasse = st.number_input("Biomasse", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Erzeugung"]["biomasse"]), 2), step=0.1, key="v_biomasse_edit")
                    v_wasser = st.number_input("Wasser", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Erzeugung"]["wasser"]), 2), step=0.1, key="v_wasser_edit")
                with col4:
                    v_sonstige = st.number_input("Sonstige", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Erzeugung"]["sonstige"]), 2), step=0.1, key="v_sonstige_edit")
                
                st.markdown("#### CAPEX EE")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    c_pv_dach = st.number_input("PV Dach", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Capex_EE"]["pv_dach"]), 2), step=0.1, key="c_pv_dach_edit")
                    c_pv_frei = st.number_input("PV Frei", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Capex_EE"]["pv_frei"]), 2), step=0.1, key="c_pv_frei_edit")
                with col2:
                    c_wind_onshore = st.number_input("Wind Onshore", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Capex_EE"]["wind_onshore"]), 2), step=0.1, key="c_wind_on_edit")
                    c_wind_offshore = st.number_input("Wind Offshore", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Capex_EE"]["wind_offshore"]), 2), step=0.1, key="c_wind_off_edit")
                with col3:
                    c_biomasse = st.number_input("Biomasse", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Capex_EE"]["biomasse"]), 2), step=0.1, key="c_biomasse_edit")
                    c_wasser = st.number_input("Wasser", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Capex_EE"]["wasser"]), 2), step=0.1, key="c_wasser_edit")
                with col4:
                    c_sonstige = st.number_input("Sonstige", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Capex_EE"]["sonstige"]), 2), step=0.1, key="c_sonstige_edit")
                
                st.markdown("#### OPEX EE")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    o_pv_dach = st.number_input("PV Dach", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Opex_EE"]["pv_dach"]), 2), step=0.1, key="o_pv_dach_edit")
                    o_pv_frei = st.number_input("PV Frei", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Opex_EE"]["pv_frei"]), 2), step=0.1, key="o_pv_frei_edit")
                with col2:
                    o_wind_onshore = st.number_input("Wind Onshore", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Opex_EE"]["wind_onshore"]), 2), step=0.1, key="o_wind_on_edit")
                    o_wind_offshore = st.number_input("Wind Offshore", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Opex_EE"]["wind_offshore"]), 2), step=0.1, key="o_wind_off_edit")
                with col3:
                    o_biomasse = st.number_input("Biomasse", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Opex_EE"]["biomasse"]), 2), step=0.1, key="o_biomasse_edit")
                    o_wasser = st.number_input("Wasser", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Opex_EE"]["wasser"]), 2), step=0.1, key="o_wasser_edit")
                with col4:
                    o_sonstige = st.number_input("Sonstige", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Opex_EE"]["sonstige"]), 2), step=0.1, key="o_sonstige_edit")
                
                st.markdown("#### CAPEX Speicher")
                col1, col2, col3 = st.columns(3)
                with col1:
                    cs_batt = st.number_input("Batteriespeicher", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Capex_Speicher"]["batteriespeicher"]), 2), step=0.1, key="cs_batt_edit")
                with col2:
                    cs_h2 = st.number_input("Wasserstoff", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Capex_Speicher"]["wasserstoff"]), 2), step=0.1, key="cs_h2_edit")
                with col3:
                    cs_pump = st.number_input("Pumpspeicher", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Capex_Speicher"]["pumpspeicher"]), 2), step=0.1, key="cs_pump_edit")
                
                st.markdown("#### OPEX Speicher")
                col1, col2, col3 = st.columns(3)
                with col1:
                    os_batt = st.number_input("Batteriespeicher", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Opex_Speicher"]["batteriespeicher"]), 2), step=0.1, key="os_batt_edit")
                with col2:
                    os_h2 = st.number_input("Wasserstoff", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Opex_Speicher"]["wasserstoff"]), 2), step=0.1, key="os_h2_edit")
                with col3:
                    os_pump = st.number_input("Pumpspeicher", min_value=0.0, value=round(float(szenario_to_edit["Veränderungsfaktoren"]["Opex_Speicher"]["pumpspeicher"]), 2), step=0.1, key="os_pump_edit")
                
                if st.button("💾 Änderungen speichern", type="primary", width='stretch'):
                    try:
                        with open(szenarien_pfad, 'r', encoding='utf-8') as f:
                            alle_szenarien = json.load(f)
                        
                        for s in alle_szenarien:
                            if s["Name"] == ausgewähltes_szenario_name:
                                s["Beschreibung"] = neue_beschreibung
                                
                                s["Ziele 2030"]["Ausbau EE"]["pv_dach"] = pv_dach_2030
                                s["Ziele 2030"]["Ausbau EE"]["pv_frei"] = pv_frei_2030
                                s["Ziele 2030"]["Ausbau EE"]["wind_onshore"] = wind_onshore_2030
                                s["Ziele 2030"]["Ausbau EE"]["wind_offshore"] = wind_offshore_2030
                                s["Ziele 2030"]["Ausbau EE"]["biomasse"] = biomasse_2030
                                s["Ziele 2030"]["Ausbau EE"]["wasser"] = wasser_2030
                                s["Ziele 2030"]["Ausbau EE"]["sonstige"] = sonstige_2030
                                
                                s["Ziele 2030"]["Ausbau Speicher"]["batteriespeicher"] = batteriespeicher_2030
                                s["Ziele 2030"]["Ausbau Speicher"]["wasserstoff"] = wasserstoff_2030
                                s["Ziele 2030"]["Ausbau Speicher"]["pumpspeicher"] = pumpspeicher_2030
                                
                                # Ziele 2045 aktualisieren
                                s["Ziele 2045"]["Ausbau EE"]["pv_dach"] = pv_dach_2045
                                s["Ziele 2045"]["Ausbau EE"]["pv_frei"] = pv_frei_2045
                                s["Ziele 2045"]["Ausbau EE"]["wind_onshore"] = wind_onshore_2045
                                s["Ziele 2045"]["Ausbau EE"]["wind_offshore"] = wind_offshore_2045
                                s["Ziele 2045"]["Ausbau EE"]["biomasse"] = biomasse_2045
                                s["Ziele 2045"]["Ausbau EE"]["wasser"] = wasser_2045
                                s["Ziele 2045"]["Ausbau EE"]["sonstige"] = sonstige_2045
                                
                                s["Ziele 2045"]["Ausbau Speicher"]["batteriespeicher"] = batteriespeicher_2045
                                s["Ziele 2045"]["Ausbau Speicher"]["wasserstoff"] = wasserstoff_2045
                                s["Ziele 2045"]["Ausbau Speicher"]["pumpspeicher"] = pumpspeicher_2045
                                
                                # Veränderungsfaktoren Erzeugung aktualisieren
                                s["Veränderungsfaktoren"]["Erzeugung"]["pv_dach"] = v_pv_dach
                                s["Veränderungsfaktoren"]["Erzeugung"]["pv_frei"] = v_pv_frei
                                s["Veränderungsfaktoren"]["Erzeugung"]["wind_onshore"] = v_wind_onshore
                                s["Veränderungsfaktoren"]["Erzeugung"]["wind_offshore"] = v_wind_offshore
                                s["Veränderungsfaktoren"]["Erzeugung"]["biomasse"] = v_biomasse
                                s["Veränderungsfaktoren"]["Erzeugung"]["wasser"] = v_wasser
                                s["Veränderungsfaktoren"]["Erzeugung"]["sonstige"] = v_sonstige
                                
                                # CAPEX EE aktualisieren
                                s["Veränderungsfaktoren"]["Capex_EE"]["pv_dach"] = c_pv_dach
                                s["Veränderungsfaktoren"]["Capex_EE"]["pv_frei"] = c_pv_frei
                                s["Veränderungsfaktoren"]["Capex_EE"]["wind_onshore"] = c_wind_onshore
                                s["Veränderungsfaktoren"]["Capex_EE"]["wind_offshore"] = c_wind_offshore
                                s["Veränderungsfaktoren"]["Capex_EE"]["biomasse"] = c_biomasse
                                s["Veränderungsfaktoren"]["Capex_EE"]["wasser"] = c_wasser
                                s["Veränderungsfaktoren"]["Capex_EE"]["sonstige"] = c_sonstige
                                
                                # OPEX EE aktualisieren
                                s["Veränderungsfaktoren"]["Opex_EE"]["pv_dach"] = o_pv_dach
                                s["Veränderungsfaktoren"]["Opex_EE"]["pv_frei"] = o_pv_frei
                                s["Veränderungsfaktoren"]["Opex_EE"]["wind_onshore"] = o_wind_onshore
                                s["Veränderungsfaktoren"]["Opex_EE"]["wind_offshore"] = o_wind_offshore
                                s["Veränderungsfaktoren"]["Opex_EE"]["biomasse"] = o_biomasse
                                s["Veränderungsfaktoren"]["Opex_EE"]["wasser"] = o_wasser
                                s["Veränderungsfaktoren"]["Opex_EE"]["sonstige"] = o_sonstige
                                
                                # CAPEX Speicher aktualisieren
                                s["Veränderungsfaktoren"]["Capex_Speicher"]["batteriespeicher"] = cs_batt
                                s["Veränderungsfaktoren"]["Capex_Speicher"]["wasserstoff"] = cs_h2
                                s["Veränderungsfaktoren"]["Capex_Speicher"]["pumpspeicher"] = cs_pump
                                
                                # OPEX Speicher aktualisieren
                                s["Veränderungsfaktoren"]["Opex_Speicher"]["batteriespeicher"] = os_batt
                                s["Veränderungsfaktoren"]["Opex_Speicher"]["wasserstoff"] = os_h2
                                s["Veränderungsfaktoren"]["Opex_Speicher"]["pumpspeicher"] = os_pump
                                
                                break
                        
                        with open(szenarien_pfad, 'w', encoding='utf-8') as f:
                            json.dump(alle_szenarien, f, indent=4, ensure_ascii=False)
                        
                        st.cache_data.clear()
                        
                        st.success(f"✅ Szenario '{ausgewähltes_szenario_name}' erfolgreich aktualisiert!")
                        
                        with st.spinner("📤 Speichere ins Repository..."):
                            success, message = git_commit_and_push(
                                szenarien_pfad.relative_to(PROJECT_ROOT),
                                f"Szenario verändert: {ausgewähltes_szenario_name}"
                            )
                            if success:
                                st.success(f"✅ {message}")
                            else:
                                st.warning(f"⚠️ Lokal gespeichert, aber Git-Operation fehlgeschlagen: {message}")
                        
                        st.balloons()
                        st.info("🔄 Seite wird neu geladen, um die Änderungen zu speichern")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Fehler beim Speichern: {str(e)}")
                        st.exception(e)


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
