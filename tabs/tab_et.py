from dash import html, dash_table
import pandas as pd
import datetime
from utils.data_manager import leer_excel

def generar_matriz_et():
    """Cruza BBDD, Equipo y Vacaciones permitiendo la acumulación de múltiples hitos por día."""
    df_maestro, df_eq, df_vac = leer_excel()
    
    # 1. CONTROL DE SEGURIDAD PARA CRONOGRAMA
    if not df_maestro.empty:
        if 'Fecha de Fin' in df_maestro.columns:
            df_maestro['Fin_dt'] = pd.to_datetime(df_maestro['Fecha de Fin'], errors='coerce')
        elif 'Fecha Fin' in df_maestro.columns:
            df_maestro['Fin_dt'] = pd.to_datetime(df_maestro['Fecha Fin'], errors='coerce')
            df_maestro['Fecha de Fin'] = df_maestro['Fecha Fin']
        else:
            df_maestro['Fin_dt'] = pd.NaT
            df_maestro['Fecha de Fin'] = pd.NaT
    else:
        df_maestro['Fin_dt'] = pd.NaT
        df_maestro['Fecha de Fin'] = pd.NaT
    
    # 2. GUARDIÁN ULTRA-SEGURO PARA VACACIONES
    df_vac['Inicio_dt'] = pd.NaT
    df_vac['Fin_dt_vac'] = pd.NaT
    
    if not df_vac.empty:
        col_ini = 'Fecha_Inicio' if 'Fecha_Inicio' in df_vac.columns else ('Fecha Inicio' if 'Fecha Inicio' in df_vac.columns else None)
        col_fin = 'Fecha_Fin' if 'Fecha_Fin' in df_vac.columns else ('Fecha Fin' if 'Fecha Fin' in df_vac.columns else None)
        
        if col_ini: df_vac['Inicio_dt'] = pd.to_datetime(df_vac[col_ini], errors='coerce')
        if col_fin: df_vac['Fin_dt_vac'] = pd.to_datetime(df_vac[col_fin], errors='coerce')
        
    hoy = datetime.date.today()
    lista_dias_obj = [hoy + datetime.timedelta(days=i) for i in range(60)]
    
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    cols_dias = [f"{d.day} {meses[d.month - 1]}" for d in lista_dias_obj]
    
    columnas_fin_semana = []
    for dia_obj, col_name in zip(lista_dias_obj, cols_dias):
        if dia_obj.weekday() >= 5:
            columnas_fin_semana.append(col_name)
    
    datos_matriz = []
    
    if not df_eq.empty:
        col_nombre_eq = 'Nombre' if 'Nombre' in df_eq.columns else df_eq.columns[0]
        
        for _, tec in df_eq.iterrows():
            nombre = tec[col_nombre_eq]
            if pd.isna(nombre): continue
            
            fila = {"Técnico": nombre}
            
            proy_tec = df_maestro[(df_maestro['Técnico 1'] == nombre) | (df_maestro['Técnico 2'] == nombre) | (df_maestro['Técnico 3'] == nombre)] if not df_maestro.empty else pd.DataFrame()
            vac_tec = df_vac[df_vac['Nombre'] == nombre] if not df_vac.empty and 'Nombre' in df_vac.columns else pd.DataFrame()
                
            for dia_obj, col_name in zip(lista_dias_obj, cols_dias):
                hitos_del_dia = []
                ausencia_val = ""
                
                # A. Detectar Ausencias
                if not vac_tec.empty:
                    for _, v in vac_tec.iterrows():
                        if pd.notnull(v['Inicio_dt']) and pd.notnull(v['Fin_dt_vac']):
                            if v['Inicio_dt'].date() <= dia_obj <= v['Fin_dt_vac'].date():
                                tipo = str(v.get('Tipo_Ausencia', 'VAC')).upper()
                                if "VAC" in tipo: ausencia_val = "VAC"
                                elif "BAJA" in tipo: ausencia_val = "BAJA"
                                else: ausencia_val = "AUS"
                                break
                
                # B. Detectar Hitos
                if not proy_tec.empty:
                    for _, p in proy_tec.iterrows():
                        if pd.notnull(p['Fin_dt']) and p['Fin_dt'].date() == dia_obj:
                            nivel = str(p.get('Nivel', 'FIN')).strip()
                            if nivel == 'nan' or not nivel: nivel = 'FIN'
                            hitos_del_dia.append(nivel)
                
                # C. Formatear la celda
                if hitos_del_dia:
                    hitos_del_dia.sort()
                    texto_hitos = " ".join(hitos_del_dia)
                    if ausencia_val:
                        celda_val = f"{texto_hitos} ({ausencia_val})"
                    else:
                        celda_val = texto_hitos
                else:
                    celda_val = ausencia_val
                            
                fila[col_name] = celda_val
                
            datos_matriz.append(fila)
            
    return pd.DataFrame(datos_matriz), cols_dias, columnas_fin_semana

def layout():
    df_matriz, cols_dias, columnas_fin_semana = generar_matriz_et()
    
    if df_matriz.empty:
        return html.Div("No hay técnicos en el directorio operativo.", style={'padding': '20px', 'color': '#DB563A', 'fontFamily': "'Outfit', sans-serif", 'fontWeight': 'bold'})

    # --- CREACIÓN DE MULTI-CABECERAS (Semanas del año) ---
    hoy_base = datetime.date.today()
    # La columna Fija del Técnico queda fusionada verticalmente
    columnas_tabla = [{"name": ["", "Técnico"], "id": "Técnico"}] 
    
    for i in range(60):
        fecha_futura = hoy_base + datetime.timedelta(days=i)
        # Extraemos el número de la semana ISO (1-52)
        semana_iso = fecha_futura.isocalendar()[1]
        col_id = cols_dias[i]
        
        columnas_tabla.append({
            "name": [f"Semana {semana_iso}", col_id], 
            "id": col_id
        })

    # 1. Capa base: Fines de semana
    estilos_condicionales = []
    for col in columnas_fin_semana:
        estilos_condicionales.append({
            'if': {'column_id': col},
            'backgroundColor': '#F0EEED',
            'color': '#B3B3B3'
        })
    
    # 2. Sistema en Cascada SERVEO
    for col in cols_dias:
        estilos_condicionales.extend([
            {'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "AUS"'}, 'backgroundColor': '#E6E6E6', 'color': '#474751', 'fontSize': '10px'},
            {'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "BAJA"'}, 'backgroundColor': '#AEA4BF', 'color': '#FFFFFF', 'fontSize': '10px'},
            {'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "VAC"'}, 'backgroundColor': '#CEC6C0', 'color': '#474751', 'fontSize': '10px'},
            {'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "FIN"'}, 'backgroundColor': '#474751', 'color': '#FFFFFF', 'fontWeight': 'bold'},
            {'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "N3"'}, 'backgroundColor': '#4383F0', 'color': '#FFFFFF', 'fontWeight': 'bold'},
            {'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "N2"'}, 'backgroundColor': '#FF4E00', 'color': '#FFFFFF', 'fontWeight': 'bold'},
            {'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "N1"'}, 'backgroundColor': '#DB563A', 'color': '#FFFFFF', 'fontWeight': 'bold'}
        ])

    estilos_cabecera_condicionales = [
        {'if': {'column_id': col}, 'backgroundColor': '#F0EEED', 'color': '#666666'} 
        for col in columnas_fin_semana
    ]

    return html.Div([
        html.H3("Matriz de Estimación Temporal (ET)", style={'color': '#FF4E00', 'fontSize': '12px', 'textTransform': 'uppercase', 'fontFamily': "'Outfit', sans-serif", 'marginBottom': '20px'}),
        
        html.Div([
            html.Span("LEYENDA: ", style={'fontWeight': 'bold', 'marginRight': '15px'}),
            html.Span("Nivel 1 (Crítico)", style={'backgroundColor': '#DB563A', 'color': '#FFFFFF', 'padding': '4px 8px', 'borderRadius': '4px', 'marginRight': '10px'}),
            html.Span("Nivel 2 (Medio)", style={'backgroundColor': '#FF4E00', 'color': '#FFFFFF', 'padding': '4px 8px', 'borderRadius': '4px', 'marginRight': '10px'}),
            html.Span("Nivel 3 (Estándar)", style={'backgroundColor': '#4383F0', 'color': '#FFFFFF', 'padding': '4px 8px', 'borderRadius': '4px', 'marginRight': '10px'}),
            html.Span("Vacaciones", style={'backgroundColor': '#CEC6C0', 'color': '#474751', 'padding': '4px 8px', 'borderRadius': '4px', 'marginRight': '10px'}),
            html.Span("Fin de Semana", style={'backgroundColor': '#F0EEED', 'color': '#474751', 'padding': '4px 8px', 'borderRadius': '4px', 'border': '1px solid #B3B3B3'})
        ], style={'fontSize': '10px', 'fontFamily': "'Outfit', sans-serif", 'color': '#474751', 'marginBottom': '20px'}),

        dash_table.DataTable(
            id='tabla-matriz-et',
            columns=columnas_tabla,
            data=df_matriz.to_dict('records'),
            merge_duplicate_headers=True, # Activa la fusión elegante de la cabecera superior "Semana X"
            fixed_columns={'headers': True, 'data': 1},
            cell_selectable=False, 
            style_header={
                'backgroundColor': '#FFFFFF', 'color': '#FF4E00', 'fontWeight': 'bold', 
                'border': '1px solid #474751', 'fontFamily': "'Outfit', sans-serif", 
                'fontSize': '9px', 'textTransform': 'uppercase', 'textAlign': 'center',
                'minWidth': '65px', 'width': '65px', 'maxWidth': '65px'
            },
            style_header_conditional=estilos_cabecera_condicionales,
            style_cell={
                'backgroundColor': '#FFFFFF', 'color': '#474751', 'border': '1px solid #F0EEED', 
                'padding': '8px 4px', 'textAlign': 'center', 'fontFamily': "'Outfit', sans-serif", 
                'fontSize': '11px', 'minWidth': '65px', 'width': '65px', 'maxWidth': '65px'
            },
            style_cell_conditional=[
                # FIX VISUAL: Fondo blanco puro y un borde derecho sólido para hacer de "Muro" separador
                {
                    'if': {'column_id': 'Técnico'}, 
                    'minWidth': '180px', 'width': '180px', 'maxWidth': '180px', 
                    'textAlign': 'left', 'fontWeight': 'bold', 
                    'backgroundColor': '#FFFFFF', 
                    'borderRight': '2px solid #474751'
                }
            ],
            style_data_conditional=estilos_condicionales,
            style_table={'overflowX': 'auto', 'minWidth': '100%', 'borderRadius': '6px'}
        )
    ], style={'paddingBottom': '40px'})

def register_callbacks(app):
    pass