from dash import html, dcc, dash_table, Input, Output, State
import dash
import pandas as pd
import datetime
from utils.data_manager import obtener_datos_eficiente, obtener_calendarios, parsear_fecha_es
from utils.icons import icono
import warnings

# --- ESTILO DE TARJETA BASE (estilo Salesforce / Lightning, look Serveo) ---
ESTILO_TARJETA = {
    'backgroundColor': '#FFFFFF',
    'border': '1px solid #e5e5e5',
    'borderRadius': 'var(--radius-container)',
    'boxShadow': '0 1px 2px rgba(71, 71, 81, 0.05)',
    'overflow': 'hidden'
}

def generar_matriz_et(tecnicos_seleccionados=None, roles_seleccionados=None, niveles_seleccionados=None, capas_activas=None):
    """
    Cruza BBDD, Equipo, Vacaciones y Calendarios por Sede.
    Integra sistema de CAPAS (LIC, VAC, FES) para activar/desactivar visualizaciones.
    """
    if capas_activas is None:
        capas_activas = ['LIC', 'VAC', 'FES']

    _, df_maestro, df_eq, df_vac, _ = obtener_datos_eficiente(force_reload=False)
    dict_cals = obtener_calendarios(force_reload=False)
    
    # --- TRADUCTOR DE FECHAS EN ESPAÑOL MEJORADO ---
    def parsear_fecha_es(fecha_val):
        if pd.isna(fecha_val): return fecha_val
        
        f_str = str(fecha_val).lower().strip()
        
        # GUARDIÁN: Si ya es un formato ISO estándar (Ej: 2026-05-13), la dejamos pasar intacta
        if len(f_str) >= 10 and f_str[0:4].isdigit() and f_str[4] == '-':
            return f_str
            
        # Si no es estándar, traducimos los meses y los conectores
        traducciones = {
            ' de ': '-', '/': '-',
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04', 
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08', 
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
        }
        for esp, num in traducciones.items():
            f_str = f_str.replace(esp, num)
            
        return f_str

    # 1. PREVENCIÓN DE TYPE MISMATCHES Y LIMPIEZA DE COLUMNAS CLAVE
    if not df_maestro.empty:
        for col in ['Código de Licitación', 'Nivel', 'Técnico 1', 'Técnico 2', 'Técnico 3', 'Nombre']:
            if col in df_maestro.columns:
                df_maestro[col] = df_maestro[col].astype(str).str.strip()
        
        # APLICAMOS EL TRADUCTOR INTELIGENTE
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if 'Fecha de Fin' in df_maestro.columns:
                df_maestro['Fin_dt'] = pd.to_datetime(df_maestro['Fecha de Fin'].apply(parsear_fecha_es))
            elif 'Fecha Fin' in df_maestro.columns:
                df_maestro['Fin_dt'] = pd.to_datetime(df_maestro['Fecha Fin'].apply(parsear_fecha_es))
                df_maestro['Fecha de Fin'] = df_maestro['Fecha Fin']
            else:
                df_maestro['Fin_dt'] = pd.NaT
                df_maestro['Fecha de Fin'] = pd.NaT
            
        if niveles_seleccionados:
            if isinstance(niveles_seleccionados, str): list_niv = [niveles_seleccionados]
            else: list_niv = list(niveles_seleccionados)
            df_maestro = df_maestro[df_maestro['Nivel'].isin(list_niv)]
    else:
        df_maestro = pd.DataFrame(columns=['Código de Licitación', 'Nivel', 'Técnico 1', 'Técnico 2', 'Técnico 3', 'Fin_dt', 'Fecha de Fin'])

    # 2. GUARDIÁN ULTRA-SEGURO PARA VACACIONES
    df_vac['Inicio_dt'] = pd.NaT
    df_vac['Fin_dt_vac'] = pd.NaT
    if not df_vac.empty:
        if 'Nombre' in df_vac.columns:
            df_vac['Nombre'] = df_vac['Nombre'].astype(str).str.strip()
        col_ini = 'Fecha_Inicio' if 'Fecha_Inicio' in df_vac.columns else ('Fecha Inicio' if 'Fecha Inicio' in df_vac.columns else None)
        col_fin = 'Fecha_Fin' if 'Fecha_Fin' in df_vac.columns else ('Fecha Fin' if 'Fecha Fin' in df_vac.columns else None)
        if col_ini: df_vac['Inicio_dt'] = pd.to_datetime(df_vac[col_ini], errors='coerce')
        if col_fin: df_vac['Fin_dt_vac'] = pd.to_datetime(df_vac[col_fin], errors='coerce')

    # 3. FILTRADO PREVIO DEL DIRECTORIO DE EQUIPO
    if not df_eq.empty:
        col_nombre_eq = 'Nombre' if 'Nombre' in df_eq.columns else df_eq.columns[0]
        df_eq[col_nombre_eq] = df_eq[col_nombre_eq].astype(str).str.strip()
        if 'Perfil Técnico' in df_eq.columns:
            df_eq['Perfil Técnico'] = df_eq['Perfil Técnico'].astype(str).str.strip()
        
        if roles_seleccionados:
            if isinstance(roles_seleccionados, str): roles_seleccionados = [roles_seleccionados]
            df_eq = df_eq[df_eq['Perfil Técnico'].isin(roles_seleccionados)]
            
        if tecnicos_seleccionados:
            if isinstance(tecnicos_seleccionados, str): tecnicos_seleccionados = [tecnicos_seleccionados]
            df_eq = df_eq[df_eq[col_nombre_eq].isin(tecnicos_seleccionados)]

    # 4. CONSTRUCCIÓN DEL EJE TEMPORAL (60 días)
    hoy = datetime.date.today()
    lista_dias_obj = [hoy + datetime.timedelta(days=i) for i in range(60)]
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    cols_dias = [f"{d.day} {meses[d.month - 1]}" for d in lista_dias_obj]
    
    columnas_fin_semana = [col_name for dia_obj, col_name in zip(lista_dias_obj, cols_dias) if dia_obj.weekday() >= 5]

    datos_matriz = []
    tooltip_data = []
    
    if not df_eq.empty:
        col_nombre_eq = 'Nombre' if 'Nombre' in df_eq.columns else df_eq.columns[0]
        
        for _, tec in df_eq.iterrows():
            nombre = tec[col_nombre_eq]
            if pd.isna(nombre) or nombre == 'nan': continue
            
            sede = str(tec.get('Sede', 'MAD (Quint)')).strip()
            if not sede or sede == 'nan': sede = 'MAD (Quint)'
            
            fila = {"Técnico": nombre}
            fila_tooltip = {}
            
            proy_tec = df_maestro[(df_maestro['Técnico 1'] == nombre) | (df_maestro['Técnico 2'] == nombre) | (df_maestro['Técnico 3'] == nombre)] if not df_maestro.empty else pd.DataFrame()
            vac_tec = df_vac[df_vac['Nombre'] == nombre] if not df_vac.empty and 'Nombre' in df_vac.columns else pd.DataFrame()
                
            for dia_obj, col_name in zip(lista_dias_obj, cols_dias):
                hitos_del_dia = []
                detalles_tooltip_hitos = []
                ausencia_val = ""
                detalles_tooltip_vac = ""
                
                # A. CAPA DE FESTIVOS (FES)
                es_festivo = False
                if 'FES' in capas_activas and dia_obj.weekday() < 5:
                    if sede in dict_cals and dia_obj in dict_cals[sede]:
                        if float(dict_cals[sede][dia_obj]) == 0.0:
                            es_festivo = True

                if es_festivo:
                    ausencia_val = "FES"
                    detalles_tooltip_vac = f"🎉 **Festivo Local/Nacional:** {sede}"
                    
                # B. CAPA DE VACACIONES (VAC)
                elif 'VAC' in capas_activas and not vac_tec.empty:
                    for _, v in vac_tec.iterrows():
                        if pd.notnull(v['Inicio_dt']) and pd.notnull(v['Fin_dt_vac']):
                            if v['Inicio_dt'].date() <= dia_obj <= v['Fin_dt_vac'].date():
                                tipo = str(v.get('Tipo_Ausencia', 'VAC')).upper()
                                if "VAC" in tipo: ausencia_val = "VAC"
                                elif "BAJA" in tipo: ausencia_val = "BAJA"
                                else: ausencia_val = "AUS"
                                
                                detalles_tooltip_vac = f"**Ausencia:** {ausencia_val}\nPeríodo: {v['Inicio_dt'].strftime('%d/%m')} al {v['Fin_dt_vac'].strftime('%d/%m')}"
                                break
                
                # C. CAPA DE LICITACIONES / HITOS (LIC)
                if 'LIC' in capas_activas and not proy_tec.empty:
                    for _, p in proy_tec.iterrows():
                        if pd.notnull(p['Fin_dt']) and p['Fin_dt'].date() == dia_obj:
                            nivel = str(p.get('Nivel', 'FIN')).strip()
                            if nivel == 'nan' or not nivel: nivel = 'FIN'
                            hitos_del_dia.append(nivel)
                            
                            cod_lic = str(p.get('Código de Licitación', 'S/C')).strip()
                            nom_proy = str(p.get('Nombre', p.get('Nombre de la Licitación', 'Sin Nombre'))).strip()
                            presupuesto = str(p.get('Presupuesto', 'S/P')).strip()
                            
                            presupuesto_limpio = f"{presupuesto}"
                            if pd.notnull(presupuesto):
                                try:
                                    pres_str = str(presupuesto).replace("€", "").strip()
                                    val_float = float(pres_str)
                                    pres_format = f"{val_float:,.2f}"
                                    presupuesto_limpio = pres_format.replace(",", "X").replace(".", ",").replace("X", ".") + " €"
                                except (ValueError, TypeError):
                                    presupuesto_limpio = f"{presupuesto} €" if not str(presupuesto).endswith("€") else f"{presupuesto}"

                            detalles_tooltip_hitos.append(
                                f"🎯 **[{nivel}]** - {cod_lic}\n\n"
                                f"💼 {nom_proy}\n\n"
                                f"💰 {presupuesto_limpio}"
                            )
                                            
                # D. Formatear el contenido visual de la celda
                if hitos_del_dia:
                    hitos_del_dia.sort()
                    texto_hitos = " ".join(hitos_del_dia)
                    celda_val = f"{texto_hitos} ({ausencia_val})" if ausencia_val else texto_hitos
                else:
                    celda_val = ausencia_val
                            
                fila[col_name] = celda_val
                
                # E. Construcción del Tooltip combinando capas activas
                markdown_piezas = []
                if detalles_tooltip_hitos:
                    markdown_piezas.append("\n\n---\n\n".join(detalles_tooltip_hitos))
                if detalles_tooltip_vac:
                    markdown_piezas.append(detalles_tooltip_vac)
                
                if markdown_piezas:
                    text_completo = "\n\n".join(markdown_piezas)
                    fila_tooltip[col_name] = {'value': text_completo, 'type': 'markdown'}
                    
            datos_matriz.append(fila)
            tooltip_data.append(fila_tooltip)
            
    return pd.DataFrame(datos_matriz), cols_dias, columnas_fin_semana, tooltip_data


def layout():
    df_matriz, cols_dias, columnas_fin_semana, tooltip_data = generar_matriz_et()
    _, df_maestro, df_eq, _, _ = obtener_datos_eficiente(force_reload=False)
    
    if df_matriz.empty:
        return html.Div("No hay técnicos que cumplan con los criterios operativos seleccionados.", 
                        style={'padding': '20px', 'color': 'var(--semantic-negative)', 'fontFamily': 'var(--font-family)', 'fontWeight': 'bold'})

    lista_tecnicos = df_matriz['Técnico'].unique().tolist() if 'Técnico' in df_matriz.columns else []
    
    opciones_roles = []
    if not df_eq.empty and 'Perfil Técnico' in df_eq.columns:
        roles_unicos = df_eq['Perfil Técnico'].dropna().unique()
        opciones_roles = [{'label': str(r), 'value': str(r)} for r in roles_unicos]

    opciones_niveles = []
    if not df_maestro.empty and 'Nivel' in df_maestro.columns:
        niveles_unicos = df_maestro['Nivel'].dropna().unique()
        opciones_niveles = [{'label': str(n), 'value': str(n)} for n in niveles_unicos if str(n).lower() != 'nan']
    if not opciones_niveles:
        opciones_niveles = [{'label': n, 'value': n} for n in ['N1', 'N2', 'N3', 'FIN']]

    hoy_base = datetime.date.today()
    columnas_tabla = [{"name": ["", "Técnico"], "id": "Técnico"}]
    
    for i in range(60):
        fecha_futura = hoy_base + datetime.timedelta(days=i)
        semana_iso = fecha_futura.isocalendar()[1]
        col_id = cols_dias[i]
        columnas_tabla.append({
            "name": [f"Semana {semana_iso}", col_id],
            "id": col_id
        })

    estilos_condicionales = []
    for col in columnas_fin_semana:
        estilos_condicionales.append({
            'if': {'column_id': col},
            'backgroundColor': '#F0EEED',
            'color': "#FFFEFE"
        })
    
    for col in cols_dias:
        estilos_condicionales.extend([
            {'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "AUS"'}, 'backgroundColor': "#CFB8B8", 'color': "#FFFFFF", 'fontSize': '10px'},
            {'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "BAJA"'}, 'backgroundColor': '#AEA4BF', 'color': '#FFFFFF', 'fontSize': '10px'},
            {'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "VAC"'}, 'backgroundColor': "#24AC18", 'color': "#FFFFFF", 'fontSize': '10px'},
            {'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "FES"'}, 'backgroundColor': '#5C9EAD', 'color': '#FFFFFF', 'fontSize': '10px'},
            {'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "FIN"'}, 'backgroundColor': '#474751', 'color': '#FFFFFF','fontSize': '10px'},
            {'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "N3"'}, 'backgroundColor': "#EBAF60", 'color': '#FFFFFF', 'fontSize': '10px'},
            {'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "N2"'}, 'backgroundColor': '#FF4E00', 'color': '#FFFFFF', 'fontSize': '10px'},
            {'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "N1"'}, 'backgroundColor': '#DB563A', 'color': '#FFFFFF', 'fontSize': '10px'}
        ])

    estilos_cabecera_condicionales = [
        {'if': {'column_id': col}, 'backgroundColor': '#F0EEED', 'color': "#FDFDFD"} for col in columnas_fin_semana
    ]

    return html.Div([

        # --- HEADER DE PÁGINA (estilo Salesforce / Claude design) ---
        html.Div([
            html.Div([
                html.Img(src=icono('matriz'), style={
                    'width': '42px', 'height': '42px', 'borderRadius': '8px', 'background': 'var(--accent)',
                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'padding': '11px',
                    'boxSizing': 'border-box', 'flex': 'none'
                }),
                html.Div([
                    html.Div("Equipo Técnico", style={'fontSize': '12px', 'color': 'var(--gray-66)', 'fontWeight': '600'}),
                    html.Div("Matriz de disponibilidad", style={'fontSize': '20px', 'fontWeight': '700', 'color': 'var(--text-border)', 'lineHeight': '1.2'})
                ])
            ], style={'display': 'flex', 'alignItems': 'center', 'gap': '13px'})
        ], style={**ESTILO_TARJETA, 'padding': '14px 18px', 'marginBottom': '16px'}),

        html.H3("Matriz de Visualización del equipo", className="serveo-titulo-pagina", style={'display': 'none'}),
        
        # --- BARRA DE FILTROS SUPERIOR ---
        html.Div([
            html.Div([
                html.Div([
                    html.Label("Rol:", className="etiqueta-dato"),
                    dcc.Dropdown(
                        id='filtro-rol-et',
                        options=opciones_roles,
                        placeholder="Todos...",
                        clearable=True,
                        multi=True
                    )
                ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '220px', 'marginRight': '16px'}),
                
                html.Div([
                    html.Label("Nivel:", className="etiqueta-dato"),
                    dcc.Dropdown(
                        id='filtro-nivel-et',
                        options=opciones_niveles,
                        placeholder="Todos...",
                        clearable=True,
                        multi=True
                    )
                ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '200px', 'marginRight': '16px'}),
                
                html.Div([
                    html.Label("Técnico:", className="etiqueta-dato"),
                    dcc.Dropdown(
                        id='filtro-tecnico-et',
                        options=[{'label': t, 'value': t} for t in lista_tecnicos],
                        placeholder="Todos...",
                        clearable=True,
                        multi=True
                    )
                ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '320px'})
                
            ], style={'display': 'flex', 'alignItems': 'flex-end', 'width': '100%'})
        ], className="contenedor-filtros", style={'backgroundColor': 'var(--card-divider)', 'padding': '16px', 'borderRadius': '12px', 'marginBottom': '16px', 'border': '1px solid #ededed'}),

        # --- CONTROL DE CAPAS VISUALES ---
        html.Div([
            html.Label("Capas Visibles en la Matriz:", className="etiqueta-dato", style={'marginRight': '24px', 'marginBottom': '0'}),
            dcc.Checklist(
                id='filtro-capas-et',
                options=[
                    {'label': html.Span(" Licitaciones (Hitos)", style={'marginLeft': '6px', 'marginRight': '24px'}), 'value': 'LIC'},
                    {'label': html.Span(" Vacaciones y Permisos", style={'marginLeft': '6px', 'marginRight': '24px'}), 'value': 'VAC'},
                    {'label': html.Span(" Festivos", style={'marginLeft': '6px', 'marginRight': '24px'}), 'value': 'FES'}
                ],
                value=['LIC', 'VAC', 'FES'],
                inline=True,
                style={'display': 'flex', 'alignItems': 'center', 'color': 'var(--color-title)', 'fontSize': '12px', 'fontWeight': 'bold'}
            )
        ], style={**ESTILO_TARJETA, 'display': 'flex', 'alignItems': 'center', 'backgroundColor': '#FAFAFA', 'padding': '12px 16px', 'marginBottom': '16px', 'boxShadow': 'none'}),

        # --- TABLA MATRIZ ---
        html.Div(
            dash_table.DataTable(
                id='tabla-matriz-et',
                columns=columnas_tabla,
                data=df_matriz.to_dict('records'),
                tooltip_data=tooltip_data,
                tooltip_delay=100,       
                tooltip_duration=None,   
                merge_duplicate_headers=True,
                fixed_columns={'headers': True, 'data': 1},
                fixed_rows={'headers': True},
                cell_selectable=False,
                style_header={
                    'backgroundColor': '#FFFFFF', 'color': '#FF4E00', 'fontWeight': 'bold',
                    'border': '1px solid #e5e5e5', 'fontFamily': "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                    'fontSize': '9px', 'textTransform': 'uppercase', 'textAlign': 'center',
                    'minWidth': '65px', 'width': '65px', 'maxWidth': '65px'
                },
                style_header_conditional=estilos_cabecera_condicionales,
                style_cell={
                    'backgroundColor': '#FFFFFF', 'color': '#474751', 'border': '1px solid #F0EEED',
                    'padding': '8px 4px', 'textAlign': 'center', 'fontFamily': "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                    'fontSize': '11px', 'minWidth': '65px', 'width': '65px', 'maxWidth': '65px'
                },
                style_cell_conditional=[
                    {
                        'if': {'column_id': 'Técnico'},
                        'minWidth': '220px', 'width': '220px', 'maxWidth': '220px',
                        'textAlign': 'left', 'fontWeight': 'bold',
                        'backgroundColor': '#FFFFFF',
                        'borderRight': '2px solid #e5e5e5'
                    }
                ],
                style_data_conditional=estilos_condicionales,
                style_table={
                    'overflowX': 'auto', 
                    'overflowY': 'auto', 
                    'maxHeight': '80vh', 
                    'minWidth': '100%'
                },
                css=[
                    {
                        'selector': 'td.dash-cell[data-dash-column]:not([data-dash-column="Técnico"])',
                        'rule': '''
                            color: #FFFFFF !important;
                        '''
                    }
                ]
            ), style=ESTILO_TARJETA
        )
    ], style={'paddingBottom': '40px'})

def register_callbacks(app):

    @app.callback(
        [Output('filtro-tecnico-et', 'options'),
         Output('filtro-tecnico-et', 'value')],
        [Input('filtro-rol-et', 'value'),
         Input('filtro-nivel-et', 'value')],
        State('filtro-tecnico-et', 'value')
    )
    def encadenar_filtros_et(roles_seleccionados, niveles_seleccionados, tecnicos_actuales):
        _, df_maestro, df_eq, _, _ = obtener_datos_eficiente(force_reload=False)
        if df_eq.empty: return [], dash.no_update
            
        df_filtrado_eq = df_eq.copy()
        
        if niveles_seleccionados and not df_maestro.empty:
            if isinstance(niveles_seleccionados, str): niveles_seleccionados = [niveles_seleccionados]
            for c in ['Técnico 1', 'Técnico 2', 'Técnico 3', 'Nivel']:
                if c in df_maestro.columns: df_maestro[c] = df_maestro[c].astype(str).str.strip()
            
            df_m_filt = df_maestro[df_maestro['Nivel'].isin(niveles_seleccionados)]
            tecs_con_nivel = set(df_m_filt['Técnico 1'].unique()).union(set(df_m_filt['Técnico 2'].unique())).union(set(df_m_filt['Técnico 3'].unique()))
            
            col_nom = 'Nombre' if 'Nombre' in df_filtrado_eq.columns else df_filtrado_eq.columns[0]
            df_filtrado_eq = df_filtrado_eq[df_filtrado_eq[col_nom].isin(tecs_con_nivel)]

        if roles_seleccionados:
            if isinstance(roles_seleccionados, str): roles_seleccionados = [roles_seleccionados]
            if 'Perfil Técnico' in df_filtrado_eq.columns:
                df_filtrado_eq = df_filtrado_eq[df_filtrado_eq['Perfil Técnico'].isin(roles_seleccionados)]

        nuevas_opciones = [{'label': str(row['Nombre']), 'value': str(row['Nombre'])} for _, row in df_filtrado_eq.iterrows() if pd.notna(row.get('Nombre'))]
        nombres_validos = [opc['value'] for opc in nuevas_opciones]
        
        nuevos_valores_tecnicos = tecnicos_actuales
        if tecnicos_actuales:
            if isinstance(tecnicos_actuales, str): tecnicos_actuales = [tecnicos_actuales]
            nuevos_valores_tecnicos = [t for t in tecnicos_actuales if t in nombres_validos]
            if not nuevos_valores_tecnicos: nuevos_valores_tecnicos = None
                
        return nuevas_opciones, nuevos_valores_tecnicos

    @app.callback(
        [Output('tabla-matriz-et', 'data'),
         Output('tabla-matriz-et', 'tooltip_data')],
        [Input('filtro-tecnico-et', 'value'),
         Input('filtro-rol-et', 'value'),
         Input('filtro-nivel-et', 'value'),
         Input('filtro-capas-et', 'value')]
    )
    def filtrar_matriz(tecnicos_seleccionados, roles_seleccionados, niveles_seleccionados, capas_activas):
        if tecnicos_seleccionados and isinstance(tecnicos_seleccionados, str): tecnicos_seleccionados = [tecnicos_seleccionados]
        if roles_seleccionados and isinstance(roles_seleccionados, str): roles_seleccionados = [roles_seleccionados]
        if niveles_seleccionados and isinstance(niveles_seleccionados, str): niveles_seleccionados = [niveles_seleccionados]
        if not capas_activas: capas_activas = []

        df_matriz, _, _, tooltip_data = generar_matriz_et(
            tecnicos_seleccionados=tecnicos_seleccionados,
            roles_seleccionados=roles_seleccionados,
            niveles_seleccionados=niveles_seleccionados,
            capas_activas=capas_activas
        )
            
        return df_matriz.to_dict('records'), tooltip_data