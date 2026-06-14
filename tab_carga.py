import dash
from dash import html, dcc, dash_table, Input, Output, State
import plotly.express as px
import pandas as pd
from utils.data_manager import leer_excel, procesar_cronograma

# Orden estricto de colores SERVEO para gráficos
PALETA_GRAFICOS = ["#FF4E00", "#474751", "#CEC6C0", "#AEA4BF", "#6AAE7A", "#986F54", "#A9CEF4", "#FFD97D"]

def layout():
    _, df_eq, _ = leer_excel()
    
    opciones_tecnicos = []
    opciones_roles = []
    
    if not df_eq.empty:
        opciones_tecnicos = [{'label': row['Nombre'], 'value': row['Nombre']} for _, row in df_eq.iterrows()]
        
        if 'Perfil Técnico' in df_eq.columns:
            roles_unicos = df_eq['Perfil Técnico'].dropna().unique()
            opciones_roles = [{'label': r, 'value': r} for r in roles_unicos]

    return html.Div([
        # Título consolidado con clase
        html.H3("Análisis de Carga de Trabajo (FTE)", className="serveo-titulo-pagina"),
        
        # --- BARRA DE FILTROS SUPERIOR ---
        html.Div([
            html.Div([
                html.Label("Filtrar por Rol:", className="etiqueta-dato"),
                dcc.Dropdown(
                    id='drop-filtro-rol',
                    options=opciones_roles,
                    placeholder="Todos los roles...",
                    clearable=True,
                    multi=True
                )
            ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '250px', 'marginRight': '8px'}),
            
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
        ], className="contenedor-filtros", style={'backgroundColor': 'var(--card-divider)', 'alignItems': 'flex-end', 'justifyContent': 'flex-start'}),
        
        # --- GRÁFICOS CON ENVOLTORIO ESTANDARIZADO ---
        html.H4("Etapa: En Estudio", className="serveo-titulo-seccion", style={'marginTop': '32px'}),
        dcc.Graph(
            id='grafico-carga-estudio', 
            style={
                'border': 'var(--border-solid)', 
                'borderRadius': 'var(--radius-container)', 
                'padding': '16px', 
                'marginBottom': '32px',
                'backgroundColor': 'var(--bg-main)'
            }
        ),
        
        html.H4("Etapa: Estudio Previo", className="serveo-titulo-seccion"),
        dcc.Graph(
            id='grafico-carga-previo', 
            style={
                'border': 'var(--border-solid)', 
                'borderRadius': 'var(--radius-container)', 
                'padding': '16px',
                'backgroundColor': 'var(--bg-main)'
            }
        )
    ], style={'paddingBottom': '40px'})

def register_callbacks(app):
    
    # =====================================================================
    # CALLBACK 1: FILTROS EN CASCADA (Lógica de Interfaz)
    # =====================================================================
    @app.callback(
        [Output('drop-filtro-tec', 'options'),
         Output('drop-filtro-tec', 'value')],
        Input('drop-filtro-rol', 'value'),
        State('drop-filtro-tec', 'value')
    )
    def encadenar_filtros(roles_seleccionados, tecnicos_actuales):
        _, df_eq, _ = leer_excel()
        
        if df_eq.empty:
            return [], dash.no_update
            
        df_filtrado = df_eq.copy()
        if roles_seleccionados:
            if isinstance(roles_seleccionados, str):
                roles_seleccionados = [roles_seleccionados]
                
            if 'Perfil Técnico' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['Perfil Técnico'].isin(roles_seleccionados)]

        nuevas_opciones = [{'label': row['Nombre'], 'value': row['Nombre']} for _, row in df_filtrado.iterrows() if pd.notna(row.get('Nombre'))]
        nombres_validos = [opc['value'] for opc in nuevas_opciones]
        nuevos_valores_tecnicos = tecnicos_actuales
        
        if tecnicos_actuales:
            if isinstance(tecnicos_actuales, str):
                tecnicos_actuales = [tecnicos_actuales]
            
            nuevos_valores_tecnicos = [t for t in tecnicos_actuales if t in nombres_validos]
            if not nuevos_valores_tecnicos:
                nuevos_valores_tecnicos = None
                
        return nuevas_opciones, nuevos_valores_tecnicos


    # =====================================================================
    # CALLBACK 2: GENERACIÓN DE GRÁFICOS
    # =====================================================================
    @app.callback(
        [Output('grafico-carga-estudio', 'figure'),
         Output('grafico-carga-previo', 'figure')],
        [Input('drop-filtro-tec', 'value'),
         Input('drop-filtro-rol', 'value')]
    )
    def actualizar_grafico(tecnicos_seleccionados, roles_seleccionados):
        
        if tecnicos_seleccionados and isinstance(tecnicos_seleccionados, str):
            tecnicos_seleccionados = [tecnicos_seleccionados]
            
        if roles_seleccionados and isinstance(roles_seleccionados, str):
            roles_seleccionados = [roles_seleccionados]

        df_cron, df_eq, _ = leer_excel()
        
        def grafico_vacio(mensaje):
            fig = px.bar(title=mensaje)
            fig.update_layout(plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF', font=dict(family="Outfit", color="#474751"))
            return fig

        if df_cron.empty:
            return grafico_vacio("Sin datos de licitaciones"), grafico_vacio("Sin datos de licitaciones")

        dict_roles = {}
        if not df_eq.empty and 'Perfil Técnico' in df_eq.columns:
            dict_roles = dict(zip(df_eq['Nombre'], df_eq['Perfil Técnico']))

        df_maestro, col_calendario = procesar_cronograma(df_cron)

        registros = []
        for _, row in df_maestro.iterrows():
            # --- AQUI ESTA EL FIX: AÑADIDO BAM A LA LISTA ---
            tecnicos = [t for t in [row.get('BAM'), row.get('Técnico 1'), row.get('Técnico 2'), row.get('Técnico 3')] if pd.notna(t) and str(t).strip() != ""]
            num_tec = len(tecnicos)
            
            etapa = str(row.get('Etapa', 'Sin Etapa')).strip()
            
            if num_tec == 0:
                continue

            for dia in col_calendario:
                fte_total = row.get(dia, 0)
                if fte_total > 0:
                    fte_por_tec = round(fte_total / num_tec, 2)
                    for t in tecnicos:
                        rol_asignado = dict_roles.get(t, "Sin Rol")
                        
                        registros.append({
                            'Técnico': t,
                            'Rol': rol_asignado,
                            'Fecha': dia,
                            'Licitación': row['Código de Licitación'],
                            'Carga (FTE)': fte_por_tec,
                            'Etapa': etapa
                        })

        df_grafico = pd.DataFrame(registros)

        def generar_figura_por_etapa(etapa_objetivo):
            if df_grafico.empty:
                return grafico_vacio("No hay cargas asignadas en los próximos 60 días.")
            
            df_etapa = df_grafico[df_grafico['Etapa'] == etapa_objetivo]
            
            if df_etapa.empty:
                return grafico_vacio(f"No hay cargas en la etapa: {etapa_objetivo}")

            # Filtrado Dual
            if roles_seleccionados:
                df_etapa = df_etapa[df_etapa['Rol'].isin(roles_seleccionados)]
                if df_etapa.empty:
                    return grafico_vacio(f"Sin cargas para el rol seleccionado en: {etapa_objetivo}")

            if tecnicos_seleccionados:
                df_etapa = df_etapa[df_etapa['Técnico'].isin(tecnicos_seleccionados)]
                if df_etapa.empty:
                    return grafico_vacio(f"Sin cargas para el técnico seleccionado en: {etapa_objetivo}")

            # Lógica Dinámica de Títulos y Colores
            if tecnicos_seleccionados:
                color_var = 'Licitación'
                if len(tecnicos_seleccionados) == 1:
                    texto_titulo = tecnicos_seleccionados[0]
                elif len(tecnicos_seleccionados) <= 3:
                    texto_titulo = ", ".join(tecnicos_seleccionados)
                else:
                    texto_titulo = f"{len(tecnicos_seleccionados)} Técnicos seleccionados"
                titulo = f"Desglose de Carga ({etapa_objetivo}): {texto_titulo}"
                
            elif roles_seleccionados:
                color_var = 'Técnico' 
                if len(roles_seleccionados) == 1:
                    texto_titulo = roles_seleccionados[0]
                else:
                    texto_titulo = "Varios Roles"
                titulo = f"Carga Operativa - Rol: {texto_titulo} ({etapa_objetivo})"
                
            else:
                color_var = 'Técnico'
                titulo = f"Carga de Trabajo Global - {etapa_objetivo}"

            fig = px.bar(
                df_etapa,
                x='Fecha',
                y='Carga (FTE)',
                color=color_var,
                title=titulo,
                color_discrete_sequence=PALETA_GRAFICOS
            )

            fig.update_layout(
                plot_bgcolor='#FFFFFF',
                paper_bgcolor='#FFFFFF',
                font=dict(family="Outfit", color="#474751"),
                title_font_color="#FF4E00",
                xaxis_title="",
                yaxis_title="Esfuerzo (FTE)",
                legend_title_text='Desglose',
                xaxis=dict(showgrid=True, gridcolor="#F0EEED", tickangle=-45),
                yaxis=dict(showgrid=True, gridcolor="#F0EEED")
            )
            return fig

        return generar_figura_por_etapa("En estudio"), generar_figura_por_etapa("Estudio previo")