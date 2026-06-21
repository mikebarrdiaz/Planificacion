from dash import html, dcc, dash_table, Input, Output, State, ctx
import dash
import pandas as pd
from utils.data_manager import obtener_datos_eficiente, guardar_sqlite_centralizado, parsear_fecha_es
from datetime import datetime

# Textos exactos confirmados
COL_CODIGO = 'Código de Licitación'
COL_NOMBRE = 'Nombre de la Licitación'

def layout(rol='lector'):
    # Pedimos los datos al Data Manager
    df_bbdd, df_cron, df_eq, df_vac, error_sistema = obtener_datos_eficiente(force_reload=False)
    
    # --- 1. EXTRACCIÓN CON ALIAS (LABEL) Y DATO REAL (VALUE) ---
    opciones_equipo = []
    opciones_bam = []
    dict_alias = {} # Diccionario para traducir nombres reales a Alias en la tabla
    
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
                
            # Rellenamos el diccionario de traducción para la tabla
            dict_alias[nombre_real] = alias_visual
                
            diccionario_opcion = {'label': alias_visual, 'value': nombre_real}
            perfil = str(row.get('Perfil Técnico', '')).strip()
            
            if perfil == 'Bidding Area Manager':
                opciones_bam.append(diccionario_opcion)
            elif perfil == 'Bidding Technician':
                opciones_equipo.append(diccionario_opcion)
            else:
                opciones_equipo.append(diccionario_opcion)
                opciones_bam.append(diccionario_opcion)

    opciones_etapa_lista = ['Pendiente Asignar', 'En estudio', 'Estudio previo']
    opciones_etapa_drop = [{'label': i, 'value': i} for i in opciones_etapa_lista]

    opciones_codigos_activos = []
    opciones_nombres_activos = []

    if not df_cron.empty:
        df_cron_tabla = df_cron.copy()
        if COL_CODIGO in df_cron_tabla.columns:
            opciones_codigos_activos = [{'label': f"{row[COL_CODIGO]} - {row.get(COL_NOMBRE, '')}", 'value': str(row[COL_CODIGO])} for _, row in df_cron_tabla.iterrows() if pd.notna(row.get(COL_CODIGO))]
        if COL_NOMBRE in df_cron_tabla.columns:
            opciones_nombres_activos = [{'label': str(n), 'value': str(n)} for n in df_cron_tabla[COL_NOMBRE].dropna().unique()]

        # --- APLICACIÓN DEL MOTOR ROBUSTO DE FECHAS EN LA TABLA ---
        if 'Fecha de Creación' in df_cron_tabla.columns:
            df_cron_tabla['Fecha de Creación'] = df_cron_tabla['Fecha de Creación'].apply(parsear_fecha_es).dt.strftime('%Y-%m-%d').fillna("")
        if 'Fecha de Fin' in df_cron_tabla.columns:
            df_cron_tabla['Fecha de Fin'] = df_cron_tabla['Fecha de Fin'].apply(parsear_fecha_es).dt.strftime('%Y-%m-%d').fillna("")
        
        # --- SUSTITUCIÓN DE NOMBRES REALES POR ALIAS EN LA TABLA VISUAL ---
        for col in ['BAM', 'Técnico 1', 'Técnico 2', 'Técnico 3']:
            if col in df_cron_tabla.columns:
                df_cron_tabla[col] = df_cron_tabla[col].map(lambda x: dict_alias.get(str(x).strip(), str(x).strip()) if pd.notna(x) and str(x).strip() != "" else "")

        df_cron_tabla = df_cron_tabla.fillna("")
        datos_diccionario = df_cron_tabla.to_dict('records')
    else:
        datos_diccionario = []


    # ==========================================
    # CONSTRUCCIÓN DE COMPONENTES DE EDICIÓN
    # ==========================================
    # Siempre los construimos para que Dash encuentre sus IDs y no haya errores de Callback
    panel_formulario = html.Details([
        html.Summary([
            html.Span("Formulario de Alta y Edición de Licitaciones", style={'textTransform': 'uppercase', 'fontWeight': 'bold', 'color': 'var(--accent)', 'fontSize': '11px'}),
            html.Span(" (Click para expandir/colapsar)", style={'fontSize': '9px', 'color': 'var(--secondary)'})
        ], style={'cursor': 'pointer', 'padding': '12px 16px', 'backgroundColor': '#FFFFFF', 'border': '1px solid var(--card-divider)', 'borderRadius': '6px', 'marginBottom': '16px', 'userSelect': 'none'}),
        
        html.Div([
            html.Div([
                html.Span("1. MODO DE OPERACIÓN", style={'color': '#FFFFFF', 'backgroundColor': 'var(--text-border)', 'padding': '8px 16px', 'fontSize': '9px', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'borderRadius': '6px', 'marginRight': '16px'}),
                dcc.Dropdown(id='drop-editar-lic', options=opciones_codigos_activos, placeholder="Cargar licitación activa para editar...", style={'width': '350px'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '24px'}),
            
            html.Div([
                html.Div([
                    html.Label("Búsqueda en BBDD (Alta Nueva)", className="etiqueta-dato"),
                    dcc.Input(
                        id='input-act-lic', type='text', placeholder="Introducir código/nombre nuevo...",
                        list='sugerencias-licitaciones', className="input-filtro", style={'width': '100%'}
                    ),
                    html.Datalist(id='sugerencias-licitaciones', children=[])
                ], className="serveo-input-wrapper", style={'flex': '2'}),
                
                html.Div([
                    html.Label("Asignar Etapa (Obligatorio)", className="etiqueta-dato", style={'color': 'var(--accent)'}),
                    dcc.Dropdown(id='drop-act-etapa', options=opciones_etapa_drop, placeholder="Selecciona etapa...") 
                ], className="serveo-input-wrapper", style={'flex': '1'})
            ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '24px'}),

            html.Div([
                html.Div([
                    html.Label("Fecha de Creación", className="etiqueta-dato"),
                    dcc.DatePickerSingle(id='date-act-fcreacion', display_format='YYYY-MM-DD', placeholder='Selecciona fecha...', style={'width': '100%'})
                ], className="serveo-input-wrapper", style={'flex': '1'}),
                
                html.Div([
                    html.Label("Fecha de Fin (Vencimiento)", className="etiqueta-dato"),
                    dcc.DatePickerSingle(id='date-act-ffin', display_format='YYYY-MM-DD', placeholder='Selecciona fecha...', style={'width': '100%'})
                ], className="serveo-input-wrapper", style={'flex': '1'}),
                
                html.Div([
                    html.Label("Horas Estimadas (Técnicos)", className="etiqueta-dato"),
                    dcc.Input(id='input-act-horas', type='number', min=0, placeholder='Horas operativas...', className="input-filtro")
                ], className="serveo-input-wrapper", style={'flex': '1'}),
                
                html.Div([
                    html.Label("Horas Estimadas (BAM)", className="etiqueta-dato", style={'color': 'var(--accent)'}),
                    dcc.Input(id='input-act-horas-bam', type='number', min=0, placeholder='Horas revisión...', className="input-filtro")
                ], className="serveo-input-wrapper", style={'flex': '1'}),
            ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '24px'}),

            html.Div([
                html.Div([
                    html.Label("Manager (BAM)", className="etiqueta-dato"),
                    dcc.Dropdown(id='drop-act-bam', options=opciones_bam, clearable=True)
                ], className="serveo-input-wrapper", style={'flex': '1'}),
                
                html.Div([
                    html.Label("Técnico 1", className="etiqueta-dato"),
                    dcc.Dropdown(id='drop-act-t1', options=opciones_equipo, clearable=True)
                ], className="serveo-input-wrapper", style={'flex': '1'}),
                
                html.Div([
                    html.Label("Técnico 2", className="etiqueta-dato"),
                    dcc.Dropdown(id='drop-act-t2', options=opciones_equipo, clearable=True)
                ], className="serveo-input-wrapper", style={'flex': '1'}),
                
                html.Div([
                    html.Label("Técnico 3", className="etiqueta-dato"),
                    dcc.Dropdown(id='drop-act-t3', options=opciones_equipo, clearable=True)
                ], className="serveo-input-wrapper", style={'flex': '1'})
            ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '24px'}),

            html.Div([
                html.Div([
                    html.Label("Personas Involucradas (Externos/Otros)", className="etiqueta-dato"),
                    dcc.Input(id='input-involucrados', type='text', placeholder='Nombres separados por comas...', className="input-filtro", style={'width': '100%'})
                ], className="serveo-input-wrapper", style={'flex': '1'}),

                html.Div([
                    html.Label("Comentario / Notas (Opcional)", className="etiqueta-dato"),
                    dcc.Input(id='input-act-comentario', type='text', placeholder='Añade un comentario...', className="input-filtro", style={'width': '100%'})
                ], className="serveo-input-wrapper", style={'flex': '1'}),
                
                html.Button('💾 Guardar / Activar', id='btn-activar', n_clicks=0, className="btn-serveo-primario", style={'alignSelf': 'flex-end', 'height': '32px', 'padding': '0 24px'})
            ], style={'display': 'flex', 'gap': '16px'}),

            html.Div([
                html.Label("Informe Generado (Copiar para Email)", className="etiqueta-dato", style={'color': 'var(--accent)'}),
                dcc.Textarea(id='area-informe', readOnly=True, style={
                    'width': '100%', 'height': '140px', 'fontFamily': 'Outfit', 'fontSize': '12px', 
                    'padding': '12px', 'borderRadius': '6px', 'border': '1px solid var(--card-divider)', 
                    'backgroundColor': '#FAFAFA', 'color': 'var(--text-border)'
                })
            ], style={'marginTop': '24px'})

        ], className="serveo-panel-accion", style={'padding': '24px', 'backgroundColor': '#FAFAFA', 'border': '1px solid var(--card-divider)', 'borderRadius': '6px', 'marginBottom': '24px'})
    ], open=False)
    
    boton_eliminar_componente = html.Button('🗑️ Eliminar Seleccionados', id='btn-eliminar', n_clicks=0, className="btn-serveo-negativo")

    # ==========================================
    # LÓGICA CONDICIONAL DE VISIBILIDAD DE ROLES
    # ==========================================
    estilo_edicion = {'display': 'block'} if rol == 'editor' else {'display': 'none'}
    estilo_eliminar = {'display': 'flex', 'gap': '16px', 'justifyContent': 'flex-start'} if rol == 'editor' else {'display': 'none'}

    return html.Div([
        html.H3("Activación y Asignación de Licitaciones", className="serveo-titulo-pagina"),
        
        # Inyectamos el panel y el botón de eliminar envueltos en sus divisores de estilo
        html.Div(panel_formulario, style=estilo_edicion),
        html.Div(error_sistema, id='msj-interaccion', style={'marginBottom': '24px', 'fontWeight': 'bold', 'fontFamily': 'var(--font-family)', 'fontSize': '13px', 'color': 'var(--semantic-negative)'}),

        html.H3("Control del Funnel Operativo", className="serveo-titulo-seccion"),
        
        html.Div([
            html.Div([
                html.Label("Código Licitación", className="etiqueta-dato"),
                dcc.Dropdown(id='filtro-asig-cod', options=[{'label': c['value'], 'value': c['value']} for c in opciones_codigos_activos], placeholder="Todos los códigos", multi=True)
            ], className="serveo-input-wrapper", style={'flex': '1', 'minWidth': '200px'}),
            
            html.Div([
                html.Label("Nombre Licitación", className="etiqueta-dato"),
                dcc.Dropdown(id='filtro-asig-nom', options=opciones_nombres_activos, placeholder="Todos los nombres", multi=True)
            ], className="serveo-input-wrapper", style={'flex': '1.5', 'minWidth': '250px'}),
            
            html.Div([
                html.Label("Etapa", className="etiqueta-dato"),
                dcc.Dropdown(id='filtro-asig-etapa', options=opciones_etapa_drop, placeholder="Todas", multi=True)
            ], className="serveo-input-wrapper", style={'flex': '1', 'minWidth': '180px'}),
            
            html.Div([
                html.Label("BAM", className="etiqueta-dato"),
                dcc.Dropdown(id='filtro-asig-bam', options=opciones_bam, placeholder="Todos", multi=True)
            ], className="serveo-input-wrapper", style={'flex': '1', 'minWidth': '150px'}),
            
            html.Div([
                html.Label("Técnico(s)", className="etiqueta-dato"),
                dcc.Dropdown(id='filtro-asig-tec', options=opciones_equipo, placeholder="Todos", multi=True)
            ], className="serveo-input-wrapper", style={'flex': '1', 'minWidth': '150px'})
        ], className="contenedor-filtros", style={'backgroundColor': 'var(--card-divider)', 'alignItems': 'flex-end', 'padding': '16px 24px', 'marginBottom': '16px', 'flexWrap': 'wrap', 'gap': '16px', 'borderRadius': '6px'}),

        dash_table.DataTable(
            id='tabla-funnel-activo',
            columns=[
                {"name": "Código", "id": COL_CODIGO, "editable": False},
                {"name": "Nombre Licitación", "id": COL_NOMBRE, "editable": False},
                {"name": "Cliente", "id": "Cliente", "editable": False},
                {"name": "F. Creación", "id": "Fecha de Creación", "editable": False},
                {"name": "F. Fin", "id": "Fecha de Fin", "editable": False},
                {"name": "Horas Tec", "id": "Horas de Licitación", "editable": False},
                {"name": "Horas BAM", "id": "Horas de Licitación BAM", "editable": False},
                {"name": "Etapa", "id": "Etapa", "editable": False},
                {"name": "BAM", "id": "BAM", "editable": False}, 
                {"name": "Técnico 1", "id": "Técnico 1", "editable": False},
                {"name": "Técnico 2", "id": "Técnico 2", "editable": False},
                {"name": "Técnico 3", "id": "Técnico 3", "editable": False},
                {"name": "Involucrados", "id": "Personas involucradas", "editable": False}, 
                {"name": "Comentario", "id": "Comentario", "editable": False}
            ],
            data=datos_diccionario,
            row_selectable="multi",
            selected_rows=[],
            
            style_table={
                'width': '100%',
                'overflowX': 'auto',
                'borderRadius': '6px', 
                'border': '1px solid var(--card-divider)', 
                'marginBottom': '24px'
            },
            style_cell={
                'backgroundColor': '#FFFFFF', 
                'color': 'var(--text-border)', 
                'borderBottom': '1px solid var(--card-divider)', 
                'padding': '12px 16px', 
                'textAlign': 'left', 
                'fontFamily': 'var(--font-family)', 
                'fontSize': '11px',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'whiteSpace': 'nowrap',
                'maxWidth': '0'
            },
            style_cell_conditional=[
                {'if': {'column_id': 'Cliente'}, 'width': '180px', 'minWidth': '180px'},
                {'if': {'column_id': COL_CODIGO}, 'width': '120px', 'minWidth': '120px'},
                {'if': {'column_id': COL_NOMBRE}, 'width': '250px', 'minWidth': '250px'},
                {'if': {'column_id': 'Horas de Licitación'}, 'width': '90px', 'minWidth': '90px', 'textAlign': 'center'},
                {'if': {'column_id': 'Horas de Licitación BAM'}, 'width': '90px', 'minWidth': '90px', 'textAlign': 'center'},
                {'if': {'column_id': 'Etapa'}, 'width': '180px', 'minWidth': '180px'},
                {'if': {'column_id': 'BAM'}, 'width': '110px', 'minWidth': '110px'},
                {'if': {'column_id': 'Técnico 1'}, 'width': '110px', 'minWidth': '110px'},
                {'if': {'column_id': 'Técnico 2'}, 'width': '110px', 'minWidth': '110px'},
                {'if': {'column_id': 'Técnico 3'}, 'width': '110px', 'minWidth': '110px'},
                {'if': {'column_id': 'Personas involucradas'}, 'width': '200px', 'minWidth': '200px'},
                {'if': {'column_id': 'Comentario'}, 'width': '300px', 'minWidth': '300px'},
                {'if': {'column_id': 'Fecha de Creación'}, 'width': '130px', 'minWidth': '130px'},
                {'if': {'column_id': 'Fecha de Fin'}, 'width': '130px', 'minWidth': '130px'}
            ],
            
            style_header={
                'backgroundColor': '#FFFFFF', 
                'color': 'var(--accent)', 
                'fontWeight': 'bold', 
                'borderBottom': '2px solid var(--text-border)', 
                'fontFamily': 'var(--font-family)', 
                'fontSize': '9px', 
                'textTransform': 'uppercase', 
                'textAlign': 'left'
            },
            style_header_conditional=[
                {'if': {'column_id': 'Horas de Licitación'}, 'textAlign': 'center'},
                {'if': {'column_id': 'Horas de Licitación BAM'}, 'textAlign': 'center'}
            ],
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#FAFAFA'
                },
                {
                    'if': {'state': 'selected'},
                    'backgroundColor': 'rgba(255, 78, 0, 0.1) !important',
                    'border': '1px solid var(--accent)'
                },
                {
                    'if': {'filter_query': '{Técnico 1} is blank && {Técnico 2} is blank && {Técnico 3} is blank && {BAM} is blank'}, 
                    'color': 'var(--semantic-negative)', 
                    'fontWeight': 'bold'
                }
            ],
            
            tooltip_data=[
                {
                    column: {'value': f"{str(value)}", 'type': 'markdown'} 
                    for column, value in row.items() if column in [COL_NOMBRE, 'Cliente', 'Comentario', 'Personas involucradas']
                } for row in datos_diccionario
            ],
            tooltip_delay=100,      
            tooltip_duration=None,   
            css=[
                {
                    'selector': 'td.dash-select-cell, th.dash-select-header, td[data-dash-column=""], th[data-dash-column=""]',
                    'rule': '''
                        width: 60px !important;
                        min-width: 60px !important;
                        max-width: 60px !important;
                        text-align: center !important;
                        padding: 0 !important;
                    '''
                },
                {
                    'selector': 'td.dash-select-cell input, th.dash-select-header input',
                    'rule': '''
                        margin: 0 auto !important;
                        display: block !important;
                        cursor: pointer !important;
                        transform: scale(1.1) !important;
                    '''
                },
                {
                    'selector': '.dash-table-tooltip',
                    'rule': '''
                        background-color: #474751 !important;
                        color: #FFFFFF !important;
                        border: 1px solid #474751 !important;
                        border-radius: 6px !important;
                        padding: 8px 12px !important;
                        font-family: 'Outfit', sans-serif !important;
                        font-size: 11px !important;
                        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.15) !important;
                        opacity: 1 !important;
                    '''
                }
            ],
            page_action='native',
            page_size=25,
        ),

        html.Div(boton_eliminar_componente, style=estilo_eliminar) # Botón oculto si es lector

    ], style={'paddingBottom': '40px'})

def register_callbacks(app):

    @app.callback(
        Output('sugerencias-licitaciones', 'children'),
        [Input('input-act-lic', 'value'),
         Input('tabla-funnel-activo', 'data')] 
    )
    def buscar_en_bbdd(search_value, tabla_data):
        df_bbdd, df_cron, _, _, _ = obtener_datos_eficiente(force_reload=False)
        if df_bbdd.empty or COL_CODIGO not in df_bbdd.columns: 
            return []

        codigos_activos = df_cron[COL_CODIGO].dropna().tolist()
        df_disp = df_bbdd[~df_bbdd[COL_CODIGO].isin(codigos_activos)]

        if search_value:
            mask = (df_disp[COL_CODIGO].astype(str).str.contains(search_value, case=False, na=False, regex=False)) | \
                   (df_disp[COL_NOMBRE].astype(str).str.contains(search_value, case=False, na=False, regex=False))
            df_disp = df_disp[mask]

        return [html.Option(value=f"{row[COL_CODIGO]} - {row.get(COL_NOMBRE, '')}") for _, row in df_disp.head(40).iterrows()]

    @app.callback(
        [Output('input-act-lic', 'value', allow_duplicate=True),
         Output('drop-editar-lic', 'value', allow_duplicate=True),
         Output('drop-act-etapa', 'value', allow_duplicate=True),
         Output('date-act-fcreacion', 'date', allow_duplicate=True),
         Output('date-act-ffin', 'date', allow_duplicate=True),
         Output('input-act-horas', 'value', allow_duplicate=True),
         Output('input-act-horas-bam', 'value', allow_duplicate=True),
         Output('drop-act-bam', 'value', allow_duplicate=True),
         Output('drop-act-t1', 'value', allow_duplicate=True),
         Output('drop-act-t2', 'value', allow_duplicate=True),
         Output('drop-act-t3', 'value', allow_duplicate=True),
         Output('input-involucrados', 'value', allow_duplicate=True),
         Output('input-act-comentario', 'value', allow_duplicate=True),
         Output('area-informe', 'value', allow_duplicate=True)], 
        [Input('input-act-lic', 'value'),
         Input('drop-editar-lic', 'value')],
        prevent_initial_call=True
    )
    def poblar_formulario(val_nuevo, val_edit):
        trigger = ctx.triggered_id
        if not trigger:
            raise dash.exceptions.PreventUpdate

        if not val_edit and not val_nuevo:
            return ("", None, None, None, None, "", "", "", "", "", "", "", "", "")

        df_bbdd, df_cron, _, _, _ = obtener_datos_eficiente(force_reload=False)
        ret = [dash.no_update] * 14

        if trigger == 'drop-editar-lic' and val_edit:
            fila = df_cron[df_cron[COL_CODIGO] == val_edit]
            if not fila.empty:
                r = fila.iloc[0]
                
                # Parseo robusto para la inyección de formulario
                fc_limpia = parsear_fecha_es(r.get('Fecha de Creación'))
                ff_limpia = parsear_fecha_es(r.get('Fecha de Fin'))
                
                ret[0] = ""
                ret[1] = val_edit
                ret[2] = r.get('Etapa', '')
                ret[3] = fc_limpia.strftime('%Y-%m-%d') if pd.notna(fc_limpia) else None
                ret[4] = ff_limpia.strftime('%Y-%m-%d') if pd.notna(ff_limpia) else None
                ret[5] = r.get('Horas de Licitación', '')
                ret[6] = r.get('Horas de Licitación BAM', '')
                ret[7] = r.get('BAM', '')
                ret[8] = r.get('Técnico 1', '')
                ret[9] = r.get('Técnico 2', '')
                ret[10] = r.get('Técnico 3', '')
                ret[11] = r.get('Personas involucradas', '')
                ret[12] = r.get('Comentario', '')
                
                tecnicos = [t for t in [ret[8], ret[9], ret[10]] if t and t.lower() != 'nan']
                ret[13] = (
                    f"📌 ACTUALIZACIÓN DE ASIGNACIÓN (SERVEO)\n"
                    f"--------------------------------------------------\n"
                    f"Código: {val_edit}\n"
                    f"Nombre: {str(r.get(COL_NOMBRE, 'Sin Nombre'))}\n"
                    f"Cliente: {str(r.get('Cliente', 'Sin Cliente'))}\n\n"
                    f"📋 ESTATUS OPERATIVO:\n"
                    f"Etapa Actual: {ret[2] if ret[2] else 'Pendiente'}\n"
                    f"BAM Responsable: {ret[7] if ret[7] and str(ret[7]).lower() != 'nan' else 'Pendiente'}\n"
                    f"Técnicos: {', '.join(tecnicos) if tecnicos else 'Pendiente'}\n"
                    f"Apoyo/Involucrados: {ret[11] if ret[11] and str(ret[11]).lower() != 'nan' else 'Ninguno'}\n\n"
                    f"⏳ PLANIFICACIÓN TÉCNICA:\n"
                    f"Fechas: {ret[3] if ret[3] else 'TBD'} al {ret[4] if ret[4] else 'TBD'}\n"
                    f"Horas Estimadas: {ret[5] if ret[5] else 0}h (Técnicos) / {ret[6] if ret[6] else 0}h (BAM)\n\n"
                    f"💬 NOTAS ADICIONALES:\n"
                    f"{ret[12] if ret[12] and str(ret[12]).lower() != 'nan' else 'Ninguna'}\n"
                    f"--------------------------------------------------"
                )
            return tuple(ret)

        elif trigger == 'input-act-lic' and val_nuevo:
            if " - " in val_nuevo:
                cod_lic = val_nuevo.split(" - ")[0].strip()
                fila = df_bbdd[df_bbdd[COL_CODIGO] == cod_lic]
                if not fila.empty:
                    r = fila.iloc[0]
                    
                    fc_limpia = parsear_fecha_es(r.get('Fecha de Creación'))
                    ff_limpia = parsear_fecha_es(r.get('Fecha de Fin'))
                    
                    ret[0] = val_nuevo
                    ret[1] = None
                    ret[2] = None
                    ret[3] = fc_limpia.strftime('%Y-%m-%d') if pd.notna(fc_limpia) else None
                    ret[4] = ff_limpia.strftime('%Y-%m-%d') if pd.notna(ff_limpia) else None
                    ret[5] = r.get('Horas de Licitación', '')
                    ret[6] = r.get('Horas de Licitación BAM', '')
                    ret[7], ret[8], ret[9], ret[10], ret[11], ret[12] = "", "", "", "", "", ""
                    
                    ret[13] = (
                        f"📌 NUEVA ASIGNACIÓN (SERVEO)\n"
                        f"--------------------------------------------------\n"
                        f"Código: {cod_lic}\n"
                        f"Nombre: {str(r.get(COL_NOMBRE, 'Sin Nombre'))}\n"
                        f"Cliente: {str(r.get('Cliente', 'Sin Cliente'))}\n\n"
                        f"📋 ESTATUS OPERATIVO:\n"
                        f"Etapa Actual: Pendiente Asignar\n"
                        f"BAM Responsable: Pendiente\n"
                        f"Técnicos: Pendiente\n"
                        f"Apoyo/Involucrados: Ninguno\n\n"
                        f"⏳ PLANIFICACIÓN TÉCNICA:\n"
                        f"Fechas: {ret[3] if ret[3] else 'TBD'} al {ret[4] if ret[4] else 'TBD'}\n"
                        f"Horas Estimadas: {ret[5] if ret[5] else 0}h (Técnicos) / {ret[6] if ret[6] else 0}h (BAM)\n\n"
                        f"💬 NOTAS ADICIONALES:\n"
                        f"Ninguna\n"
                        f"--------------------------------------------------"
                    )
            return tuple(ret)

        return tuple(ret)

    @app.callback(
        [Output('tabla-funnel-activo', 'data'),
         Output('msj-interaccion', 'children'),
         Output('msj-interaccion', 'style'),
         Output('input-act-lic', 'value'),
         Output('drop-editar-lic', 'value'),
         Output('drop-act-etapa', 'value'),
         Output('drop-act-bam', 'value'),
         Output('drop-act-t1', 'value'),
         Output('drop-act-t2', 'value'),
         Output('drop-act-t3', 'value'),
         Output('input-involucrados', 'value'),
         Output('input-act-comentario', 'value'), 
         Output('tabla-funnel-activo', 'selected_rows'),
         Output('filtro-asig-cod', 'options'), 
         Output('filtro-asig-nom', 'options'),
         Output('area-informe', 'value')],
        [Input('btn-activar', 'n_clicks'),
         Input('btn-eliminar', 'n_clicks'),
         Input('filtro-asig-cod', 'value'),
         Input('filtro-asig-nom', 'value'),
         Input('filtro-asig-etapa', 'value'),
         Input('filtro-asig-bam', 'value'),
         Input('filtro-asig-tec', 'value')],
        [State('input-act-lic', 'value'),
         State('drop-editar-lic', 'value'),
         State('drop-act-etapa', 'value'),
         State('drop-act-bam', 'value'),
         State('drop-act-t1', 'value'),
         State('drop-act-t2', 'value'),
         State('drop-act-t3', 'value'),
         State('input-involucrados', 'value'),
         State('date-act-fcreacion', 'date'),
         State('date-act-ffin', 'date'),
         State('input-act-horas', 'value'),
         State('input-act-horas-bam', 'value'), 
         State('input-act-comentario', 'value'), 
         State('tabla-funnel-activo', 'data'),
         State('tabla-funnel-activo', 'selected_rows')]
    )
    def gestor_maestro_funnel(n_activar, n_eliminar, f_cod, f_nom, f_etapa, f_bam, f_tec, 
                              cod_lic_input, edit_lic_input, etapa, bam_val, t1, t2, t3, involucrados_val, high_fcreacion, high_ffin, high_horas, high_horas_bam, comentario_input,
                              tabla_data, filas_seleccionadas):
        trigger = ctx.triggered_id
        if not trigger:
            raise dash.exceptions.PreventUpdate

        df_bbdd, df_cron, df_eq, df_vac, error_sistema = obtener_datos_eficiente(force_reload=False)
        estilo_msg = {'marginBottom': '24px', 'fontWeight': 'bold', 'fontFamily': 'var(--font-family)', 'fontSize': '13px'}
        
        if error_sistema:
            estilo_msg['color'] = 'var(--semantic-negative)'
            return dash.no_update, error_sistema, estilo_msg, *[dash.no_update]*13

        cols_necesarias = [COL_CODIGO, COL_NOMBRE, 'Cliente', 'Fecha de Creación', 'Fecha de Fin', 'Horas de Licitación', 'Horas de Licitación BAM', 'BAM', 'Técnico 1', 'Técnico 2', 'Técnico 3', 'Personas involucradas', 'Etapa', 'Comentario']
        for col in cols_necesarias:
            if col not in df_cron.columns: df_cron[col] = ""

        def depurar_celda(valor):
            if pd.isna(valor) or valor is None or str(valor).strip() == "" or str(valor).strip().lower() == "none":
                return ""
            return str(valor).strip()

        mensaje = ""
        informe_generado = dash.no_update
        exito = False
        es_accion = trigger in ['btn-activar', 'btn-eliminar']

        if es_accion:
            if trigger == 'btn-activar':
                if not cod_lic_input and not edit_lic_input:
                    estilo_msg['color'] = 'var(--semantic-negative)'
                    return dash.no_update, "⚠️ Selecciona una licitación (Nueva o Activa).", estilo_msg, *[dash.no_update]*13

                if not etapa:
                    estilo_msg['color'] = 'var(--semantic-negative)'
                    return dash.no_update, "⚠️ La etapa es un campo obligatorio.", estilo_msg, *[dash.no_update]*13

                cod_lic = str(edit_lic_input).strip() if edit_lic_input else str(cod_lic_input).split(" - ")[0].strip()
                
                t1_val, t2_val, t3_val, bam_clean = depurar_celda(t1), depurar_celda(t2), depurar_celda(t3), depurar_celda(bam_val)
                comentario_val = depurar_celda(comentario_input)
                invol_clean = depurar_celda(involucrados_val)
                hay_tecnicos = bool(t1_val or t2_val or t3_val)
                
                if etapa != 'Pendiente Asignar' and not hay_tecnicos and not bam_clean:
                    estilo_msg['color'] = 'var(--semantic-negative)'
                    return dash.no_update, f"⚠️ La etapa '{etapa}' exige asignar al menos un BAM o un Técnico.", estilo_msg, *[dash.no_update]*13
                
                if etapa == 'Pendiente Asignar': 
                    t1_val = t2_val = t3_val = bam_clean = ""

                is_update = cod_lic in df_cron[COL_CODIGO].astype(str).values
                
                if is_update:
                    mask = df_cron[COL_CODIGO].astype(str) == cod_lic
                    df_cron.loc[mask, 'Etapa'] = etapa
                    df_cron.loc[mask, 'BAM'] = bam_clean
                    df_cron.loc[mask, 'Técnico 1'] = t1_val
                    df_cron.loc[mask, 'Técnico 2'] = t2_val
                    df_cron.loc[mask, 'Técnico 3'] = t3_val
                    df_cron.loc[mask, 'Personas involucradas'] = invol_clean
                    df_cron.loc[mask, 'Comentario'] = comentario_val
                    
                    df_cron.loc[mask, 'Fecha de Creación'] = str(high_fcreacion).strip() if high_fcreacion else ""
                    df_cron.loc[mask, 'Fecha de Fin'] = str(high_ffin).strip() if high_ffin else ""
                    
                    try: df_cron.loc[mask, 'Horas de Licitación'] = float(high_horas) if high_horas else ""
                    except: df_cron.loc[mask, 'Horas de Licitación'] = ""
                    
                    try: df_cron.loc[mask, 'Horas de Licitación BAM'] = float(high_horas_bam) if high_horas_bam else ""
                    except: df_cron.loc[mask, 'Horas de Licitación BAM'] = ""
                    
                    nom_proy = str(df_cron.loc[mask, COL_NOMBRE].values[0])
                    cliente = str(df_cron.loc[mask, 'Cliente'].values[0])
                    mensaje = f"💾 ¡Datos de la licitación {cod_lic} actualizados!"
                else:
                    fila_virgen = df_bbdd[df_bbdd[COL_CODIGO].astype(str) == cod_lic].copy()
                    if fila_virgen.empty:
                        estilo_msg['color'] = 'var(--semantic-negative)'
                        return dash.no_update, "⚠️ Error: Ese código no existe en BBDD.", estilo_msg, *[dash.no_update]*13

                    nom_proy = str(fila_virgen.iloc[0].get(COL_NOMBRE, 'Sin Nombre'))
                    cliente = str(fila_virgen.iloc[0].get('Cliente', 'Sin Cliente'))

                    fila_virgen['Etapa'] = etapa
                    fila_virgen['BAM'] = bam_clean
                    fila_virgen['Técnico 1'], fila_virgen['Técnico 2'], fila_virgen['Técnico 3'] = t1_val, t2_val, t3_val
                    fila_virgen['Personas involucradas'] = invol_clean
                    fila_virgen['Comentario'] = comentario_val
                    
                    if 'Cliente' not in fila_virgen.columns: fila_virgen['Cliente'] = ""
                    
                    fila_virgen['Fecha de Creación'] = str(high_fcreacion).strip() if high_fcreacion else ""
                    fila_virgen['Fecha de Fin'] = str(high_ffin).strip() if high_ffin else ""
                    
                    try: fila_virgen['Horas de Licitación'] = float(high_horas) if high_horas else ""
                    except: fila_virgen['Horas de Licitación'] = ""

                    try: fila_virgen['Horas de Licitación BAM'] = float(high_horas_bam) if high_horas_bam else ""
                    except: fila_virgen['Horas de Licitación BAM'] = ""

                    df_cron = pd.concat([df_cron, fila_virgen], ignore_index=True)
                    mensaje = f"🚀 ¡Licitación {cod_lic} inyectada al Funnel Operativo!"

                informe_generado = (
                    f"📌 ACTUALIZACIÓN DE ASIGNACIÓN (SERVEO)\n"
                    f"--------------------------------------------------\n"
                    f"Código: {cod_lic}\n"
                    f"Nombre: {nom_proy}\n"
                    f"Cliente: {cliente}\n\n"
                    f"📋 ESTATUS OPERATIVO:\n"
                    f"Etapa Actual: {etapa}\n"
                    f"BAM Responsable: {bam_clean if bam_clean else 'Pendiente'}\n"
                    f"Técnicos: {', '.join([t for t in [t1_val, t2_val, t3_val] if t]) or 'Pendiente'}\n"
                    f"Apoyo/Involucrados: {invol_clean if invol_clean else 'Ninguno'}\n\n"
                    f"⏳ PLANIFICACIÓN TÉCNICA:\n"
                    f"Fechas: {high_fcreacion if high_fcreacion else 'TBD'} al {high_ffin if high_ffin else 'TBD'}\n"
                    f"Horas Estimadas: {high_horas if high_horas else 0}h (Técnicos) / {high_horas_bam if high_horas_bam else 0}h (BAM)\n\n"
                    f"💬 NOTAS ADICIONALES:\n"
                    f"{comentario_val if comentario_val else 'Ninguna'}\n"
                    f"--------------------------------------------------"
                )

                estilo_msg['color'] = 'var(--semantic-positive)'
                exito = True

            elif trigger == 'btn-eliminar':
                if not filas_seleccionadas:
                    estilo_msg['color'] = 'var(--semantic-negative)'
                    return dash.no_update, "⚠️ Selecciona filas para eliminar.", estilo_msg, *[dash.no_update]*13
                
                codigos_a_borrar = [str(tabla_data[i][COL_CODIGO]).strip() for i in filas_seleccionadas]
                df_cron = df_cron[~df_cron[COL_CODIGO].isin(codigos_a_borrar)]
                estilo_msg['color'] = 'var(--semantic-negative)' 
                exito = True

            if exito:
                guardado_exitoso, msg_sistema = guardar_sqlite_centralizado(df_cron_new=df_cron)
                if guardado_exitoso:
                    if trigger == 'btn-eliminar': mensaje = f"🗑️ ¡{len(codigos_a_borrar)} proyecto(s) devuelto(s) a BBDD!"
                else:
                    return dash.no_update, msg_sistema, {'color':'var(--semantic-negative)'}, *[dash.no_update]*13

        df_filtrado = df_cron.copy()

        if f_cod:
            if isinstance(f_cod, str): f_cod = [f_cod]
            df_filtrado = df_filtrado[df_filtrado[COL_CODIGO].astype(str).isin(f_cod)]
        if f_nom:
            if isinstance(f_nom, str): f_nom = [f_nom]
            df_filtrado = df_filtrado[df_filtrado[COL_NOMBRE].astype(str).isin(f_nom)]
        if f_etapa:
            if isinstance(f_etapa, str): f_etapa = [f_etapa]
            df_filtrado = df_filtrado[df_filtrado['Etapa'].isin(f_etapa)]
        if f_bam:
            if isinstance(f_bam, str): f_bam = [f_bam]
            df_filtrado = df_filtrado[df_filtrado['BAM'].isin(f_bam)]
        if f_tec:
            if isinstance(f_tec, str): f_tec = [f_tec]
            mask_tec = pd.Series(False, index=df_filtrado.index)
            for col in ['Técnico 1', 'Técnico 2', 'Técnico 3']:
                if col in df_filtrado.columns: mask_tec = mask_tec | df_filtrado[col].isin(f_tec)
            df_filtrado = df_filtrado[mask_tec]

        if not df_filtrado.empty:
            # --- LIMPIEZA ADICIONAL PARA CELDAS FILTRADAS EN TABLA VISUAL ---
            if 'Fecha de Creación' in df_filtrado.columns:
                df_filtrado['Fecha de Creación'] = df_filtrado['Fecha de Creación'].apply(parsear_fecha_es).dt.strftime('%Y-%m-%d').fillna("")
            if 'Fecha de Fin' in df_filtrado.columns:
                df_filtrado['Fecha de Fin'] = df_filtrado['Fecha de Fin'].apply(parsear_fecha_es).dt.strftime('%Y-%m-%d').fillna("")
            
            # --- MAPEO DE ALIAS PARA LA TABLA TRAS EL FILTRADO ---
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
            
            for col in ['BAM', 'Técnico 1', 'Técnico 2', 'Técnico 3']:
                if col in df_filtrado.columns:
                    df_filtrado[col] = df_filtrado[col].map(lambda x: dict_alias.get(str(x).strip(), str(x).strip()) if pd.notna(x) and str(x).strip() != "" else "")
            
            df_filtrado = df_filtrado.fillna("")
            datos_tabla_final = df_filtrado.to_dict('records')
        else:
            datos_tabla_final = []

        nuevas_opc_cod = [{'label': f"{c} - {n}", 'value': str(c)} for c, n in zip(df_cron[COL_CODIGO], df_cron.get(COL_NOMBRE, [""]*len(df_cron))) if pd.notna(c)] if COL_CODIGO in df_cron.columns else []
        nuevas_opc_nom = [{'label': str(n), 'value': str(n)} for n in df_cron[COL_NOMBRE].dropna().unique()] if COL_NOMBRE in df_cron.columns else []

        if es_accion:
            return (
                datos_tabla_final, mensaje, estilo_msg, 
                dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, 
                dash.no_update, dash.no_update, dash.no_update, dash.no_update, 
                [] if trigger == 'btn-eliminar' else dash.no_update,
                nuevas_opc_cod, nuevas_opc_nom, informe_generado
            )
        else:
            return datos_tabla_final, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, [], nuevas_opc_cod, nuevas_opc_nom, dash.no_update