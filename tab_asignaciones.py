from dash import html, dcc, dash_table, Input, Output, State, ctx
import dash
import pandas as pd
from utils.data_manager import ARCHIVO_EXCEL
from datetime import datetime

# Textos exactos confirmados por las sábanas del Excel
COL_CODIGO = 'Código de Licitación'
COL_NOMBRE = 'Nombre de la Licitación'

def leer_datos_completos():
    """Lectura ultra-segura que elimina espacios fantasma y detecta bloqueos del Excel."""
    try:
        with pd.ExcelFile(ARCHIVO_EXCEL, engine='openpyxl') as xls:
            hojas = {sheet.lower().strip(): sheet for sheet in xls.sheet_names}
            
            df_bbdd = pd.read_excel(xls, sheet_name=hojas.get('bbdd')) if 'bbdd' in hojas else pd.DataFrame()
            df_cron = pd.read_excel(xls, sheet_name=hojas.get('cronograma')) if 'cronograma' in hojas else pd.DataFrame()
            df_eq = pd.read_excel(xls, sheet_name=hojas.get('equipo')) if 'equipo' in hojas else pd.DataFrame()
            
            if not df_bbdd.empty: df_bbdd.columns = df_bbdd.columns.str.strip()
            if not df_cron.empty: df_cron.columns = df_cron.columns.str.strip()
            if not df_eq.empty: df_eq.columns = df_eq.columns.str.strip()
            
            if COL_CODIGO in df_bbdd.columns: df_bbdd[COL_CODIGO] = df_bbdd[COL_CODIGO].astype(str).str.strip()
            if COL_CODIGO in df_cron.columns: df_cron[COL_CODIGO] = df_cron[COL_CODIGO].astype(str).str.strip()
            
            return df_bbdd, df_cron, df_eq, ""
    except PermissionError:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), "⚠️ EXCEL BLOQUEADO: Cierra el archivo Excel en tu ordenador y recarga la página."
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), f"⚠️ ERROR DE LECTURA: {str(e)}"

def layout():
    df_bbdd, df_cron, df_eq, error_sistema = leer_datos_completos()
    
    opciones_licitaciones = []
    if not df_bbdd.empty and COL_CODIGO in df_bbdd.columns:
        codigos_activos = df_cron[COL_CODIGO].tolist() if not df_cron.empty and COL_CODIGO in df_cron.columns else []
        df_disponibles = df_bbdd[~df_bbdd[COL_CODIGO].isin(codigos_activos)]
        
        for _, row in df_disponibles.iterrows():
            if pd.notna(row.get(COL_CODIGO)) and str(row.get(COL_CODIGO)).strip() != "" and str(row.get(COL_CODIGO)).lower() != "nan":
                codigo = str(row[COL_CODIGO])
                nombre = str(row.get(COL_NOMBRE, 'Sin Nombre'))
                etiqueta = f"{codigo} - {nombre}"
                opciones_licitaciones.append({'label': etiqueta, 'value': codigo})

    opciones_equipo_nombres = []
    opciones_bam_nombres = []
    if not df_eq.empty and 'Nombre' in df_eq.columns:
        if 'Perfil Técnico' in df_eq.columns:
            opciones_bam_nombres = df_eq[df_eq['Perfil Técnico'] == 'Business Area Manager']['Nombre'].dropna().tolist()
            opciones_equipo_nombres = df_eq[df_eq['Perfil Técnico'] == 'Bidding Technician']['Nombre'].dropna().tolist()
        else:
            opciones_equipo_nombres = df_eq['Nombre'].dropna().tolist()
            opciones_bam_nombres = opciones_equipo_nombres
            
    opciones_equipo_drop = [{'label': n, 'value': n} for n in opciones_equipo_nombres]
    opciones_bam_drop = [{'label': n, 'value': n} for n in opciones_bam_nombres]

    opciones_etapa_lista = ['Pendiente Asignar', 'En estudio', 'Estudio previo']
    opciones_etapa_drop = [{'label': i, 'value': i} for i in opciones_etapa_lista]

    if error_sistema:
        placeholder_texto = "🔒 Error de acceso (Ver abajo)"
    elif df_bbdd.empty:
        placeholder_texto = "⚠️ Pestaña BBDD vacía o no encontrada"
    elif COL_CODIGO not in df_bbdd.columns:
        placeholder_texto = "⚠️ Cabeceras incorrectas en Excel"
    elif len(opciones_licitaciones) == 0:
        placeholder_texto = "✅ Todos los proyectos de la BBDD ya están en el Funnel"
    else:
        placeholder_texto = "Buscar por código o nombre..."

    if not df_cron.empty:
        df_cron_tabla = df_cron.copy()
        if 'Fecha de Creación' in df_cron_tabla.columns:
            df_cron_tabla['Fecha de Creación'] = pd.to_datetime(df_cron_tabla['Fecha de Creación'], errors='coerce').dt.strftime('%Y-%m-%d')
        if 'Fecha de Fin' in df_cron_tabla.columns:
            df_cron_tabla['Fecha de Fin'] = pd.to_datetime(df_cron_tabla['Fecha de Fin'], errors='coerce').dt.strftime('%Y-%m-%d')
        df_cron_tabla = df_cron_tabla.fillna("")
        datos_diccionario = df_cron_tabla.to_dict('records')
    else:
        datos_diccionario = []

    return html.Div([
        
        html.H3("Activación y Asignación de Licitaciones", className="serveo-titulo-pagina"),
        
        # --- PANEL DE ACCIÓN SUPERIOR ---
        html.Div([
            html.Div("Extraer de BBDD, Editar Campos Clave e Inyectar al Funnel", style={'color': '#FFFFFF', 'backgroundColor': 'var(--text-border)', 'padding': '8px 16px', 'fontSize': '9px', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'marginBottom': '24px', 'borderRadius': '6px', 'display': 'inline-block'}),
            
            # Fila 1: Licitación y Etapa
            html.Div([
                html.Div([
                    html.Label("1. Selecciona Licitación de la Base de Datos Maestra", className="etiqueta-dato"),
                    dcc.Dropdown(id='drop-act-lic', options=opciones_licitaciones, placeholder=placeholder_texto, searchable=True)
                ], className="serveo-input-wrapper", style={'flex': '2'}),
                
                html.Div([
                    html.Label("2. Asignar Etapa (Obligatorio)", className="etiqueta-dato", style={'color': 'var(--accent)'}),
                    dcc.Dropdown(id='drop-act-etapa', options=opciones_etapa_drop, placeholder="Selecciona etapa...") 
                ], className="serveo-input-wrapper", style={'flex': '1'})
            ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '24px'}),

            # --- NUEVA FILA 1B: SELECTORES DE CALENDARIO (DCC.DATEPICKERSINGLE) ---
            html.Div([
                html.Div([
                    html.Label("Fecha de Creación", className="etiqueta-dato"),
                    dcc.DatePickerSingle(
                        id='date-act-fcreacion',
                        display_format='YYYY-MM-DD',
                        placeholder='Selecciona fecha...',
                        style={'width': '100%'}
                    )
                ], className="serveo-input-wrapper", style={'flex': '1'}),
                
                html.Div([
                    html.Label("Fecha de Fin (Vencimiento)", className="etiqueta-dato"),
                    dcc.DatePickerSingle(
                        id='date-act-ffin',
                        display_format='YYYY-MM-DD',
                        placeholder='Selecciona fecha...',
                        style={'width': '100%'}
                    )
                ], className="serveo-input-wrapper", style={'flex': '1'}),
                
                html.Div([
                    html.Label("Horas Estimadas de Licitación", className="etiqueta-dato"),
                    dcc.Input(id='input-act-horas', type='number', min=0, placeholder='Ej. 120', className="input-filtro")
                ], className="serveo-input-wrapper", style={'flex': '1'}),
            ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '24px'}),

            # Fila 2: BAM, Técnicos y Botón
            html.Div([
                html.Div([
                    html.Label("Manager (BAM)", className="etiqueta-dato"),
                    dcc.Dropdown(id='drop-act-bam', options=opciones_bam_drop, clearable=True)
                ], className="serveo-input-wrapper"),
                
                html.Div([
                    html.Label("Técnico 1", className="etiqueta-dato"),
                    dcc.Dropdown(id='drop-act-t1', options=opciones_equipo_drop, clearable=True)
                ], className="serveo-input-wrapper"),
                
                html.Div([
                    html.Label("Técnico 2", className="etiqueta-dato"),
                    dcc.Dropdown(id='drop-act-t2', options=opciones_equipo_drop, clearable=True)
                ], className="serveo-input-wrapper"),
                
                html.Div([
                    html.Label("Técnico 3", className="etiqueta-dato"),
                    dcc.Dropdown(id='drop-act-t3', options=opciones_equipo_drop, clearable=True)
                ], className="serveo-input-wrapper"),
                
                html.Button('Activar en Funnel', id='btn-activar', n_clicks=0, className="btn-serveo-primario", style={'alignSelf': 'flex-end', 'height': '32px', 'padding': '0 24px'})
            ], style={'display': 'flex', 'gap': '16px'})
            
        ], className="serveo-panel-accion", style={'marginBottom': '24px'}),

        html.Div(error_sistema, id='msj-interaccion', style={'marginBottom': '24px', 'fontWeight': 'bold', 'fontFamily': 'var(--font-family)', 'fontSize': '13px', 'color': 'var(--semantic-negative)'}),

        # --- TITULO SECCIÓN ---
        html.H3("Control y Edición del Funnel Operativo", className="serveo-titulo-seccion"),
        
        # --- BARRA DE FILTROS PARA LA TABLA ---
        html.Div([
            html.Div([
                html.Label("Código Licitación", className="etiqueta-dato"),
                dcc.Input(id='filtro-asig-cod', placeholder="Buscar...", className="input-filtro")
            ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '250px'}),
            
            html.Div([
                html.Label("Nombre Licitación", className="etiqueta-dato"),
                dcc.Input(id='filtro-asig-nom', placeholder="Buscar...", className="input-filtro")
            ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '300px'}),
            
            html.Div([
                html.Label("Etapa", className="etiqueta-dato"),
                dcc.Dropdown(id='filtro-asig-etapa', options=opciones_etapa_drop, placeholder="Todas", multi=True)
            ], className="serveo-input-wrapper", style={'flex': '1.5'}),
            
            html.Div([
                html.Label("BAM", className="etiqueta-dato"),
                dcc.Dropdown(id='filtro-asig-bam', options=opciones_bam_drop, placeholder="Todos", multi=True)
            ], className="serveo-input-wrapper", style={'flex': '1.5'}),
            
            html.Div([
                html.Label("Técnico(s)", className="etiqueta-dato"),
                dcc.Dropdown(id='filtro-asig-tec', options=opciones_equipo_drop, placeholder="Todos", multi=True)
            ], className="serveo-input-wrapper", style={'flex': '2'})
        ], className="contenedor-filtros", style={'backgroundColor': 'var(--card-divider)', 'alignItems': 'flex-end', 'padding': '16px 24px', 'marginBottom': '16px', 'flexWrap': 'wrap'}),

        # --- TABLA DE EDICIÓN ---
        dash_table.DataTable(
            id='tabla-funnel-activo',
            columns=[
                {"name": "Código Licitación", "id": COL_CODIGO, "editable": False},
                {"name": "Nombre Licitación", "id": COL_NOMBRE, "editable": False},
                {"name": "F. Creación", "id": "Fecha de Creación", "editable": False},
                {"name": "F. Fin", "id": "Fecha de Fin", "editable": False},
                {"name": "Etapa", "id": "Etapa", "editable": True, "presentation": "dropdown"},
                {"name": "BAM", "id": "BAM", "editable": True, "presentation": "dropdown"}, 
                {"name": "Técnico 1", "id": "Técnico 1", "editable": True, "presentation": "dropdown"},
                {"name": "Técnico 2", "id": "Técnico 2", "editable": True, "presentation": "dropdown"},
                {"name": "Técnico 3", "id": "Técnico 3", "editable": True, "presentation": "dropdown"}
            ],
            data=datos_diccionario,
            dropdown={
                'Etapa': {'options': [{'label': i, 'value': i} for i in opciones_etapa_lista]},
                'BAM': {'options': [{'label': i, 'value': i} for i in opciones_bam_nombres]},
                'Técnico 1': {'options': [{'label': i, 'value': i} for i in opciones_equipo_nombres]},
                'Técnico 2': {'options': [{'label': i, 'value': i} for i in opciones_equipo_nombres]},
                'Técnico 3': {'options': [{'label': i, 'value': i} for i in opciones_equipo_nombres]}
            },
            row_selectable="multi",
            selected_rows=[],
            style_header={'backgroundColor': 'var(--card-divider)', 'color': 'var(--text-border)', 'fontWeight': 'bold', 'border': 'var(--border-solid)', 'fontFamily': 'var(--font-family)', 'fontSize': '9px', 'textTransform': 'uppercase', 'textAlign': 'left'},
            style_cell={'backgroundColor': 'var(--bg-main)', 'color': 'var(--text-border)', 'border': '1px solid var(--card-divider)', 'padding': '12px', 'textAlign': 'left', 'fontFamily': 'var(--font-family)', 'fontSize': '12px'},
            style_data_conditional=[
                {'if': {'filter_query': '{Técnico 1} is blank && {Técnico 2} is blank && {Técnico 3} is blank'}, 'backgroundColor': 'rgba(219, 86, 58, 0.1)', 'color': 'var(--semantic-negative)', 'fontWeight': 'bold'}
            ],
            style_table={'overflowX': 'auto', 'borderRadius': 'var(--radius-interactive)', 'border': 'var(--border-solid)', 'marginBottom': '24px'}
        ),

        html.Div([
            html.Button('💾 Guardar Cambios', id='btn-guardar-edicion', n_clicks=0, className="btn-serveo-primario"),
            html.Button('🗑️ Eliminar Seleccionados', id='btn-eliminar', n_clicks=0, className="btn-serveo-negativo")
        ], style={'display': 'flex', 'gap': '16px', 'justifyContent': 'flex-start'})

    ], style={'paddingBottom': '40px'})

def register_callbacks(app):

    # =====================================================================
    # CALLBACK: PRE-POBLAR AUTOMÁTICAMENTE LOS CALENDARIOS AL SELECCIONAR
    # =====================================================================
    @app.callback(
        [Output('date-act-fcreacion', 'date'),
         Output('date-act-ffin', 'date'),
         Output('input-act-horas', 'value')],
        Input('drop-act-lic', 'value')
    )
    def pre_poblar_campos_activacion(cod_lic_seleccionado):
        if not cod_lic_seleccionado:
            return None, None, ""
        
        df_bbdd, _, _, _ = leer_datos_completos()
        if df_bbdd.empty:
            return None, None, ""
            
        fila = df_bbdd[df_bbdd[COL_CODIGO] == str(cod_lic_seleccionado).strip()]
        if fila.empty:
            return None, None, ""
            
        f_creacion = None
        if 'Fecha de Creación' in df_bbdd.columns and pd.notna(fila.iloc[0]['Fecha de Creación']):
            try: f_creacion = pd.to_datetime(fila.iloc[0]['Fecha de Creación']).strftime('%Y-%m-%d')
            except: pass
            
        f_fin = None
        if 'Fecha de Fin' in df_bbdd.columns and pd.notna(fila.iloc[0]['Fecha de Fin']):
            try: f_fin = pd.to_datetime(fila.iloc[0]['Fecha de Fin']).strftime('%Y-%m-%d')
            except: pass
            
        horas = ""
        if 'Horas de Licitación' in df_bbdd.columns and pd.notna(fila.iloc[0]['Horas de Licitación']):
            try: horas = int(fila.iloc[0]['Horas de Licitación'])
            except: pass
            
        return f_creacion, f_fin, horas


    # =====================================================================
    # CALLBACK PRINCIPAL: CONTROLADOR DEL FUNNEL MAESTRO
    # =====================================================================
    @app.callback(
        [Output('tabla-funnel-activo', 'data'),
         Output('drop-act-lic', 'options'),
         Output('msj-interaccion', 'children'),
         Output('msj-interaccion', 'style'),
         Output('drop-act-lic', 'value'),
         Output('drop-act-etapa', 'value'),
         Output('drop-act-bam', 'value'),
         Output('drop-act-t1', 'value'),
         Output('drop-act-t2', 'value'),
         Output('drop-act-t3', 'value'),
         Output('drop-act-lic', 'placeholder'),
         Output('tabla-funnel-activo', 'selected_rows')],
        [Input('btn-activar', 'n_clicks'),
         Input('btn-guardar-edicion', 'n_clicks'),
         Input('btn-eliminar', 'n_clicks'),
         Input('filtro-asig-cod', 'value'),
         Input('filtro-asig-nom', 'value'),
         Input('filtro-asig-etapa', 'value'),
         Input('filtro-asig-bam', 'value'),
         Input('filtro-asig-tec', 'value')],
        [State('drop-act-lic', 'value'),
         State('drop-act-etapa', 'value'),
         State('drop-act-bam', 'value'),
         State('drop-act-t1', 'value'),
         State('drop-act-t2', 'value'),
         State('drop-act-t3', 'value'),
         # Captura limpia de los DatePickers como States
         State('date-act-fcreacion', 'date'),
         State('date-act-ffin', 'date'),
         State('input-act-horas', 'value'),
         State('tabla-funnel-activo', 'data'),
         State('tabla-funnel-activo', 'selected_rows')]
    )
    def gestor_maestro_funnel(n_activar, n_guardar, n_eliminar, f_cod, f_nom, f_etapa, f_bam, f_tec, 
                              cod_lic, etapa, bam_val, t1, t2, t3, high_fcreacion, high_ffin, high_horas,
                              tabla_data, filas_seleccionadas):
        trigger = ctx.triggered_id
        if not trigger:
            raise dash.exceptions.PreventUpdate

        df_bbdd, df_cron, df_eq, error_sistema = leer_datos_completos()
        estilo_msg = {'marginBottom': '24px', 'fontWeight': 'bold', 'fontFamily': 'var(--font-family)', 'fontSize': '13px'}
        
        if error_sistema:
            estilo_msg['color'] = 'var(--semantic-negative)'
            return dash.no_update, dash.no_update, error_sistema, estilo_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        for col in [COL_CODIGO, COL_NOMBRE, 'Fecha de Creación', 'Fecha de Fin', 'Horas de Licitación', 'BAM', 'Técnico 1', 'Técnico 2', 'Técnico 3', 'Etapa']:
            if col not in df_cron.columns: df_cron[col] = ""

        def depurar_celda(valor):
            if pd.isna(valor) or valor is None or str(valor).strip() == "" or str(valor).strip().lower() == "none":
                return ""
            return str(valor).strip()

        mensaje = ""
        exito = False
        es_accion = trigger in ['btn-activar', 'btn-guardar-edicion', 'btn-eliminar']

        # ==========================================
        # FASE 1: PROCESAMIENTO DE ACCIONES DE DATOS
        # ==========================================
        if es_accion:
            if trigger == 'btn-activar':
                if not cod_lic or not etapa:
                    estilo_msg['color'] = 'var(--semantic-negative)'
                    return dash.no_update, dash.no_update, "⚠️ Selecciona licitación y etapa.", estilo_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

                t1_val, t2_val, t3_val, bam_clean = depurar_celda(t1), depurar_celda(t2), depurar_celda(t3), depurar_celda(bam_val)
                hay_tecnicos = bool(t1_val or t2_val or t3_val)
                
                if etapa != 'Pendiente Asignar' and not hay_tecnicos:
                    estilo_msg['color'] = 'var(--semantic-negative)'
                    return dash.no_update, dash.no_update, f"⚠️ La etapa '{etapa}' exige seleccionar al menos un técnico.", estilo_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
                
                if etapa == 'Pendiente Asignar': t1_val = t2_val = t3_val = ""

                cod_lic_str = str(cod_lic).strip()
                fila_virgen = df_bbdd[df_bbdd[COL_CODIGO] == cod_lic_str].copy()
                if fila_virgen.empty:
                    estilo_msg['color'] = 'var(--semantic-negative)'
                    return dash.no_update, dash.no_update, "⚠️ Error: Licitación no encontrada en BBDD.", estilo_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

                # Inyección limpia de metadatos temporales validados
                fila_virgen['Etapa'] = etapa
                fila_virgen['BAM'] = bam_clean
                fila_virgen['Técnico 1'], fila_virgen['Técnico 2'], fila_virgen['Técnico 3'] = t1_val, t2_val, t3_val
                
                # El DatePicker garantiza formato AAAA-MM-DD o None
                fila_virgen['Fecha de Creación'] = str(high_fcreacion).strip() if high_fcreacion else ""
                fila_virgen['Fecha de Fin'] = str(high_ffin).strip() if high_ffin else ""
                
                # Validación del campo Horas para evitar roturas de tipo de dato en Excel
                if high_horas is not None and str(high_horas).strip() != "":
                    try: fila_virgen['Horas de Licitación'] = float(high_horas)
                    except: fila_virgen['Horas de Licitación'] = ""
                else:
                    fila_virgen['Horas de Licitación'] = ""

                df_cron = pd.concat([df_cron, fila_virgen], ignore_index=True)
                mensaje = f"🚀 ¡Licitación {cod_lic} activada correctamente!"
                estilo_msg['color'] = 'var(--semantic-positive)'
                exito = True

            elif trigger == 'btn-guardar-edicion':
                df_editado = pd.DataFrame(tabla_data)
                for _, row in df_editado.iterrows():
                    etapa_act = depurar_celda(row.get('Etapa'))
                    hay_tec = bool(depurar_celda(row.get('Técnico 1')) or depurar_celda(row.get('Técnico 2')) or depurar_celda(row.get('Técnico 3')))
                    if etapa_act != 'Pendiente Asignar' and not hay_tec:
                        estilo_msg['color'] = 'var(--semantic-negative)'
                        return dash.no_update, dash.no_update, f"⚠️ Error ({str(row[COL_CODIGO]).strip()}): Falta asignar técnico.", estilo_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

                for _, row in df_editado.iterrows():
                    mask = df_cron[COL_CODIGO] == str(row[COL_CODIGO]).strip()
                    df_cron.loc[mask, 'Etapa'] = depurar_celda(row.get('Etapa'))
                    df_cron.loc[mask, 'BAM'] = depurar_celda(row.get('BAM'))
                    t1_v, t2_v, t3_v = depurar_celda(row.get('Técnico 1')), depurar_celda(row.get('Técnico 2')), depurar_celda(row.get('Técnico 3'))
                    if depurar_celda(row.get('Etapa')) == 'Pendiente Asignar': t1_v = t2_v = t3_v = ""
                    df_cron.loc[mask, 'Técnico 1'], df_cron.loc[mask, 'Técnico 2'], df_cron.loc[mask, 'Técnico 3'] = t1_v, t2_v, t3_v
                
                mensaje = "💾 ¡Cambios guardados correctamente!"
                estilo_msg['color'] = 'var(--semantic-positive)'
                exito = True

            elif trigger == 'btn-eliminar':
                if not filas_seleccionadas:
                    estilo_msg['color'] = 'var(--semantic-negative)'
                    return dash.no_update, dash.no_update, "⚠️ Selecciona filas para eliminar.", estilo_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
                
                codigos_a_borrar = [str(tabla_data[i][COL_CODIGO]).strip() for i in filas_seleccionadas]
                df_cron = df_cron[~df_cron[COL_CODIGO].isin(codigos_a_borrar)]
                mensaje = f"🗑️ ¡{len(codigos_a_borrar)} proyecto(s) devuelto(s)!"
                estilo_msg['color'] = 'var(--semantic-negative)' 
                exito = True

            if exito:
                df_vac = pd.DataFrame()
                try:
                    with pd.ExcelFile(ARCHIVO_EXCEL, engine='openpyxl') as xls:
                        if 'vacaciones' in xls.sheet_names: df_vac = pd.read_excel(xls, sheet_name='vacaciones')
                except Exception: pass

                try:
                    with pd.ExcelWriter(ARCHIVO_EXCEL, engine='openpyxl', mode='w') as writer:
                        df_bbdd.to_excel(writer, sheet_name='bbdd', index=False)
                        df_cron.to_excel(writer, sheet_name='cronograma', index=False)
                        if not df_eq.empty: df_eq.to_excel(writer, sheet_name='equipo', index=False)
                        if not df_vac.empty: df_vac.to_excel(writer, sheet_name='vacaciones', index=False)
                except PermissionError:
                    return dash.no_update, dash.no_update, "⚠️ Cierra el Excel para guardar.", {'color':'var(--semantic-negative)'}, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
            else:
                return dash.no_update, dash.no_update, mensaje, estilo_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # ==========================================
        # FASE 2: FILTRADO VISUAL TRAS ACCIÓN / CARGA
        # ==========================================
        df_filtrado = df_cron.copy()

        if f_cod:
            df_filtrado = df_filtrado[df_filtrado[COL_CODIGO].astype(str).str.contains(f_cod, case=False, na=False)]
        if f_nom:
            df_filtrado = df_filtrado[df_filtrado[COL_NOMBRE].astype(str).str.contains(f_nom, case=False, na=False)]
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
            if 'Fecha de Creación' in df_filtrado.columns:
                df_filtrado['Fecha de Creación'] = pd.to_datetime(df_filtrado['Fecha de Creación'], errors='coerce').dt.strftime('%Y-%m-%d')
            if 'Fecha de Fin' in df_filtrado.columns:
                df_filtrado['Fecha de Fin'] = pd.to_datetime(df_filtrado['Fecha de Fin'], errors='coerce').dt.strftime('%Y-%m-%d')
            df_filtrado = df_filtrado.fillna("")
            datos_tabla_final = df_filtrado.to_dict('records')
        else:
            datos_tabla_final = []

        # ==========================================
        # FASE 3: RETORNOS INTELIGENTES
        # ==========================================
        if es_accion:
            nuevas_opciones = []
            activos = df_cron[COL_CODIGO].tolist()
            disp = df_bbdd[~df_bbdd[COL_CODIGO].isin(activos)]
            for _, r in disp.iterrows():
                if pd.notna(r.get(COL_CODIGO)) and str(r.get(COL_CODIGO)).strip() != "" and str(r.get(COL_CODIGO)).lower() != "nan":
                    nuevas_opciones.append({'label': f"{r[COL_CODIGO]} - {r.get(COL_NOMBRE, '')}", 'value': str(r[COL_CODIGO])})
            
            return (
                datos_tabla_final, nuevas_opciones, mensaje, estilo_msg, 
                "" if trigger == 'btn-activar' else dash.no_update, 
                "" if trigger == 'btn-activar' else dash.no_update, 
                "" if trigger == 'btn-activar' else dash.no_update, 
                "" if trigger == 'btn-activar' else dash.no_update, 
                "" if trigger == 'btn-activar' else dash.no_update, 
                "" if trigger == 'btn-activar' else dash.no_update, 
                "✅ BBDD vaciada" if len(nuevas_opciones) == 0 else "Buscar...", 
                [] if trigger == 'btn-eliminar' else dash.no_update
            )
        else:
            return datos_tabla_final, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, []