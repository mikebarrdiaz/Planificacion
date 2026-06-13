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

    return html.Div([
        html.H3("Directorio del Equipo Técnico", style={'color': '#FF4E00', 'fontSize': '12px', 'textTransform': 'uppercase', 'fontFamily': "'Outfit', sans-serif", 'marginBottom': '24px'}),
        
        # --- PANEL DE CONTROL DUAL ---
        html.Div([
            
            # BLOQUE IZQUIERDO: Añadir Técnico
            html.Div([
                html.Div("Dar de Alta Nuevo Técnico", style={'color': '#FFFFFF', 'backgroundColor': '#474751', 'padding': '8px 16px', 'fontSize': '9px', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'marginBottom': '16px', 'borderRadius': '6px'}),
                
                html.Div([
                    html.Div([
                        html.Label("ID Técnico", style={'fontWeight': 'bold', 'color': '#474751', 'fontSize': '9px', 'textTransform': 'uppercase', 'marginBottom': '8px', 'display': 'block'}),
                        dcc.Input(id='input-id', placeholder='Ej. TEC-01', style={'fontFamily': "'Outfit', sans-serif", 'borderRadius': '6px', 'border': '1px solid #474751', 'padding': '8px 12px', 'width': '100%', 'boxSizing': 'border-box'})
                    ], style={'width': '20%', 'marginRight': '16px'}),
                    
                    html.Div([
                        html.Label("Nombre Completo", style={'fontWeight': 'bold', 'color': '#474751', 'fontSize': '9px', 'textTransform': 'uppercase', 'marginBottom': '8px', 'display': 'block'}),
                        dcc.Input(id='input-nombre', placeholder='Nombre y apellidos', style={'fontFamily': "'Outfit', sans-serif", 'borderRadius': '6px', 'border': '1px solid #474751', 'padding': '8px 12px', 'width': '100%', 'boxSizing': 'border-box'})
                    ], style={'width': '35%', 'marginRight': '16px'}),
                    
                    html.Div([
                        html.Label("Perfil / Rol", style={'fontWeight': 'bold', 'color': '#474751', 'fontSize': '9px', 'textTransform': 'uppercase', 'marginBottom': '8px', 'display': 'block'}),
                        dcc.Input(id='input-perfil', placeholder='Ej. Ingeniero Senior', style={'fontFamily': "'Outfit', sans-serif", 'borderRadius': '6px', 'border': '1px solid #474751', 'padding': '8px 12px', 'width': '100%', 'boxSizing': 'border-box'})
                    ], style={'width': '25%', 'marginRight': '16px'}),
                    
                    html.Div([
                        html.Label("Horas/Día", style={'fontWeight': 'bold', 'color': '#474751', 'fontSize': '9px', 'textTransform': 'uppercase', 'marginBottom': '8px', 'display': 'block'}),
                        dcc.Input(id='input-horas', placeholder='Ej. 8', type='number', style={'fontFamily': "'Outfit', sans-serif", 'borderRadius': '6px', 'border': '1px solid #474751', 'padding': '8px 12px', 'width': '100%', 'boxSizing': 'border-box'})
                    ], style={'width': '15%'})
                ], style={'display': 'flex', 'marginBottom': '16px'}),
                
                html.Button('Añadir al Equipo', id='btn-anadir', n_clicks=0, style={'backgroundColor': '#4383F0', 'color': '#FFFFFF', 'border': 'none', 'padding': '8px 24px', 'cursor': 'pointer', 'fontFamily': "'Outfit', sans-serif", 'fontWeight': 'bold', 'textTransform': 'uppercase', 'fontSize': '11px', 'borderRadius': '999px', 'float': 'right'})
                
            ], style={'width': '65%', 'padding': '24px', 'backgroundColor': '#FFFFFF', 'border': '1px solid #474751', 'borderRadius': '12px', 'marginRight': '24px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'}),

            # BLOQUE DERECHO: Eliminar Técnico
            html.Div([
                html.Div("Baja de Técnico", style={'color': '#FFFFFF', 'backgroundColor': '#DB563A', 'padding': '8px 16px', 'fontSize': '9px', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'marginBottom': '16px', 'borderRadius': '6px'}),
                
                html.Label("Seleccionar para eliminar:", style={'fontWeight': 'bold', 'color': '#474751', 'fontSize': '9px', 'textTransform': 'uppercase', 'marginBottom': '8px', 'display': 'block'}),
                dcc.Dropdown(id='drop-eliminar-id', options=opciones_borrar, placeholder="Busca por ID o Nombre...", style={'fontFamily': "'Outfit', sans-serif", 'borderRadius': '6px', 'border': '1px solid #474751', 'marginBottom': '24px'}),
                
                html.Button('Eliminar del Sistema', id='btn-eliminar', n_clicks=0, style={'backgroundColor': '#DB563A', 'color': '#FFFFFF', 'border': 'none', 'padding': '8px 24px', 'cursor': 'pointer', 'fontFamily': "'Outfit', sans-serif", 'fontWeight': 'bold', 'textTransform': 'uppercase', 'fontSize': '11px', 'borderRadius': '999px', 'width': '100%'})
                
            ], style={'width': '35%', 'padding': '24px', 'backgroundColor': '#FFFFFF', 'border': '1px solid #474751', 'borderRadius': '12px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'})
            
        ], style={'display': 'flex', 'padding': '24px', 'backgroundColor': '#F0EEED', 'borderRadius': '12px', 'border': '1px solid #474751', 'marginBottom': '24px'}),
        
        # Chivato de notificaciones
        html.Div(id='mensaje-equipo', style={'marginBottom': '24px', 'fontWeight': 'bold', 'fontFamily': "'Outfit', sans-serif", 'fontSize': '13px'}),
        
        # --- TABLA DEL DIRECTORIO ---
        html.H3("Plantilla Actual", style={'color': '#474751', 'fontSize': '10px', 'textTransform': 'uppercase', 'fontFamily': "'Outfit', sans-serif", 'marginBottom': '16px'}),
        dash_table.DataTable(
            id='tabla-directorio',
            data=df_equipo.to_dict('records'),
            columns=columnas_tabla,
            style_header={
                'backgroundColor': '#FFFFFF', 'color': '#FF4E00', 'fontWeight': 'bold', 
                'border': '1px solid #474751', 'fontFamily': "'Outfit', sans-serif", 
                'fontSize': '9px', 'textTransform': 'uppercase', 'textAlign': 'left'
            },
            style_cell={
                'backgroundColor': '#FFFFFF', 'color': '#474751', 'border': '1px solid #474751', 
                'padding': '12px 16px', 'textAlign': 'left', 'fontFamily': "'Outfit', sans-serif", 
                'fontSize': '13px'
            },
            style_table={'overflowX': 'auto', 'borderRadius': '6px'}
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

        # Lectura segura
        _, df_eq, _ = leer_excel()
        mensaje = ""
        estilo_mensaje = {'marginBottom': '24px', 'fontWeight': 'bold', 'fontFamily': "'Outfit', sans-serif", 'fontSize': '13px'}

        # Variables para limpiar los inputs
        c_id, c_nom, c_perf, c_hor, c_del = dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # ====================
        # AÑADIR
        # ====================
        if trigger == 'btn-anadir':
            if not i_id or not i_nom:
                estilo_mensaje['color'] = '#DB563A'
                return dash.no_update, dash.no_update, dash.no_update, "⚠️ El ID y el Nombre son obligatorios.", estilo_mensaje, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
                
            # Verificar si el ID ya existe
            if not df_eq.empty and i_id in df_eq['ID_Tecnico'].astype(str).values:
                estilo_mensaje['color'] = '#DB563A'
                return dash.no_update, dash.no_update, dash.no_update, f"⚠️ Error: El ID {i_id} ya existe en el sistema.", estilo_mensaje, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

            nueva_fila = pd.DataFrame([{'ID_Tecnico': i_id, 'Nombre': i_nom, 'Perfil Técnico': i_perf, 'Horas_Jornada': i_hor}])
            df_eq = pd.concat([df_eq, nueva_fila], ignore_index=True)
            mensaje = f"✅ Técnico {i_nom} dado de alta con éxito."
            estilo_mensaje['color'] = '#4383F0'
            c_id, c_nom, c_perf, c_hor = "", "", "", "" # Limpiamos campos de inserción

        # ====================
        # ELIMINAR
        # ====================
        elif trigger == 'btn-eliminar':
            if not del_id:
                estilo_mensaje['color'] = '#DB563A'
                return dash.no_update, dash.no_update, dash.no_update, "⚠️ Selecciona un técnico del desplegable para eliminar.", estilo_mensaje, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
                
            if del_id in df_eq['ID_Tecnico'].astype(str).values:
                # Filtrar el DataFrame
                df_eq = df_eq[df_eq['ID_Tecnico'].astype(str) != str(del_id)]
                mensaje = f"💾 Técnico con ID {del_id} eliminado del directorio."
                estilo_mensaje['color'] = '#4383F0'
                c_del = None # Limpiamos el desplegable
            else:
                estilo_mensaje['color'] = '#DB563A'
                mensaje = "⚠️ ID no encontrado en la base de datos."

        # ====================
        # GUARDADO SEGURO
        # ====================
        try:
            # ¡REPARACIÓN CRÍTICA!: Leemos todo el archivo para no machacar la pestaña 'bbdd'
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
            estilo_mensaje['color'] = '#DB563A'
            _, df_eq, _ = leer_excel() # Revertimos cambios visuales si falla el guardado

        # Actualizamos la UI
        columnas = [{"name": i, "id": i} for i in df_eq.columns] if not df_eq.empty else []
        nuevas_opciones = generar_opciones_borrado(df_eq)

        return df_eq.to_dict('records'), columnas, nuevas_opciones, mensaje, estilo_mensaje, c_id, c_nom, c_perf, c_hor, c_del