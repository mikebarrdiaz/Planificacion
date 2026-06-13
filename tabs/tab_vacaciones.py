from dash import html, dcc, dash_table, Input, Output, State, ctx
import dash
import plotly.express as px
import plotly.graph_objects as go
import datetime
import pandas as pd
from utils.data_manager import leer_excel, sincronizar_vacaciones

def generar_grafico_vacaciones(df_vacaciones, nombres_equipo):
    if not nombres_equipo:
        fig = go.Figure()
        fig.update_layout(title="No hay equipo registrado.")
        return fig
        
    if df_vacaciones.empty:
        fig = go.Figure()
        fig.update_xaxes(type='date')
    else:
        df_vac = df_vacaciones.copy()
        df_vac['Fecha_Inicio'] = pd.to_datetime(df_vac['Fecha_Inicio'], errors='coerce')
        df_vac['Fecha_Fin'] = pd.to_datetime(df_vac['Fecha_Fin'], errors='coerce')
        df_vac = df_vac.dropna(subset=['Fecha_Inicio', 'Fecha_Fin'])
        
        if df_vac.empty:
            fig = go.Figure()
        else:
            fig = px.timeline(
                df_vac, 
                x_start="Fecha_Inicio", 
                x_end="Fecha_Fin", 
                y="Nombre", 
                color="Tipo_Ausencia",
                color_discrete_sequence=["#4383F0", "#FF4E00", "#CEC6C0"]
            )
        
    fig.update_yaxes(
        type='category',
        categoryorder='array',
        categoryarray=nombres_equipo,
        autorange="reversed"
    )
    
    hoy_str = datetime.date.today().strftime('%Y-%m-%d')
    fig.add_vline(x=hoy_str, line_width=2, line_dash="dash", line_color="#FF4E00", annotation_text="Hoy", annotation_position="top", annotation_font_color="#FF4E00", annotation_font_family="Outfit")
    
    fig.update_layout(
        plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
        font=dict(family="Outfit", color="#474751"),
        title="Cronograma de Ausencias Global", title_font_color="#FF4E00",
        xaxis=dict(showgrid=True, gridcolor="#F0EEED", title=""),
        yaxis=dict(showgrid=True, gridcolor="#F0EEED", title=""),
        margin=dict(t=50, b=20, l=20, r=20)
    )
    return fig

def generar_opciones_borrado(df_vacaciones):
    """Genera las opciones forzando el formato de fecha para asegurar un cruce exacto al borrar."""
    if df_vacaciones.empty:
        return []
        
    opciones = []
    df_temp = df_vacaciones.copy()
    # ESTA ES LA CLAVE: Estandarizamos el string de la fecha desde el principio
    df_temp['fecha_limpia'] = pd.to_datetime(df_temp['Fecha_Inicio'], errors='coerce').dt.strftime('%Y-%m-%d')
    
    for _, row in df_temp.iterrows():
        # Filtro de seguridad por si hay filas vacías perdidas en el Excel
        if pd.isna(row['Nombre']) or pd.isna(row['fecha_limpia']): 
            continue
            
        val_key = f"{row['Nombre']}|{row['fecha_limpia']}"
        label_text = f"{row['Nombre']} (Desde: {row['fecha_limpia']}) - {row['Tipo_Ausencia']}"
        opciones.append({'label': label_text, 'value': val_key})
        
    return opciones

def layout():
    _, df_eq, df_vacaciones = leer_excel()
    nombres_equipo = df_eq['Nombre'].dropna().tolist() if not df_eq.empty else []
    
    opciones_tecnicos = [{'label': nombre, 'value': nombre} for nombre in nombres_equipo]
    tipos_ausencia = [{'label': 'Vacaciones', 'value': 'Vacaciones'}, {'label': 'Baja Médica', 'value': 'Baja Médica'}, {'label': 'Permiso Personal', 'value': 'Permiso Personal'}]

    if not df_vacaciones.empty:
        df_vac_tabla = df_vacaciones.copy()
        df_vac_tabla['Fecha_Inicio'] = pd.to_datetime(df_vac_tabla['Fecha_Inicio'], errors='coerce').dt.strftime('%Y-%m-%d')
        df_vac_tabla['Fecha_Fin'] = pd.to_datetime(df_vac_tabla['Fecha_Fin'], errors='coerce').dt.strftime('%Y-%m-%d')
        df_vac_tabla = df_vac_tabla.fillna("")
        datos_diccionario = df_vac_tabla.to_dict('records')
    else:
        datos_diccionario = []

    figura_inicial = generar_grafico_vacaciones(df_vacaciones, nombres_equipo)
    opciones_borrar_inicial = generar_opciones_borrado(df_vacaciones)

    return html.Div([
        html.H3("Panel de Gestión de Ausencias", style={'color': '#FF4E00', 'fontSize': '12px', 'textTransform': 'uppercase', 'fontFamily': "'Outfit', sans-serif", 'marginBottom': '20px'}),
        
        html.Div([
            
            # --- AÑADIR REGISTRO ---
            html.Div([
                html.Div("Añadir Nuevo Registro", style={'color': '#FFFFFF', 'backgroundColor': '#474751', 'padding': '6px 12px', 'fontSize': '9px', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'marginBottom': '10px', 'borderRadius': '6px'}),
                html.Div([
                    html.Div([
                        html.Label("Técnico", style={'fontWeight': 'bold', 'color': '#474751', 'fontSize': '9px', 'textTransform': 'uppercase', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Dropdown(id='in-vac-tec', options=opciones_tecnicos, placeholder="Técnico...", style={'fontFamily': "'Outfit', sans-serif", 'borderRadius': '6px', 'border': '1px solid #474751'})
                    ], style={'width': '30%', 'marginRight': '10px'}),
                    
                    html.Div([
                        html.Label("Fechas", style={'fontWeight': 'bold', 'color': '#474751', 'fontSize': '9px', 'textTransform': 'uppercase', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.DatePickerRange(id='in-vac-fecha', display_format='DD/MM/YYYY', style={'fontFamily': "'Outfit', sans-serif", 'border': '1px solid #474751', 'borderRadius': '6px'})
                    ], style={'width': '35%', 'marginRight': '10px'}),
                    
                    html.Div([
                        html.Label("Tipo", style={'fontWeight': 'bold', 'color': '#474751', 'fontSize': '9px', 'textTransform': 'uppercase', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Dropdown(id='in-vac-tipo', options=tipos_ausencia, placeholder="Motivo...", style={'fontFamily': "'Outfit', sans-serif", 'borderRadius': '6px', 'border': '1px solid #474751'})
                    ], style={'width': '20%', 'marginRight': '10px'}),
                    
                    html.Button('Añadir', id='btn-add-vac', n_clicks=0, style={'backgroundColor': '#4383F0', 'color': '#FFFFFF', 'border': 'none', 'padding': '0 20px', 'cursor': 'pointer', 'fontFamily': "'Outfit', sans-serif", 'fontWeight': 'bold', 'textTransform': 'uppercase', 'fontSize': '11px', 'height': '36px', 'borderRadius': '999px', 'alignSelf': 'flex-end'})
                ], style={'display': 'flex', 'alignItems': 'flex-end'})
            ], style={'width': '65%', 'padding': '15px', 'backgroundColor': '#FFFFFF', 'border': '1px solid #474751', 'borderRadius': '12px', 'marginRight': '20px'}),

            # --- ELIMINAR REGISTRO ---
            html.Div([
                html.Div("Eliminar Registro Existente", style={'color': '#FFFFFF', 'backgroundColor': '#DB563A', 'padding': '6px 12px', 'fontSize': '9px', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'marginBottom': '10px', 'borderRadius': '6px'}),
                html.Label("Selecciona el registro a borrar:", style={'fontWeight': 'bold', 'color': '#474751', 'fontSize': '9px', 'textTransform': 'uppercase', 'marginBottom': '4px', 'display': 'block'}),
                dcc.Dropdown(id='drop-del-vac', options=opciones_borrar_inicial, placeholder="Busca un registro activo...", style={'fontFamily': "'Outfit', sans-serif", 'borderRadius': '6px', 'border': '1px solid #474751', 'marginBottom': '10px'}),
                html.Button('Eliminar Seleccionado', id='btn-del-vac', n_clicks=0, style={'backgroundColor': '#DB563A', 'color': '#FFFFFF', 'border': 'none', 'padding': '10px 20px', 'cursor': 'pointer', 'fontFamily': "'Outfit', sans-serif", 'fontWeight': 'bold', 'textTransform': 'uppercase', 'fontSize': '11px', 'width': '100%', 'borderRadius': '999px'})
            ], style={'width': '35%', 'padding': '15px', 'backgroundColor': '#FFFFFF', 'border': '1px solid #474751', 'borderRadius': '12px'})
            
        ], style={'display': 'flex', 'padding': '20px', 'backgroundColor': '#F0EEED', 'borderRadius': '12px', 'border': '1px solid #474751', 'marginBottom': '15px'}),
        
        html.Div(id='msj-accion-vac', style={'marginBottom': '20px', 'fontWeight': 'bold', 'fontFamily': "'Outfit', sans-serif", 'fontSize': '13px'}),
        
        html.H3("Registros Activos", style={'color': '#474751', 'fontSize': '10px', 'textTransform': 'uppercase', 'fontFamily': "'Outfit', sans-serif", 'marginBottom': '10px'}),
        dash_table.DataTable(
            id='tabla-vac-readonly',
            columns=[
                {"name": "Técnico", "id": "Nombre"},
                {"name": "Inicio", "id": "Fecha_Inicio"},
                {"name": "Fin", "id": "Fecha_Fin"},
                {"name": "Motivo", "id": "Tipo_Ausencia"}
            ],
            data=datos_diccionario,
            style_header={'backgroundColor': '#FFFFFF', 'color': '#FF4E00', 'fontWeight': 'bold', 'border': '1px solid #474751', 'fontFamily': "'Outfit', sans-serif", 'fontSize': '9px', 'textTransform': 'uppercase', 'textAlign': 'left'},
            style_cell={'backgroundColor': '#FFFFFF', 'color': '#474751', 'border': '1px solid #474751', 'padding': '8px 12px', 'textAlign': 'left', 'fontFamily': "'Outfit', sans-serif", 'fontSize': '12px'},
            style_table={'marginBottom': '30px', 'overflowX': 'auto', 'borderRadius': '6px'}
        ),
        
        dcc.Graph(id='grafico-vac', figure=figura_inicial, style={'border': '1px solid #474751', 'borderRadius': '12px'})
    ], style={'paddingBottom': '40px'})


def register_callbacks(app):
    @app.callback(
        [Output('tabla-vac-readonly', 'data'),
         Output('grafico-vac', 'figure'),
         Output('drop-del-vac', 'options'),
         Output('msj-accion-vac', 'children'),
         Output('msj-accion-vac', 'style'),
         # Limpiamos los inputs tras usarlos para que la UI quede fresca
         Output('in-vac-tec', 'value'),
         Output('in-vac-fecha', 'start_date'),
         Output('in-vac-fecha', 'end_date'),
         Output('in-vac-tipo', 'value'),
         Output('drop-del-vac', 'value')],
        [Input('btn-add-vac', 'n_clicks'),
         Input('btn-del-vac', 'n_clicks')],
        [State('in-vac-tec', 'value'),
         State('in-vac-fecha', 'start_date'),
         State('in-vac-fecha', 'end_date'),
         State('in-vac-tipo', 'value'),
         State('drop-del-vac', 'value')]
    )
    def orquestador_vacaciones(btn_add, btn_del, nombre, start_date, end_date, tipo, valor_borrar):
        trigger = ctx.triggered_id
        
        if not trigger:
            raise dash.exceptions.PreventUpdate

        _, df_eq, df_vac = leer_excel()
        nombres = df_eq['Nombre'].dropna().tolist() if not df_eq.empty else []
        estilo_msg = {'marginBottom': '20px', 'fontWeight': 'bold', 'fontFamily': "'Outfit', sans-serif", 'fontSize': '13px'}
        mensaje = ""

        # Retornos de limpieza por defecto
        clear_tec, clear_start, clear_end, clear_tipo, clear_del = dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # --- AÑADIR ---
        if trigger == 'btn-add-vac':
            if not all([nombre, start_date, end_date, tipo]):
                estilo_msg['color'] = '#DB563A'
                return dash.no_update, dash.no_update, dash.no_update, "⚠️ Completa todos los campos para añadir.", estilo_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
            id_tec = ""
            if not df_eq.empty:
                match = df_eq[df_eq['Nombre'] == nombre]
                if not match.empty:
                    id_tec = match.iloc[0].get('ID_Tecnico', '')

            nueva_fila = pd.DataFrame([{
                'ID_Tecnico': id_tec,
                'Nombre': nombre,
                'Fecha_Inicio': pd.to_datetime(start_date).strftime('%Y-%m-%d'),
                'Fecha_Fin': pd.to_datetime(end_date).strftime('%Y-%m-%d'),
                'Tipo_Ausencia': tipo
            }])
            
            df_vac = pd.concat([df_vac, nueva_fila], ignore_index=True)
            exito, msj_sync = sincronizar_vacaciones(df_vac.to_dict('records'))
            
            if exito:
                estilo_msg['color'] = '#4383F0'
                mensaje = f"✅ {nombre} añadido correctamente."
                clear_tec, clear_start, clear_end, clear_tipo = None, None, None, None
            else:
                estilo_msg['color'] = '#DB563A'
                mensaje = msj_sync

        # --- ELIMINAR ---
        elif trigger == 'btn-del-vac':
            if not valor_borrar:
                estilo_msg['color'] = '#DB563A'
                return dash.no_update, dash.no_update, dash.no_update, "⚠️ Selecciona un registro del desplegable para eliminar.", estilo_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
            tec_a_borrar, fecha_a_borrar = valor_borrar.split('|')
            
            # Normalizamos la fecha temporalmente para que el cruce sea 100% exacto
            df_vac['fecha_str'] = pd.to_datetime(df_vac['Fecha_Inicio'], errors='coerce').dt.strftime('%Y-%m-%d')
            
            # Aplicamos la eliminación
            df_vac = df_vac[~((df_vac['Nombre'] == tec_a_borrar) & (df_vac['fecha_str'] == fecha_a_borrar))]
            df_vac = df_vac.drop(columns=['fecha_str'])
            
            exito, msj_sync = sincronizar_vacaciones(df_vac.to_dict('records'))
            
            if exito:
                estilo_msg['color'] = '#4383F0'
                mensaje = f"💾 Registro de {tec_a_borrar} eliminado del sistema."
                clear_del = None
            else:
                estilo_msg['color'] = '#DB563A'
                mensaje = msj_sync

        # --- PREPARACIÓN VISUAL TRAS LOS CAMBIOS ---
        if not df_vac.empty:
            df_vac_str = df_vac.copy()
            df_vac_str['Fecha_Inicio'] = pd.to_datetime(df_vac_str['Fecha_Inicio'], errors='coerce').dt.strftime('%Y-%m-%d')
            df_vac_str['Fecha_Fin'] = pd.to_datetime(df_vac_str['Fecha_Fin'], errors='coerce').dt.strftime('%Y-%m-%d')
            df_vac_str = df_vac_str.fillna("")
            datos_tabla = df_vac_str.to_dict('records')
        else:
            datos_tabla = []
            
        figura_actualizada = generar_grafico_vacaciones(df_vac, nombres)
        nuevas_opciones_borrado = generar_opciones_borrado(df_vac)

        return datos_tabla, figura_actualizada, nuevas_opciones_borrado, mensaje, estilo_msg, clear_tec, clear_start, clear_end, clear_tipo, clear_del