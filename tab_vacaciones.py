from dash import html, dcc, dash_table, Input, Output, State, ctx
import dash
import plotly.express as px
import plotly.graph_objects as go
import datetime
import pandas as pd
from utils.data_manager import obtener_datos_eficiente, sincronizar_vacaciones

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
    if df_vacaciones.empty:
        return []
        
    opciones = []
    df_temp = df_vacaciones.copy()
    df_temp['fecha_limpia'] = pd.to_datetime(df_temp['Fecha_Inicio'], errors='coerce').dt.strftime('%Y-%m-%d')
    
    for _, row in df_temp.iterrows():
        if pd.isna(row['Nombre']) or pd.isna(row['fecha_limpia']): 
            continue
            
        val_key = f"{row['Nombre']}|{row['fecha_limpia']}"
        label_text = f"{row['Nombre']} (Desde: {row['fecha_limpia']}) - {row['Tipo_Ausencia']}"
        opciones.append({'label': label_text, 'value': val_key})
        
    return opciones

# --- RENDERS DE TARJETAS AGRUPADAS POR PERSONA ---
def generar_tarjetas_ausencias(df_vacaciones):
    if df_vacaciones.empty:
        return html.Div("No hay registros de ausencias activos en este momento.", 
                        style={'color': 'var(--gray-b3)', 'fontFamily': 'var(--font-family)', 'fontStyle': 'italic', 'padding': '16px'})

    tarjetas = []
    df_temp = df_vacaciones.copy()
    
    df_temp['Fecha_Inicio_dt'] = pd.to_datetime(df_temp['Fecha_Inicio'], errors='coerce')
    df_temp = df_temp.sort_values(by='Fecha_Inicio_dt', ascending=True)

    for nombre, grupo in df_temp.groupby('Nombre'):
        bloques_ausencias = []
        
        for _, row in grupo.iterrows():
            motivo = row.get('Tipo_Ausencia', 'Ausencia')
            
            if "VACACIONES" in str(motivo).upper():
                color_badge = 'var(--semantic-positive)'
                bg_badge = 'var(--semantic-positive-bg)'
            elif "BAJA" in str(motivo).upper():
                color_badge = 'var(--semantic-negative)'
                bg_badge = 'var(--semantic-negative-bg)'
            else:
                color_badge = 'var(--color-title)'
                bg_badge = 'var(--card-divider)'

            f_inicio = pd.to_datetime(row.get('Fecha_Inicio')).strftime('%d/%m/%Y') if pd.notna(row.get('Fecha_Inicio')) else "N/A"
            f_fin = pd.to_datetime(row.get('Fecha_Fin')).strftime('%d/%m/%Y') if pd.notna(row.get('Fecha_Fin')) else "N/A"

            bloque = html.Div([
                html.Span(f"{f_inicio} al {f_fin}", style={'fontSize': '12px', 'fontWeight': '600', 'color': 'var(--text-border)'}),
                html.Span(motivo, style={
                    'color': color_badge, 'backgroundColor': bg_badge, 
                    'padding': '2px 8px', 'borderRadius': 'var(--radius-pill)', 
                    'fontSize': '9px', 'fontWeight': '700', 'textTransform': 'uppercase'
                })
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'padding': '6px 0'})
            
            bloques_ausencias.append(bloque)

        tarjeta = html.Div([
            html.Div([
                html.Span(nombre, style={'fontWeight': '700', 'fontSize': '15px', 'color': 'var(--color-title)'}),
                html.Span(f"{len(bloques_ausencias)} Registro(s)", style={'fontSize': '10px', 'color': 'var(--gray-66)', 'textTransform': 'uppercase', 'fontWeight': 'bold'})
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '12px', 'borderBottom': '1px solid var(--text-border)', 'paddingBottom': '8px'}),
            
            html.Div(bloques_ausencias, style={'display': 'flex', 'flexDirection': 'column', 'gap': '4px'})
            
        ], className="card-serveo", style={'marginBottom': '0', 'boxShadow': '0 4px 12px rgba(71, 71, 81, 0.03)', 'padding': '20px'})
        
        tarjetas.append(tarjeta)

    return html.Div(tarjetas, style={
        'display': 'grid', 
        'gridTemplateColumns': 'repeat(auto-fill, minmax(310px, 1fr))', 
        'gap': '24px', 
        'marginBottom': '32px'
    })


def layout(rol='lector'):
    _, _, df_eq, df_vacaciones, _ = obtener_datos_eficiente(force_reload=False)
    
    nombres_equipo = df_eq['Nombre'].dropna().tolist() if not df_eq.empty else []
    
    opciones_tecnicos = [{'label': nombre, 'value': nombre} for nombre in nombres_equipo]
    tipos_ausencia = [{'label': 'Vacaciones', 'value': 'Vacaciones'}, {'label': 'Baja Médica', 'value': 'Baja Médica'}, {'label': 'Permiso Personal', 'value': 'Permiso Personal'}]

    figura_inicial = generar_grafico_vacaciones(df_vacaciones, nombres_equipo)
    opciones_borrar_inicial = generar_opciones_borrado(df_vacaciones)
    tarjetas_iniciales = generar_tarjetas_ausencias(df_vacaciones)

    # --- LÓGICA DE SEGURIDAD MANTENIENDO TU LAYOUT EXACTO ---
    # Si es editor, mantenemos tu estilo original. Si no, lo ocultamos.
    estilo_panel_dual = {'display': 'flex', 'gap': '24px', 'marginBottom': '32px'} if rol == 'editor' else {'display': 'none'}

    return html.Div([
        html.H3("Panel de Gestión de Ausencias", className="serveo-titulo-pagina"),
        
        # --- PANEL DE CONTROL DUAL ORIGINAL ---
        html.Div([
            
            # --- AÑADIR REGISTRO ---
            html.Div([
                html.Div("Añadir Nuevo Registro", style={'color': '#FFFFFF', 'backgroundColor': 'var(--text-border)', 'padding': '8px 16px', 'fontSize': '9px', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'marginBottom': '24px', 'borderRadius': '6px', 'display': 'inline-block'}),
                
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
            
        ], style=estilo_panel_dual), # <--- AQUÍ APLICAMOS LA REGLA SIN ROMPER LA ESTRUCTURA HTML
        
        # Chivato de notificaciones
        html.Div(id='msj-accion-vac', style={'marginBottom': '24px', 'fontWeight': 'bold', 'fontFamily': 'var(--font-family)', 'fontSize': '13px'}),
        
        # --- SECCIÓN DE TARJETAS INTEGRADAS POR PERSONA ---
        html.H3("Fichas de Disponibilidad de la Plantilla", className="serveo-titulo-seccion"),
        html.Div(id='contenedor-tarjetas-vacaciones', children=tarjetas_iniciales),
        
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
        [Output('contenedor-tarjetas-vacaciones', 'children', allow_duplicate=True),
         Output('grafico-vac', 'figure', allow_duplicate=True),
         Output('drop-del-vac', 'options', allow_duplicate=True),
         Output('msj-accion-vac', 'children', allow_duplicate=True),
         Output('msj-accion-vac', 'style', allow_duplicate=True),
         Output('in-vac-tec', 'value', allow_duplicate=True),
         Output('in-vac-fecha', 'start_date', allow_duplicate=True),
         Output('in-vac-fecha', 'end_date', allow_duplicate=True),
         Output('in-vac-tipo', 'value', allow_duplicate=True),
         Output('drop-del-vac', 'value', allow_duplicate=True)],
        [Input('btn-add-vac', 'n_clicks'),
         Input('btn-del-vac', 'n_clicks')],
        [State('in-vac-tec', 'value'),
         State('in-vac-fecha', 'start_date'),
         State('in-vac-fecha', 'end_date'),
         State('in-vac-tipo', 'value'),
         State('drop-del-vac', 'value')],
        prevent_initial_call=True
    )
    def orquestador_vacaciones(btn_add, btn_del, nombre, start_date, end_date, tipo, valor_borrar):
        trigger = ctx.triggered_id
        
        if not trigger:
            raise dash.exceptions.PreventUpdate

        _, _, df_eq, df_vac, error_sistema = obtener_datos_eficiente(force_reload=False)
        nombres = df_eq['Nombre'].dropna().tolist() if not df_eq.empty else []
        estilo_msg = {'marginBottom': '20px', 'fontWeight': 'bold', 'fontFamily': 'var(--font-family)', 'fontSize': '13px'}
        mensaje = ""

        if error_sistema:
            estilo_msg['color'] = 'var(--semantic-negative)'
            return dash.no_update, dash.no_update, dash.no_update, error_sistema, estilo_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        clear_tec, clear_start, clear_end, clear_tipo, clear_del = dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        exito = False

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
            df_vac['fecha_str'] = pd.to_datetime(df_vac['Fecha_Inicio'], errors='coerce').dt.strftime('%Y-%m-%d')
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

        if exito:
            _, _, df_eq, df_vac, _ = obtener_datos_eficiente(force_reload=True)

        # --- RE-RENDERIZADO AUTOMÁTICO ---
        html_tarjetas_actualizadas = generar_tarjetas_ausencias(df_vac)
        figura_actualizada = generar_grafico_vacaciones(df_vac, nombres)
        nuevas_opciones_borrado = generar_opciones_borrado(df_vac)

        return html_tarjetas_actualizadas, figura_actualizada, nuevas_opciones_borrado, mensaje, estilo_msg, clear_tec, clear_start, clear_end, clear_tipo, clear_del