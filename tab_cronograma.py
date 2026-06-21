import dash
from dash import html, dcc, dash_table, Input, Output, State
import pandas as pd
import datetime
import numpy as np
from utils.data_manager import obtener_datos_eficiente, procesar_cronograma, parsear_fecha_es
from utils.icons import icono

def generar_estilos_tabla(col_calendario, columnas_fin_semana):
    estilos_celdas_condicionales = [
        {'if': {'column_id': 'Código de Licitación'}, 'minWidth': '100px', 'width': '100px', 'maxWidth': '100px'},
        {'if': {'column_id': 'Nombre de la Licitación'}, 'minWidth': '240px', 'width': '240px', 'maxWidth': '240px'},
        {'if': {'column_id': 'Nivel'}, 'minWidth': '60px', 'width': '60px', 'maxWidth': '60px'},
        {'if': {'column_id': 'BAM'}, 'minWidth': '80px', 'width': '80px', 'maxWidth': '80px'},
        {'if': {'column_id': 'Técnico 1'}, 'minWidth': '80px', 'width': '80px', 'maxWidth': '80px'},
        {'if': {'column_id': 'Técnico 2'}, 'minWidth': '80px', 'width': '80px', 'maxWidth': '80px'},
        {'if': {'column_id': 'Técnico 3'}, 'minWidth': '80px', 'width': '80px', 'maxWidth': '80px'},
        {'if': {'column_id': 'Presupuesto'}, 'minWidth': '110px', 'width': '110px', 'maxWidth': '110px'},
        {'if': {'column_id': 'Horas'}, 'minWidth': '50px', 'width': '50px', 'maxWidth': '50px'},
        {'if': {'column_id': 'Horas BAM'}, 'minWidth': '60px', 'width': '60px', 'maxWidth': '60px'},
        {'if': {'column_id': 'Fecha de Creación'}, 'minWidth': '100px', 'width': '100px', 'maxWidth': '100px'},
        {'if': {'column_id': 'Fecha de Fin'}, 'minWidth': '100px', 'width': '100px', 'maxWidth': '100px'}
    ] + [
        {
            'if': {'column_id': col},
            'minWidth': '75px', 'width': '75px', 'maxWidth': '75px',
            'textAlign': 'center', 'padding': '2px'
        } for col in col_calendario
    ]

    estilos_datos_condicionales = []
    for col in columnas_fin_semana:
        estilos_datos_condicionales.append({
            'if': {'column_id': col},
            'backgroundColor': '#F0EEED',
            'color': '#B3B3B3'
        })

    for col in col_calendario:
        estilos_datos_condicionales.append(
            {'if': {'column_id': col, 'filter_query': f'{{{col}}} != ""'}, 'backgroundColor': 'rgba(189, 235, 223, 0.3)', 'color': '#474751', 'fontWeight': 'bold'}
        )

    for col in col_calendario:
        estilos_datos_condicionales.append({
            'if': {
                'column_id': col,
                'filter_query': f'{{Hito_Fin}} eq "{col}"'
            },
            'backgroundColor': 'rgba(255, 78, 0, 0.3)',
            'border': '2px solid #FF4E00',
            'color': '#FF4E00',
            'fontWeight': 'bold'
        })

    estilos_datos_condicionales.append({
        'if': {'filter_query': '{Código de Licitación} eq "TOTAL FTES"'},
        'backgroundColor': '#F0EEED', 'color': '#FF4E00', 'fontWeight': 'bold'
    })

    return {
        'style_header': {
            'backgroundColor': '#FFFFFF', 
            'color': '#FF4E00', 
            'border': '1px solid #e5e5e5',
            'fontWeight': 'bold',
            'fontSize': '9px',
            'textTransform': 'uppercase',
            'fontFamily': "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            'textAlign': 'center',
            'height': '40px', 'minHeight': '40px', 'maxHeight': '40px',
            'whiteSpace': 'normal'
        },
        'style_cell': {
            'backgroundColor': '#FFFFFF', 
            'color': '#474751', 
            'border': '1px solid #f0f0f0', 
            'fontFamily': "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            'fontSize': '13px',
            'padding': '0px 12px',
            'textAlign': 'left',
            'textOverflow': 'ellipsis',
            'overflow': 'hidden',
            'height': '35px', 'minHeight': '35px', 'maxHeight': '35px',
            'whiteSpace': 'nowrap'
        },
        'style_cell_conditional': estilos_celdas_condicionales,
        'style_data_conditional': estilos_datos_condicionales
    }

# --- ESTILO DE TARJETA BASE (estilo Salesforce / Lightning, look Serveo) ---
ESTILO_TARJETA = {
    'backgroundColor': '#FFFFFF',
    'border': '1px solid #e5e5e5',
    'borderRadius': 'var(--radius-container)',
    'boxShadow': '0 1px 2px rgba(71, 71, 81, 0.05)',
    'overflow': 'hidden'
}

ESTILO_BADGE_SECCION = {
    'pendiente': {'color': '#a86100', 'backgroundColor': '#fdf0dd'},
    'estudio': {'color': '#9a3412', 'backgroundColor': '#ffe1d0'},
    'previo': {'color': '#4b327f', 'backgroundColor': '#ece4fb'},
    'global': {'color': '#1d4ed8', 'backgroundColor': '#dbeafe'},
}


def header_seccion(nombre_icono, etiqueta, titulo, tono='global'):
    estilo_badge = ESTILO_BADGE_SECCION.get(tono, ESTILO_BADGE_SECCION['global'])
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
                html.Div(titulo, style={'fontSize': '16px', 'fontWeight': '700', 'color': 'var(--text-border)', 'lineHeight': '1.2'})
            ])
        ], style={'display': 'flex', 'alignItems': 'center', 'gap': '12px'})
    ], style={'marginBottom': '14px', 'marginTop': '28px'})


# --- TARJETA CLÁSICA (UN VALOR) ---
def crear_tarjeta_kpi(id_componente, titulo, bg_color='#FFFFFF'):
    return html.Div([
        html.Div(titulo, style={'fontSize': '10px', 'color': 'var(--gray-66)', 'textTransform': 'uppercase', 'fontWeight': '700', 'letterSpacing': '0.5px'}),
        html.Div("0", id=id_componente, style={'fontSize': '22px', 'fontWeight': '700', 'color': 'var(--color-title)', 'marginTop': '6px'})
    ], style={**ESTILO_TARJETA, 'flex': '1', 'padding': '16px 18px', 'backgroundColor': bg_color})

# --- TARJETA DOBLE (DESGLOSE TÉCNICOS / BAM) ---
def crear_tarjeta_kpi_desglose(id_tec, id_bam, titulo, bg_color='#FFFFFF'):
    return html.Div([
        html.Div(titulo, style={'fontSize': '10px', 'color': 'var(--gray-66)', 'textTransform': 'uppercase', 'fontWeight': '700', 'letterSpacing': '0.5px'}),
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
    
def layout():
    _, df_cronograma, df_eq, _, _ = obtener_datos_eficiente(force_reload=False)
    df_maestro, col_calendario = procesar_cronograma(df_cronograma)
    
    if df_maestro.empty:
        return html.Div("No hay datos en el cronograma.", style={'color': 'var(--semantic-negative)', 'fontFamily': 'var(--font-family)', 'padding': '20px'})

    opciones_tecnicos = []
    opciones_roles = []
    opciones_niveles = []
    
    if not df_eq.empty:
        # --- EXTRACCIÓN DE ALIAS PARA EL DESPLEGABLE DE TÉCNICOS ---
        col_id = 'ID_Tecnico' if 'ID_Tecnico' in df_eq.columns else ('ID_Técnico' if 'ID_Técnico' in df_eq.columns else 'Nombre')
        col_nom = 'Nombre' if 'Nombre' in df_eq.columns else df_eq.columns[0]
        
        for _, row in df_eq.iterrows():
            nombre_real = str(row.get(col_nom, '')).strip()
            alias_visual = str(row.get(col_id, '')).strip()
            if not nombre_real or nombre_real == 'nan': continue
            if not alias_visual or alias_visual == 'nan': alias_visual = nombre_real
            opciones_tecnicos.append({'label': alias_visual, 'value': nombre_real})
            
        if 'Perfil Técnico' in df_eq.columns:
            roles_unicos = df_eq['Perfil Técnico'].dropna().unique()
            opciones_roles = [{'label': r, 'value': r} for r in roles_unicos]
            
    if 'Nivel' in df_maestro.columns:
        niveles_unicos = df_maestro['Nivel'].dropna().unique()
        opciones_niveles = [{'label': str(n), 'value': str(n)} for n in niveles_unicos]

    columnas_fin_semana = []
    hoy_base = datetime.date.today()
    meses_abrev = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    
    for i in range(60):
        fecha_futura = hoy_base + datetime.timedelta(days=i)
        nombre_col_esperado = f"{fecha_futura.day} {meses_abrev[fecha_futura.month - 1]}"
        if fecha_futura.weekday() >= 5 and nombre_col_esperado in col_calendario:
            columnas_fin_semana.append(nombre_col_esperado)

    estilos_cabecera_condicionales = [
        {'if': {'column_id': col}, 'backgroundColor': '#F0EEED', 'color': '#666666'} 
        for col in columnas_fin_semana
    ]

    base_comun = ["Código de Licitación", "Nombre de la Licitación"]
    if 'Nivel' in df_maestro.columns:
        base_comun.append("Nivel")
        
    cierres_comunes = ["Presupuesto", "Horas", "Horas BAM", "Fecha de Creación", "Fecha de Fin"]

    if "Horas de Licitación" in df_maestro.columns:
        df_maestro = df_maestro.rename(columns={"Horas de Licitación": "Horas"})
    if "Horas Licitación BAM" in df_maestro.columns:
        df_maestro = df_maestro.rename(columns={"Horas Licitación BAM": "Horas BAM"})

    fijas_pendientes = base_comun + cierres_comunes
    cols_pendientes = [{"name": c, "id": c} for c in fijas_pendientes + col_calendario]

    fijas_activas = base_comun.copy()
    if 'BAM' in df_maestro.columns:
        fijas_activas.append("BAM")
    fijas_activas.extend(["Técnico 1", "Técnico 2", "Técnico 3"])
    fijas_activas.extend(cierres_comunes)
    cols_activas = [{"name": c, "id": c} for c in fijas_activas + col_calendario]
    
    config_tabla = generar_estilos_tabla(col_calendario, columnas_fin_semana)
    config_tabla['style_header_conditional'] = estilos_cabecera_condicionales

    opciones_codigos = []
    opciones_nombres = []
    if not df_maestro.empty:
        if 'Código de Licitación' in df_maestro.columns:
            codigos_unicos = df_maestro['Código de Licitación'].dropna().unique()
            opciones_codigos = [{'label': str(c), 'value': str(c)} for c in codigos_unicos]
        if 'Nombre de la Licitación' in df_maestro.columns:
            nombres_unicos = df_maestro['Nombre de la Licitación'].dropna().unique()
            opciones_nombres = [{'label': str(n), 'value': str(n)} for n in nombres_unicos]

    return html.Div([

        # --- HEADER DE PÁGINA (estilo Salesforce / Claude design) ---
        html.Div([
            html.Div([
                html.Img(src=icono('calendario'), style={
                    'width': '42px', 'height': '42px', 'borderRadius': '8px', 'background': 'var(--accent)',
                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'padding': '11px',
                    'boxSizing': 'border-box', 'flex': 'none'
                }),
                html.Div([
                    html.Div("Cronograma", style={'fontSize': '12px', 'color': 'var(--gray-66)', 'fontWeight': '600'}),
                    html.Div("Carga del equipo · FTE diario", style={'fontSize': '20px', 'fontWeight': '700', 'color': 'var(--text-border)', 'lineHeight': '1.2'})
                ])
            ], style={'display': 'flex', 'alignItems': 'center', 'gap': '13px'})
        ], style={**ESTILO_TARJETA, 'padding': '14px 18px', 'marginBottom': '16px'}),

        html.H3("CRONOGRAMA DEL EQUIPO", className="serveo-titulo-pagina", style={'display': 'none'}),

        # --- BARRA DE FILTROS SUPERIOR ---
        html.Div([
            html.Div([
                html.Label("Código Licitación", className="etiqueta-dato"),
                dcc.Dropdown(
                    id="filtro-codigo", 
                    options=opciones_codigos, 
                    placeholder="Todos", 
                    clearable=True, 
                    multi=True
                )
            ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '200px'}),
            
            html.Div([
                html.Label("Nombre Licitación", className="etiqueta-dato"),
                dcc.Dropdown(
                    id="filtro-nombre", 
                    options=opciones_nombres, 
                    placeholder="Todas", 
                    clearable=True, 
                    multi=True
                )
            ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '300px'}),
            
            html.Div([
                html.Label("Nivel:", className="etiqueta-dato"),
                dcc.Dropdown(id='drop-filtro-nivel-cron', options=opciones_niveles, placeholder="Todos", clearable=True, multi=True)
            ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '140px'}),
            
            html.Div([
                html.Label("Rol:", className="etiqueta-dato"),
                dcc.Dropdown(id='drop-filtro-rol-cron', options=opciones_roles, placeholder="Todos los roles...", clearable=True, multi=True)
            ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '240px'}),
            
            html.Div([
                html.Label("Técnico(s):", className="etiqueta-dato"),
                dcc.Dropdown(id='drop-filtro-tec-cron', options=opciones_tecnicos, placeholder="Todo el equipo operativo...", clearable=True, multi=True)
            ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '340px'})
            
        ], className="contenedor-filtros", style={'backgroundColor': 'var(--card-divider)', 'alignItems': 'flex-end', 'justifyContent': 'flex-start', 'flexWrap': 'wrap', 'gap': '16px', 'border': '1px solid #ededed'}),
        
        # --- VISIÓN GLOBAL DEL PIPELINE ---
        header_seccion("matriz", "Visión global", "Pipeline completo", tono='global'),
        html.Div([
            crear_tarjeta_kpi('kpi-global-pres', 'Presupuesto Total Agregado', bg_color='#FAFAFA'),
            crear_tarjeta_kpi_desglose('kpi-global-hor', 'kpi-global-hor-bam', 'Horas Totales Requeridas', bg_color='#FAFAFA'),
            crear_tarjeta_kpi_desglose('kpi-global-fte', 'kpi-global-fte-bam', 'FTEs Globales (Hoy)', bg_color='#FAFAFA')
        ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '8px'}),

        # --- TABLA: LICITACIONES NO ASIGNADAS ---
        header_seccion("reloj", "Pendientes", "Pendientes de asignación", tono='pendiente'),
        html.Div([
            crear_tarjeta_kpi('kpi-pend-pres', 'Presupuesto'),
            crear_tarjeta_kpi_desglose('kpi-pend-hor', 'kpi-pend-hor-bam', 'Total Horas Licitación'),
            crear_tarjeta_kpi_desglose('kpi-pend-fte', 'kpi-pend-fte-bam', 'FTEs Totales (Hoy)')
        ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '16px'}),
        html.Div(
            dash_table.DataTable(
                id='tabla-no-asignadas', 
                columns=cols_pendientes, 
                fixed_columns={'headers': True, 'data': len(fijas_pendientes)},
                style_table={'overflowX': 'auto', 'width': '100%', 'minWidth': '100%', 'maxWidth': '100%'},
                cell_selectable=False,
                **config_tabla
            ), style={**ESTILO_TARJETA, 'marginBottom': '8px'}
        ),

        # --- TABLA: EN ESTUDIO ---
        header_seccion("busqueda", "Activas", "En estudio", tono='estudio'),
        html.Div([
            crear_tarjeta_kpi('kpi-est-pres', 'Presupuesto'),
            crear_tarjeta_kpi_desglose('kpi-est-hor', 'kpi-est-hor-bam', 'Total Horas Licitación'),
            crear_tarjeta_kpi_desglose('kpi-est-fte', 'kpi-est-fte-bam', 'FTEs Totales (Hoy)')
        ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '16px'}),
        html.Div(
            dash_table.DataTable(
                id='tabla-estudio', 
                columns=cols_activas, 
                fixed_columns={'headers': True, 'data': len(fijas_activas)},
                style_table={'overflowX': 'auto', 'width': '100%', 'minWidth': '100%', 'maxWidth': '100%'},
                cell_selectable=False,
                **config_tabla
            ), style={**ESTILO_TARJETA, 'marginBottom': '8px'}
        ),
        
        # --- TABLA: ESTUDIO PREVIO ---
        header_seccion("documento", "Preliminar", "Estudio previo", tono='previo'),
        html.Div([
            crear_tarjeta_kpi('kpi-prev-pres', 'Presupuesto'),
            crear_tarjeta_kpi_desglose('kpi-prev-hor', 'kpi-prev-hor-bam', 'Total Horas Licitación'),
            crear_tarjeta_kpi_desglose('kpi-prev-fte', 'kpi-prev-fte-bam', 'FTEs Totales (Hoy)')
        ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '16px'}),
        html.Div(
            dash_table.DataTable(
                id='tabla-previo', 
                columns=cols_activas, 
                fixed_columns={'headers': True, 'data': len(fijas_activas)},
                style_table={'overflowX': 'auto', 'width': '100%', 'minWidth': '100%', 'maxWidth': '100%'},
                cell_selectable=False,
                **config_tabla
            ), style=ESTILO_TARJETA
        )
    ], style={'paddingBottom': '40px'})


def register_callbacks(app):

    @app.callback(
        [Output('drop-filtro-tec-cron', 'options'),
         Output('drop-filtro-tec-cron', 'value')],
        Input('drop-filtro-rol-cron', 'value'),
        State('drop-filtro-tec-cron', 'value')
    )
    def encadenar_filtros_cronograma(roles_seleccionados, tecnicos_actuales):
        _, _, df_eq, _, _ = obtener_datos_eficiente(force_reload=False)
        if df_eq.empty: return [], dash.no_update
            
        df_filtrado = df_eq.copy()
        if roles_seleccionados:
            if isinstance(roles_seleccionados, str): roles_seleccionados = [roles_seleccionados]
            if 'Perfil Técnico' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['Perfil Técnico'].isin(roles_seleccionados)]

        # --- APLICAMOS ALIAS TAMBIÉN AL RECARGAR EL FILTRO SECUNDARIO ---
        col_id = 'ID_Tecnico' if 'ID_Tecnico' in df_filtrado.columns else ('ID_Técnico' if 'ID_Técnico' in df_filtrado.columns else 'Nombre')
        col_nom = 'Nombre' if 'Nombre' in df_filtrado.columns else df_filtrado.columns[0]
        
        nuevas_opciones = []
        for _, row in df_filtrado.iterrows():
            nr = str(row.get(col_nom, '')).strip()
            al = str(row.get(col_id, '')).strip()
            if not nr or nr == 'nan': continue
            if not al or al == 'nan': al = nr
            nuevas_opciones.append({'label': al, 'value': nr})

        nombres_validos = [opc['value'] for opc in nuevas_opciones]
        
        nuevos_valores_tecnicos = tecnicos_actuales
        if tecnicos_actuales:
            if isinstance(tecnicos_actuales, str): tecnicos_actuales = [tecnicos_actuales]
            nuevos_valores_tecnicos = [t for t in tecnicos_actuales if t in nombres_validos]
            if not nuevos_valores_tecnicos: nuevos_valores_tecnicos = None
                
        return nuevas_opciones, nuevos_valores_tecnicos


    @app.callback(
        [Output('kpi-global-pres', 'children'),
         Output('kpi-global-hor', 'children'),
         Output('kpi-global-hor-bam', 'children'),
         Output('kpi-global-fte', 'children'),
         Output('kpi-global-fte-bam', 'children'),
         
         Output('tabla-no-asignadas', 'data'), 
         Output('kpi-pend-pres', 'children'),
         Output('kpi-pend-hor', 'children'),
         Output('kpi-pend-hor-bam', 'children'),
         Output('kpi-pend-fte', 'children'),
         Output('kpi-pend-fte-bam', 'children'),
         
         Output('tabla-estudio', 'data'), 
         Output('kpi-est-pres', 'children'),
         Output('kpi-est-hor', 'children'),
         Output('kpi-est-hor-bam', 'children'),
         Output('kpi-est-fte', 'children'),
         Output('kpi-est-fte-bam', 'children'),
         
         Output('tabla-previo', 'data'),
         Output('kpi-prev-pres', 'children'),
         Output('kpi-prev-hor', 'children'),
         Output('kpi-prev-hor-bam', 'children'),
         Output('kpi-prev-fte', 'children'),
         Output('kpi-prev-fte-bam', 'children')],
         
        [Input('filtro-codigo', 'value'), 
         Input('filtro-nombre', 'value'),
         Input('drop-filtro-nivel-cron', 'value'),
         Input('drop-filtro-rol-cron', 'value'),
         Input('drop-filtro-tec-cron', 'value')]
    )
    def filtrar_cronograma(cod, nom, niveles_seleccionados, roles_seleccionados, tecnicos_seleccionados):
        if cod and isinstance(cod, str): cod = [cod]
        if nom and isinstance(nom, str): nom = [nom]
        if tecnicos_seleccionados and isinstance(tecnicos_seleccionados, str): tecnicos_seleccionados = [tecnicos_seleccionados]
        if roles_seleccionados and isinstance(roles_seleccionados, str): roles_seleccionados = [roles_seleccionados]
        if niveles_seleccionados and isinstance(niveles_seleccionados, str): niveles_seleccionados = [niveles_seleccionados]

        # Consumo optimizado de RAM
        _, df_cronograma, df_eq, _, _ = obtener_datos_eficiente(force_reload=False)
        df_maestro, col_calendario = procesar_cronograma(df_cronograma)
        
        # Tuple extendido (23 devoluciones)
        vacio = (
            "0 €", "0 h", "0 h", "0.00", "0.00",
            [], "0 €", "0 h", "0 h", "0.00", "0.00", 
            [], "0 €", "0 h", "0 h", "0.00", "0.00", 
            [], "0 €", "0 h", "0 h", "0.00", "0.00"
        )
        if df_maestro.empty: return vacio
        
        # --- LIMPIEZA VISUAL DE FECHAS APROVECHANDO LOS DATETIMES YA PARSEADOS ---
        if 'Creacion_dt' in df_maestro.columns:
            df_maestro['Fecha de Creación'] = df_maestro['Creacion_dt'].dt.strftime('%Y-%m-%d').fillna("")
        if 'Fin_dt' in df_maestro.columns:
            df_maestro['Fecha de Fin'] = df_maestro['Fin_dt'].dt.strftime('%Y-%m-%d').fillna("")
        
        hoy = pd.Timestamp(datetime.date.today())
        if 'Fin_dt' in df_maestro.columns:
            # Ahora Fin_dt es fiable y cruzable matemáticamente con hoy
            mask_fecha = df_maestro['Fin_dt'].isna() | (df_maestro['Fin_dt'] >= hoy)
            df_maestro = df_maestro[mask_fecha]

        if cod: 
            df_maestro = df_maestro[df_maestro['Código de Licitación'].astype(str).isin(cod)]
        if nom: 
            df_maestro = df_maestro[df_maestro['Nombre de la Licitación'].astype(str).isin(nom)]

        if niveles_seleccionados and 'Nivel' in df_maestro.columns:
            df_maestro = df_maestro[df_maestro['Nivel'].astype(str).isin(niveles_seleccionados)]
            
        target_tecnicos = None
        if tecnicos_seleccionados:
            target_tecnicos = tecnicos_seleccionados
        elif roles_seleccionados and not df_eq.empty and 'Perfil Técnico' in df_eq.columns:
            target_tecnicos = df_eq[df_eq['Perfil Técnico'].isin(roles_seleccionados)]['Nombre'].dropna().tolist()

        if target_tecnicos is not None:
            cols_to_check = [c for c in ['Técnico 1', 'Técnico 2', 'Técnico 3', 'BAM'] if c in df_maestro.columns]
            if cols_to_check:
                mask_tec = pd.Series(False, index=df_maestro.index)
                for c in cols_to_check:
                    mask_tec = mask_tec | df_maestro[c].isin(target_tecnicos)
                df_maestro = df_maestro[mask_tec]

        if "Horas de Licitación" in df_maestro.columns:
            df_maestro = df_maestro.rename(columns={"Horas de Licitación": "Horas"})
        if "Horas Licitación BAM" in df_maestro.columns:
            df_maestro = df_maestro.rename(columns={"Horas Licitación BAM": "Horas BAM"})

        for c in ['Técnico 1', 'Técnico 2', 'Técnico 3', 'BAM', 'Nivel', 'Horas', 'Horas BAM']:
            if c not in df_maestro.columns:
                df_maestro[c] = ""

        if 'Etapa' not in df_maestro.columns:
            df_maestro['Etapa'] = ""
        df_maestro['Etapa_Norm'] = df_maestro['Etapa'].astype(str).str.strip().str.lower()

        columnas_tecnicos = ['Técnico 1', 'Técnico 2', 'Técnico 3']
        df_temp = df_maestro[columnas_tecnicos].astype(str)
        mask_sin_tecnicos = df_temp.apply(lambda col: col.str.strip().str.lower().isin(['nan', 'none', '', '<na>'])).all(axis=1)

        mask_pendiente = df_maestro['Etapa_Norm'].str.contains('pendiente', na=False) | mask_sin_tecnicos
        df_no_asignadas = df_maestro[mask_pendiente].copy()
        
        df_resto = df_maestro[~mask_pendiente]
        df_estudio = df_resto[df_resto['Etapa_Norm'].str.contains('en estudio', na=False)].copy()
        df_previo = df_resto[df_resto['Etapa_Norm'].str.contains('estudio previo', na=False)].copy()
        
        # Consolidado para la Visión Global
        df_global = pd.concat([df_no_asignadas, df_estudio, df_previo], ignore_index=True)

        def calcular_kpis(df):
            if df.empty: return "0 €", "0 h", "0 h", "0.00", "0.00"
            
            def limpiar_numero(val):
                if pd.isna(val) or val == "": 
                    return 0
                if isinstance(val, (int, float)): 
                    return float(val)
                
                val_str = str(val).upper().replace('€', '').replace('EUR', '').replace('H', '').replace(' ', '').strip()
                if not val_str: 
                    return 0
                    
                if ',' in val_str:
                    val_str = val_str.replace('.', '').replace(',', '.')
                elif '.' in val_str:
                    if val_str.count('.') > 1:
                        val_str = val_str.replace('.', '')
                    else:
                        partes = val_str.split('.')
                        if len(partes[1]) == 3:
                            val_str = val_str.replace('.', '')
                try:
                    return float(val_str)
                except:
                    return 0

            presupuesto = df['Presupuesto'].apply(limpiar_numero).sum() if 'Presupuesto' in df.columns else 0
            
            # Arrays de Horas para cálculos proporcionales
            horas_tec_arr = df['Horas'].apply(limpiar_numero) if 'Horas' in df.columns else pd.Series([0.0]*len(df))
            horas_bam_arr = df['Horas BAM'].apply(limpiar_numero) if 'Horas BAM' in df.columns else pd.Series([0.0]*len(df))
            
            horas = horas_tec_arr.sum()
            horas_bam = horas_bam_arr.sum()
            
            hoy_fecha = datetime.date.today()
            meses_abrev = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            col_hoy = f"{hoy_fecha.day} {meses_abrev[hoy_fecha.month - 1]}"
            
            # FTE Total por fila (Día actual)
            fte_total_hoy = pd.to_numeric(df[col_hoy], errors='coerce').fillna(0) if col_hoy in df.columns else pd.Series([0.0]*len(df))
            
            horas_totales_arr = horas_tec_arr + horas_bam_arr
            
            # REPARTO PROPORCIONAL DE FTE:
            fte_tec_arr = np.where(horas_totales_arr > 0, fte_total_hoy * (horas_tec_arr / horas_totales_arr), fte_total_hoy)
            fte_bam_arr = np.where(horas_totales_arr > 0, fte_total_hoy * (horas_bam_arr / horas_totales_arr), 0.0)

            return (
                f"{presupuesto:,.0f} €".replace(",", "."), 
                f"{horas:,.0f} h".replace(",", "."), 
                f"{horas_bam:,.0f} h".replace(",", "."), 
                f"{fte_tec_arr.sum():.2f}", 
                f"{fte_bam_arr.sum():.2f}"
            )

        # Ejecutamos el cálculo de KPIs (ANTES del reemplazo de Alias para evitar alterar lógica)
        kg_pres, kg_hor, kg_hor_bam, kg_fte, kg_fte_bam = calcular_kpis(df_global)
        kp_pres, kp_hor, kp_hor_bam, kp_fte, kp_fte_bam = calcular_kpis(df_no_asignadas)
        ke_pres, ke_hor, ke_hor_bam, ke_fte, ke_fte_bam = calcular_kpis(df_estudio)
        kpr_pres, kpr_hor, kpr_hor_bam, kpr_fte, kpr_fte_bam = calcular_kpis(df_previo)

        # --- REEMPLAZO DE NOMBRES REALES POR ALIAS EN LAS TABLAS FINALES ---
        dict_alias = {}
        if not df_eq.empty:
            col_id = 'ID_Tecnico' if 'ID_Tecnico' in df_eq.columns else ('ID_Técnico' if 'ID_Técnico' in df_eq.columns else 'Nombre')
            col_nom = 'Nombre' if 'Nombre' in df_eq.columns else df_eq.columns[0]
            for _, r in df_eq.iterrows():
                nr = str(r.get(col_nom, '')).strip()
                al = str(r.get(col_id, '')).strip()
                if not nr or nr == 'nan': continue
                if not al or al == 'nan': al = nr
                dict_alias[nr] = al

        columnas_personas = ['BAM', 'Técnico 1', 'Técnico 2', 'Técnico 3']
        for df_target in [df_no_asignadas, df_estudio, df_previo]:
            if not df_target.empty:
                for col in columnas_personas:
                    if col in df_target.columns:
                        df_target[col] = df_target[col].map(lambda x: dict_alias.get(str(x).strip(), str(x).strip()) if pd.notna(x) and str(x).strip() != "" else "")

        def limpiar_y_totalizar(df):
            if df.empty: return df
            total = {col: "" for col in df.columns}
            total['Código de Licitación'] = "TOTAL FTES"
            
            df_clean = df.copy()
            for col in col_calendario: 
                val_total = round(pd.to_numeric(df_clean[col], errors='coerce').fillna(0).sum(), 2)
                total[col] = val_total if val_total > 0 else ""
                
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
                df_clean[col] = df_clean[col].apply(lambda x: x if x > 0 else "")
                
            return pd.concat([df_clean, pd.DataFrame([total])], ignore_index=True)
            
        return (
            kg_pres, kg_hor, kg_hor_bam, kg_fte, kg_fte_bam,
            limpiar_y_totalizar(df_no_asignadas).to_dict('records'), kp_pres, kp_hor, kp_hor_bam, kp_fte, kp_fte_bam,
            limpiar_y_totalizar(df_estudio).to_dict('records'), ke_pres, ke_hor, ke_hor_bam, ke_fte, ke_fte_bam,
            limpiar_y_totalizar(df_previo).to_dict('records'), kpr_pres, kpr_hor, kpr_hor_bam, kpr_fte, kpr_fte_bam
        )