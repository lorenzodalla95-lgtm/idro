import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# --- 1. DATI STORICI E CONFIGURAZIONE GRAFICA ---
data_storica = {
    'Evento': ['Ottobre 2024', 'Dicembre 2025', 'Settembre 2024', 'Maggio 2023 I', 'Maggio 2023 II'],
    'Pioggia_mm': [100, 145, 180, 160, 240],
    'Livello_m': [1.45, 1.75, 1.82, 1.85, 2.15],
    'Esito': ['Allagamento', 'Tenuta', 'Allagamento', 'Allagamento', 'Allagamento']
}
df_storico = pd.DataFrame(data_storica)

# --- 2. FUNZIONE DI RECUPERO DATI ---
def fetch_realtime_data():
    lat, lon = 44.39, 11.58
    meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=precipitation&past_days=1"
    try:
        res_meteo = requests.get(meteo_url).json()
        pioggia_24h = sum(res_meteo['hourly']['precipitation'][:24])
        livello_live = 0.85 # Qui va il collegamento al tuo sensore
        return livello_live, round(pioggia_24h, 1)
    except:
        return 0.0, 0.0

# --- 3. INTERFACCIA STREAMLIT ---
st.set_page_config(page_title="Sillaro Real-Time Sentinel", layout="wide")
st.title("🌊 Sillaro Real-Time Sentinel")

# Esecuzione recupero dati
livello_att, pioggia_att = fetch_realtime_data()

# --- BLOCCO METRICHE E COMANDI (SOPRA IL GRAFICO) ---
col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

with col1:
    st.metric("Livello Idrometrico CSP", f"{livello_att} m")
with col2:
    st.metric("Pioggia Cumulata 24h", f"{pioggia_att} mm")
with col3:
    st.write(f"**Ultimo Update**")
    st.write(datetime.now().strftime('%H:%M:%S'))
with col4:
    st.write("") # Spazio per allineare il bottone
    if st.button('🔄 AGGIORNA'):
        st.rerun()

st.divider()

# --- 4. PREPARAZIONE E RENDER GRAFICO ---
df_plot = df_storico.copy()
nuovo_punto = pd.DataFrame({
    'Evento': ['SITUAZIONE ATTUALE'], 
    'Pioggia_mm': [pioggia_att], 
    'Livello_m': [livello_att], 
    'Esito': ['ATTUALE']
})
df_combined = pd.concat([df_plot, nuovo_punto], ignore_index=True)

fig = px.scatter(
    df_combined, 
    x="Pioggia_mm", 
    y="Livello_m", 
    text="Evento", 
    color="Esito",
    size=[12, 12, 12, 12, 12, 25], # Attuale più visibile
    color_discrete_map={
        'Allagamento': 'red', 
        'Tenuta': 'green', 
        'ATTUALE': 'black'
    }
)

# Etichette in alto (top center)
fig.update_traces(textposition='top center')

fig.update_layout(
    xaxis_title="Pioggia Cumulata 24h (mm)",
    yaxis_title="Livello Idrometrico Castel San Pietro (m)",
    template="plotly_white",
    height=600,
    legend_title_text='Legenda Esiti'
)

st.plotly_chart(fig, use_container_width=True)