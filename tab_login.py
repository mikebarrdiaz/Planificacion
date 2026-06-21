from dash import html, dcc, Input, Output, State, ctx
import dash

# --- DICCIONARIO DE SEGURIDAD (Puedes pasarlo a BBDD en el futuro) ---
USUARIOS_AUTORIZADOS = {
    'admin': {'pass': 'admin123', 'rol': 'editor'},      # Acceso total
    'oficina': {'pass': 'serveo2026', 'rol': 'lector'}   # Solo ver
}


def layout():
    return html.Div([

        # ================= PANEL IZQUIERDO: MARCA =================
        html.Div([
            # Círculos decorativos de fondo (estilo Salesforce)
            html.Div(style={
                'position': 'absolute', 'width': '520px', 'height': '520px', 'borderRadius': '50%',
                'background': 'rgba(255,255,255,0.07)', 'top': '-160px', 'right': '-150px'
            }),
            html.Div(style={
                'position': 'absolute', 'width': '340px', 'height': '340px', 'borderRadius': '50%',
                'background': 'rgba(255,255,255,0.06)', 'bottom': '-120px', 'left': '-90px'
            }),
            html.Div(style={
                'position': 'absolute', 'width': '200px', 'height': '200px', 'borderRadius': '50%',
                'border': '1px solid rgba(255,255,255,0.14)', 'bottom': '120px', 'right': '60px'
            }),

            # Logo + nombre de la app
            html.Div([
                html.Img(src='/assets/logo.svg', style={'height': '32px', 'filter': 'brightness(0) invert(1)'}),
                html.Span("Gestión de Licitaciones", style={
                    'fontSize': '16px', 'fontWeight': '700', 'color': '#fff', 'letterSpacing': '0.01em'
                })
            ], style={'position': 'relative', 'display': 'flex', 'alignItems': 'center', 'gap': '12px'}),

            # Mensaje de marca central
            html.Div([
                html.Div("Plataforma corporativa", style={
                    'fontSize': '13px', 'fontWeight': '700', 'letterSpacing': '0.14em',
                    'color': 'rgba(255,255,255,0.72)', 'textTransform': 'uppercase', 'marginBottom': '18px'
                }),
                html.H1("Planifica licitaciones y la carga del equipo técnico", style={
                    'fontSize': '38px', 'lineHeight': '1.15', 'fontWeight': '700', 'color': '#fff', 'margin': '0'
                }),
                html.P("Gestión de equipo, cronograma de dedicación diaria (FTE) y asignación de licitaciones.", style={
                    'fontSize': '16px', 'lineHeight': '1.6', 'color': 'rgba(255,255,255,0.86)', 'margin': '20px 0 0', 'maxWidth': '430px'
                })
            ], style={'position': 'relative'}),

            # Copyright
            html.Div("© 2026 · Bidding · Uso interno", style={
                'position': 'relative', 'fontSize': '12px', 'color': 'rgba(255,255,255,0.66)'
            })

        ], style={
            'width': '46%', 'minWidth': '420px', 'position': 'relative',
            'background': 'linear-gradient(150deg, #FF4E00 0%, #d63e00 56%, #9e2e00 100%)',
            'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'space-between',
            'padding': '46px 52px', 'overflow': 'hidden', 'boxSizing': 'border-box'
        }),

        # ================= PANEL DERECHO: FORMULARIO =================
        html.Div([
            html.Div([

                html.Div([
                    html.Div("Bienvenido, ", style={'fontSize': '13px', 'color': '#706e6b', 'fontWeight': '600'}),
                    html.H2("Inicia sesión", style={'fontSize': '26px', 'fontWeight': '700', 'color': '#181818', 'margin': '5px 0 0'}),
                    html.P("Accede con tus credenciales de rol.", style={'fontSize': '14px', 'color': '#706e6b', 'margin': '7px 0 0'})
                ], style={'marginBottom': '30px'}),

                html.Div([
                    html.Label("Usuario", className="etiqueta-dato"),
                    dcc.Input(id='login-usuario', type='text', placeholder='Usuario', className="input-filtro",
                              style={'width': '100%', 'height': '44px', 'boxSizing': 'border-box'})
                ], className="serveo-input-wrapper", style={'marginBottom': '16px'}),

                html.Div([
                    html.Label("Contraseña de acceso", className="etiqueta-dato"),
                    dcc.Input(id='login-password', type='password', placeholder='Contraseña', className="input-filtro",
                              style={'width': '100%', 'height': '44px', 'boxSizing': 'border-box'})
                ], className="serveo-input-wrapper", style={'marginBottom': '28px'}),

                html.Button('Accede', id='btn-login', n_clicks=0, className="btn-serveo-primario",
                            style={'width': '100%', 'height': '46px', 'fontSize': '14px', 'boxSizing': 'border-box'}),

                html.Div(id='login-mensaje', style={
                    'color': 'var(--semantic-negative)', 'marginTop': '16px', 'fontSize': '12px',
                    'textAlign': 'center', 'fontWeight': 'bold', 'fontFamily': 'var(--font-family)'
                })

            ], style={'width': '100%', 'maxWidth': '380px'})
        ], style={
            'flex': '1', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
            'padding': '40px 24px', 'backgroundColor': '#f3f3f3', 'boxSizing': 'border-box'
        })

    ], style={
        'position': 'fixed', 'top': '0', 'left': '0', 'right': '0', 'bottom': '0',
        'margin': '0', 'padding': '0', 'display': 'flex',
        'fontFamily': 'var(--font-family)', 'color': '#181818',
        'zIndex': '9999', 'overflow': 'hidden'
    })


def register_callbacks(app):
    @app.callback(
        [Output('sesion-usuario', 'data', allow_duplicate=True),
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