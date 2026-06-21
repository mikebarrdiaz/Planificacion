import dash
from dash import html, dcc, Input, Output, State, ctx
from tabs import tab_cronograma, tab_equipo, tab_vacaciones, tab_asignaciones, tab_carga, tab_et, tab_login
import webbrowser
import pandas as pd
from threading import Timer

# Inicialización
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "Consola Operativa Government"

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

ESTILO_PESTANA_MODERNA = {
    'height': '88px',
    'display': 'flex',
    'alignItems': 'center',
    'justifyContent': 'center', 
    'minWidth': '180px',
    'color': '#FFFFFF',
    'backgroundColor': 'transparent',
    'border': 'none',
    'borderBottom': '4px solid transparent',
    'fontFamily': "'Outfit', sans-serif",
    'fontSize': '12px',
    'fontWeight': 'bold',
    'textTransform': 'uppercase',
    'cursor': 'pointer'
}

ESTILO_PESTANA_ACTIVA = {
    **ESTILO_PESTANA_MODERNA,
    'borderBottom': '4px solid #FFFFFF'
}

# --- LAYOUT PRINCIPAL BLINDADO ---
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    
    # 🔒 MEMORIA DE SESIÓN INVISIBLE (Se borra al cerrar el navegador)
    dcc.Store(id='sesion-usuario', storage_type='session'),

    # --- NAVBAR REESTRUCTURADO (Oculto por defecto hasta loguearse) ---
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
                dcc.Tab(label='Ausencias', value='tab-vacaciones', style=ESTILO_PESTANA_MODERNA, selected_style=ESTILO_PESTANA_ACTIVA),
                dcc.Tab(label='Equipo', value='tab-equipo', style=ESTILO_PESTANA_MODERNA, selected_style=ESTILO_PESTANA_ACTIVA),
            ]
        )
    ], id='navbar-header', style={'display': 'none'}), # <- Controlado por el callback

    html.Div([
        html.H2("Planificación y Control Operativo - Government", id='titulo-cabecera', style={'display': 'none'}),
        html.Div(id='contenido-pestanas')
    ], className='cuerpo-operativo') 
], style={'backgroundColor': '#FFFFFF', 'minHeight': '100vh'})

# --- CALLBACK MAESTRO DE ENRUTAMIENTO Y SEGURIDAD ---
@app.callback(
    [Output('url', 'pathname'), 
     Output('tabs-aplicacion', 'value'), 
     Output('contenido-pestanas', 'children'),
     Output('navbar-header', 'style'),
     Output('titulo-cabecera', 'style')],
    [Input('url', 'pathname'), 
     Input('tabs-aplicacion', 'value')],
    [State('sesion-usuario', 'data')] # Leemos el token de seguridad
)
def enrutador_maestro(pathname, tab_value, datos_sesion):
    trigger = ctx.triggered_id

    # 1. VERIFICACIÓN DE CREDENCIALES
    autenticado = False
    rol_usuario = 'lector' # Rol por defecto de máxima seguridad
    
    if datos_sesion and datos_sesion.get('autenticado'):
        autenticado = True
        rol_usuario = datos_sesion.get('rol', 'lector')

    # Estilos de visibilidad
    estilo_nav_visible = {'backgroundColor': '#FF4E00', 'display': 'flex', 'alignItems': 'center', 'padding': '0 32px', 'height': '88px', 'boxShadow': '0 4px 16px rgba(0,0,0,0.06)'}
    estilo_nav_oculto = {'display': 'none'}
    estilo_tit_visible = {'color': '#474751', 'fontFamily': "'Outfit', sans-serif", 'fontSize': '28px', 'marginBottom': '40px', 'fontWeight': 'bold'}
    estilo_tit_oculto = {'display': 'none'}

    # Si NO está autenticado, bloqueamos la app y mostramos el Login
    if not autenticado:
        return '/login', dash.no_update, tab_login.layout(), estilo_nav_oculto, estilo_tit_oculto

    # 2. ENRUTAMIENTO DE LA APLICACIÓN AUTENTICADA
    def cargar_layout(tab_id, rol):
        try:
            if tab_id == 'tab-cronograma': return tab_cronograma.layout()
            # Pasamos el ROL a las pestañas que requieran esconder botones de edición
            if tab_id == 'tab-equipo': return tab_equipo.layout(rol=rol) 
            if tab_id == 'tab-vacaciones': return tab_vacaciones.layout(rol=rol)
            if tab_id == 'tab-asignaciones': return tab_asignaciones.layout(rol=rol) 
            if tab_id == 'tab-carga': return tab_carga.layout()
            if tab_id == 'tab-et': return tab_et.layout()
        except Exception as e:
            return html.Div(f"Error cargando módulo: {str(e)}", style={'color': '#DB563A', 'padding': '40px'})
        return html.Div("Módulo no encontrado.")

    if trigger == 'url' or not trigger:
        # Si intenta ir a /login pero ya está logueado, lo redirigimos al inicio
        if pathname == '/login':
            nuevo_tab = 'tab-et'
            return '/', nuevo_tab, cargar_layout(nuevo_tab, rol_usuario), estilo_nav_visible, estilo_tit_visible
            
        nuevo_tab = MAPA_URLS.get(pathname, 'tab-et')
        return dash.no_update, nuevo_tab, cargar_layout(nuevo_tab, rol_usuario), estilo_nav_visible, estilo_tit_visible
    else:
        nueva_url = MAPA_PESTANAS.get(tab_value, '/matriz-et')
        return nueva_url, dash.no_update, cargar_layout(tab_value, rol_usuario), estilo_nav_visible, estilo_tit_visible

# Registros (Importante añadir tab_login)
for tab in [tab_login, tab_cronograma, tab_equipo, tab_vacaciones, tab_asignaciones, tab_carga, tab_et]:
    tab.register_callbacks(app)

if __name__ == '__main__':
    # Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:8050/")).start()
    app.run(debug=True)