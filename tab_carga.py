import dash
from dash import html, dcc, dash_table, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import datetime
from utils.data_manager import obtener_datos_eficiente, procesar_cronograma, formato_fecha_es
from utils.icons import icono

# --- ESTILO DE TARJETA BASE (estilo Salesforce / Lightning, look Serveo) ---
ESTILO_TARJETA = {
    'backgroundColor': '#FFFFFF',
    'border': '1px solid #e5e5e5',
    'borderRadius': 'var(--radius-container)',
    'boxShadow': '0 1px 2px rgba(71, 71, 81, 0.05)',
    'overflow': 'hidden'
}

ESTILO_BADGE_SECCION = {
    'estudio': {'color': '#9a3412', 'backgroundColor': '#ffe1d0'},
    'previo': {'color': '#4b327f', 'backgroundColor': '#ece4fb'},
    'global': {'color': '#1d4ed8', 'backgroundColor': '#dbeafe'},
}


def header_seccion(nombre_icono, etiqueta, titulo, tono='estudio', tooltip=None, extra_derecha=None):
    estilo_badge = ESTILO_BADGE_SECCION.get(tono, ESTILO_BADGE_SECCION['estudio'])
    return html.Div([
        html.Div([
            html.Img(src=icono(nombre_icono, color=estilo_badge['color']), style={
                'width': '36px', 'height': '36px', 'borderRadius': '8px',
                'backgroundColor': estilo_badge['backgroundColor'],
                'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                'padding': '8px', 'boxSizing': 'border-box', 'flex': 'none'
            }),
            html.Div([
                html.Div(etiqueta, style={'fontSize': '11px', 'color': 'var(--gray-66)', 'fontWeight': '700', 'textTransform': 'uppercase', 'letterSpacing': '0.03em'}),
                html.Div([
                    html.Span(titulo, style={'fontSize': '16px', 'fontWeight': '700', 'color': 'var(--text-border)', 'lineHeight': '1.2'}),
                    info_tooltip(tooltip) if tooltip else None
                ], style={'display': 'flex', 'alignItems': 'center'})
            ])
        ], style={'display': 'flex', 'alignItems': 'center', 'gap': '12px'}),
        html.Div(extra_derecha, style={'display': 'flex', 'alignItems': 'center', 'gap': '8px', 'flex': 'none'}) if extra_derecha else None
    ], style={'marginBottom': '14px', 'marginTop': '28px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'flexWrap': 'wrap', 'gap': '12px'})


def info_tooltip(texto, tamano='14px'):
    """Icono 'i' circular con tooltip nativo (title) explicando un cálculo o métrica."""
    return html.Span(
        "i",
        title=texto,
        style={
            'display': 'inline-flex', 'alignItems': 'center', 'justifyContent': 'center',
            'width': tamano, 'height': tamano, 'borderRadius': '50%',
            'backgroundColor': '#ededed', 'color': '#706e6b',
            'fontSize': '10px', 'fontWeight': '700', 'fontStyle': 'italic',
            'fontFamily': 'Georgia, serif', 'cursor': 'help', 'flex': 'none',
            'marginLeft': '6px', 'userSelect': 'none', 'lineHeight': '1'
        }
    )


# --- TARJETA CLÁSICA (UN VALOR), igual que en Cronograma ---
def crear_tarjeta_kpi(id_componente, titulo, valor_inicial="0", bg_color='#FFFFFF', tooltip=None):
    return html.Div([
        html.Div([
            html.Span(titulo, style={'fontSize': '10px', 'color': 'var(--gray-66)', 'textTransform': 'uppercase', 'fontWeight': '700', 'letterSpacing': '0.5px'}),
            info_tooltip(tooltip) if tooltip else None
        ], style={'display': 'flex', 'alignItems': 'center'}),
        html.Div(valor_inicial, id=id_componente, style={'fontSize': '22px', 'fontWeight': '700', 'color': 'var(--color-title)', 'marginTop': '6px'})
    ], style={**ESTILO_TARJETA, 'flex': '1', 'padding': '16px 18px', 'backgroundColor': bg_color})


# --- TARJETA DOBLE (DESGLOSE TÉCNICOS / BAM), igual que en Cronograma ---
def crear_tarjeta_kpi_desglose(id_tec, id_bam, titulo, bg_color='#FFFFFF', tooltip=None):
    return html.Div([
        html.Div([
            html.Span(titulo, style={'fontSize': '10px', 'color': 'var(--gray-66)', 'textTransform': 'uppercase', 'fontWeight': '700', 'letterSpacing': '0.5px'}),
            info_tooltip(tooltip) if tooltip else None
        ], style={'display': 'flex', 'alignItems': 'center'}),
        html.Div([
            html.Div([
                html.Span("TEC", style={'fontSize': '10px', 'color': 'var(--text-border)', 'fontWeight': '700', 'backgroundColor': 'var(--card-divider)', 'borderRadius': '4px', 'padding': '1px 6px'}),
                html.Span("0", id=id_tec, style={'fontSize': '19px', 'fontWeight': '700', 'color': 'var(--color-title)'})
            ], style={'flex': '1', 'display': 'flex', 'alignItems': 'baseline', 'gap': '8px'}),
            html.Div([
                html.Span("BAM", style={'fontSize': '10px', 'color': '#fff', 'fontWeight': '700', 'backgroundColor': 'var(--accent)', 'borderRadius': '4px', 'padding': '1px 6px'}),
                html.Span("0", id=id_bam, style={'fontSize': '19px', 'fontWeight': '700', 'color': 'var(--accent)'})
            ], style={'flex': '1', 'display': 'flex', 'alignItems': 'baseline', 'gap': '8px', 'borderLeft': '1px solid var(--card-divider)', 'paddingLeft': '14px'})
        ], style={'display': 'flex', 'marginTop': '8px'})
    ], style={**ESTILO_TARJETA, 'flex': '1.5', 'padding': '16px 18px', 'backgroundColor': bg_color})


# Orden estricto de colores SERVEO expandido (16 colores armonizados)
PALETA_GRAFICOS = [
    "#FF4E00", # 1. Acento corporativo
    "#474751", # 2. Base oscuro
    "#4383F0", # 3. Semántico Positivo (Azul)
    "#6AAE7A", # 4. Verde corporativo
    "#DB563A", # 5. Semántico Negativo (Rojo)
    "#CEC6C0", # 6. Secundario 1
    "#A9CEF4", # 7. Azul claro
    "#986F54", # 8. Marrón
    "#AEA4BF", # 9. Morado grisáceo
    "#FFD97D", # 10. Amarillo/Dorado
    "#BDEBDF", # 11. Semántico Neutral (Verde agua)
    "#38385C", # 12. Azul marino oscuro
    "#E68A5C", # 13. Naranja suave
    "#8DB38B", # 14. Verde oliva
    "#5C9EAD", # 15. Azul verdoso
    "#B3B3B3"  # 16. Gris medio
]

FUENTE = "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"


def layout():
    # Sincronización ultra-rápida desde RAM
    _, _, df_eq, _, _ = obtener_datos_eficiente(force_reload=False)

    opciones_tecnicos = []
    opciones_roles = []
    opciones_sedes = []

    if not df_eq.empty:
        col_id = 'ID_Tecnico' if 'ID_Tecnico' in df_eq.columns else ('ID_Técnico' if 'ID_Técnico' in df_eq.columns else 'Nombre')
        col_nom = 'Nombre' if 'Nombre' in df_eq.columns else df_eq.columns[0]

        df_eq[col_nom] = df_eq[col_nom].astype(str).str.strip()
        df_eq[col_id] = df_eq[col_id].astype(str).str.strip()

        for _, row in df_eq.iterrows():
            nombre_real = row[col_nom]
            alias_visual = row[col_id]
            if pd.isna(nombre_real) or nombre_real == 'nan': continue
            if pd.isna(alias_visual) or alias_visual == 'nan' or not alias_visual:
                alias_visual = nombre_real

            opciones_tecnicos.append({'label': alias_visual, 'value': nombre_real})

        if 'Perfil Técnico' in df_eq.columns:
            roles_unicos = df_eq['Perfil Técnico'].dropna().unique()
            opciones_roles = [{'label': str(r).strip(), 'value': str(r).strip()} for r in roles_unicos if str(r).strip() != 'nan']

        if 'Sede' in df_eq.columns:
            sedes_unicas = df_eq['Sede'].dropna().unique()
            opciones_sedes = [{'label': str(s).strip(), 'value': str(s).strip()} for s in sedes_unicas if str(s).strip() != 'nan']
        else:
            opciones_sedes = [
                {'label': 'MAD (Quint)', 'value': 'MAD (Quint)'},
                {'label': 'BCN (T. Auditori)', 'value': 'BCN (T. Auditori)'},
                {'label': 'VALENCIA', 'value': 'VALENCIA'}
            ]

    return html.Div([

        # --- HEADER DE PÁGINA (estilo Salesforce / Claude design) ---
        html.Div([
            html.Div([
                html.Img(src=icono('grafico'), style={
                    'width': '42px', 'height': '42px', 'borderRadius': '8px', 'background': 'var(--accent)',
                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'padding': '11px',
                    'boxSizing': 'border-box', 'flex': 'none'
                }),
                html.Div([
                    html.Div("Análisis de carga", style={'fontSize': '12px', 'color': 'var(--gray-66)', 'fontWeight': '600'}),
                    html.Div("Carga de trabajo (FTE)", style={'fontSize': '20px', 'fontWeight': '700', 'color': 'var(--text-border)', 'lineHeight': '1.2'})
                ])
            ], style={'display': 'flex', 'alignItems': 'center', 'gap': '13px'})
        ], style={**ESTILO_TARJETA, 'padding': '14px 18px', 'marginBottom': '16px'}),

        html.H3("Análisis de Carga de Trabajo (FTE)", className="serveo-titulo-pagina", style={'display': 'none'}),

        # --- BARRA DE FILTROS SUPERIOR ---
        html.Div([
            html.Div([
                html.Label("Filtrar por Sede:", className="etiqueta-dato"),
                dcc.Dropdown(
                    id='drop-filtro-sede-carga',
                    options=opciones_sedes,
                    placeholder="Todas las sedes...",
                    clearable=True,
                    multi=True
                )
            ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '220px', 'marginRight': '8px'}),

            html.Div([
                html.Label("Filtrar por Rol:", className="etiqueta-dato"),
                dcc.Dropdown(
                    id='drop-filtro-rol',
                    options=opciones_roles,
                    placeholder="Todos los roles...",
                    clearable=True,
                    multi=True
                )
            ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '220px', 'marginRight': '8px'}),

            html.Div([
                html.Label("Filtrar por Técnico(s):", className="etiqueta-dato"),
                dcc.Dropdown(
                    id='drop-filtro-tec',
                    options=opciones_tecnicos,
                    placeholder="Mostrando todo el equipo...",
                    clearable=True,
                    multi=True
                )
            ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '300px'})
        ], className="contenedor-filtros", style={'backgroundColor': 'var(--card-divider)', 'alignItems': 'flex-end', 'justifyContent': 'flex-start', 'border': '1px solid #ededed'}),

        # --- VISIÓN GLOBAL: KPIs AGREGADOS (estilo Cronograma) ---
        header_seccion(
            "matriz", "Visión global", "Carga agregada", tono='global',
            tooltip="Las tarjetas y la barra de ocupación de abajo muestran la foto del día elegido a la "
                    "derecha. Por defecto es hoy, pero puedes elegir cualquier día dentro de los próximos "
                    "60 días para ver cómo evoluciona la ocupación del equipo.",
            extra_derecha=[
                html.Span("Ver día:", style={'fontSize': '12px', 'fontWeight': '600', 'color': 'var(--gray-66)'}),
                dcc.DatePickerSingle(
                    id='date-kpi-carga',
                    date=datetime.date.today(),
                    min_date_allowed=datetime.date.today(),
                    max_date_allowed=datetime.date.today() + datetime.timedelta(days=60),
                    display_format='DD/MM/YYYY',
                    placeholder='Selecciona un día',
                    first_day_of_week=1
                )
            ]
        ),
        html.Div([
            crear_tarjeta_kpi(
                'kpi-carga-ocupacion', 'Ocupación del equipo', bg_color='#FAFAFA',
                tooltip="FTE total asignado en la fecha elegida ÷ nº de personas del equipo (según filtros "
                        "activos). Cada persona aporta 1.0 FTE/día de capacidad. Si hay 10 personas y se "
                        "asignan 6.5 FTE ese día, la ocupación es 65%."
            ),
            crear_tarjeta_kpi_desglose(
                'kpi-carga-fte-tec', 'kpi-carga-fte-bam', 'FTE asignado', bg_color='#FAFAFA',
                tooltip="Suma de FTE de la fecha elegida, repartido proporcionalmente entre Técnicos y BAM "
                        "según las horas de licitación de cada perfil. Incluye licitaciones en estudio y "
                        "estudio previo."
            ),
        ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '8px'}),

        # --- BARRA DE OCUPACIÓN + LEYENDA (estilo Cronograma) ---
        html.Div([
            html.Div([
                html.Div([
                    html.Span("Ocupación del equipo", id='label-fecha-ocupacion', style={'fontSize': '13px', 'fontWeight': '700', 'color': 'var(--text-border)'}),
                    info_tooltip(
                        "Compara el FTE asignado en la fecha elegida (naranja = en estudio, morado = estudio "
                        "previo) frente a la capacidad total del equipo filtrado. El tramo gris es capacidad "
                        "libre, es decir, personas sin carga asignada ese día."
                    )
                ], style={'display': 'flex', 'alignItems': 'center'}),
                html.Div("0%", id='label-ocupacion-carga', style={'fontSize': '13px', 'fontWeight': '700', 'color': 'var(--text-border)'})
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'marginBottom': '11px'}),
            html.Div([
                html.Div(id='barra-ocupacion-estudio', style={
                    'position': 'absolute', 'left': '0', 'top': '0', 'bottom': '0', 'width': '0%',
                    'backgroundColor': '#FF4E00'
                }),
                html.Div(id='barra-ocupacion-previo', style={
                    'position': 'absolute', 'top': '0', 'bottom': '0', 'left': '0%', 'width': '0%',
                    'backgroundColor': '#7a5cd0'
                }),
            ], style={'position': 'relative', 'height': '26px', 'backgroundColor': '#ededed', 'borderRadius': '5px', 'overflow': 'hidden'}),
            html.Div([
                html.Div([
                    html.Span(style={'width': '11px', 'height': '11px', 'borderRadius': '3px', 'backgroundColor': '#FF4E00', 'display': 'inline-block'}),
                    html.Span("En estudio · ", id='leyenda-estudio-label'),
                    html.Span("0.00 FTE", id='leyenda-estudio-valor'),
                    info_tooltip("Licitaciones cuya etapa actual es 'En estudio': ya están activas y en preparación de oferta.")
                ], style={'display': 'flex', 'alignItems': 'center', 'gap': '7px', 'fontSize': '12px', 'color': '#5c5c5c', 'fontWeight': '600'}),
                html.Div([
                    html.Span(style={'width': '11px', 'height': '11px', 'borderRadius': '3px', 'backgroundColor': '#7a5cd0', 'display': 'inline-block'}),
                    html.Span("Estudio previo · "),
                    html.Span("0.00 FTE", id='leyenda-previo-valor'),
                    info_tooltip("Licitaciones en fase preliminar de viabilidad, antes de confirmarse como activas.")
                ], style={'display': 'flex', 'alignItems': 'center', 'gap': '7px', 'fontSize': '12px', 'color': '#5c5c5c', 'fontWeight': '600'}),
                html.Div([
                    html.Span(style={'width': '11px', 'height': '11px', 'borderRadius': '3px', 'backgroundColor': '#ededed', 'border': '1px solid #d8d8d8', 'display': 'inline-block'}),
                    html.Span("Capacidad libre · "),
                    html.Span("0.00 FTE", id='leyenda-libre-valor'),
                    info_tooltip("FTE del equipo (según filtros) que no tiene ninguna carga asignada en la fecha elegida.")
                ], style={'display': 'flex', 'alignItems': 'center', 'gap': '7px', 'fontSize': '12px', 'color': '#5c5c5c', 'fontWeight': '600', 'marginLeft': 'auto'}),
            ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '18px', 'marginTop': '12px'})
        ], style={**ESTILO_TARJETA, 'padding': '16px 18px', 'marginBottom': '8px'}),

        header_seccion(
            "busqueda", "Activas", "En estudio", tono='estudio',
            tooltip="Carga diaria (FTE) de las licitaciones en etapa 'En estudio', dentro del rango de "
                    "fechas seleccionado. El reparto entre personas es proporcional a las horas de "
                    "licitación asignadas a cada Técnico/BAM. Este rango no afecta a los KPIs de arriba.",
            extra_derecha=[
                html.Span("Del:", style={'fontSize': '12px', 'fontWeight': '600', 'color': 'var(--gray-66)'}),
                dcc.DatePickerSingle(
                    id='date-rango-inicio',
                    date=datetime.date.today(),
                    min_date_allowed=datetime.date.today(),
                    max_date_allowed=datetime.date.today() + datetime.timedelta(days=60),
                    display_format='DD/MM/YYYY',
                    first_day_of_week=1
                ),
                html.Span("al:", style={'fontSize': '12px', 'fontWeight': '600', 'color': 'var(--gray-66)'}),
                dcc.DatePickerSingle(
                    id='date-rango-fin',
                    date=datetime.date.today() + datetime.timedelta(days=60),
                    min_date_allowed=datetime.date.today(),
                    max_date_allowed=datetime.date.today() + datetime.timedelta(days=60),
                    display_format='DD/MM/YYYY',
                    first_day_of_week=1
                )
            ]
        ),
        dcc.Loading(
            type="circle", color="#FF4E00",
            children=html.Div(
                dcc.Graph(
                    id='grafico-carga-estudio',
                    config={'displayModeBar': False},
                    style={'padding': '16px'}
                ), style={**ESTILO_TARJETA, 'marginBottom': '8px'}
            )
        ),

        header_seccion(
            "documento", "Preliminar", "Estudio previo", tono='previo',
            tooltip="Carga diaria (FTE) de licitaciones en fase preliminar 'Estudio previo', dentro del "
                    "rango de días seleccionado. Se calcula igual que el gráfico de 'En estudio'."
        ),
        dcc.Loading(
            type="circle", color="#FF4E00",
            children=html.Div(
                dcc.Graph(
                    id='grafico-carga-previo',
                    config={'displayModeBar': False},
                    style={'padding': '16px'}
                ), style=ESTILO_TARJETA
            )
        ),
    ], style={'paddingBottom': '40px'})


def register_callbacks(app):

    # =====================================================================
    # CALLBACK 1: FILTROS EN CASCADA (Sede -> Rol -> Técnico)
    # =====================================================================
    @app.callback(
        [Output('drop-filtro-tec', 'options'),
         Output('drop-filtro-tec', 'value')],
        [Input('drop-filtro-sede-carga', 'value'),
         Input('drop-filtro-rol', 'value')],
        State('drop-filtro-tec', 'value')
    )
    def encadenar_filtros(sedes_seleccionadas, roles_seleccionados, tecnicos_actuales):
        _, _, df_eq, _, _ = obtener_datos_eficiente(force_reload=False)

        if df_eq.empty:
            return [], dash.no_update

        df_filtrado = df_eq.copy()

        # Filtro Cascada: Sede
        if sedes_seleccionadas:
            if isinstance(sedes_seleccionadas, str): sedes_seleccionadas = [sedes_seleccionadas]
            if 'Sede' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['Sede'].isin(sedes_seleccionadas)]

        # Filtro Cascada: Rol
        if roles_seleccionados:
            if isinstance(roles_seleccionados, str): roles_seleccionados = [roles_seleccionados]
            if 'Perfil Técnico' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['Perfil Técnico'].isin(roles_seleccionados)]

        col_id = 'ID_Tecnico' if 'ID_Tecnico' in df_filtrado.columns else ('ID_Técnico' if 'ID_Técnico' in df_filtrado.columns else 'Nombre')
        col_nom = 'Nombre' if 'Nombre' in df_filtrado.columns else df_filtrado.columns[0]

        nuevas_opciones = []
        nombres_validos = []
        for _, row in df_filtrado.iterrows():
            nr = str(row.get(col_nom, '')).strip()
            al = str(row.get(col_id, '')).strip()
            if not nr or nr == 'nan': continue
            if not al or al == 'nan': al = nr

            nuevas_opciones.append({'label': al, 'value': nr})
            nombres_validos.append(nr)

        nuevos_valores_tecnicos = tecnicos_actuales
        if tecnicos_actuales:
            if isinstance(tecnicos_actuales, str): tecnicos_actuales = [tecnicos_actuales]
            nuevos_valores_tecnicos = [t for t in tecnicos_actuales if t in nombres_validos]
            if not nuevos_valores_tecnicos: nuevos_valores_tecnicos = None

        return nuevas_opciones, nuevos_valores_tecnicos


    # =====================================================================
    # CALLBACK 2: GENERACIÓN DE GRÁFICOS + KPIs (REPARTO PROPORCIONAL FTE)
    # =====================================================================
    @app.callback(
        [Output('grafico-carga-estudio', 'figure'),
         Output('grafico-carga-previo', 'figure'),
         Output('kpi-carga-ocupacion', 'children'),
         Output('kpi-carga-fte-tec', 'children'),
         Output('kpi-carga-fte-bam', 'children'),
         Output('label-ocupacion-carga', 'children'),
         Output('label-fecha-ocupacion', 'children'),
         Output('barra-ocupacion-estudio', 'style'),
         Output('barra-ocupacion-previo', 'style'),
         Output('leyenda-estudio-valor', 'children'),
         Output('leyenda-previo-valor', 'children'),
         Output('leyenda-libre-valor', 'children')],
        [Input('drop-filtro-sede-carga', 'value'),
         Input('drop-filtro-tec', 'value'),
         Input('drop-filtro-rol', 'value'),
         Input('date-kpi-carga', 'date'),
         Input('date-rango-inicio', 'date'),
         Input('date-rango-fin', 'date')]
    )
    def actualizar_grafico(sedes_seleccionadas, tecnicos_seleccionados, roles_seleccionados,
                            fecha_kpi_str, fecha_inicio_str, fecha_fin_str):

        if sedes_seleccionadas and isinstance(sedes_seleccionadas, str): sedes_seleccionadas = [sedes_seleccionadas]
        if tecnicos_seleccionados and isinstance(tecnicos_seleccionados, str): tecnicos_seleccionados = [tecnicos_seleccionados]
        if roles_seleccionados and isinstance(roles_seleccionados, str): roles_seleccionados = [roles_seleccionados]

        hoy = datetime.date.today()

        def parsear_iso(s, fallback):
            if not s: return fallback
            try: return datetime.date.fromisoformat(str(s)[:10])
            except (ValueError, TypeError): return fallback

        fecha_kpi = parsear_iso(fecha_kpi_str, hoy)
        fecha_inicio = parsear_iso(fecha_inicio_str, hoy)
        fecha_fin = parsear_iso(fecha_fin_str, hoy + datetime.timedelta(days=60))
        if fecha_fin < fecha_inicio:
            fecha_inicio, fecha_fin = fecha_fin, fecha_inicio

        col_hoy_kpi = formato_fecha_es(fecha_kpi)
        texto_fecha_kpi = f"Ocupación del equipo · {fecha_kpi.strftime('%d/%m/%Y')}"

        _, df_cron, df_eq, _, _ = obtener_datos_eficiente(force_reload=False)

        # Estilos "vacíos" reutilizables para las barras de ocupación
        estilo_barra_vacia_estudio = {
            'position': 'absolute', 'left': '0', 'top': '0', 'bottom': '0', 'width': '0%',
            'backgroundColor': '#FF4E00'
        }
        estilo_barra_vacia_previo = {
            'position': 'absolute', 'top': '0', 'bottom': '0', 'left': '0%', 'width': '0%',
            'backgroundColor': '#7a5cd0'
        }

        def grafico_vacio(mensaje):
            fig = px.bar(title=mensaje)
            fig.update_layout(
                plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
                font=dict(family=FUENTE, color="#474751"),
                title_font=dict(size=14, color="#181818"),
                margin=dict(t=50, l=10, r=10, b=10)
            )
            return fig

        kpis_vacios = (
            "0%", "0.00", "0.00", "0% ocupado", texto_fecha_kpi,
            estilo_barra_vacia_estudio, estilo_barra_vacia_previo,
            "0.00 FTE", "0.00 FTE", "0.00 FTE"
        )

        if df_cron.empty:
            return (grafico_vacio("Sin datos de licitaciones"), grafico_vacio("Sin datos de licitaciones")) + kpis_vacios

        dict_roles = {}
        dict_alias = {}
        dict_sedes = {}
        if not df_eq.empty:
            col_id = 'ID_Tecnico' if 'ID_Tecnico' in df_eq.columns else ('ID_Técnico' if 'ID_Técnico' in df_eq.columns else 'Nombre')
            col_nom = 'Nombre' if 'Nombre' in df_eq.columns else df_eq.columns[0]

            for _, r in df_eq.iterrows():
                nr = str(r.get(col_nom, '')).strip()
                al = str(r.get(col_id, '')).strip()
                sede = str(r.get('Sede', 'MAD (Quint)')).strip()

                if not nr or nr == 'nan': continue
                if not al or al == 'nan': al = nr
                if not sede or sede == 'nan': sede = 'MAD (Quint)'

                dict_alias[nr] = al
                dict_roles[nr] = str(r.get('Perfil Técnico', 'Sin Rol')).strip()
                dict_sedes[nr] = sede

        df_maestro, col_calendario = procesar_cronograma(df_cron)

        # Recorte del calendario al rango de fechas elegido en los selectores de calendario
        # (solo afecta a los gráficos; los KPIs usan col_hoy_kpi, calculado sobre la fecha de referencia)
        set_calendario = set(col_calendario)
        col_calendario_rango = []
        cursor = fecha_inicio
        while cursor <= fecha_fin:
            nombre_col = formato_fecha_es(cursor)
            if nombre_col in set_calendario:
                col_calendario_rango.append(nombre_col)
            cursor += datetime.timedelta(days=1)

        texto_rango_fechas = f"{fecha_inicio.strftime('%d/%m/%Y')} → {fecha_fin.strftime('%d/%m/%Y')}"

        def extraer_float(val):
            try: return float(str(val).replace(',', '.'))
            except: return 0.0

        registros = []
        for _, row in df_maestro.iterrows():

            bam_val = str(row.get('BAM', '')).strip()
            bam_val = bam_val if bam_val and bam_val != 'nan' else None

            tecs = [str(row.get(f'Técnico {i}', '')).strip() for i in range(1, 4)]
            tecs_validos = [t for t in tecs if t and t != 'nan']

            if not bam_val and not tecs_validos:
                continue

            etapa = str(row.get('Etapa', 'Sin Etapa')).strip()
            licitacion = str(row.get('Código de Licitación', 'S/C')).strip()

            h_tec = extraer_float(row.get('Horas de Licitación', row.get('Horas', 0)))
            h_bam = extraer_float(row.get('Horas de Licitación BAM', row.get('Horas BAM', 0)))
            h_total = h_tec + h_bam

            if h_total > 0:
                prop_bam = h_bam / h_total if bam_val else 0.0
                prop_tecs = h_tec / h_total if tecs_validos else 0.0
            else:
                personas_totales = len(tecs_validos) + (1 if bam_val else 0)
                prop_bam = 1.0 / personas_totales if bam_val else 0.0
                prop_tecs = len(tecs_validos) / personas_totales if tecs_validos else 0.0

            for dia in col_calendario:
                fte_dia = extraer_float(row.get(dia, 0))

                if fte_dia > 0:
                    if bam_val and prop_bam > 0:
                        registros.append({
                            'Nombre_Real': bam_val,
                            'Técnico': dict_alias.get(bam_val, bam_val),
                            'Rol': dict_roles.get(bam_val, "Bidding Area Manager"),
                            'Sede': dict_sedes.get(bam_val, "MAD (Quint)"),
                            'Fecha': dia,
                            'Licitación': licitacion,
                            'Carga (FTE)': fte_dia * prop_bam,
                            'Etapa': etapa
                        })

                    if tecs_validos and prop_tecs > 0:
                        fte_per_tec = (fte_dia * prop_tecs) / len(tecs_validos)
                        for t in tecs_validos:
                            registros.append({
                                'Nombre_Real': t,
                                'Técnico': dict_alias.get(t, t),
                                'Rol': dict_roles.get(t, "Bidding Technician"),
                                'Sede': dict_sedes.get(t, "MAD (Quint)"),
                                'Fecha': dia,
                                'Licitación': licitacion,
                                'Carga (FTE)': fte_per_tec,
                                'Etapa': etapa
                            })

        df_grafico = pd.DataFrame(registros)

        def generar_figura_por_etapa(etapa_objetivo):
            if df_grafico.empty:
                return grafico_vacio("No hay cargas asignadas en los próximos 60 días.")

            df_etapa = df_grafico[df_grafico['Etapa'] == etapa_objetivo]

            if df_etapa.empty:
                return grafico_vacio(f"No hay cargas en la etapa: {etapa_objetivo}")

            # --- FILTRADO TRIPLE ---
            if sedes_seleccionadas:
                df_etapa = df_etapa[df_etapa['Sede'].isin(sedes_seleccionadas)]
                if df_etapa.empty:
                    return grafico_vacio(f"Sin cargas para la Sede seleccionada en: {etapa_objetivo}")

            if roles_seleccionados:
                df_etapa = df_etapa[df_etapa['Rol'].isin(roles_seleccionados)]
                if df_etapa.empty:
                    return grafico_vacio(f"Sin cargas para el Rol seleccionado en: {etapa_objetivo}")

            if tecnicos_seleccionados:
                df_etapa = df_etapa[df_etapa['Nombre_Real'].isin(tecnicos_seleccionados)]
                if df_etapa.empty:
                    return grafico_vacio(f"Sin cargas para el Técnico seleccionado en: {etapa_objetivo}")

            # --- FILTRADO POR RANGO DE DÍAS (slider) ---
            df_etapa = df_etapa[df_etapa['Fecha'].isin(col_calendario_rango)]
            if df_etapa.empty:
                return grafico_vacio(f"Sin cargas en el rango de días seleccionado para: {etapa_objetivo}")

            # --- TÍTULOS DINÁMICOS ---
            if tecnicos_seleccionados:
                color_var = 'Licitación'
                if len(tecnicos_seleccionados) == 1:
                    texto_titulo = dict_alias.get(tecnicos_seleccionados[0], tecnicos_seleccionados[0])
                elif len(tecnicos_seleccionados) <= 3:
                    texto_titulo = ", ".join([dict_alias.get(t, t) for t in tecnicos_seleccionados])
                else:
                    texto_titulo = f"{len(tecnicos_seleccionados)} Miembros seleccionados"
                titulo = f"Desglose de Carga ({etapa_objetivo}): {texto_titulo}"

            elif roles_seleccionados:
                color_var = 'Técnico'
                if len(roles_seleccionados) == 1:
                    texto_titulo = roles_seleccionados[0]
                else:
                    texto_titulo = "Varios Roles"
                titulo = f"Carga Operativa - Rol: {texto_titulo} ({etapa_objetivo})"

            elif sedes_seleccionadas:
                color_var = 'Técnico'
                if len(sedes_seleccionadas) == 1:
                    texto_titulo = sedes_seleccionadas[0]
                else:
                    texto_titulo = "Varias Sedes"
                titulo = f"Carga Operativa - Sede: {texto_titulo} ({etapa_objetivo})"

            else:
                color_var = 'Técnico'
                titulo = f"Carga de Trabajo Global - {etapa_objetivo}"

            # Construcción de la gráfica base (estilo Salesforce/Lightning: línea de referencia 1.0 FTE)
            fig = px.bar(
                df_etapa,
                x='Fecha',
                y='Carga (FTE)',
                color=color_var,
                title=f"<b style='color:#181818;'>{titulo}</b>",
                color_discrete_sequence=PALETA_GRAFICOS
            )
            fig.update_traces(marker_line_width=0)

            # Texto Total por Día
            df_totales = df_etapa.groupby('Fecha', as_index=False)['Carga (FTE)'].sum()
            fig.add_trace(go.Scatter(
                x=df_totales['Fecha'],
                y=df_totales['Carga (FTE)'],
                mode='text',
                text=df_totales['Carga (FTE)'].apply(lambda x: f"{x:.2f}" if x > 0 else ""),
                textposition='top center',
                textfont=dict(family=FUENTE, size=12, color="#706e6b"),
                showlegend=False,
                hoverinfo='skip'
            ))

            max_y = df_totales['Carga (FTE)'].max() if not df_totales.empty else 1
            rango_y = [0, max_y * 1.18] if max_y > 0 else [0, 1]

            fig.update_layout(
                plot_bgcolor='#FFFFFF',
                paper_bgcolor='#FFFFFF',
                font=dict(family=FUENTE, color="#474751", size=12),
                title_font=dict(size=14),
                title_x=0.0,
                xaxis_title="",
                yaxis_title="Esfuerzo (FTE)",
                legend_title_text='Desglose',
                legend=dict(bgcolor='rgba(255,255,255,0)', font=dict(size=11)),
                bargap=0.28,
                margin=dict(t=50, l=10, r=10, b=10),
                xaxis=dict(showgrid=True, gridcolor="#F0F0F0", tickangle=-45, linecolor="#e5e5e5"),
                yaxis=dict(showgrid=True, gridcolor="#F0F0F0", range=rango_y, zerolinecolor="#e5e5e5")
            )

            # Línea de referencia 1.0 FTE (capacidad de una persona), igual a la lógica de Cronograma
            fig.add_hline(
                y=1.0, line_dash="dot", line_color="#a8a8a8", line_width=1,
                annotation_text="1.0 FTE", annotation_font=dict(size=10, color="#9a9a9a"),
                annotation_position="top left"
            )

            return fig, df_etapa

        # --- GENERACIÓN DE FIGURAS ---
        resultado_estudio = generar_figura_por_etapa("En estudio")
        resultado_previo = generar_figura_por_etapa("Estudio previo")

        if isinstance(resultado_estudio, tuple):
            fig_estudio, df_filtrado_estudio = resultado_estudio
        else:
            fig_estudio, df_filtrado_estudio = resultado_estudio, pd.DataFrame()

        if isinstance(resultado_previo, tuple):
            fig_previo, df_filtrado_previo = resultado_previo
        else:
            fig_previo, df_filtrado_previo = resultado_previo, pd.DataFrame()

        # --- CÁLCULO DE KPIs AGREGADOS (sobre la fecha de referencia, independiente del rango de gráficos) ---
        # Partimos de df_grafico filtrado por sede/rol/técnico, SIN aplicar el rango de fechas de los gráficos
        df_kpi_base = df_grafico.copy() if not df_grafico.empty else pd.DataFrame()
        if not df_kpi_base.empty:
            if sedes_seleccionadas:
                df_kpi_base = df_kpi_base[df_kpi_base['Sede'].isin(sedes_seleccionadas)]
            if roles_seleccionados:
                df_kpi_base = df_kpi_base[df_kpi_base['Rol'].isin(roles_seleccionados)]
            if tecnicos_seleccionados:
                df_kpi_base = df_kpi_base[df_kpi_base['Nombre_Real'].isin(tecnicos_seleccionados)]

        # Tamaño del equipo filtrado (capacidad total = 1.0 FTE por persona/día)
        df_eq_filtrado = df_eq.copy()
        if not df_eq_filtrado.empty:
            if sedes_seleccionadas and 'Sede' in df_eq_filtrado.columns:
                df_eq_filtrado = df_eq_filtrado[df_eq_filtrado['Sede'].isin(sedes_seleccionadas)]
            if roles_seleccionados and 'Perfil Técnico' in df_eq_filtrado.columns:
                df_eq_filtrado = df_eq_filtrado[df_eq_filtrado['Perfil Técnico'].isin(roles_seleccionados)]
            if tecnicos_seleccionados:
                col_nom = 'Nombre' if 'Nombre' in df_eq_filtrado.columns else df_eq_filtrado.columns[0]
                df_eq_filtrado = df_eq_filtrado[df_eq_filtrado[col_nom].astype(str).str.strip().isin(tecnicos_seleccionados)]

        capacidad_total = max(len(df_eq_filtrado), 1) if not df_eq.empty else max(len(dict_alias), 1)

        if not df_kpi_base.empty and 'Fecha' in df_kpi_base.columns:
            df_dia_estudio = df_kpi_base[(df_kpi_base['Fecha'] == col_hoy_kpi) & (df_kpi_base['Etapa'] == 'En estudio')]
            df_dia_previo = df_kpi_base[(df_kpi_base['Fecha'] == col_hoy_kpi) & (df_kpi_base['Etapa'] == 'Estudio previo')]
        else:
            df_dia_estudio = pd.DataFrame()
            df_dia_previo = pd.DataFrame()

        fte_estudio_hoy = df_dia_estudio['Carga (FTE)'].sum() if not df_dia_estudio.empty else 0.0
        fte_previo_hoy = df_dia_previo['Carga (FTE)'].sum() if not df_dia_previo.empty else 0.0
        fte_total_hoy = fte_estudio_hoy + fte_previo_hoy

        df_dia_total = pd.concat([df_dia_estudio, df_dia_previo], ignore_index=True) if not (df_dia_estudio.empty and df_dia_previo.empty) else pd.DataFrame()

        # Desglose TEC vs BAM (en la fecha de referencia)
        if not df_dia_total.empty:
            mask_bam = df_dia_total['Rol'].str.contains('Bidding Area Manager|BAM', case=False, na=False)
            fte_bam_hoy = df_dia_total[mask_bam]['Carga (FTE)'].sum()
            fte_tec_hoy = df_dia_total[~mask_bam]['Carga (FTE)'].sum()
        else:
            fte_bam_hoy = 0.0
            fte_tec_hoy = 0.0

        pct_ocupacion = min((fte_total_hoy / capacidad_total) * 100, 100) if capacidad_total > 0 else 0
        pct_estudio = min((fte_estudio_hoy / capacidad_total) * 100, 100) if capacidad_total > 0 else 0
        pct_previo = min((fte_previo_hoy / capacidad_total) * 100, 100 - pct_estudio) if capacidad_total > 0 else 0
        fte_libre = max(capacidad_total - fte_total_hoy, 0)

        estilo_barra_estudio = {
            'position': 'absolute', 'left': '0', 'top': '0', 'bottom': '0',
            'width': f'{pct_estudio}%', 'backgroundColor': '#FF4E00', 'transition': 'width 0.4s ease'
        }
        estilo_barra_previo = {
            'position': 'absolute', 'top': '0', 'bottom': '0', 'left': f'{pct_estudio}%',
            'width': f'{pct_previo}%', 'backgroundColor': '#7a5cd0', 'transition': 'width 0.4s ease, left 0.4s ease'
        }

        return (
            fig_estudio, fig_previo,
            f"{pct_ocupacion:.0f}%",
            f"{fte_tec_hoy:.2f}",
            f"{fte_bam_hoy:.2f}",
            f"{pct_ocupacion:.0f}% ocupado",
            texto_fecha_kpi,
            estilo_barra_estudio, estilo_barra_previo,
            f"{fte_estudio_hoy:.2f} FTE",
            f"{fte_previo_hoy:.2f} FTE",
            f"{fte_libre:.2f} FTE"
        )