import pandas as pd
import folium
from folium import DivIcon

# 1) Ler e preparar o DataFrame
df = pd.read_csv('BasePromotores.csv', encoding="ISO-8859-1", sep=";")

# Converter colunas de coordenadas para valores numéricos
df['LATITUDE CASA']  = pd.to_numeric(df['LATITUDE CASA'], errors='coerce')
df['LONGITUDE CASA'] = pd.to_numeric(df['LONGITUDE CASA'], errors='coerce')
df['LATITUDE']       = pd.to_numeric(df['LATITUDE'], errors='coerce')
df['LONGITUDE']      = pd.to_numeric(df['LONGITUDE'], errors='coerce')

# Filtrar linhas que possuem PROMOTOR e SUPERVISOR
df = df.dropna(subset=['PROMOTOR', 'SUPERVISOR'])

# 2) Preparar cores distintas (em formato hex)
cores = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#393b79", "#637939", "#8c6d31", "#843c39", "#7b4173",
    "#3182bd", "#31a354", "#756bb1", "#636363", "#e6550d",
    "#969696", "#fec44f", "#bdbdbd"
]
PROMOTORes = df['PROMOTOR'].unique()
cores_PROMOTOR = {PROMOTOR: cores[i % len(cores)] for i, PROMOTOR in enumerate(PROMOTORes)}

# 3) Criar o mapa base
mapa = folium.Map(location=[-3.7424091, -38.4867581], zoom_start=13)

# CSS para ícone da casa piscante
css = """
<style>
@keyframes blink { 0%{opacity:1;} 50%{opacity:0;} 100%{opacity:1;} }
.blinking-home { animation: blink 1s infinite; font-size:24px; }
</style>
"""
mapa.get_root().html.add_child(folium.Element(css))

seller_layers = {}
supervisor_layers = {}

# 4) Construir overlays
for PROMOTOR in PROMOTORes:
    df_p = df[ df['PROMOTOR']==PROMOTOR ]
    df_p = df_p.dropna(subset=['LATITUDE CASA','LONGITUDE CASA','LATITUDE','LONGITUDE'])
    if df_p.empty: continue
    supervisor = df_p.iloc[0]['SUPERVISOR']
    cor = cores_PROMOTOR[PROMOTOR]

    # Overlay do PROMOTOR
    fg = folium.FeatureGroup(name=f"PROMOTOR: {PROMOTOR}", show=False)
    casa = [float(df_p.iloc[0]['LATITUDE CASA']), float(df_p.iloc[0]['LONGITUDE CASA'])]
    folium.Marker(
        location=casa,
        popup=f"Casa do PROMOTOR {PROMOTOR}",
        icon=DivIcon(
            icon_size=(30,30), icon_anchor=(15,15),
            html=f'<div class=\"blinking-home\" style=\"color:{cor};\"><i class=\"fa fa-home\"></i></div>'
        )
    ).add_to(fg)
    rota = [casa]

    # Marcadores de clientes usando DivIcon (círculo clicável)
    for _, row in df_p.iterrows():
        coords = [float(row['LATITUDE']), float(row['LONGITUDE'])]
        html = (
            f'<div style="width:16px;height:16px;border-radius:50%;'
            f'background:{cor};border:2px solid white;box-shadow:0 0 2px #555;">'
            f'</div>'
        )
        folium.Marker(
            location=coords,
            popup=row['CLIENTE'],
            icon=DivIcon(icon_size=(20,20), icon_anchor=(10,10), html=html)
        ).add_to(fg)
        rota.append(coords)

    if len(rota)>1:
        folium.PolyLine(rota, color=cor, weight=4).add_to(fg)

    mapa.add_child(fg)
    seller_layers[PROMOTOR] = fg

    # Overlay do SUPERVISOR
    if supervisor not in supervisor_layers:
        sup_fg = folium.FeatureGroup(name=f"SUPERVISOR: {supervisor}", show=False)
        supervisor_layers[supervisor] = sup_fg
        mapa.add_child(sup_fg)
    sup_fg = supervisor_layers[supervisor]

    # Reutiliza ícones do promotor no supervisor
    folium.Marker(
        location=casa,
        popup=f"Casa do PROMOTOR {PROMOTOR}",
        icon=DivIcon(
            icon_size=(30,30), icon_anchor=(15,15),
            html=f'<div class=\"blinking-home\" style=\"color:{cor};\"><i class=\"fa fa-home\"></i></div>'
        )
    ).add_to(sup_fg)
    for _, row in df_p.iterrows():
        coords = [float(row['LATITUDE']), float(row['LONGITUDE'])]
        folium.Marker(
            location=coords,
            popup=row['CLIENTE'],
            icon=DivIcon(icon_size=(20,20), icon_anchor=(10,10), html=html)
        ).add_to(sup_fg)
    if len(rota)>1:
        folium.PolyLine(rota, color=cor, weight=4).add_to(sup_fg)

# Controle de camadas e salvamento
folium.LayerControl(collapsed=True).add_to(mapa)
mapa.save("mapa_PROMOTORES_SUPERVISORES.html")
print("Mapa salvo!")
