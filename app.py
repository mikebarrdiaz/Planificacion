import dash
from dash import html, dcc, Input, Output, ctx
from tabs import tab_cronograma, tab_equipo, tab_vacaciones, tab_asignaciones, tab_carga, tab_et
import webbrowser
from threading import Timer

# Inicialización
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "Consola Operativa Bidding"

# --- MAPEO DE RUTAS ---
MAPA_URLS = {
    '/': 'tab-et',
    '/matriz-et': 'tab-et',
    '/carga': 'tab-carga',
    '/cronograma': 'tab-cronograma',
    '/asignaciones': 'tab-asignaciones',
    '/equipo': 'tab-equipo',
    '/vacaciones': 'tab-vacaciones'
}
MAPA_PESTANAS = {v: k for k, v in MAPA_URLS.items() if k != '/'}
# Definimos un estilo base uniforme para las pestañas
# Definimos el estilo base con tu ancho deseado
ESTILO_PESTANA_MODERNA = {
    'height': '88px',
    'display': 'flex',
    'alignItems': 'center',
    'justifyContent': 'center', 
    'minWidth': '180px',        # Aumentado para mayor presencia
    'color': '#FFFFFF',
    'backgroundColor': 'transparent',
    'border': 'none',
    'borderBottom': '4px solid transparent', # Base transparente
    'fontFamily': "'Outfit', sans-serif",
    'fontSize': '12px',
    'fontWeight': 'bold',
    'textTransform': 'uppercase',
    'cursor': 'pointer'
}

# Definimos el estilo activo manteniendo la barrita blanca
ESTILO_PESTANA_ACTIVA = {
    **ESTILO_PESTANA_MODERNA, # Hereda todo lo anterior
    'borderBottom': '4px solid #FFFFFF' # AQUÍ MANTENEMOS TU BARRITA BLANCA
}
# --- LAYOUT PRINCIPAL ---
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),

    # --- NAVBAR REESTRUCTURADO ---
    html.Header([
        html.Img(src='/assets/logo.svg', style={'height': '36px', 'flexShrink': '0'}, width=160),
        dcc.Tabs(
            id="tabs-aplicacion", 
            value='tab-et',
            parent_style={'display': 'flex', 'alignItems': 'center', 'height': '100%', 'marginLeft': '100px', 'width': 'auto'},
            style={'height': '100%', 'borderBottom': 'none', 'display': 'flex'},
            children=[
                dcc.Tab(label='ET', value='tab-et', style=ESTILO_PESTANA_MODERNA, selected_style=ESTILO_PESTANA_ACTIVA),
                dcc.Tab(label='Cronograma', value='tab-cronograma', style=ESTILO_PESTANA_MODERNA, selected_style=ESTILO_PESTANA_ACTIVA),
                dcc.Tab(label='Carga de Trabajo', value='tab-carga', style=ESTILO_PESTANA_MODERNA, selected_style=ESTILO_PESTANA_ACTIVA),
                dcc.Tab(label='Activación licitaciones', value='tab-asignaciones', style=ESTILO_PESTANA_MODERNA, selected_style=ESTILO_PESTANA_ACTIVA),
                dcc.Tab(label='Vacaciones', value='tab-vacaciones', style=ESTILO_PESTANA_MODERNA, selected_style=ESTILO_PESTANA_ACTIVA),
                dcc.Tab(label='Equipo', value='tab-equipo', style=ESTILO_PESTANA_MODERNA, selected_style=ESTILO_PESTANA_ACTIVA),
                
            ]
        )
    ], style={'backgroundColor': '#FF4E00', 'display': 'flex', 'alignItems': 'center', 'padding': '0 32px', 'height': '88px', 'boxShadow': '0 4px 16px rgba(0,0,0,0.06)'}),

    html.Div([
        html.H2("Consola de Planificación y Control Operativo - Bidding", style={'color': '#474751', 'fontFamily': "'Outfit', sans-serif", 'fontSize': '24px', 'marginBottom': '40px', 'fontWeight': 'bold'}),
        html.Div(id='contenido-pestanas')
    ], className='cuerpo-operativo') 
], style={'backgroundColor': '#FFFFFF', 'minHeight': '100vh'})

# --- CALLBACK MAESTRO ---
@app.callback(
    [Output('url', 'pathname'), Output('tabs-aplicacion', 'value'), Output('contenido-pestanas', 'children')],
    [Input('url', 'pathname'), Input('tabs-aplicacion', 'value')]
)
def enrutador_maestro(pathname, tab_value):
    trigger = ctx.triggered_id

    def cargar_layout(tab_id):
        try:
            if tab_id == 'tab-cronograma': return tab_cronograma.layout()
            if tab_id == 'tab-equipo': return tab_equipo.layout()
            if tab_id == 'tab-vacaciones': return tab_vacaciones.layout()
            if tab_id == 'tab-asignaciones': return tab_asignaciones.layout()
            if tab_id == 'tab-carga': return tab_carga.layout()
            if tab_id == 'tab-et': return tab_et.layout()
        except Exception as e:
            return html.Div(f"Error cargando módulo: {str(e)}", style={'color': '#DB563A', 'padding': '40px'})
        return html.Div("Módulo no encontrado.")

    if trigger == 'url' or not trigger:
        nuevo_tab = MAPA_URLS.get(pathname, 'tab-et')
        return dash.no_update, nuevo_tab, cargar_layout(nuevo_tab)
    else:
        nueva_url = MAPA_PESTANAS.get(tab_value, '/matriz-et')
        return nueva_url, dash.no_update, cargar_layout(tab_value)

# Registros (Se mantienen igual)
for tab in [tab_cronograma, tab_equipo, tab_vacaciones, tab_asignaciones, tab_carga, tab_et]:
    tab.register_callbacks(app)

if __name__ == '__main__':
    #Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:8050/")).start()
    app.run(debug=True)