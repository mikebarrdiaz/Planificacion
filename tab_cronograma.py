import dash
from dash import html, dcc, dash_table, Input, Output
import pandas as pd
import datetime
import numpy as np
from utils.data_manager import leer_excel, procesar_cronograma

def generar_estilos_tabla(col_calendario, columnas_fin_semana):
    # 1. Anchos estrictos ampliados para dar mayor legibilidad a los datos fijos
    estilos_celdas_condicionales = [
        {'if': {'column_id': 'Código de Licitación'}, 'minWidth': '140px', 'width': '140px', 'maxWidth': '140px'},
        {'if': {'column_id': 'Nombre de la Licitación'}, 'minWidth': '240px', 'width': '240px', 'maxWidth': '240px'},
        {'if': {'column_id': 'Cliente'}, 'minWidth': '160px', 'width': '160px', 'maxWidth': '160px'},
        {'if': {'column_id': 'Etapa'}, 'minWidth': '120px', 'width': '120px', 'maxWidth': '120px'},
        {'if': {'column_id': 'Presupuesto'}, 'minWidth': '110px', 'width': '110px', 'maxWidth': '110px'},
        {'if': {'column_id': 'Horas de Licitación'}, 'minWidth': '100px', 'width': '100px', 'maxWidth': '100px'},
        {'if': {'column_id': 'Fecha de Creación'}, 'minWidth': '100px', 'width': '100px', 'maxWidth': '100px'},
        {'if': {'column_id': 'Fecha de Fin'}, 'minWidth': '100px', 'width': '100px', 'maxWidth': '100px'}
    ] + [
        {
            'if': {'column_id': col},
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
            # Como ahora desde Python mandamos un string vacío (""), solo teñimos si la celda no está vacía
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
            'padding': '0px 15px',
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
    df_cronograma, _, _ = leer_excel()
    df_maestro, col_calendario = procesar_cronograma(df_cronograma)
    
    if df_maestro.empty:
        return html.Div("No hay datos en el cronograma.", style={'color': 'var(--semantic-negative)', 'fontFamily': 'var(--font-family)', 'padding': '20px'})
        
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

    col_fijas = ["Código de Licitación", "Nombre de la Licitación", "Cliente", "Etapa", "Presupuesto", "Horas de Licitación", "Fecha de Creación", "Fecha de Fin"]
    todas_cols = [{"name": c, "id": c} for c in col_fijas + col_calendario]
    
    config_tabla = generar_estilos_tabla(col_calendario, columnas_fin_semana)
    config_tabla['style_header_conditional'] = estilos_cabecera_condicionales

    return html.Div([

        # Título consolidado con clase
        html.H3("CRONOGRAMA DEL EQUIPO", className="serveo-titulo-pagina"),
        
        # --- BARRA DE FILTROS SUPERIOR ---
        html.Div([
            html.Div([
                html.Label("Código Licitación", className="etiqueta-dato"),
                dcc.Input(id="filtro-codigo", type="text", placeholder="Ej: LIC-2026...", className="input-filtro")
            ], className="grupo-filtro", style={'flex': 'none', 'width': '300px'}),
            
            html.Div([
                html.Label("Nombre Proyecto", className="etiqueta-dato"),
                dcc.Input(id="filtro-nombre", type="text", placeholder="Buscar por nombre...", className="input-filtro")
            ], className="grupo-filtro", style={'flex': 'none', 'width': '300px'})
            
        ], className="contenedor-filtros", style={'backgroundColor': 'var(--card-divider)', 'alignItems': 'flex-end', 'justifyContent': 'flex-start'}),
        
        # --- TABLA: LICITACIONES NO ASIGNADAS ---
        html.H3("Licitaciones Pendientes de Asignación", className="serveo-titulo-seccion", style={'color': 'var(--semantic-negative)', 'marginBottom': '12px'}),
        dash_table.DataTable(
            id='tabla-no-asignadas', 
            columns=todas_cols, 
            fixed_columns={'headers': True, 'data': 8},
            style_table={'overflowX': 'auto', 'width': '100%', 'minWidth': '100%', 'maxWidth': '100%', 'marginBottom': '40px'},
            cell_selectable=False,
            **config_tabla
        ),

        # --- TABLA: EN ESTUDIO ---
        html.H3("Etapa: En Estudio", className="serveo-titulo-seccion", style={'color': 'var(--accent)', 'marginBottom': '12px'}),
        dash_table.DataTable(
            id='tabla-estudio', 
            columns=todas_cols, 
            fixed_columns={'headers': True, 'data': 8},
            style_table={'overflowX': 'auto', 'width': '100%', 'minWidth': '100%', 'maxWidth': '100%', 'marginBottom': '40px'},
            cell_selectable=False,
            **config_tabla
        ),
        
        # --- TABLA: ESTUDIO PREVIO ---
        html.H3("Etapa: Estudio Previo", className="serveo-titulo-seccion", style={'color': 'var(--accent)', 'marginBottom': '12px'}),
        dash_table.DataTable(
            id='tabla-previo', 
            columns=todas_cols, 
            fixed_columns={'headers': True, 'data': 8},
            style_table={'overflowX': 'auto', 'width': '100%', 'minWidth': '100%', 'maxWidth': '100%'},
            cell_selectable=False,
            **config_tabla
        )
    ], style={'paddingBottom': '40px'})

def register_callbacks(app):
    @app.callback(
        [Output('tabla-no-asignadas', 'data'), 
         Output('tabla-estudio', 'data'), 
         Output('tabla-previo', 'data')],
        [Input('filtro-codigo', 'value'), Input('filtro-nombre', 'value')]
    )
    def filtrar_cronograma(cod, nom):
        df_cronograma, _, _ = leer_excel()
        df_maestro, col_calendario = procesar_cronograma(df_cronograma)
        
        if df_maestro.empty: return [], [], []
        
        hoy = pd.Timestamp(datetime.date.today())
        if 'Fin_dt' in df_maestro.columns:
            mask_fecha = df_maestro['Fin_dt'].isna() | (df_maestro['Fin_dt'] >= hoy)
            df_maestro = df_maestro[mask_fecha]

        if cod: df_maestro = df_maestro[df_maestro['Código de Licitación'].astype(str).str.contains(cod, case=False, na=False)]
        if nom: df_maestro = df_maestro[df_maestro['Nombre de la Licitación'].astype(str).str.contains(nom, case=False, na=False)]

        if 'Etapa' not in df_maestro.columns:
            df_maestro['Etapa'] = ""
        df_maestro['Etapa_Norm'] = df_maestro['Etapa'].astype(str).str.strip().str.lower()

        columnas_tecnicos = ['Técnico 1', 'Técnico 2', 'Técnico 3']
        columnas_existentes = [col for col in columnas_tecnicos if col in df_maestro.columns]
        
        if columnas_existentes:
            df_temp = df_maestro[columnas_existentes].astype(str)
            mask_sin_tecnicos = df_temp.apply(lambda col: col.str.strip().str.lower().isin(['nan', 'none', '', '<na>'])).all(axis=1)
        else:
            mask_sin_tecnicos = pd.Series(True, index=df_maestro.index)

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
                # 1. Calculamos la suma total real
                val_total = round(pd.to_numeric(df_clean[col], errors='coerce').fillna(0).sum(), 2)
                total[col] = val_total if val_total > 0 else ""
                
                # 2. Vaciamos las celdas individuales que sean 0 para ocultarlas en la tabla
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
                df_clean[col] = df_clean[col].apply(lambda x: x if x > 0 else "")
                
            return pd.concat([df_clean, pd.DataFrame([total])], ignore_index=True)
            
        return (limpiar_y_totalizar(df_no_asignadas).to_dict('records'), 
                limpiar_y_totalizar(df_estudio).to_dict('records'), 
                limpiar_y_totalizar(df_previo).to_dict('records'))