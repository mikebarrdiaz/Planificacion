from dash import html, dcc, Input, Output, State, ctx
import dash

# --- DICCIONARIO DE SEGURIDAD (Puedes pasarlo a BBDD en el futuro) ---
USUARIOS_AUTORIZADOS = {
    'admin': {'pass': 'admin123', 'rol': 'editor'},      # Acceso total
    'oficina': {'pass': 'serveo2026', 'rol': 'lector'}   # Solo ver
}

def layout():
    return html.Div([
        # Contenedor del Overlay oscuro para que el formulario resalte sobre el fondo
        html.Div([
            html.Div([
                # Logo / Cabecera
                html.Img(src='/assets/logo2.png', style={'height': '80px', 'display': 'block', 'margin': '0 auto', 'marginBottom': '8px'}),
                html.Div("Plataforma de Planificación Operativa", style={'color': '#474751', 'fontSize': '12px', 'textAlign': 'center', 'marginBottom': '32px', 'fontWeight': 'bold', 'textTransform': 'uppercase'}),

                # Formulario
                html.Div([
                    html.Label("Usuario", className="etiqueta-dato"),
                    # boxSizing asegura que los inputs no se salgan de la caja blanca
                    dcc.Input(id='login-usuario', type='text', placeholder='Usuario', className="input-filtro", style={'width': '100%', 'boxSizing': 'border-box'})
                ], style={'marginBottom': '16px'}),

                html.Div([
                    html.Label("Contraseña de Acceso", className="etiqueta-dato"),
                    dcc.Input(id='login-password', type='password', placeholder='Contraseña', className="input-filtro", style={'width': '100%', 'boxSizing': 'border-box'})
                ], style={'marginBottom': '32px'}),

                html.Button('Accede', id='btn-login', n_clicks=0, className="btn-serveo-primario", style={'width': '100%', 'height': '40px', 'fontSize': '14px', 'boxSizing': 'border-box'}),

                html.Div(id='login-mensaje', style={'color': 'var(--semantic-negative)', 'marginTop': '16px', 'fontSize': '12px', 'textAlign': 'center', 'fontWeight': 'bold', 'fontFamily': 'Outfit'})

            ], style={
                'backgroundColor': '#FFFFFF', 'padding': '48px 40px', 'borderRadius': '12px', 
                'boxShadow': '0 24px 64px rgba(0, 0, 0, 0.4)', 'width': '380px',
                'borderTop': '4px solid #FF4E00', 'boxSizing': 'border-box'
            })
        ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'height': '100%', 'width': '100%', 'backgroundColor': 'rgba(0,0,0,0.5)'}) 
        
    ], style={
        # --- FIX ANTI-SCROLL DEFINITIVO ---
        # position 'fixed' anclado a las 4 esquinas hace que la imagen ocupe exactamente 
        # el espacio visible de la pantalla, ignorando los márgenes del navegador.
        'position': 'fixed',
        'top': '0',
        'left': '0',
        'right': '0',
        'bottom': '0',
        'margin': '0',
        'padding': '0',
        'backgroundImage': 'url("/assets/foto_equipo1.jpg")', 
        'backgroundSize': 'cover',
        'backgroundPosition': 'center',
        'zIndex': '9999' # Se asegura de tapar cualquier otra cosa que Dash intente cargar debajo
    })

def register_callbacks(app):
    @app.callback(
        [Output('sesion-usuario', 'data'),
         Output('url', 'pathname', allow_duplicate=True),
         Output('login-mensaje', 'children')],
        Input('btn-login', 'n_clicks'),
        [State('login-usuario', 'value'),
         State('login-password', 'value')],
        prevent_initial_call=True
    )
    def verificar_credenciales(n_clicks, usuario, password):
        if not n_clicks or n_clicks == 0:
            raise dash.exceptions.PreventUpdate

        if not usuario or not password:
            return dash.no_update, dash.no_update, "⚠️ Completa todos los campos."
            
        user_limpio = str(usuario).strip().lower()
        
        if user_limpio in USUARIOS_AUTORIZADOS:
            if USUARIOS_AUTORIZADOS[user_limpio]['pass'] == str(password).strip():
                token_sesion = {
                    'usuario': user_limpio,
                    'rol': USUARIOS_AUTORIZADOS[user_limpio]['rol'],
                    'autenticado': True
                }
                # Redirige a la matriz cuando la contraseña es correcta
                return token_sesion, '/matriz-et', "" 
            else:
                return dash.no_update, dash.no_update, "❌ Contraseña incorrecta."
        else:
            return dash.no_update, dash.no_update, "❌ Usuario no autorizado."