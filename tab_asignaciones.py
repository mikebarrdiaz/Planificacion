from dash import html, dcc, dash_table, Input, Output, State, ctx
import dash
import pandas as pd
from utils.data_manager import ARCHIVO_EXCEL

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
            
            # NORMALIZACIÓN ESTRICTA: Forzar los códigos a texto para evitar el "Type Mismatch"
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
    if not df_eq.empty and 'Nombre' in df_eq.columns:
        opciones_equipo_nombres = df_eq['Nombre'].dropna().tolist()
        
    opciones_equipo_drop = [{'label': n, 'value': n} for n in opciones_equipo_nombres]

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

    return html.Div([
        
        # Título consolidado
        html.H3("Activación y Asignación de Licitaciones", className="serveo-titulo-pagina"),
        
        # --- PANEL DE ACCIÓN SUPERIOR ---
        html.Div([
            html.Div("Extraer de BBDD e Inyectar al Funnel", style={'color': '#FFFFFF', 'backgroundColor': 'var(--text-border)', 'padding': '8px 16px', 'fontSize': '9px', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'marginBottom': '24px', 'borderRadius': '6px', 'display': 'inline-block'}),
            
            # Fila 1: Licitación y Etapa
            html.Div([
                html.Div([
                    html.Label("1. Selecciona Licitación de la Base de Datos Maestra", className="etiqueta-dato"),
                    dcc.Dropdown(
                        id='drop-act-lic', 
                        options=opciones_licitaciones, 
                        placeholder=placeholder_texto, 
                        searchable=True,
                        className="input-filtro"
                    )
                ], className="serveo-input-wrapper", style={'flex': '2'}),
                
                html.Div([
                    html.Label("2. Asignar Etapa (Obligatorio)", className="etiqueta-dato", style={'color': 'var(--accent)'}),
                    dcc.Dropdown(
                        id='drop-act-etapa', 
                        options=opciones_etapa_drop, 
                        placeholder="Selecciona etapa...", 
                        className="input-filtro",
                        style={'border': '1px solid var(--accent)'} # Mantenemos el borde naranja para resaltar obligatoriedad
                    )
                ], className="serveo-input-wrapper", style={'flex': '1'})
            ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '24px'}),

            # Fila 2: Técnicos y Botón
            html.Div([
                html.Div([
                    html.Label("Técnico 1 (Opcional)", className="etiqueta-dato"),
                    dcc.Dropdown(id='drop-act-t1', options=opciones_equipo_drop, clearable=True, className="input-filtro")
                ], className="serveo-input-wrapper"),
                
                html.Div([
                    html.Label("Técnico 2 (Opcional)", className="etiqueta-dato"),
                    dcc.Dropdown(id='drop-act-t2', options=opciones_equipo_drop, clearable=True, className="input-filtro")
                ], className="serveo-input-wrapper"),
                
                html.Div([
                    html.Label("Técnico 3 (Opcional)", className="etiqueta-dato"),
                    dcc.Dropdown(id='drop-act-t3', options=opciones_equipo_drop, clearable=True, className="input-filtro")
                ], className="serveo-input-wrapper"),
                
                html.Button('Activar en Funnel', id='btn-activar', n_clicks=0, className="btn-serveo-primario", style={'alignSelf': 'flex-end', 'height': '38px', 'padding': '0 32px'})
            ], style={'display': 'flex', 'gap': '16px'})
            
        ], className="serveo-panel-accion", style={'marginBottom': '24px'}),

        html.Div(error_sistema, id='msj-interaccion', style={'marginBottom': '24px', 'fontWeight': 'bold', 'fontFamily': 'var(--font-family)', 'fontSize': '13px', 'color': 'var(--semantic-negative)'}),

        # --- TABLA DE EDICIÓN ---
        html.H3("Control y Edición del Funnel Operativo", className="serveo-titulo-seccion"),
        
        dash_table.DataTable(
            id='tabla-funnel-activo',
            columns=[
                {"name": "Código", "id": COL_CODIGO, "editable": False},
                {"name": "Nombre Proyecto", "id": COL_NOMBRE, "editable": False},
                {"name": "Etapa", "id": "Etapa", "editable": True, "presentation": "dropdown"},
                {"name": "Técnico 1", "id": "Técnico 1", "editable": True, "presentation": "dropdown"},
                {"name": "Técnico 2", "id": "Técnico 2", "editable": True, "presentation": "dropdown"},
                {"name": "Técnico 3", "id": "Técnico 3", "editable": True, "presentation": "dropdown"}
            ],
            data=df_cron.to_dict('records') if not df_cron.empty else [],
            dropdown={
                'Etapa': {'options': [{'label': i, 'value': i} for i in opciones_etapa_lista]},
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
    @app.callback(
        [Output('tabla-funnel-activo', 'data'),
         Output('drop-act-lic', 'options'),
         Output('msj-interaccion', 'children'),
         Output('msj-interaccion', 'style'),
         Output('drop-act-lic', 'value'),
         Output('drop-act-etapa', 'value'),
         Output('drop-act-t1', 'value'),
         Output('drop-act-t2', 'value'),
         Output('drop-act-t3', 'value'),
         Output('drop-act-lic', 'placeholder'),
         Output('tabla-funnel-activo', 'selected_rows')],
        [Input('btn-activar', 'n_clicks'),
         Input('btn-guardar-edicion', 'n_clicks'),
         Input('btn-eliminar', 'n_clicks')],
        [State('drop-act-lic', 'value'),
         State('drop-act-etapa', 'value'),
         State('drop-act-t1', 'value'),
         State('drop-act-t2', 'value'),
         State('drop-act-t3', 'value'),
         State('tabla-funnel-activo', 'data'),
         State('tabla-funnel-activo', 'selected_rows')]
    )
    def gestor_maestro_funnel(n_activar, n_guardar, n_eliminar, cod_lic, etapa, t1, t2, t3, tabla_data, filas_seleccionadas):
        trigger = ctx.triggered_id
        if not trigger:
            raise dash.exceptions.PreventUpdate

        df_bbdd, df_cron, df_eq, error_sistema = leer_datos_completos()
        estilo_msg = {'marginBottom': '24px', 'fontWeight': 'bold', 'fontFamily': 'var(--font-family)', 'fontSize': '13px'}
        
        if error_sistema:
            estilo_msg['color'] = 'var(--semantic-negative)'
            return dash.no_update, dash.no_update, error_sistema, estilo_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        for col in [COL_CODIGO, COL_NOMBRE, 'Técnico 1', 'Técnico 2', 'Técnico 3', 'Etapa']:
            if col not in df_cron.columns: df_cron[col] = ""

        def depurar_celda(valor):
            if pd.isna(valor) or valor is None or str(valor).strip() == "" or str(valor).strip().lower() == "none":
                return ""
            return str(valor).strip()

        mensaje = ""
        exito = False

        # --- FLUJO 1: ACTIVAR NUEVA LICITACIÓN ---
        if trigger == 'btn-activar':
            if not cod_lic or not etapa:
                estilo_msg['color'] = 'var(--semantic-negative)'
                return dash.no_update, dash.no_update, "⚠️ Selecciona una licitación y una etapa para poder activarla.", estilo_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

            t1_val, t2_val, t3_val = depurar_celda(t1), depurar_celda(t2), depurar_celda(t3)
            hay_tecnicos = bool(t1_val or t2_val or t3_val)
            
            if etapa != 'Pendiente Asignar' and not hay_tecnicos:
                estilo_msg['color'] = 'var(--semantic-negative)'
                return dash.no_update, dash.no_update, f"⚠️ Error: Para asignar la etapa '{etapa}', debes seleccionar al menos un técnico.", estilo_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
            if etapa == 'Pendiente Asignar':
                t1_val = t2_val = t3_val = ""

            cod_lic_str = str(cod_lic).strip()
            fila_virgen = df_bbdd[df_bbdd[COL_CODIGO] == cod_lic_str].copy()
            
            if fila_virgen.empty:
                estilo_msg['color'] = 'var(--semantic-negative)'
                return dash.no_update, dash.no_update, "⚠️ Error crítico: La licitación no existe en la BBDD.", estilo_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

            fila_virgen['Etapa'] = etapa
            fila_virgen['Técnico 1'] = t1_val
            fila_virgen['Técnico 2'] = t2_val
            fila_virgen['Técnico 3'] = t3_val

            df_cron = pd.concat([df_cron, fila_virgen], ignore_index=True)
            mensaje = f"🚀 ¡Licitación {cod_lic} activada en el funnel!"
            estilo_msg['color'] = 'var(--semantic-positive)'
            exito = True

        # --- FLUJO 2: GUARDAR EDICIÓN EN LÍNEA ---
        elif trigger == 'btn-guardar-edicion':
            df_editado = pd.DataFrame(tabla_data)
            
            for _, row in df_editado.iterrows():
                cod_actual = str(row[COL_CODIGO]).strip()
                etapa_actual = depurar_celda(row.get('Etapa'))
                hay_tecnicos_fila = bool(depurar_celda(row.get('Técnico 1')) or depurar_celda(row.get('Técnico 2')) or depurar_celda(row.get('Técnico 3')))

                if etapa_actual != 'Pendiente Asignar' and not hay_tecnicos_fila:
                    estilo_msg['color'] = 'var(--semantic-negative)'
                    return dash.no_update, dash.no_update, f"⚠️ Error en tabla ({cod_actual}): La etapa '{etapa_actual}' exige seleccionar al menos un técnico en su fila.", estilo_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

            for _, row in df_editado.iterrows():
                cod_actual_str = str(row[COL_CODIGO]).strip()
                mask = df_cron[COL_CODIGO] == cod_actual_str
                
                etapa_actual = depurar_celda(row.get('Etapa'))
                t1_val = depurar_celda(row.get('Técnico 1'))
                t2_val = depurar_celda(row.get('Técnico 2'))
                t3_val = depurar_celda(row.get('Técnico 3'))
                
                if etapa_actual == 'Pendiente Asignar':
                    t1_val = t2_val = t3_val = ""
                
                df_cron.loc[mask, 'Etapa'] = etapa_actual
                df_cron.loc[mask, 'Técnico 1'] = t1_val
                df_cron.loc[mask, 'Técnico 2'] = t2_val
                df_cron.loc[mask, 'Técnico 3'] = t3_val
            
            mensaje = "💾 ¡Cambios de la tabla guardados correctamente!"
            estilo_msg['color'] = 'var(--semantic-positive)'
            exito = True

        # --- FLUJO 3: ELIMINAR DEL FUNNEL ---
        elif trigger == 'btn-eliminar':
            if not filas_seleccionadas:
                estilo_msg['color'] = 'var(--semantic-negative)'
                return dash.no_update, dash.no_update, "⚠️ Selecciona al menos una fila en la tabla para eliminar.", estilo_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
            codigos_a_borrar = [str(tabla_data[i][COL_CODIGO]).strip() for i in filas_seleccionadas]
            df_cron = df_cron[~df_cron[COL_CODIGO].isin(codigos_a_borrar)]
            
            mensaje = f"🗑️ ¡{len(codigos_a_borrar)} proyecto(s) devuelto(s) a la BBDD!"
            estilo_msg['color'] = 'var(--semantic-negative)' 
            exito = True

        # --- ESCRITURA GLOBAL EN DISCO ---
        if exito:
            df_vac = pd.DataFrame()
            try:
                with pd.ExcelFile(ARCHIVO_EXCEL, engine='openpyxl') as xls:
                    hojas = {sheet.lower().strip(): sheet for sheet in xls.sheet_names}
                    if 'vacaciones' in hojas: df_vac = pd.read_excel(xls, sheet_name=hojas['vacaciones'])
            except Exception: pass

            try:
                with pd.ExcelWriter(ARCHIVO_EXCEL, engine='openpyxl', mode='w') as writer:
                    df_bbdd.to_excel(writer, sheet_name='bbdd', index=False)
                    df_cron.to_excel(writer, sheet_name='cronograma', index=False)
                    if not df_eq.empty: df_eq.to_excel(writer, sheet_name='equipo', index=False)
                    if not df_vac.empty: df_vac.to_excel(writer, sheet_name='vacaciones', index=False)
            except PermissionError:
                exito = False
                mensaje = "⚠️ ERROR AL GUARDAR: Cierra el archivo Excel en tu ordenador."
                estilo_msg['color'] = 'var(--semantic-negative)'

        if not exito:
            return dash.no_update, dash.no_update, mensaje, estilo_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # Actualizar componentes de UI
        nuevas_opciones = []
        codigos_activos = df_cron[COL_CODIGO].tolist()
        df_disponibles = df_bbdd[~df_bbdd[COL_CODIGO].isin(codigos_activos)]
        for _, row in df_disponibles.iterrows():
            if pd.notna(row.get(COL_CODIGO)) and str(row.get(COL_CODIGO)).strip() != "" and str(row.get(COL_CODIGO)).lower() != "nan":
                codigo = str(row[COL_CODIGO])
                nombre = str(row.get(COL_NOMBRE, 'Sin Nombre'))
                etiqueta = f"{codigo} - {nombre}"
                nuevas_opciones.append({'label': etiqueta, 'value': codigo})

        placeholder_actualizado = "✅ Todos los proyectos de la BBDD ya están en el Funnel" if len(nuevas_opciones) == 0 else "Buscar por código o nombre..."

        val_reset = "" if trigger == 'btn-activar' else dash.no_update
        filas_reset = [] if trigger == 'btn-eliminar' else dash.no_update

        return df_cron.to_dict('records'), nuevas_opciones, mensaje, estilo_msg, val_reset, val_reset, val_reset, val_reset, val_reset, placeholder_actualizado, filas_reset