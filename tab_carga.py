import dash
from dash import html, dcc, dash_table, Input, Output
import plotly.express as px
import pandas as pd
from utils.data_manager import leer_excel, procesar_cronograma

# Orden estricto de colores SERVEO para gráficos
PALETA_GRAFICOS = ["#FF4E00", "#474751", "#CEC6C0", "#AEA4BF", "#6AAE7A", "#986F54", "#A9CEF4", "#FFD97D"]

def layout():
    _, df_eq, _ = leer_excel()
    
    opciones_tecnicos = []
    if not df_eq.empty:
        opciones_tecnicos = [{'label': row['Nombre'], 'value': row['Nombre']} for _, row in df_eq.iterrows()]

    return html.Div([
        # Título consolidado con clase
        html.H3("Análisis de Carga de Trabajo (FTE)", className="serveo-titulo-pagina"),
        
        # --- BARRA DE FILTROS SUPERIOR ---
        html.Div([
            html.Div([
                html.Label("Filtrar por Técnico(s):", className="etiqueta-dato"),
                dcc.Dropdown(
                    id='drop-filtro-tec',
                    options=opciones_tecnicos,
                    placeholder="Mostrando todo el equipo...",
                    clearable=True,
                    className="input-filtro",
                    multi=True
                )
            ], className="grupo-filtro", style={'flex': 'none', 'width': '300px'})
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
    @app.callback(
        [Output('grafico-carga-estudio', 'figure'),
         Output('grafico-carga-previo', 'figure')],
        Input('drop-filtro-tec', 'value')
    )
    def actualizar_grafico(tecnicos_seleccionados):
        
        # 1. BLINDAJE DE VARIABLE SUPERIOR (El arreglo del UnboundLocalError)
        # Normalizamos a lista una sola vez en el scope principal.
        if tecnicos_seleccionados and isinstance(tecnicos_seleccionados, str):
            tecnicos_seleccionados = [tecnicos_seleccionados]

        df_cron, df_eq, _ = leer_excel()
        
        # Función de apoyo para gráficos vacíos con tu estilo
        def grafico_vacio(mensaje):
            fig = px.bar(title=mensaje)
            fig.update_layout(plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF', font=dict(family="Outfit", color="#474751"))
            return fig

        if df_cron.empty:
            return grafico_vacio("Sin datos de licitaciones"), grafico_vacio("Sin datos de licitaciones")

        df_maestro, col_calendario = procesar_cronograma(df_cron)

        # Transformar la matriz en un formato tabular
        registros = []
        for _, row in df_maestro.iterrows():
            tecnicos = [t for t in [row.get('Técnico 1'), row.get('Técnico 2'), row.get('Técnico 3')] if pd.notna(t) and str(t).strip() != ""]
            num_tec = len(tecnicos)
            
            # Rescatamos la etapa de la fila
            etapa = str(row.get('Etapa', 'Sin Etapa')).strip()
            
            if num_tec == 0:
                continue # Proyecto sin asignar

            # Distribuir la carga diaria
            for dia in col_calendario:
                fte_total = row.get(dia, 0)
                if fte_total > 0:
                    fte_por_tec = round(fte_total / num_tec, 2)
                    for t in tecnicos:
                        registros.append({
                            'Técnico': t,
                            'Fecha': dia,
                            'Licitación': row['Código de Licitación'],
                            'Carga (FTE)': fte_por_tec,
                            'Etapa': etapa
                        })

        df_grafico = pd.DataFrame(registros)

        # 2. Función constructora de gráficos
        def generar_figura_por_etapa(etapa_objetivo):
            if df_grafico.empty:
                return grafico_vacio("No hay cargas asignadas en los próximos 60 días.")
            
            # Filtramos por etapa
            df_etapa = df_grafico[df_grafico['Etapa'] == etapa_objetivo]
            
            if df_etapa.empty:
                return grafico_vacio(f"No hay cargas en la etapa: {etapa_objetivo}")

            # Filtrado por técnico (sin miedo a errores de scope porque solo 'leemos' la variable)
            if tecnicos_seleccionados:
                df_etapa = df_etapa[df_etapa['Técnico'].isin(tecnicos_seleccionados)]
                
                # Blindaje extra: Por si el técnico seleccionado no tiene cargas en esta etapa concreta
                if df_etapa.empty:
                    return grafico_vacio(f"Sin cargas para la selección en la etapa: {etapa_objetivo}")

                color_var = 'Licitación'
                
                if len(tecnicos_seleccionados) == 1:
                    texto_titulo = tecnicos_seleccionados[0]
                elif len(tecnicos_seleccionados) <= 3:
                    texto_titulo = ", ".join(tecnicos_seleccionados)
                else:
                    texto_titulo = f"{len(tecnicos_seleccionados)} Técnicos seleccionados"
                    
                titulo = f"Desglose de Carga ({etapa_objetivo}): {texto_titulo}"
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

            # Estilos directos de Plotly
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

        # 3. Retornamos las dos figuras por separado
        return generar_figura_por_etapa("En estudio"), generar_figura_por_etapa("Estudio previo")