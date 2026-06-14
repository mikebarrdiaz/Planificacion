from dash import html, dcc, dash_table, Input, Output, State, ctx
import dash
import pandas as pd
from utils.data_manager import leer_excel, ARCHIVO_EXCEL

def generar_opciones_borrado(df_equipo):
    """Genera las opciones para el desplegable de eliminar basado en los datos reales."""
    if df_equipo.empty:
        return []
    return [{'label': f"{row['ID_Tecnico']} - {row['Nombre']}", 'value': row['ID_Tecnico']} 
            for _, row in df_equipo.iterrows() if pd.notna(row.get('ID_Tecnico'))]

def layout():
    _, df_equipo, _ = leer_excel()
    
    opciones_borrar = generar_opciones_borrado(df_equipo)
    
    # Definición de columnas limpia para la tabla
    columnas_tabla = [{"name": i, "id": i} for i in df_equipo.columns] if not df_equipo.empty else []

    # Opciones fijas para el pick list de Perfil / Rol
    opciones_roles = [
        {'label': 'Business Area Manager', 'value': 'Business Area Manager'},
        {'label': 'Bidding Technician', 'value': 'Bidding Technician'}
    ]

    return html.Div([
        # Título consolidado con clase
        html.H3("Directorio del Equipo Técnico", className="serveo-titulo-pagina"),
        
        # --- PANEL DE CONTROL DUAL ---
        html.Div([
            
            # BLOQUE IZQUIERDO: Añadir Técnico
            html.Div([
                html.Div("Dar de Alta Nuevo Técnico", style={'color': '#FFFFFF', 'backgroundColor': 'var(--text-border)', 'padding': '8px 16px', 'fontSize': '9px', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'marginBottom': '24px', 'borderRadius': '6px', 'display': 'inline-block'}),
                
                # Fila de Inputs
                html.Div([
                    html.Div([
                        html.Label("ID Técnico", className="etiqueta-dato"),
                        dcc.Input(id='input-id', placeholder='Ej. TEC-01', className="input-filtro")
                    ], className="serveo-input-wrapper", style={'flex': '1'}),
                    
                    html.Div([
                        html.Label("Nombre Completo", className="etiqueta-dato"),
                        dcc.Input(id='input-nombre', placeholder='Nombre y apellidos', className="input-filtro")
                    ], className="serveo-input-wrapper", style={'flex': '2'}),
                    
                    # --- MODIFICACIÓN: dcc.Input cambiado por dcc.Dropdown ---
                    html.Div([
                        html.Label("Perfil / Rol", className="etiqueta-dato"),
                        dcc.Dropdown(
                            id='input-perfil', 
                            options=opciones_roles, 
                            placeholder='Selecciona rol...',
                            clearable=True,
                            searchable=False # Al ser solo dos opciones, desactivar búsqueda da un look más limpio
                        )
                    ], className="serveo-input-wrapper", style={'flex': '2'}),
                    
                    html.Div([
                        html.Label("Horas/Día", className="etiqueta-dato"),
                        dcc.Input(id='input-horas', placeholder='Ej. 8', type='number', className="input-filtro")
                    ], className="serveo-input-wrapper", style={'flex': '1'})
                ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '24px'}),
                
                html.Button('Añadir al Equipo', id='btn-anadir', n_clicks=0, className="btn-serveo-primario", style={'float': 'right'})
                
            ], className="serveo-panel-accion", style={'flex': '2', 'marginBottom': '0'}),

            # BLOQUE DERECHO: Eliminar Técnico
            html.Div([
                html.Div("Baja de Técnico", style={'color': '#FFFFFF', 'backgroundColor': 'var(--semantic-negative)', 'padding': '8px 16px', 'fontSize': '9px', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'marginBottom': '24px', 'borderRadius': '6px', 'display': 'inline-block'}),
                
                html.Div([
                    html.Label("Seleccionar para eliminar:", className="etiqueta-dato"),
                    dcc.Dropdown(id='drop-eliminar-id', options=opciones_borrar, placeholder="Busca por ID o Nombre...")
                ], className="serveo-input-wrapper", style={'marginBottom': '24px'}),
                
                html.Button('Eliminar del Sistema', id='btn-eliminar', n_clicks=0, className="btn-serveo-negativo", style={'width': '100%'})
                
            ], className="serveo-panel-accion", style={'flex': '1', 'marginBottom': '0'})
            
        ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '32px'}),
        
        # Chivato de notificaciones
        html.Div(id='mensaje-equipo', style={'marginBottom': '24px', 'fontWeight': 'bold', 'fontFamily': 'var(--font-family)', 'fontSize': '13px'}),
        
        # --- TABLA DEL DIRECTORIO ---
        html.H3("Plantilla Actual", className="serveo-titulo-seccion"),
        dash_table.DataTable(
            id='tabla-directorio',
            data=df_equipo.to_dict('records'),
            columns=columnas_tabla,
            style_header={
                'backgroundColor': 'var(--card-divider)', 'color': 'var(--text-border)', 'fontWeight': 'bold', 
                'border': 'var(--border-solid)', 'fontFamily': 'var(--font-family)', 
                'fontSize': '9px', 'textTransform': 'uppercase', 'textAlign': 'left'
            },
            style_cell={
                'backgroundColor': 'var(--bg-main)', 'color': 'var(--text-border)', 'border': '1px solid var(--card-divider)', 
                'padding': '12px 16px', 'textAlign': 'left', 'fontFamily': 'var(--font-family)', 
                'fontSize': '13px'
            },
            style_table={'overflowX': 'auto', 'borderRadius': 'var(--radius-interactive)', 'border': 'var(--border-solid)'}
        )
    ], style={'paddingBottom': '40px'})

def register_callbacks(app):
    @app.callback(
        [Output('tabla-directorio', 'data'),
         Output('tabla-directorio', 'columns'),
         Output('drop-eliminar-id', 'options'),
         Output('mensaje-equipo', 'children'),
         Output('mensaje-equipo', 'style'),
         # Limpieza de inputs al terminar la acción
         Output('input-id', 'value'),
         Output('input-nombre', 'value'),
         Output('input-perfil', 'value'),
         Output('input-horas', 'value'),
         Output('drop-eliminar-id', 'value')],
        [Input('btn-anadir', 'n_clicks'),
         Input('btn-eliminar', 'n_clicks')],
        [State('input-id', 'value'),
         State('input-nombre', 'value'),
         State('input-perfil', 'value'),
         State('input-horas', 'value'),
         State('drop-eliminar-id', 'value')]
    )
    def gestionar_equipo(btn_add, btn_del, i_id, i_nom, i_perf, i_hor, del_id):
        trigger = ctx.triggered_id
        if not trigger:
            raise dash.exceptions.PreventUpdate

        _, df_eq, _ = leer_excel()
        mensaje = ""
        estilo_mensaje = {'marginBottom': '24px', 'fontWeight': 'bold', 'fontFamily': 'var(--font-family)', 'fontSize': '13px'}

        c_id, c_nom, c_perf, c_hor, c_del = dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # ====================
        # AÑADIR
        # ====================
        if trigger == 'btn-anadir':
            if not i_id or not i_nom:
                estilo_mensaje['color'] = 'var(--semantic-negative)'
                return dash.no_update, dash.no_update, dash.no_update, "⚠️ El ID y el Nombre son obligatorios.", estilo_mensaje, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
                
            if not df_eq.empty and i_id in df_eq['ID_Tecnico'].astype(str).values:
                estilo_mensaje['color'] = 'var(--semantic-negative)'
                return dash.no_update, dash.no_update, dash.no_update, f"⚠️ Error: El ID {i_id} ya existe en el sistema.", estilo_mensaje, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

            # El valor de i_perf vendrá ahora sanitizado de la pick list fija
            nueva_fila = pd.DataFrame([{'ID_Tecnico': i_id, 'Nombre': i_nom, 'Perfil Técnico': i_perf, 'Horas_Jornada': i_hor}])
            df_eq = pd.concat([df_eq, nueva_fila], ignore_index=True)
            mensaje = f"✅ Técnico {i_nom} dado de alta con éxito."
            estilo_mensaje['color'] = 'var(--semantic-positive)'
            c_id, c_nom, c_perf, c_hor = "", "", None, "" # Reseteamos el dropdown devolviéndolo a None

        # ====================
        # ELIMINAR
        # ====================
        elif trigger == 'btn-eliminar':
            if not del_id:
                estilo_mensaje['color'] = 'var(--semantic-negative)'
                return dash.no_update, dash.no_update, dash.no_update, "⚠️ Selecciona un técnico del desplegable para eliminar.", estilo_mensaje, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
                
            if del_id in df_eq['ID_Tecnico'].astype(str).values:
                df_eq = df_eq[df_eq['ID_Tecnico'].astype(str) != str(del_id)]
                mensaje = f"💾 Técnico con ID {del_id} eliminado del directorio."
                estilo_mensaje['color'] = 'var(--semantic-positive)'
                c_del = None
            else:
                estilo_mensaje['color'] = 'var(--semantic-negative)'
                mensaje = "⚠️ ID no encontrado en la base de datos."

        # ====================
        # GUARDADO SEGURO
        # ====================
        try:
            with pd.ExcelFile(ARCHIVO_EXCEL, engine='openpyxl') as xls:
                df_bbdd = pd.read_excel(xls, sheet_name='bbdd') if 'bbdd' in xls.sheet_names else pd.DataFrame()
                df_cron = pd.read_excel(xls, sheet_name='cronograma') if 'cronograma' in xls.sheet_names else pd.DataFrame()
                df_vac = pd.read_excel(xls, sheet_name='vacaciones') if 'vacaciones' in xls.sheet_names else pd.DataFrame()

            with pd.ExcelWriter(ARCHIVO_EXCEL, engine='openpyxl', mode='w') as writer:
                if not df_bbdd.empty: df_bbdd.to_excel(writer, sheet_name='bbdd', index=False)
                df_cron.to_excel(writer, sheet_name='cronograma', index=False)
                df_eq.to_excel(writer, sheet_name='equipo', index=False)
                df_vac.to_excel(writer, sheet_name='vacaciones', index=False)
                
        except PermissionError:
            mensaje = "⚠️ ERROR: El archivo Excel está abierto. Ciérralo y vuelve a intentarlo."
            estilo_mensaje['color'] = 'var(--semantic-negative)'
            _, df_eq, _ = leer_excel()

        columnas = [{"name": i, "id": i} for i in df_eq.columns] if not df_eq.empty else []
        nuevas_opciones = generar_opciones_borrado(df_eq)

        return df_eq.to_dict('records'), columnas, nuevas_opciones, mensaje, estilo_mensaje, c_id, c_nom, c_perf, c_hor, c_del