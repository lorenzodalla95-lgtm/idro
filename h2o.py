import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime

# --- 1. DATI STORICI ---
data_storica = {
    'Evento': ['Dicembre 2025', 'Ottobre 2024', 'Settembre 2024', 'Maggio 2023 II', 'Maggio 2023 I'],
    'Livello_m': [1.75, 1.45, 1.82, 2.15, 1.85],
    'Pioggia_mm': [145, 100, 180, 240, 160],
    'Esito': ['Tenuta', 'Allagamento', 'Allagamento', 'Allagamento', 'Allagamento']
}
df_storico = pd.DataFrame(data_storica)

# --- 2. RECUPERO DATI REALI ---
def fetch_realtime_data():
    idro_url = "https://simc.arpae.it/meteozen/rt_data/lastdata/-/1158841,4438103/simnbo/254,0,0/1,-,-,-/B13215"
    meteo_url = "https://api.open-meteo.com/v1/forecast?latitude=44.39&longitude=11.58&hourly=precipitation&past_days=1"
    
    res_idro = requests.get(idro_url, timeout=10)
    res_idro.raise_for_status() 
    livello = float(res_idro.json()['value'])
    
    res_meteo = requests.get(meteo_url, timeout=10)
    res_meteo.raise_for_status()
    pioggia = round(sum(res_meteo.json()['hourly']['precipitation'][:24]), 1)
    
    return livello, pioggia

# --- 3. CONFIGURAZIONE UI ---
st.set_page_config(page_title="Sillaro Sentinel Mobile", layout="wide")
colors = {"VERDE": "#2ecc71", "GIALLO": "#f1c40f", "ROSSO": "#e74c3c", "BLU": "#3498db", "GRIGIO": "#34495e"}

st.markdown(f"""<style>.main {{ background-color: #ffffff; }} div.stButton > button {{ border-radius: 12px; border: 2px solid #ecf0f1; font-weight: bold; height: 3.5em; }}</style>""", unsafe_allow_html=True)

try:
    livello_att, pioggia_att = fetch_realtime_data()
except Exception as e:
    st.error(f"### ❌ DATI NON DISPONIBILI\n`Errore: {e}`")
    if st.button("🔄 RIPROVA CONNESSIONE"): st.rerun()
    st.stop() 

# --- 4. HEADER ---
if livello_att > 1.75: status, color_main, icon = "ALLERTA ROSSA", colors["ROSSO"], "🚨"
elif livello_att >= 1.45: status, color_main, icon = "ALLERTA GIALLA", colors["GIALLO"], "⚠️"
else: status, color_main, icon = "SITUAZIONE ORDINARIA", colors["VERDE"], "✅"

st.markdown(f"""<div style="background-color:{color_main}; padding:20px; border-radius:15px; text-align:center; margin-bottom:20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"><h1 style="color:white; margin:0; font-family:sans-serif; font-size: 26px;">{icon} {status}</h1><p style="color:white; margin:5px 0 0 0; font-size: 18px;"><b>{livello_att}m</b> attuale | <b>{pioggia_att}mm</b> pioggia</p></div>""", unsafe_allow_html=True)

# --- 5. TACHIMETRI ---
c1, c2 = st.columns(2)
def create_gauge(value, title, max_val, suffix, bar_color, steps):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        number={'suffix': suffix, 'font': {'size': 50, 'color': colors['GRIGIO']}, 'valueformat': '.2f'},
        title={'text': title, 'font': {'size': 20, 'color': colors['GRIGIO'], 'weight': 'bold'}},
        gauge={'axis': {'range': [0, max_val], 'tickwidth': 2}, 'bar': {'color': bar_color, 'thickness': 0.6}, 'bgcolor': "#f8f9fa", 'steps': steps}
    ))
    fig.update_layout(height=280, margin=dict(l=50, r=50, t=60, b=20), paper_bgcolor='rgba(0,0,0,0)')
    return fig

with c1:
    st.plotly_chart(create_gauge(livello_att, "LIVELLO FIUME", 2.5, "m", colors['GRIGIO'], [{'range': [0, 1.45], 'color': colors["VERDE"]}, {'range': [1.45, 1.75], 'color': colors["GIALLO"]}, {'range': [1.75, 2.5], 'color': colors["ROSSO"]}]), use_container_width=True)
with c2:
    st.plotly_chart(create_gauge(pioggia_att, "PRECIPITAZIONI", 300, "mm", colors['BLU'], [{'range': [0, 100], 'color': '#d6eaf8'}, {'range': [100, 300], 'color': colors["BLU"]}]), use_container_width=True)

st.divider()

# --- 6. GRAFICO STORICO (CORRETTO) ---
st.markdown(f"<h4 style='color:{colors['GRIGIO']};'>📊 Analisi Comparativa</h4>", unsafe_allow_html=True)

labels = ['<b>LIVE</b>'] + df_storico['Evento'].tolist()
livelli = [livello_att] + df_storico['Livello_m'].tolist()
piogge = [pioggia_att] + df_storico['Pioggia_mm'].tolist()
colors_bar = [color_main] + [colors['ROSSO'] if x == 'Allagamento' else colors['VERDE'] for x in df_storico['Esito']]

fig_hist = go.Figure()
fig_hist.add_trace(go.Bar(y=labels, x=livelli, orientation='h', marker_color=colors_bar, text=[f"<b>{v}m</b>" for v in livelli], textposition='outside', width=0.6))
fig_hist.add_trace(go.Scatter(y=labels, x=piogge, mode='markers', xaxis='x2', marker=dict(symbol='circle', size=12, color=colors['BLU'], line=dict(width=1, color='white')), hovertemplate='%{x} mm'))

fig_hist.update_layout(
    margin=dict(l=10, r=60, t=60, b=40), height=450,
    plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(
        title={'text': "Livello Idrometrico (m)", 'font': {'color': colors['GRIGIO']}},
        range=[0, 2.6], showgrid=True, gridcolor='#f0f0f0', showline=True, linecolor=colors['GRIGIO']
    ),
    xaxis2=dict(
        title={'text': "Pioggia Cumulata (mm)", 'font': {'color': colors['BLU']}},
        range=[0, 350], overlaying='x', side='top', showgrid=False, showline=True, linecolor=colors['BLU'],
        tickfont=dict(color=colors['BLU'])
    ),
    yaxis=dict(autorange="reversed", showgrid=False, showline=True, linecolor=colors['GRIGIO'], tickfont=dict(size=12, color=colors['GRIGIO'])),
    showlegend=False
)

st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})

if st.button('🔄 AGGIORNA TUTTO'): st.rerun()
