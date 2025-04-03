import pandas as pd
import folium
from folium import DivIcon

# 1) Ler e preparar o DataFrame
df = pd.read_csv('dbPromotores.csv', encoding="ISO-8859-1", sep=";")

# Converter colunas de coordenadas para valores numéricos
df['LATITUDE CASA']  = pd.to_numeric(df['LATITUDE CASA'], errors='coerce')
df['LONGITUDE CASA'] = pd.to_numeric(df['LONGITUDE CASA'], errors='coerce')
df['LATITUDE']       = pd.to_numeric(df['LATITUDE'], errors='coerce')
df['LONGITUDE']      = pd.to_numeric(df['LONGITUDE'], errors='coerce')

# Filtrar linhas que possuem PROMOTOR e SUPERVISOR
df = df.dropna(subset=['PROMOTOR', 'SUPERVISOR'])

# 2) Preparar 23 cores distintas (em formato hex)
cores = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#393b79", "#637939", "#8c6d31", "#843c39", "#7b4173",
    "#3182bd", "#31a354", "#756bb1", "#636363", "#e6550d",
    "#969696", "#fec44f", "#bdbdbd"
]
PROMOTORes = df['PROMOTOR'].unique()
cores_PROMOTOR = {PROMOTOR: cores[i % len(cores)] for i, PROMOTOR in enumerate(PROMOTORes)}

# 3) Criar o mapa base (centralizado em uma localização de referência)
mapa = folium.Map(location=[-3.7424091, -38.4867581], zoom_start=13)

# Adicionar CSS para a animação do ícone piscante
css = """
<style>
@keyframes blink {
    0% { opacity: 1; }
    50% { opacity: 0; }
    100% { opacity: 1; }
}
.blinking-home {
    animation: blink 1s infinite;
    font-size: 24px;
}
</style>
"""
mapa.get_root().html.add_child(folium.Element(css))

# Dicionários para armazenar os overlays
seller_layers = {}       # Overlay individual para cada PROMOTOR
supervisor_layers = {}   # Overlay agrupado por SUPERVISOR

# 4) Construir overlays para cada PROMOTOR e agrupar por SUPERVISOR
for PROMOTOR in PROMOTORes:
    # Selecionar registros válidos para este PROMOTOR
    df_PROMOTOR = df[
        (df['PROMOTOR'] == PROMOTOR) &
        (df['LATITUDE CASA'].notna()) &
        (df['LONGITUDE CASA'].notna()) &
        (df['LATITUDE'].notna()) &
        (df['LONGITUDE'].notna())
    ]
    
    if df_PROMOTOR.empty:
        continue  # Pula se não houver dados válidos
    
    # Considera que todas as linhas deste PROMOTOR possuem o mesmo supervisor
    supervisor = df_PROMOTOR.iloc[0]['SUPERVISOR']
    cor = cores_PROMOTOR[PROMOTOR]
    
    # --- Overlay do PROMOTOR ---
    fg_PROMOTOR = folium.FeatureGroup(name=f"PROMOTOR: {PROMOTOR}", show=False)
    
    # Converter explicitamente as coordenadas para float
    casa_lat = float(df_PROMOTOR.iloc[0]['LATITUDE CASA'])
    casa_lon = float(df_PROMOTOR.iloc[0]['LONGITUDE CASA'])
    casa_coords = [casa_lat, casa_lon]
    
    # Ícone da casa com efeito piscante usando DivIcon e o ícone "home" do Font Awesome
    folium.Marker(
        location=casa_coords,
        popup=f"Casa do PROMOTOR {PROMOTOR}",
        icon=DivIcon(
            icon_size=(30, 30),
            icon_anchor=(15, 15),
            html=f'<div class="blinking-home" style="color:{cor};"><i class="fa fa-home"></i></div>'
        )
    ).add_to(fg_PROMOTOR)
    
    # Inicializa a rota com a casa do PROMOTOR
    rota = [casa_coords]
    
    # Adicionar marcadores para os clientes usando CircleMarker (para aceitar as cores em hex)
    for idx, row in df_PROMOTOR.iterrows():
        cliente_coords = [float(row['LATITUDE']), float(row['LONGITUDE'])]
        folium.CircleMarker(
            location=cliente_coords,
            radius=6,
            color=cor,
            fill=True,
            fill_color=cor,
            fill_opacity=1,
            popup=row['CLIENTE']
        ).add_to(fg_PROMOTOR)
        rota.append(cliente_coords)
    
    # Exibe no console o promotor e sua rota (para depuração)
    print(PROMOTOR, rota)
    
    # Desenhar a rota se houver pelo menos dois pontos, utilizando a mesma cor
    if len(rota) > 1:
        folium.PolyLine(rota, color=cor, weight=5).add_to(fg_PROMOTOR)
    
    seller_layers[PROMOTOR] = fg_PROMOTOR
    mapa.add_child(fg_PROMOTOR)
    
    # --- Overlay do SUPERVISOR ---
    if supervisor not in supervisor_layers:
        fg_supervisor = folium.FeatureGroup(name=f"SUPERVISOR: {supervisor}", show=False)
        supervisor_layers[supervisor] = fg_supervisor
        mapa.add_child(fg_supervisor)
    else:
        fg_supervisor = supervisor_layers[supervisor]
    
    # Adicionar os mesmos elementos deste PROMOTOR ao overlay do supervisor, com a mesma cor
    folium.Marker(
        location=casa_coords,
        popup=f"Casa do PROMOTOR {PROMOTOR}",
        icon=DivIcon(
            icon_size=(30, 30),
            icon_anchor=(15, 15),
            html=f'<div class="blinking-home" style="color:{cor};"><i class="fa fa-home"></i></div>'
        )
    ).add_to(fg_supervisor)
    
    for idx, row in df_PROMOTOR.iterrows():
        cliente_coords = [float(row['LATITUDE']), float(row['LONGITUDE'])]
        folium.CircleMarker(
            location=cliente_coords,
            radius=6,
            color=cor,
            fill=True,
            fill_color=cor,
            fill_opacity=1,
            popup=row['CLIENTE']
        ).add_to(fg_supervisor)
    
    if len(rota) > 1:
        folium.PolyLine(rota, color=cor, weight=5).add_to(fg_supervisor)

# 5) Adicionar o controle de camadas (inicialmente fechado)
folium.LayerControl(collapsed=True).add_to(mapa)

# 6) Salvar o mapa em HTML
mapa.save("mapa_PROMOTORES_SUPERVISORES.html")
print("Mapa salvo!")
