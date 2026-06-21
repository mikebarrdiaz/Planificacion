import dash
from dash import html, dcc, dash_table, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.data_manager import obtener_datos_eficiente, procesar_cronograma
from utils.icons import icono

# --- ESTILO DE TARJETA BASE (estilo Salesforce / Lightning, look Serveo) ---
ESTILO_TARJETA = {
    'backgroundColor': '#FFFFFF',
    'border': '1px solid #e5e5e5',
    'borderRadius': 'var(--radius-container)',
    'boxShadow': '0 1px 2px rgba(71, 71, 81, 0.05)',
    'overflow': 'hidden'
}

ESTILO_BADGE_SECCION = {
    'estudio': {'color': '#9a3412', 'backgroundColor': '#ffe1d0'},
    'previo': {'color': '#4b327f', 'backgroundColor': '#ece4fb'},
}


def header_seccion(nombre_icono, etiqueta, titulo, tono='estudio'):
    estilo_badge = ESTILO_BADGE_SECCION.get(tono, ESTILO_BADGE_SECCION['estudio'])
    return html.Div([
        html.Div([
            html.Img(src=icono(nombre_icono, color=estilo_badge['color']), style={
                'width': '36px', 'height': '36px', 'borderRadius': '8px',
                'backgroundColor': estilo_badge['backgroundColor'],
                'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                'padding': '8px', 'boxSizing': 'border-box', 'flex': 'none'
            }),
            html.Div([
                html.Div(etiqueta, style={'fontSize': '11px', 'color': 'var(--gray-66)', 'fontWeight': '700', 'textTransform': 'uppercase', 'letterSpacing': '0.03em'}),
                html.Div(titulo, style={'fontSize': '16px', 'fontWeight': '700', 'color': 'var(--text-border)', 'lineHeight': '1.2'})
            ])
        ], style={'display': 'flex', 'alignItems': 'center', 'gap': '12px'})
    ], style={'marginBottom': '14px', 'marginTop': '28px'})

# Orden estricto de colores SERVEO expandido (16 colores armonizados)
PALETA_GRAFICOS = [
    "#FF4E00", # 1. Acento corporativo
    "#474751", # 2. Base oscuro
    "#4383F0", # 3. Semántico Positivo (Azul)
    "#6AAE7A", # 4. Verde corporativo
    "#DB563A", # 5. Semántico Negativo (Rojo)
    "#CEC6C0", # 6. Secundario 1
    "#A9CEF4", # 7. Azul claro
    "#986F54", # 8. Marrón
    "#AEA4BF", # 9. Morado grisáceo
    "#FFD97D", # 10. Amarillo/Dorado
    "#BDEBDF", # 11. Semántico Neutral (Verde agua)
    "#38385C", # 12. Azul marino oscuro
    "#E68A5C", # 13. Naranja suave
    "#8DB38B", # 14. Verde oliva
    "#5C9EAD", # 15. Azul verdoso
    "#B3B3B3"  # 16. Gris medio
]

def layout():
    # Sincronización ultra-rápida desde RAM
    _, _, df_eq, _, _ = obtener_datos_eficiente(force_reload=False)
    
    opciones_tecnicos = []
    opciones_roles = []
    opciones_sedes = []
    
    if not df_eq.empty:
        col_id = 'ID_Tecnico' if 'ID_Tecnico' in df_eq.columns else ('ID_Técnico' if 'ID_Técnico' in df_eq.columns else 'Nombre')
        col_nom = 'Nombre' if 'Nombre' in df_eq.columns else df_eq.columns[0]
        
        df_eq[col_nom] = df_eq[col_nom].astype(str).str.strip()
        df_eq[col_id] = df_eq[col_id].astype(str).str.strip()
        
        for _, row in df_eq.iterrows():
            nombre_real = row[col_nom]
            alias_visual = row[col_id]
            if pd.isna(nombre_real) or nombre_real == 'nan': continue
            if pd.isna(alias_visual) or alias_visual == 'nan' or not alias_visual: 
                alias_visual = nombre_real 
                
            opciones_tecnicos.append({'label': alias_visual, 'value': nombre_real})
            
        if 'Perfil Técnico' in df_eq.columns:
            roles_unicos = df_eq['Perfil Técnico'].dropna().unique()
            opciones_roles = [{'label': str(r).strip(), 'value': str(r).strip()} for r in roles_unicos if str(r).strip() != 'nan']
            
        if 'Sede' in df_eq.columns:
            sedes_unicas = df_eq['Sede'].dropna().unique()
            opciones_sedes = [{'label': str(s).strip(), 'value': str(s).strip()} for s in sedes_unicas if str(s).strip() != 'nan']
        else:
            opciones_sedes = [
                {'label': 'MAD (Quint)', 'value': 'MAD (Quint)'},
                {'label': 'BCN (T. Auditori)', 'value': 'BCN (T. Auditori)'},
                {'label': 'VALENCIA', 'value': 'VALENCIA'}
            ]

    return html.Div([

        # --- HEADER DE PÁGINA (estilo Salesforce / Claude design) ---
        html.Div([
            html.Div([
                html.Img(src=icono('grafico'), style={
                    'width': '42px', 'height': '42px', 'borderRadius': '8px', 'background': 'var(--accent)',
                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'padding': '11px',
                    'boxSizing': 'border-box', 'flex': 'none'
                }),
                html.Div([
                    html.Div("Análisis de carga", style={'fontSize': '12px', 'color': 'var(--gray-66)', 'fontWeight': '600'}),
                    html.Div("Carga de trabajo (FTE)", style={'fontSize': '20px', 'fontWeight': '700', 'color': 'var(--text-border)', 'lineHeight': '1.2'})
                ])
            ], style={'display': 'flex', 'alignItems': 'center', 'gap': '13px'})
        ], style={**ESTILO_TARJETA, 'padding': '14px 18px', 'marginBottom': '16px'}),

        html.H3("Análisis de Carga de Trabajo (FTE)", className="serveo-titulo-pagina", style={'display': 'none'}),
        
        # --- BARRA DE FILTROS SUPERIOR (NUEVO FILTRO DE SEDE) ---
        html.Div([
            html.Div([
                html.Label("Filtrar por Sede:", className="etiqueta-dato"),
                dcc.Dropdown(
                    id='drop-filtro-sede-carga',
                    options=opciones_sedes,
                    placeholder="Todas las sedes...",
                    clearable=True,
                    multi=True
                )
            ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '220px', 'marginRight': '8px'}),

            html.Div([
                html.Label("Filtrar por Rol:", className="etiqueta-dato"),
                dcc.Dropdown(
                    id='drop-filtro-rol',
                    options=opciones_roles,
                    placeholder="Todos los roles...",
                    clearable=True,
                    multi=True
                )
            ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '220px', 'marginRight': '8px'}),
            
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
        ], className="contenedor-filtros", style={'backgroundColor': 'var(--card-divider)', 'alignItems': 'flex-end', 'justifyContent': 'flex-start', 'border': '1px solid #ededed'}),
        
        # --- GRÁFICOS CON ENVOLTORIO ESTANDARIZADO ---
        header_seccion("busqueda", "Activas", "En estudio", tono='estudio'),
        dcc.Loading(
            type="circle", color="#FF4E00",
            children=html.Div(
                dcc.Graph(
                    id='grafico-carga-estudio',
                    style={'padding': '16px'}
                ), style={**ESTILO_TARJETA, 'marginBottom': '8px'}
            )
        ),
        
        header_seccion("documento", "Preliminar", "Estudio previo", tono='previo'),
        dcc.Loading(
            type="circle", color="#FF4E00",
            children=html.Div(
                dcc.Graph(
                    id='grafico-carga-previo',
                    style={'padding': '16px'}
                ), style=ESTILO_TARJETA
            )
        )
    ], style={'paddingBottom': '40px'})

def register_callbacks(app):
    
    # =====================================================================
    # CALLBACK 1: FILTROS EN CASCADA (Sede -> Rol -> Técnico)
    # =====================================================================
    @app.callback(
        [Output('drop-filtro-tec', 'options'),
         Output('drop-filtro-tec', 'value')],
        [Input('drop-filtro-sede-carga', 'value'),
         Input('drop-filtro-rol', 'value')],
        State('drop-filtro-tec', 'value')
    )
    def encadenar_filtros(sedes_seleccionadas, roles_seleccionados, tecnicos_actuales):
        _, _, df_eq, _, _ = obtener_datos_eficiente(force_reload=False)
        
        if df_eq.empty:
            return [], dash.no_update
            
        df_filtrado = df_eq.copy()
        
        # Filtro Cascada: Sede
        if sedes_seleccionadas:
            if isinstance(sedes_seleccionadas, str): sedes_seleccionadas = [sedes_seleccionadas]
            if 'Sede' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['Sede'].isin(sedes_seleccionadas)]

        # Filtro Cascada: Rol
        if roles_seleccionados:
            if isinstance(roles_seleccionados, str): roles_seleccionados = [roles_seleccionados]
            if 'Perfil Técnico' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['Perfil Técnico'].isin(roles_seleccionados)]

        col_id = 'ID_Tecnico' if 'ID_Tecnico' in df_filtrado.columns else ('ID_Técnico' if 'ID_Técnico' in df_filtrado.columns else 'Nombre')
        col_nom = 'Nombre' if 'Nombre' in df_filtrado.columns else df_filtrado.columns[0]
        
        nuevas_opciones = []
        nombres_validos = []
        for _, row in df_filtrado.iterrows():
            nr = str(row.get(col_nom, '')).strip()
            al = str(row.get(col_id, '')).strip()
            if not nr or nr == 'nan': continue
            if not al or al == 'nan': al = nr
            
            nuevas_opciones.append({'label': al, 'value': nr})
            nombres_validos.append(nr)
            
        nuevos_valores_tecnicos = tecnicos_actuales
        if tecnicos_actuales:
            if isinstance(tecnicos_actuales, str): tecnicos_actuales = [tecnicos_actuales]
            nuevos_valores_tecnicos = [t for t in tecnicos_actuales if t in nombres_validos]
            if not nuevos_valores_tecnicos: nuevos_valores_tecnicos = None
                
        return nuevas_opciones, nuevos_valores_tecnicos


    # =====================================================================
    # CALLBACK 2: GENERACIÓN DE GRÁFICOS (REPARTO PROPORCIONAL FTE)
    # =====================================================================
    @app.callback(
        [Output('grafico-carga-estudio', 'figure'),
         Output('grafico-carga-previo', 'figure')],
        [Input('drop-filtro-sede-carga', 'value'),
         Input('drop-filtro-tec', 'value'),
         Input('drop-filtro-rol', 'value')]
    )
    def actualizar_grafico(sedes_seleccionadas, tecnicos_seleccionados, roles_seleccionados):
        
        if sedes_seleccionadas and isinstance(sedes_seleccionadas, str): sedes_seleccionadas = [sedes_seleccionadas]
        if tecnicos_seleccionados and isinstance(tecnicos_seleccionados, str): tecnicos_seleccionados = [tecnicos_seleccionados]
        if roles_seleccionados and isinstance(roles_seleccionados, str): roles_seleccionados = [roles_seleccionados]

        _, df_cron, df_eq, _, _ = obtener_datos_eficiente(force_reload=False)
        
        def grafico_vacio(mensaje):
            fig = px.bar(title=mensaje)
            fig.update_layout(plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF', font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif", color="#474751"))
            return fig

        if df_cron.empty:
            return grafico_vacio("Sin datos de licitaciones"), grafico_vacio("Sin datos de licitaciones")

        dict_roles = {}
        dict_alias = {}
        dict_sedes = {}
        if not df_eq.empty:
            col_id = 'ID_Tecnico' if 'ID_Tecnico' in df_eq.columns else ('ID_Técnico' if 'ID_Técnico' in df_eq.columns else 'Nombre')
            col_nom = 'Nombre' if 'Nombre' in df_eq.columns else df_eq.columns[0]
            
            for _, r in df_eq.iterrows():
                nr = str(r.get(col_nom, '')).strip()
                al = str(r.get(col_id, '')).strip()
                sede = str(r.get('Sede', 'MAD (Quint)')).strip()
                
                if not nr or nr == 'nan': continue
                if not al or al == 'nan': al = nr
                if not sede or sede == 'nan': sede = 'MAD (Quint)'
                
                dict_alias[nr] = al
                dict_roles[nr] = str(r.get('Perfil Técnico', 'Sin Rol')).strip()
                dict_sedes[nr] = sede

        df_maestro, col_calendario = procesar_cronograma(df_cron)

        def extraer_float(val):
            try: return float(str(val).replace(',', '.'))
            except: return 0.0

        registros = []
        for _, row in df_maestro.iterrows():
            
            bam_val = str(row.get('BAM', '')).strip()
            bam_val = bam_val if bam_val and bam_val != 'nan' else None
            
            tecs = [str(row.get(f'Técnico {i}', '')).strip() for i in range(1, 4)]
            tecs_validos = [t for t in tecs if t and t != 'nan']
            
            if not bam_val and not tecs_validos:
                continue

            etapa = str(row.get('Etapa', 'Sin Etapa')).strip()
            licitacion = str(row.get('Código de Licitación', 'S/C')).strip()

            h_tec = extraer_float(row.get('Horas de Licitación', row.get('Horas', 0)))
            h_bam = extraer_float(row.get('Horas Licitación BAM', row.get('Horas BAM', 0)))
            h_total = h_tec + h_bam
            
            if h_total > 0:
                prop_bam = h_bam / h_total if bam_val else 0.0
                prop_tecs = h_tec / h_total if tecs_validos else 0.0
            else:
                personas_totales = len(tecs_validos) + (1 if bam_val else 0)
                prop_bam = 1.0 / personas_totales if bam_val else 0.0
                prop_tecs = len(tecs_validos) / personas_totales if tecs_validos else 0.0

            for dia in col_calendario:
                fte_dia = extraer_float(row.get(dia, 0))
                
                if fte_dia > 0:
                    if bam_val and prop_bam > 0:
                        registros.append({
                            'Nombre_Real': bam_val,
                            'Técnico': dict_alias.get(bam_val, bam_val), 
                            'Rol': dict_roles.get(bam_val, "Bidding Area Manager"),
                            'Sede': dict_sedes.get(bam_val, "MAD (Quint)"),
                            'Fecha': dia,
                            'Licitación': licitacion,
                            'Carga (FTE)': fte_dia * prop_bam,
                            'Etapa': etapa
                        })
                    
                    if tecs_validos and prop_tecs > 0:
                        fte_per_tec = (fte_dia * prop_tecs) / len(tecs_validos)
                        for t in tecs_validos:
                            registros.append({
                                'Nombre_Real': t,
                                'Técnico': dict_alias.get(t, t), 
                                'Rol': dict_roles.get(t, "Bidding Technician"),
                                'Sede': dict_sedes.get(t, "MAD (Quint)"),
                                'Fecha': dia,
                                'Licitación': licitacion,
                                'Carga (FTE)': fte_per_tec,
                                'Etapa': etapa
                            })

        df_grafico = pd.DataFrame(registros)

        def generar_figura_por_etapa(etapa_objetivo):
            if df_grafico.empty:
                return grafico_vacio("No hay cargas asignadas en los próximos 60 días.")
            
            df_etapa = df_grafico[df_grafico['Etapa'] == etapa_objetivo]
            
            if df_etapa.empty:
                return grafico_vacio(f"No hay cargas en la etapa: {etapa_objetivo}")

            # --- FILTRADO TRIPLE ---
            if sedes_seleccionadas:
                df_etapa = df_etapa[df_etapa['Sede'].isin(sedes_seleccionadas)]
                if df_etapa.empty:
                    return grafico_vacio(f"Sin cargas para la Sede seleccionada en: {etapa_objetivo}")

            if roles_seleccionados:
                df_etapa = df_etapa[df_etapa['Rol'].isin(roles_seleccionados)]
                if df_etapa.empty:
                    return grafico_vacio(f"Sin cargas para el Rol seleccionado en: {etapa_objetivo}")

            if tecnicos_seleccionados:
                df_etapa = df_etapa[df_etapa['Nombre_Real'].isin(tecnicos_seleccionados)]
                if df_etapa.empty:
                    return grafico_vacio(f"Sin cargas para el Técnico seleccionado en: {etapa_objetivo}")

            # --- TÍTULOS DINÁMICOS ---
            if tecnicos_seleccionados:
                color_var = 'Licitación'
                if len(tecnicos_seleccionados) == 1:
                    texto_titulo = dict_alias.get(tecnicos_seleccionados[0], tecnicos_seleccionados[0])
                elif len(tecnicos_seleccionados) <= 3:
                    texto_titulo = ", ".join([dict_alias.get(t, t) for t in tecnicos_seleccionados])
                else:
                    texto_titulo = f"{len(tecnicos_seleccionados)} Miembros seleccionados"
                titulo = f"Desglose de Carga ({etapa_objetivo}): {texto_titulo}"
                
            elif roles_seleccionados:
                color_var = 'Técnico' 
                if len(roles_seleccionados) == 1:
                    texto_titulo = roles_seleccionados[0]
                else:
                    texto_titulo = "Varios Roles"
                titulo = f"Carga Operativa - Rol: {texto_titulo} ({etapa_objetivo})"

            elif sedes_seleccionadas:
                color_var = 'Técnico'
                if len(sedes_seleccionadas) == 1:
                    texto_titulo = sedes_seleccionadas[0]
                else:
                    texto_titulo = "Varias Sedes"
                titulo = f"Carga Operativa - Sede: {texto_titulo} ({etapa_objetivo})"
                
            else:
                color_var = 'Técnico'
                titulo = f"Carga de Trabajo Global - {etapa_objetivo}"

            # Construcción de la gráfica base
            fig = px.bar(
                df_etapa,
                x='Fecha',
                y='Carga (FTE)',
                color=color_var,
                title=titulo,
                color_discrete_sequence=PALETA_GRAFICOS
            )

            # Texto Total por Día
            df_totales = df_etapa.groupby('Fecha', as_index=False)['Carga (FTE)'].sum()
            fig.add_trace(go.Scatter(
                x=df_totales['Fecha'],
                y=df_totales['Carga (FTE)'],
                mode='text',
                text=df_totales['Carga (FTE)'].apply(lambda x: f"{x:.2f}" if x > 0 else ""),
                textposition='top center',
                textfont=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif", size=13, color="#474751"),
                showlegend=False,
                hoverinfo='skip'
            ))

            max_y = df_totales['Carga (FTE)'].max() if not df_totales.empty else 1
            rango_y = [0, max_y * 1.15] if max_y > 0 else [0, 1]

            fig.update_layout(
                plot_bgcolor='#FFFFFF',
                paper_bgcolor='#FFFFFF',
                font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif", color="#474751"),
                title_font_color="#FF4E00",
                xaxis_title="",
                yaxis_title="Esfuerzo (FTE)",
                legend_title_text='Desglose',
                xaxis=dict(showgrid=True, gridcolor="#F0EEED", tickangle=-45),
                yaxis=dict(showgrid=True, gridcolor="#F0EEED", range=rango_y)
            )
            return fig

        return generar_figura_por_etapa("En estudio"), generar_figura_por_etapa("Estudio previo")