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
        html.H3("Análisis de Carga de Trabajo (FTE)", style={'color': '#FF4E00', 'fontSize': '12px', 'textTransform': 'uppercase', 'fontFamily': "'Outfit', sans-serif"}),
        
        html.Div([
            html.Label("Filtrar por Técnico:", style={'fontWeight': 'bold', 'color': '#474751', 'fontSize': '9px', 'textTransform': 'uppercase', 'marginBottom': '8px', 'display': 'block'}),
            dcc.Dropdown(
                id='drop-filtro-tec',
                options=opciones_tecnicos,
                placeholder="Mostrando todo el equipo...",
                clearable=True,
                style={'fontFamily': "'Outfit', sans-serif", 'border': '1px solid #474751', 'borderRadius': '0px', 'width': '300px'}
            )
        ], style={'marginBottom': '30px', 'padding': '15px', 'border': '1px solid #474751', 'backgroundColor': '#F0EEED'}),
        
        dcc.Graph(id='grafico-carga', style={'border': '1px solid #474751', 'padding': '10px'})
    ])

def register_callbacks(app):
    @app.callback(
        Output('grafico-carga', 'figure'),
        Input('drop-filtro-tec', 'value')
    )
    def actualizar_grafico(tecnico_seleccionado):
        df_cron, df_eq, _ = leer_excel()
        
        if df_cron.empty:
            return px.bar(title="Sin datos de licitaciones")

        df_maestro, col_calendario = procesar_cronograma(df_cron)

        # 1. Transformar la matriz en un formato tabular para Plotly
        registros = []
        for _, row in df_maestro.iterrows():
            # Extraer técnicos válidos asignados a esta licitación
            tecnicos = [t for t in [row.get('Técnico 1'), row.get('Técnico 2'), row.get('Técnico 3')] if pd.notna(t) and str(t).strip() != ""]
            num_tec = len(tecnicos)
            
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
                            'Carga (FTE)': fte_por_tec
                        })

        df_grafico = pd.DataFrame(registros)

        # 2. Renderizar el gráfico visual
        if df_grafico.empty:
            fig = px.bar(title="No hay cargas asignadas en los próximos 60 días.")
        else:
            if tecnico_seleccionado:
                df_grafico = df_grafico[df_grafico['Técnico'] == tecnico_seleccionado]
                color_var = 'Licitación'
                titulo = f"Desglose de Carga: {tecnico_seleccionado}"
            else:
                color_var = 'Técnico'
                titulo = "Carga de Trabajo Global del Equipo"

            fig = px.bar(
                df_grafico,
                x='Fecha',
                y='Carga (FTE)',
                color=color_var,
                title=titulo,
                color_discrete_sequence=PALETA_GRAFICOS
            )

        # Aplicación estricta de variables CSS globales al lienzo sin la línea de capacidad
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