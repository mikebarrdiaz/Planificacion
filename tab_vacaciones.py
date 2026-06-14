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
    
    # Mantenemos Hexadecimales en Plotly por compatibilidad interna de renderizado
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
    # Estandarizamos el string de la fecha desde el principio
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
        # Título consolidado con clase
        html.H3("Panel de Gestión de Ausencias", className="serveo-titulo-pagina"),
        
        # --- PANEL DE CONTROL DUAL ---
        html.Div([
            
            # --- AÑADIR REGISTRO ---
            html.Div([
                html.Div("Añadir Nuevo Registro", style={'color': '#FFFFFF', 'backgroundColor': 'var(--text-border)', 'padding': '8px 16px', 'fontSize': '9px', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'marginBottom': '24px', 'borderRadius': '6px', 'display': 'inline-block'}),
                
                # Fila de Inputs
                html.Div([
                    html.Div([
                        html.Label("Técnico", className="etiqueta-dato"),
                        dcc.Dropdown(id='in-vac-tec', options=opciones_tecnicos, placeholder="Técnico...")
                    ], className="serveo-input-wrapper", style={'flex': '2'}),
                    
                    html.Div([
                        html.Label("Fechas", className="etiqueta-dato"),
                        dcc.DatePickerRange(
                            id='in-vac-fecha', 
                            display_format='DD/MM/YYYY', 
                            style={'fontFamily': 'var(--font-family)', 'borderRadius': 'var(--radius-interactive)'}
                        )
                    ], className="serveo-input-wrapper", style={'flex': '2'}),
                    
                    html.Div([
                        html.Label("Tipo", className="etiqueta-dato"),
                        dcc.Dropdown(id='in-vac-tipo', options=tipos_ausencia, placeholder="Motivo...")
                    ], className="serveo-input-wrapper", style={'flex': '1'}),
                    
                    html.Button('Añadir', id='btn-add-vac', n_clicks=0, className="btn-serveo-primario", style={'alignSelf': 'flex-end', 'height': '32px'})
                ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '24px'})
                
            ], className="serveo-panel-accion", style={'flex': '2', 'marginBottom': '0'}),

            # --- ELIMINAR REGISTRO ---
            html.Div([
                html.Div("Eliminar Registro Existente", style={'color': '#FFFFFF', 'backgroundColor': 'var(--semantic-negative)', 'padding': '8px 16px', 'fontSize': '9px', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'marginBottom': '24px', 'borderRadius': '6px', 'display': 'inline-block'}),
                
                html.Div([
                    html.Label("Selecciona el registro a borrar:", className="etiqueta-dato"),
                    dcc.Dropdown(id='drop-del-vac', options=opciones_borrar_inicial, placeholder="Busca un registro activo...")
                ], className="serveo-input-wrapper", style={'marginBottom': '24px'}),
                
                html.Button('Eliminar Seleccionado', id='btn-del-vac', n_clicks=0, className="btn-serveo-negativo", style={'width': '100%'})
                
            ], className="serveo-panel-accion", style={'flex': '1', 'marginBottom': '0'})
            
        ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '32px'}),
        
        # Chivato de notificaciones
        html.Div(id='msj-accion-vac', style={'marginBottom': '24px', 'fontWeight': 'bold', 'fontFamily': 'var(--font-family)', 'fontSize': '13px'}),
        
        # --- TABLA REGISTROS ---
        html.H3("Registros Activos", className="serveo-titulo-seccion"),
        dash_table.DataTable(
            id='tabla-vac-readonly',
            columns=[
                {"name": "Técnico", "id": "Nombre"},
                {"name": "Inicio", "id": "Fecha_Inicio"},
                {"name": "Fin", "id": "Fecha_Fin"},
                {"name": "Motivo", "id": "Tipo_Ausencia"}
            ],
            data=datos_diccionario,
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
            style_table={'marginBottom': '32px', 'overflowX': 'auto', 'borderRadius': 'var(--radius-interactive)', 'border': 'var(--border-solid)'}
        ),
        
        # --- GRÁFICO GANTT ---
        dcc.Graph(
            id='grafico-vac', 
            figure=figura_inicial, 
            style={
                'border': 'var(--border-solid)', 
                'borderRadius': 'var(--radius-container)', 
                'padding': '16px', 
                'backgroundColor': 'var(--bg-main)'
            }
        )
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
        estilo_msg = {'marginBottom': '20px', 'fontWeight': 'bold', 'fontFamily': 'var(--font-family)', 'fontSize': '13px'}
        mensaje = ""

        # Retornos de limpieza por defecto
        clear_tec, clear_start, clear_end, clear_tipo, clear_del = dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # --- AÑADIR ---
        if trigger == 'btn-add-vac':
            if not all([nombre, start_date, end_date, tipo]):
                estilo_msg['color'] = 'var(--semantic-negative)'
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
                estilo_msg['color'] = 'var(--semantic-positive)'
                mensaje = f"✅ {nombre} añadido correctamente."
                clear_tec, clear_start, clear_end, clear_tipo = None, None, None, None
            else:
                estilo_msg['color'] = 'var(--semantic-negative)'
                mensaje = msj_sync

        # --- ELIMINAR ---
        elif trigger == 'btn-del-vac':
            if not valor_borrar:
                estilo_msg['color'] = 'var(--semantic-negative)'
                return dash.no_update, dash.no_update, dash.no_update, "⚠️ Selecciona un registro del desplegable para eliminar.", estilo_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
            tec_a_borrar, fecha_a_borrar = valor_borrar.split('|')
            
            # Normalizamos la fecha temporalmente para que el cruce sea 100% exacto
            df_vac['fecha_str'] = pd.to_datetime(df_vac['Fecha_Inicio'], errors='coerce').dt.strftime('%Y-%m-%d')
            
            # Aplicamos la eliminación
            df_vac = df_vac[~((df_vac['Nombre'] == tec_a_borrar) & (df_vac['fecha_str'] == fecha_a_borrar))]
            df_vac = df_vac.drop(columns=['fecha_str'])
            
            exito, msj_sync = sincronizar_vacaciones(df_vac.to_dict('records'))
            
            if exito:
                estilo_msg['color'] = 'var(--semantic-positive)'
                mensaje = f"💾 Registro de {tec_a_borrar} eliminado del sistema."
                clear_del = None
            else:
                estilo_msg['color'] = 'var(--semantic-negative)'
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