import dash
from dash import html, dcc, Input, Output, ctx
from tabs import tab_cronograma, tab_equipo, tab_vacaciones, tab_asignaciones, tab_carga, tab_et
import pandas as pd
import datetime

# Inicialización de la aplicación
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "Consola Operativa Bidding"

# --- CONFIGURACIÓN DE ESTILOS GEOMÉTRICOS Y NAVEGACIÓN SERVEO ---
ESTILO_NAVBAR = {
    'backgroundColor': '#FF4E00',  # Naranja Corporativo SERVEO
    'display': 'flex',
    'alignItems': 'center',
    'padding': '0 32px',
    'height': '88px',              # Altura premium uniforme
    'width': '100%',               # Cobertura completa de borde a borde
    'boxSizing': 'border-box',
    'boxShadow': '0 4px 16px rgba(0,0,0,0.06)',
    'margin': '0',
    'position': 'relative',
    'zIndex': '1000'
}

ESTILO_LOGO = {
    'height': '36px',
    'display': 'block',
    'flexShrink': '0'              # Evita que el logo se deforme en pantallas pequeñas
}

ESTILO_PESTANAS = {
    'padding': '0 24px',
    'height': '88px',              # Emparejado estricto con la barra superior
    'display': 'flex',
    'alignItems': 'center',
    'color': '#FFFFFF',
    'backgroundColor': 'transparent',
    'border': 'none',
    'borderBottom': '4px solid transparent', # Evita saltos de layout al cambiar de pestaña
    'fontFamily': "'Outfit', sans-serif",
    'fontSize': '12px',
    'fontWeight': 'bold',
    'textTransform': 'uppercase',
    'cursor': 'pointer',
    'transition': 'all 0.2s ease'
}

ESTILO_PESTANA_ACTIVA = {
    'padding': '0 24px',
    'height': '88px',
    'display': 'flex',
    'alignItems': 'center',
    'color': '#FFFFFF',
    'backgroundColor': 'transparent',
    'border': 'none',
    'borderBottom': '4px solid #FFFFFF', # Barrita blanca minimalista debajo
    'fontFamily': "'Outfit', sans-serif",
    'fontSize': '12px',
    'fontWeight': 'bold',
    'textTransform': 'uppercase',
    'cursor': 'pointer'
}

# --- MAPEO DE URLS A PESTAÑAS ---
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


# --- LAYOUT PRINCIPAL REESTRUCTURADO ---
app.layout = html.Div([

    # Motor de enrutamiento invisible
    dcc.Location(id='url', refresh=False),

    # --- BARRA SUPERIOR INFINITA (NAVBAR) ---
    html.Header([
        # Logotipo corporativo
        html.Img(src='/assets/logo.svg', style=ESTILO_LOGO, width= 160),
        
        # dcc.Tabs extendido y corregido
        dcc.Tabs(
            id="tabs-aplicacion", 
            value='tab-et', # Valor inicial por defecto
            parent_style={
                'display': 'flex', 
                'alignItems': 'center', 
                'height': '100%', 
                'marginLeft': '48px', 
                'width': 'auto'
            },
            style={
                'height': '100%', 
                'borderBottom': 'none', 
                'display': 'flex'
            },
            children=[
                dcc.Tab(label='Matriz ET', value='tab-et', style=ESTILO_PESTANAS, selected_style=ESTILO_PESTANA_ACTIVA),
                dcc.Tab(label='Visualización de Carga', value='tab-carga', style=ESTILO_PESTANAS, selected_style=ESTILO_PESTANA_ACTIVA),
                dcc.Tab(label='Cronograma de Proyectos', value='tab-cronograma', style=ESTILO_PESTANAS, selected_style=ESTILO_PESTANA_ACTIVA),
                dcc.Tab(label='Asignación de Recursos', value='tab-asignaciones', style=ESTILO_PESTANAS, selected_style=ESTILO_PESTANA_ACTIVA),
                dcc.Tab(label='Directorio del Equipo', value='tab-equipo', style=ESTILO_PESTANAS, selected_style=ESTILO_PESTANA_ACTIVA),
                dcc.Tab(label='Calendario Vacacional', value='tab-vacaciones', style=ESTILO_PESTANAS, selected_style=ESTILO_PESTANA_ACTIVA),
            ]
        )
    ], style=ESTILO_NAVBAR),
    
    # --- CUERPO OPERATIVO CON CLASE CSS ---
    html.Div([
        html.H2(
            "Consola de Planificación y Control Operativo", 
            style={
                'color': '#474751', 
                'fontFamily': "'Outfit', sans-serif", 
                'fontSize': '24px', 
                'marginBottom': '40px',
                'fontWeight': 'bold'
            }
        ),
        html.Div(id='contenido-pestanas')
    ], className='cuerpo-operativo') 
    
], style={'backgroundColor': '#FFFFFF', 'minHeight': '100vh', 'margin': '0', 'padding': '0', 'width': '100%', 'boxSizing': 'border-box'})


# --- SÚPER-CALLBACK DE ENRUTAMIENTO (Fix para la Dependencia Circular) ---
@app.callback(
    [Output('url', 'pathname'),
     Output('tabs-aplicacion', 'value'),
     Output('contenido-pestanas', 'children')],
    [Input('url', 'pathname'),
     Input('tabs-aplicacion', 'value')]
)
def enrutador_maestro(pathname, tab_value):
    trigger = ctx.triggered_id

    # Función interna que extrae el layout correcto
    def obtener_contenido(tab_activa):
        if tab_activa == 'tab-cronograma': return tab_cronograma.layout()
        elif tab_activa == 'tab-equipo': return tab_equipo.layout()
        elif tab_activa == 'tab-vacaciones': return tab_vacaciones.layout()
        elif tab_activa == 'tab-asignaciones': return tab_asignaciones.layout()
        elif tab_activa == 'tab-carga': return tab_carga.layout()
        elif tab_activa == 'tab-et': return tab_et.layout()
        return html.Div("Módulo no encontrado.", style={'padding': '40px', 'color': '#DB563A', 'fontFamily': "'Outfit', sans-serif"})

    # 1. Si el usuario carga la página web directa, recarga (F5) o cambia el texto de la URL
    if trigger == 'url' or not trigger:
        nuevo_tab = MAPA_URLS.get(pathname, 'tab-et')
        return dash.no_update, nuevo_tab, obtener_contenido(nuevo_tab)
        
    # 2. Si el usuario hace clic físicamente en una pestaña (Dibuja la vista y actualiza la URL en silencio)
    elif trigger == 'tabs-aplicacion':
        nueva_url = MAPA_PESTANAS.get(tab_value, '/matriz-et')
        return nueva_url, dash.no_update, obtener_contenido(tab_value)


# Registro de los componentes reactivos
tab_cronograma.register_callbacks(app)
tab_equipo.register_callbacks(app)
tab_asignaciones.register_callbacks(app)
tab_carga.register_callbacks(app)
tab_vacaciones.register_callbacks(app)
tab_et.register_callbacks(app)


import webbrowser
from threading import Timer

def abrir_navegador():
    webbrowser.open_new("http://127.0.0.1:8050/")

if __name__ == '__main__':
    # Apagamos el debug y lanzamos un temporizador para abrir el navegador en 1.5 segundos
    Timer(1.5, abrir_navegador).start()
    app.run(debug=False)