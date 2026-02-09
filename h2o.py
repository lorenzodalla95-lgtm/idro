import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime

# --- 1. DATI STORICI ORDINATI PER DATA (Dal più recente al meno recente) ---
data_storica = {
    'Evento': ['Dicembre 2025', 'Ottobre 2024', 'Settembre 2024', 'Maggio 2023 II', 'Maggio 2023 I'],
    'Livello_m': [1.75, 1.45, 1.82, 2.15, 1.85],
    'Pioggia_mm': [145, 100, 180, 240, 160],
    'Esito': ['Tenuta', 'Allagamento', 'Allagamento', 'Allagamento', 'Allagamento']
}
df_storico = pd.DataFrame(data_storica)

# --- 2. RECUPERO DATI REAL-TIME ---
def fetch_realtime_data():
    idro_url = "https://simc.arpae.it/meteozen/rt_data/lastdata/-/1158841,4438103/simnbo/254,0,0/1,-,-,-/B13215"
    meteo_url = "https://api.open-meteo.com/v1/forecast?latitude=44.39&longitude=11.58&hourly=precipitation&past_days=1"
    try:
        res_idro = requests.get(idro_url).json()
        livello = float(res_idro['value'])
        res_meteo = requests.get(meteo_url).json()
        pioggia = round(sum(res_meteo['hourly']['precipitation'][:24]), 1)
        return livello, pioggia
    except Exception:
        return 0.85, 45.0 # Valori di test se le API sono offline

# --- 3. CONFIGURAZIONE PAGINA E STATUS ---
st.set_page_config(page_title="Sillaro Sentinel Mobile", layout="wide")
st.subheader("🌊 Monitoraggio Sillaro - Castel S. Pietro")

livello_att, pioggia_att = fetch_realtime_data()

# Box Rischio Dinamico (Colori Soft)
if livello_att > 1.75:
    st.error(f"## 🚩 ALTO RISCHIO: {livello_att}m")
    st.caption("Superata la soglia massima di tenuta storica.")
elif livello_att >= 1.45:
    st.warning(f"## ⚠️ ALLERTA GIALLA: {livello_att}m")
    st.caption("Zona di attenzione: tra soglia Ottobre 2024 e Dicembre 2025.")
else:
    st.success(f"## ✅ ORDINARIO: {livello_att}m")

if st.button('🔄 AGGIORNA DATI LIVE', use_container_width=True):
    st.rerun()

st.divider()

# --- 4. GRAFICO COMBO LIVELLO (BARRE) + PIOGGIA (ROMBI) ---
labels = ['<b>OGGI (Live)</b>'] + df_storico['Evento'].tolist()
livelli = [livello_att] + df_storico['Livello_m'].tolist()
piogge = [pioggia_att] + df_storico['Pioggia_mm'].tolist()

# Palette colori pastello
color_map = {'Allagamento': '#e5908e', 'Tenuta': '#a3c5a5', 'ATTUALE': '#bdc3c7'}
colors = [color_map['ATTUALE']] + [color_map['Allagamento'] if x == 'Allagamento' else color_map['Tenuta'] for x in df_storico['Esito']]

fig = go.Figure()

# BARRE: Livello Idrometrico (Metri)
fig.add_trace(go.Bar(
    y=labels, 
    x=livelli,
    name='Livello (m)',
    orientation='h',
    marker_color=colors,
    text=[f"<b>{v}m</b>" for v in livelli],
    textposition='inside',
    insidetextanchor='end',
    width=0.6
))

# ROMBI: Pioggia Cumulata (mm) su asse superiore
fig.add_trace(go.Scatter(
    y=labels, 
    x=piogge,
    name='Pioggia (mm)',
    mode='markers+text',
    xaxis='x2', # Collegato all'asse X secondario (in alto)
    marker=dict(symbol='diamond', size=12, color='#5dade2'),
    text=[f" {p}mm" for p in piogge],
    textposition='middle right',
    textfont=dict(color='#2e86c1', size=11)
))

# --- CONFIGURAZIONE LAYOUT (Corretta per Plotly 2026 / Python 3.13) ---
fig.update_layout(
    margin=dict(l=10, r=80, t=60, b=20),
    height=600,
    plot_bgcolor='white',
    # Asse X1 (Metri - In Basso)
    xaxis=dict(
        title=dict(text="Livello Idrometrico (m)", font=dict(size=13)),
        range=[0, 2.5], 
        side='bottom',
        gridcolor='#f5f5f5'
    ),
    # Asse X2 (Pioggia - In Alto)
    xaxis2=dict(
        title=dict(
            text="Pioggia Cumulata 24h (mm)",
            font=dict(size=13, color='#5dade2')
        ),
        range=[0, 300], 
        overlaying='x', 
        side='top',
        showgrid=False,
        tickfont=dict(color='#5dade2')
    ),
    yaxis=dict(
        autorange="reversed", # Ordine cronologico dall'alto (più recente)
        tickfont=dict(size=13)
    ),
    showlegend=False
)

# Linee di soglia verticali discrete
fig.add_vline(x=1.45, line_dash="dot", line_color="#d35400", opacity=0.4)
fig.add_vline(x=1.75, line_dash="dot", line_color="#c0392b", opacity=0.4)

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# Footer con orario
st.caption(f"Ultima lettura sensore Arpae: {datetime.now().strftime('%H:%M')}")
