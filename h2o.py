import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# --- 1. DATI STORICI ---
data_storica = {
    'Evento': ['Ottobre 2024', 'Dicembre 2025', 'Settembre 2024', 'Maggio 2023 I', 'Maggio 2023 II'],
    'Pioggia_mm': [100, 145, 180, 160, 240],
    'Livello_m': [1.45, 1.75, 1.82, 1.85, 2.15],
    'Esito': ['Allagamento', 'Tenuta', 'Allagamento', 'Allagamento', 'Allagamento']
}
df_storico = pd.DataFrame(data_storica)

# --- 2. RECUPERO DATI REAL-TIME ---
def fetch_realtime_data():
    idro_url = "https://simc.arpae.it/meteozen/rt_data/lastdata/-/1158841,4438103/simnbo/254,0,0/1,-,-,-/B13215"
    meteo_url = "https://api.open-meteo.com/v1/forecast?latitude=44.39&longitude=11.58&hourly=precipitation&past_days=1"
    
    try:
        res_idro = requests.get(idro_url).json()
        livello_live = float(res_idro['value'])
        res_meteo = requests.get(meteo_url).json()
        pioggia_24h = sum(res_meteo['hourly']['precipitation'][:24])
        return livello_live, round(pioggia_24h, 1)
    except Exception:
        return 0.85, 45.0 

# --- 3. LOGICA DI SIMULAZIONE RISCHIO CALIBRATA ---
def get_risk_status(livello):
    # ROSSO: Oltre il limite di tenuta testato a Dicembre 2025
    if livello > 1.75:
        return "🔴 RISCHIO ALTO: SUPERATA SOGLIA DICEMBRE 2025", "error"
    # GIALLO: Zona critica tra l'esondazione 2024 e la tenuta 2025
    elif livello >= 1.45:
        return "🟡 RISCHIO MEDIO: AREA TEST TENUTA (Scenario Dicembre 2025)", "warning"
    # VERDE: Sotto il livello di esondazione storica di Ottobre 2024
    else:
        return "🟢 RISCHIO BASSO: SITUAZIONE ORDINARIA", "success"

# --- 4. UI ---
st.set_page_config(page_title="Sillaro Sentinel LIVE", layout="wide")
st.title("🌊 Sillaro Real-Time Sentinel")

livello_att, pioggia_att = fetch_realtime_data()

# VISUALIZZAZIONE RISCHIO IN ALTO
stato_testo, stato_tipo = get_risk_status(livello_att)
if stato_tipo == "error":
    st.error(f"### {stato_testo}")
elif stato_tipo == "warning":
    st.warning(f"### {stato_testo}")
else:
    st.success(f"### {stato_testo}")

# Metriche
m1, m2 = st.columns(2)
m1.metric("Livello LIVE (m)", f"{livello_att}")
m2.metric("Pioggia 24h (mm)", f"{pioggia_att}")

if st.button('🔄 AGGIORNA DATI', use_container_width=True):
    st.rerun()

st.divider()

# --- 5. GRAFICO SCATTER ---
df_plot = df_storico.copy()
nuovo_punto = pd.DataFrame({
    'Evento': ['ORA'], 'Pioggia_mm': [pioggia_att], 
    'Livello_m': [livello_att], 'Esito': ['ATTUALE']
})
df_combined = pd.concat([df_plot, nuovo_punto], ignore_index=True)

fig = px.scatter(
    df_combined, x="Pioggia_mm", y="Livello_m", text="Evento", color="Esito",
    size=[15, 15, 15, 15, 15, 30],
    color_discrete_map={'Allagamento': 'red', 'Tenuta': 'green', 'ATTUALE': 'black'}
)

fig.update_traces(textposition='top center', textfont=dict(size=14, family="Arial Black"))
fig.update_layout(
    xaxis=dict(title=dict(text="Pioggia Cumulata (mm)", font=dict(size=18))),
    yaxis=dict(title=dict(text="Livello Sillaro CSP (m)", font=dict(size=18))),
    template="plotly_white", height=600,
    legend=dict(font=dict(size=16), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)
