import dash
from dash import html, dcc, dash_table, Input, Output, State
import pandas as pd
import datetime
import numpy as np
from utils.data_manager import leer_excel, procesar_cronograma

def generar_estilos_tabla(col_calendario, columnas_fin_semana):
    # DISTRIBUCIÓN ESTRICTA DE ESPACIO (SIN CLIENTE): Datos críticos optimizados para ocupar el 60% total
    estilos_celdas_condicionales = [
        {'if': {'column_id': 'Código de Licitación'}, 'minWidth': '12%', 'width': '10%', 'maxWidth': '12%'},
        {'if': {'column_id': 'Nombre de la Licitación'}, 'minWidth': '20%', 'width': '16%', 'maxWidth': '20%'},
        {'if': {'column_id': 'Nivel'}, 'minWidth': '5%', 'width': '4%', 'maxWidth': '5%'},
        {'if': {'column_id': 'BAM'}, 'minWidth': '9%', 'width': '8%', 'maxWidth': '9%'},
        {'if': {'column_id': 'Técnico 1'}, 'minWidth': '9%', 'width': '8%', 'maxWidth': '9%'},
        {'if': {'column_id': 'Técnico 2'}, 'minWidth': '9%', 'width': '8%', 'maxWidth': '9%'},
        {'if': {'column_id': 'Técnico 3'}, 'minWidth': '9%', 'width': '8%', 'maxWidth': '9%'},
        {'if': {'column_id': 'Presupuesto'}, 'minWidth': '7%', 'width': '7%', 'maxWidth': '7%'},
        {'if': {'column_id': 'Horas'}, 'minWidth': '6%', 'width': '5%', 'maxWidth': '6%'},
        {'if': {'column_id': 'Fecha de Creación'}, 'minWidth': '5%', 'width': '4%', 'maxWidth': '5%'},
        {'if': {'column_id': 'Fecha de Fin'}, 'minWidth': '5%', 'width': '4%', 'maxWidth': '5%'}
    ] + [
        {
            'if': {'column_id': col},
            # El 40% del espacio de la pantalla se lo lleva este bloque dinámico
            'minWidth': '75px', 'width': '75px', 'maxWidth': '75px',
            'textAlign': 'center', 'padding': '2px'
        } for col in col_calendario
    ]

    # CAPA 1: Base para Fines de semana (Gris clarito SERVEO)
    estilos_datos_condicionales = []
    for col in columnas_fin_semana:
        estilos_datos_condicionales.append({
            'if': {'column_id': col},
            'backgroundColor': '#F0EEED',
            'color': '#B3B3B3'
        })

    # CAPA 2: Reglas de negocio (Color para FTE > 0)
    for col in col_calendario:
        estilos_datos_condicionales.append(
            {'if': {'column_id': col, 'filter_query': f'{{{col}}} != ""'}, 'backgroundColor': 'rgba(189, 235, 223, 0.3)', 'color': '#474751', 'fontWeight': 'bold'}
        )

    # Hitos de fin de proyecto
    for col in col_calendario:
        estilos_datos_condicionales.append({
            'if': {
                'column_id': col,
                'filter_query': f'{{Hito_Fin}} eq "{col}"'
            },
            'backgroundColor': 'rgba(255, 78, 0, 0.3)',
            'border': '2px solid #FF4E00',
            'color': '#FF4E00',
            'fontWeight': 'bold'
        })

    # Fila final de totales
    estilos_datos_condicionales.append({
        'if': {'filter_query': '{Código de Licitación} eq "TOTAL FTES"'},
        'backgroundColor': '#F0EEED', 'color': '#FF4E00', 'fontWeight': 'bold'
    })

    return {
        'style_header': {
            'backgroundColor': '#FFFFFF', 
            'color': '#FF4E00', 
            'border': '1px solid #474751',
            'fontWeight': 'bold',
            'fontSize': '9px',
            'textTransform': 'uppercase',
            'fontFamily': "'Outfit', sans-serif",
            'textAlign': 'center',
            'height': '40px', 'minHeight': '40px', 'maxHeight': '40px',
            'whiteSpace': 'normal'
        },
        'style_cell': {
            'backgroundColor': '#FFFFFF', 
            'color': '#474751', 
            'border': '1px solid #474751', 
            'fontFamily': "'Outfit', sans-serif",
            'fontSize': '13px',
            'padding': '0px 12px',
            'textAlign': 'left',
            'textOverflow': 'ellipsis',
            'overflow': 'hidden',
            'height': '35px', 'minHeight': '35px', 'maxHeight': '35px',
            'whiteSpace': 'nowrap'
        },
        'style_cell_conditional': estilos_celdas_condicionales,
        'style_data_conditional': estilos_datos_condicionales
    }
    
def layout():
    df_cronograma, df_eq, _ = leer_excel()
    df_maestro, col_calendario = procesar_cronograma(df_cronograma)
    
    if df_maestro.empty:
        return html.Div("No hay datos en el cronograma.", style={'color': 'var(--semantic-negative)', 'fontFamily': 'var(--font-family)', 'padding': '20px'})

    # Generación de Opciones para Filtros
    opciones_tecnicos = []
    opciones_roles = []
    opciones_niveles = []
    
    if not df_eq.empty:
        opciones_tecnicos = [{'label': row['Nombre'], 'value': row['Nombre']} for _, row in df_eq.iterrows()]
        if 'Perfil Técnico' in df_eq.columns:
            roles_unicos = df_eq['Perfil Técnico'].dropna().unique()
            opciones_roles = [{'label': r, 'value': r} for r in roles_unicos]
            
    if 'Nivel' in df_maestro.columns:
        niveles_unicos = df_maestro['Nivel'].dropna().unique()
        opciones_niveles = [{'label': str(n), 'value': str(n)} for n in niveles_unicos]

    columnas_fin_semana = []
    hoy_base = datetime.date.today()
    meses_abrev = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    
    for i in range(60):
        fecha_futura = hoy_base + datetime.timedelta(days=i)
        nombre_col_esperado = f"{fecha_futura.day} {meses_abrev[fecha_futura.month - 1]}"
        if fecha_futura.weekday() >= 5 and nombre_col_esperado in col_calendario:
            columnas_fin_semana.append(nombre_col_esperado)

    estilos_cabecera_condicionales = [
        {'if': {'column_id': col}, 'backgroundColor': '#F0EEED', 'color': '#666666'} 
        for col in columnas_fin_semana
    ]

    # --- SANEAMIENTO: UNIFICACIÓN ESTRUCTURAL DE COLUMNAS (SÓLO HORAS CORTO) ---
    base_comun = ["Código de Licitación", "Nombre de la Licitación"]
    if 'Nivel' in df_maestro.columns:
        base_comun.append("Nivel")
        
    cierres_comunes = ["Presupuesto", "Horas", "Fecha de Creación", "Fecha de Fin"]

    # 1. Columnas para Pendiente de Asignar (Sin BAM, Técnicos)
    fijas_pendientes = base_comun + cierres_comunes
    cols_pendientes = [{"name": c, "id": c} for c in fijas_pendientes + col_calendario]

    # 2. Columnas para Etapas Activas (Con BAM y Técnicos)
    fijas_activas = base_comun.copy()
    if 'BAM' in df_maestro.columns:
        fijas_activas.append("BAM")
    fijas_activas.extend(["Técnico 1", "Técnico 2", "Técnico 3"])
    fijas_activas.extend(cierres_comunes)
    cols_activas = [{"name": c, "id": c} for c in fijas_activas + col_calendario]
    
    config_tabla = generar_estilos_tabla(col_calendario, columnas_fin_semana)
    config_tabla['style_header_conditional'] = estilos_cabecera_condicionales

    return html.Div([

        html.H3("CRONOGRAMA DEL EQUIPO", className="serveo-titulo-pagina"),
        
        # --- BARRA DE FILTROS SUPERIOR CON WIDTHS AMPLIADOS ---
        html.Div([
            html.Div([
                html.Label("Código Licitación", className="etiqueta-dato"),
                dcc.Input(id="filtro-codigo", type="text", placeholder="LIC-2026...", className="input-filtro")
            ], className="grupo-filtro", style={'flex': 'none', 'width': '160px'}),
            
            html.Div([
                html.Label("Nombre Licitación", className="etiqueta-dato"),
                dcc.Input(id="filtro-nombre", type="text", placeholder="Buscar licitación...", className="input-filtro")
            ], className="grupo-filtro", style={'flex': 'none', 'width': '240px'}),
            
            html.Div([
                html.Label("Nivel:", className="etiqueta-dato"),
                dcc.Dropdown(id='drop-filtro-nivel-cron', options=opciones_niveles, placeholder="Todos", clearable=True, multi=True)
            ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '140px'}),
            
            html.Div([
                html.Label("Rol:", className="etiqueta-dato"),
                dcc.Dropdown(id='drop-filtro-rol-cron', options=opciones_roles, placeholder="Todos los roles...", clearable=True, multi=True)
            ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '240px'}),
            
            html.Div([
                html.Label("Técnico(s):", className="etiqueta-dato"),
                dcc.Dropdown(id='drop-filtro-tec-cron', options=opciones_tecnicos, placeholder="Todo el equipo operativo...", clearable=True, multi=True)
            ], className="serveo-input-wrapper", style={'flex': 'none', 'width': '340px'})
            
        ], className="contenedor-filtros", style={'backgroundColor': 'var(--card-divider)', 'alignItems': 'flex-end', 'justifyContent': 'flex-start', 'flexWrap': 'wrap', 'gap': '16px'}),
        
        # --- TABLA: LICITACIONES NO ASIGNADAS ---
        html.H3("Licitaciones Pendientes de Asignación", className="serveo-titulo-seccion", style={'color': 'var(--semantic-negative)', 'marginBottom': '12px'}),
        dash_table.DataTable(
            id='tabla-no-asignadas', 
            columns=cols_pendientes, 
            fixed_columns={'headers': True, 'data': len(fijas_pendientes)},
            style_table={'overflowX': 'auto', 'width': '100%', 'minWidth': '100%', 'maxWidth': '100%', 'marginBottom': '40px'},
            cell_selectable=False,
            **config_tabla
        ),

        # --- TABLA: EN ESTUDIO ---
        html.H3("Etapa: En Estudio", className="serveo-titulo-seccion", style={'color': 'var(--accent)', 'marginBottom': '12px'}),
        dash_table.DataTable(
            id='tabla-estudio', 
            columns=cols_activas, 
            fixed_columns={'headers': True, 'data': len(fijas_activas)},
            style_table={'overflowX': 'auto', 'width': '100%', 'minWidth': '100%', 'maxWidth': '100%', 'marginBottom': '40px'},
            cell_selectable=False,
            **config_tabla
        ),
        
        # --- TABLA: ESTUDIO PREVIO ---
        html.H3("Etapa: Estudio Previo", className="serveo-titulo-seccion", style={'color': 'var(--accent)', 'marginBottom': '12px'}),
        dash_table.DataTable(
            id='tabla-previo', 
            columns=cols_activas, 
            fixed_columns={'headers': True, 'data': len(fijas_activas)},
            style_table={'overflowX': 'auto', 'width': '100%', 'minWidth': '100%', 'maxWidth': '100%'},
            cell_selectable=False,
            **config_tabla
        )
    ], style={'paddingBottom': '40px'})


def register_callbacks(app):

    # =====================================================================
    # CALLBACK 1: FILTROS EN CASCADA (Lógica de Interfaz)
    # =====================================================================
    @app.callback(
        [Output('drop-filtro-tec-cron', 'options'),
         Output('drop-filtro-tec-cron', 'value')],
        Input('drop-filtro-rol-cron', 'value'),
        State('drop-filtro-tec-cron', 'value')
    )
    def encadenar_filtros_cronograma(roles_seleccionados, tecnicos_actuales):
        _, df_eq, _ = leer_excel()
        if df_eq.empty: return [], dash.no_update
            
        df_filtrado = df_eq.copy()
        if roles_seleccionados:
            if isinstance(roles_seleccionados, str): roles_seleccionados = [roles_seleccionados]
            if 'Perfil Técnico' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['Perfil Técnico'].isin(roles_seleccionados)]

        nuevas_opciones = [{'label': row['Nombre'], 'value': row['Nombre']} for _, row in df_filtrado.iterrows() if pd.notna(row.get('Nombre'))]
        nombres_validos = [opc['value'] for opc in nuevas_opciones]
        
        nuevos_valores_tecnicos = tecnicos_actuales
        if tecnicos_actuales:
            if isinstance(tecnicos_actuales, str): tecnicos_actuales = [tecnicos_actuales]
            nuevos_valores_tecnicos = [t for t in tecnicos_actuales if t in nombres_validos]
            if not nuevos_valores_tecnicos: nuevos_valores_tecnicos = None
                
        return nuevas_opciones, nuevos_valores_tecnicos


    # =====================================================================
    # CALLBACK 2: FILTRADO DE TABLAS COMPLETO (CON HORAS ACTUALIZADO)
    # =====================================================================
    @app.callback(
        [Output('tabla-no-asignadas', 'data'), 
         Output('tabla-estudio', 'data'), 
         Output('tabla-previo', 'data')],
        [Input('filtro-codigo', 'value'), 
         Input('filtro-nombre', 'value'),
         Input('drop-filtro-nivel-cron', 'value'),
         Input('drop-filtro-rol-cron', 'value'),
         Input('drop-filtro-tec-cron', 'value')]
    )
    def filtrar_cronograma(cod, nom, niveles_seleccionados, roles_seleccionados, tecnicos_seleccionados):
        if tecnicos_seleccionados and isinstance(tecnicos_seleccionados, str):
            tecnicos_seleccionados = [tecnicos_seleccionados]
        if roles_seleccionados and isinstance(roles_seleccionados, str):
            roles_seleccionados = [roles_seleccionados]
        if niveles_seleccionados and isinstance(niveles_seleccionados, str):
            niveles_seleccionados = [niveles_seleccionados]

        df_cronograma, df_eq, _ = leer_excel()
        df_maestro, col_calendario = procesar_cronograma(df_cronograma)
        
        if df_maestro.empty: return [], [], []
        
        hoy = pd.Timestamp(datetime.date.today())
        if 'Fin_dt' in df_maestro.columns:
            mask_fecha = df_maestro['Fin_dt'].isna() | (df_maestro['Fin_dt'] >= hoy)
            df_maestro = df_maestro[mask_fecha]

        if cod: df_maestro = df_maestro[df_maestro['Código de Licitación'].astype(str).str.contains(cod, case=False, na=False)]
        if nom: df_maestro = df_maestro[df_maestro['Nombre de la Licitación'].astype(str).str.contains(nom, case=False, na=False)]

        if niveles_seleccionados and 'Nivel' in df_maestro.columns:
            df_maestro = df_maestro[df_maestro['Nivel'].astype(str).isin(niveles_seleccionados)]

        target_tecnicos = None
        if tecnicos_seleccionados:
            target_tecnicos = tecnicos_seleccionados
        elif roles_seleccionados and not df_eq.empty and 'Perfil Técnico' in df_eq.columns:
            target_tecnicos = df_eq[df_eq['Perfil Técnico'].isin(roles_seleccionados)]['Nombre'].dropna().tolist()

        if target_tecnicos is not None:
            cols_to_check = [c for c in ['Técnico 1', 'Técnico 2', 'Técnico 3', 'BAM'] if c in df_maestro.columns]
            if cols_to_check:
                mask_tec = pd.Series(False, index=df_maestro.index)
                for c in cols_to_check:
                    mask_tec = mask_tec | df_maestro[c].isin(target_tecnicos)
                df_maestro = df_maestro[mask_tec]

        # --- AQUI ESTA EL RENOMBRADO SEGURO DE HORAS ---
        if "Horas de Licitación" in df_maestro.columns:
            df_maestro = df_maestro.rename(columns={"Horas de Licitación": "Horas"})

        for c in ['Técnico 1', 'Técnico 2', 'Técnico 3', 'BAM', 'Nivel', 'Horas']:
            if c not in df_maestro.columns:
                df_maestro[c] = ""

        if 'Etapa' not in df_maestro.columns:
            df_maestro['Etapa'] = ""
        df_maestro['Etapa_Norm'] = df_maestro['Etapa'].astype(str).str.strip().str.lower()

        columnas_tecnicos = ['Técnico 1', 'Técnico 2', 'Técnico 3']
        df_temp = df_maestro[columnas_tecnicos].astype(str)
        mask_sin_tecnicos = df_temp.apply(lambda col: col.str.strip().str.lower().isin(['nan', 'none', '', '<na>'])).all(axis=1)

        mask_pendiente = df_maestro['Etapa_Norm'].str.contains('pendiente', na=False) | mask_sin_tecnicos
        df_no_asignadas = df_maestro[mask_pendiente].copy()
        
        df_resto = df_maestro[~mask_pendiente]
        df_estudio = df_resto[df_resto['Etapa_Norm'].str.contains('en estudio', na=False)].copy()
        df_previo = df_resto[df_resto['Etapa_Norm'].str.contains('estudio previo', na=False)].copy()
        
        def limpiar_y_totalizar(df):
            if df.empty: return df
            total = {col: "" for col in df.columns}
            total['Código de Licitación'] = "TOTAL FTES"
            
            df_clean = df.copy()
            for col in col_calendario: 
                val_total = round(pd.to_numeric(df_clean[col], errors='coerce').fillna(0).sum(), 2)
                total[col] = val_total if val_total > 0 else ""
                
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
                df_clean[col] = df_clean[col].apply(lambda x: x if x > 0 else "")
                
            return pd.concat([df_clean, pd.DataFrame([total])], ignore_index=True)
            
        return (limpiar_y_totalizar(df_no_asignadas).to_dict('records'), 
                limpiar_y_totalizar(df_estudio).to_dict('records'), 
                limpiar_y_totalizar(df_previo).to_dict('records'))