from dash import html, dcc, Input, Output, State, ctx
import dash
import pandas as pd
import datetime
from utils.data_manager import obtener_datos_eficiente, guardar_sqlite_centralizado, obtener_calendarios

def generar_opciones_empleados(df_equipo):
    if df_equipo.empty:
        return []
    return [{'label': f"{row['ID_Tecnico']} - {row['Nombre']}", 'value': row['ID_Tecnico']} 
            for _, row in df_equipo.iterrows() if pd.notna(row.get('ID_Tecnico'))]

def obtener_opciones_responsables(df_equipo):
    if df_equipo.empty:
        return []
    heads = df_equipo[df_equipo['Perfil Técnico'].astype(str).str.contains('Head', case=False, na=False)]
    return [{'label': f"{row['Nombre']} ({row['Perfil Técnico']})", 'value': row['Nombre']} for _, row in heads.iterrows()]

# --- RENDERS DE TARJETAS AGRUPADAS POR RESPONSABLE (CON CÁLCULO DINÁMICO DE VACACIONES) ---
def generar_tarjetas_equipo(df_equipo, df_vac):
    if df_equipo.empty:
        return html.Div("No hay técnicos registrados en el directorio.", 
                        style={'color': 'var(--gray-b3)', 'fontFamily': 'var(--font-family)', 'fontStyle': 'italic', 'padding': '16px'})

    df_temp = df_equipo.copy()
    dict_cals = obtener_calendarios(force_reload=False)
    
    if not df_vac.empty:
        col_ini = 'Fecha_Inicio' if 'Fecha_Inicio' in df_vac.columns else ('Fecha Inicio' if 'Fecha Inicio' in df_vac.columns else None)
        col_fin = 'Fecha_Fin' if 'Fecha_Fin' in df_vac.columns else ('Fecha Fin' if 'Fecha Fin' in df_vac.columns else None)
        df_vac['Inicio_dt'] = pd.to_datetime(df_vac[col_ini], errors='coerce') if col_ini else pd.NaT
        df_vac['Fin_dt_vac'] = pd.to_datetime(df_vac[col_fin], errors='coerce') if col_fin else pd.NaT
    
    df_heads = df_temp[df_temp['Perfil Técnico'].astype(str).str.contains('Head of Bidding', case=False, na=False)]
    df_resto = df_temp[~df_temp['Perfil Técnico'].astype(str).str.contains('Head of Bidding', case=False, na=False)]

    def construir_tarjeta_individual(row, nivel_rol):
        tec_id = row.get('ID_Tecnico', 'TEC-XX')
        nombre = row.get('Nombre', 'Técnico')
        rol = row.get('Perfil Técnico', 'Sin Rol Definido')
        sede = row.get('Sede', 'MAD (Quint)')
        
        vac_pasado = row.get('Vac_Pasado', 0)
        vac_este = row.get('Vac_Este', 0)
        
        vac_pasado = 0 if pd.isna(vac_pasado) or vac_pasado == "" else float(vac_pasado)
        vac_este = 0 if pd.isna(vac_este) or vac_este == "" else float(vac_este)
        
        vac_consumidas = 0.0
        if not df_vac.empty and 'Nombre' in df_vac.columns:
            vacs_tecnico = df_vac[(df_vac['Nombre'] == nombre) & (df_vac['Tipo_Ausencia'].str.contains('VAC', case=False, na=False))]
            for _, v in vacs_tecnico.iterrows():
                if pd.notnull(v['Inicio_dt']) and pd.notnull(v['Fin_dt_vac']):
                    start_d = v['Inicio_dt'].date()
                    end_d = v['Fin_dt_vac'].date()
                    
                    if start_d <= end_d:
                        curr_d = start_d
                        while curr_d <= end_d:
                            if curr_d.weekday() < 5: 
                                es_festivo = False
                                if sede in dict_cals and curr_d in dict_cals[sede]:
                                    if float(dict_cals[sede][curr_d]) == 0.0:
                                        es_festivo = True
                                
                                if not es_festivo:
                                    vac_consumidas += 1.0
                                    
                            curr_d += datetime.timedelta(days=1)

        vac_totales = vac_pasado + vac_este
        vac_restantes = vac_totales - vac_consumidas

        if nivel_rol == 2:
            color_bg, text_color, badge_bg = '#FAFAFA', '#4383F0', 'rgba(67, 131, 240, 0.1)'
        else:
            color_bg, text_color, badge_bg = '#FFFFFF', '#FF4E00', 'rgba(255, 78, 0, 0.1)'

        return html.Div([
            html.Div([
                html.Div(str(nombre)[:2].upper(), style={
                    'width': '36px', 'height': '36px', 'borderRadius': '999px',
                    'backgroundColor': 'var(--card-divider)', 'color': 'var(--text-border)',
                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                    'fontWeight': '700', 'fontSize': '12px', 'fontFamily': 'Outfit'
                }),
                html.Span(f"#{tec_id}", style={'fontSize': '11px', 'fontWeight': '700', 'color': 'var(--gray-66)', 'fontFamily': 'Outfit'})
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '12px'}),
            
            html.Div(nombre, style={'fontWeight': '700', 'fontSize': '15px', 'color': 'var(--color-title)', 'marginBottom': '4px', 'textOverflow': 'ellipsis', 'overflow': 'hidden', 'whiteSpace': 'nowrap'}),
            
            html.Div([
                html.Span(rol, style={
                    'color': text_color, 'backgroundColor': badge_bg,
                    'padding': '3px 8px', 'borderRadius': 'var(--radius-pill)',
                    'fontSize': '9px', 'fontWeight': '700', 'textTransform': 'uppercase', 'letterSpacing': '0.5px'
                }),
                html.Span(sede, style={
                    'color': 'var(--text-border)', 'backgroundColor': 'var(--card-divider)',
                    'padding': '3px 8px', 'borderRadius': 'var(--radius-pill)',
                    'fontSize': '9px', 'fontWeight': '700', 'textTransform': 'uppercase', 'letterSpacing': '0.5px'
                })
            ], style={'marginBottom': '0px', 'display': 'flex', 'flexWrap': 'wrap', 'gap': '6px'}),
            
            html.Div([
                html.Div([
                    html.Span("Asignadas", style={'fontSize': '9px', 'color': 'var(--gray-66)', 'textTransform': 'uppercase'}),
                    html.Span(f"{vac_totales:g}d", style={'fontSize': '13px', 'fontWeight': '700', 'color': 'var(--color-title)'})
                ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'flex-start', 'flex': '1'}),
                
                html.Div([
                    html.Span("Consumidas", style={'fontSize': '9px', 'color': 'var(--gray-66)', 'textTransform': 'uppercase'}),
                    html.Span(f"{vac_consumidas:g}d", style={'fontSize': '13px', 'fontWeight': '700', 'color': 'var(--semantic-negative)'})
                ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'flex': '1', 'borderLeft': '1px solid var(--card-divider)', 'borderRight': '1px solid var(--card-divider)'}),
                
                html.Div([
                    html.Span("Restantes", style={'fontSize': '9px', 'color': 'var(--gray-66)', 'textTransform': 'uppercase'}),
                    html.Span(f"{vac_restantes:g}d", style={'fontSize': '13px', 'fontWeight': '700', 'color': 'var(--semantic-positive)'})
                ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'flex-end', 'flex': '1'})
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginTop': '16px', 'paddingTop': '12px', 'borderTop': '1px solid var(--card-divider)'})
            
        ], className="card-serveo", style={'marginBottom': '0', 'boxShadow': '0 4px 12px rgba(71, 71, 81, 0.02)', 'padding': '16px', 'backgroundColor': color_bg})

    bloques_jerarquicos = []

    for _, head_row in df_heads.iterrows():
        head_nombre = head_row['Nombre']
        mi_equipo = df_resto[df_resto['Responsable'] == head_nombre]
        
        mis_bams = mi_equipo[mi_equipo['Perfil Técnico'].astype(str).str.contains('Area Manager', case=False, na=False)]
        mis_tecs = mi_equipo[mi_equipo['Perfil Técnico'].astype(str).str.contains('Technician', case=False, na=False)]
        
        grid_bams = html.Div(
            [construir_tarjeta_individual(r, 2) for _, r in mis_bams.iterrows()],
            style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fill, minmax(260px, 1fr))', 'gap': '16px', 'marginTop': '12px'}
        ) if not mis_bams.empty else html.Div("Sin BAMs asignados.", style={'color': 'var(--gray-b3)', 'fontStyle': 'italic', 'fontSize': '12px', 'marginTop': '12px'})

        grid_tecs = html.Div(
            [construir_tarjeta_individual(r, 3) for _, r in mis_tecs.iterrows()],
            style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fill, minmax(260px, 1fr))', 'gap': '16px', 'marginTop': '12px'}
        ) if not mis_tecs.empty else html.Div("Sin Técnicos asignados.", style={'color': 'var(--gray-b3)', 'fontStyle': 'italic', 'fontSize': '12px', 'marginTop': '12px'})

        bloque_head = html.Div([
            html.Div([
                html.Div([
                    html.Span("Head of Bidding:", style={'fontSize': '11px', 'color': 'var(--text-border)', 'textTransform': 'uppercase', 'fontWeight': 'bold', 'display': 'block'}),
                    html.Span(head_nombre, style={'fontSize': '22px', 'fontWeight': '800', 'color': 'var(--color-title)'})
                ]),
                html.Span(f"HEAD ({head_row.get('Sede', 'MAD')})", style={'fontSize': '11px', 'backgroundColor': 'var(--text-border)', 'color': '#FFFFFF', 'padding': '4px 12px', 'borderRadius': '4px', 'fontWeight': 'bold'})
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'borderBottom': '3px solid var(--text-border)', 'paddingBottom': '16px', 'marginBottom': '24px'}),
            
            html.H4("Bidding Area Managers", style={'fontSize': '13px', 'color': 'var(--color-title)', 'marginBottom': '0'}),
            grid_bams,
            html.Div(style={'height': '1px', 'backgroundColor': 'var(--card-divider)', 'margin': '24px 0'}),
            
            html.H4("Bidding Technicians", style={'fontSize': '13px', 'color': 'var(--color-title)', 'marginBottom': '0'}),
            grid_tecs
            
        ], style={'backgroundColor': '#FFFFFF', 'border': '2px solid var(--card-divider)', 'borderRadius': 'var(--radius-container)', 'padding': '32px', 'marginBottom': '40px', 'boxShadow': '0 8px 24px rgba(71, 71, 81, 0.04)'})
        
        bloques_jerarquicos.append(bloque_head)

    nombres_heads = df_heads['Nombre'].tolist()
    empleados_huerfanos = df_resto[~df_resto['Responsable'].isin(nombres_heads) | df_resto['Responsable'].isna()]
    
    if not empleados_huerfanos.empty:
        bloque_huerfanos = html.Div([
            html.Div("Personal Pendiente de Asignación de Responsable", style={'fontSize': '13px', 'fontWeight': '700', 'color': 'var(--semantic-negative)', 'borderBottom': '1px solid var(--semantic-negative)', 'paddingBottom': '6px', 'marginBottom': '16px'}),
            html.Div([construir_tarjeta_individual(h_row, 3) for _, h_row in empleados_huerfanos.iterrows()],
                     style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fill, minmax(260px, 1fr))', 'gap': '16px'})
        ], style={'backgroundColor': 'rgba(219,86,58,0.03)', 'border': '1px dashed var(--semantic-negative)', 'borderRadius': 'var(--radius-container)', 'padding': '24px', 'marginBottom': '32px'})
        bloques_jerarquicos.append(bloque_huerfanos)

    return html.Div(bloques_jerarquicos)


def layout(rol='lector'):
    _, _, df_equipo, df_vac, _ = obtener_datos_eficiente(force_reload=False)
    
    opciones_empleados = generar_opciones_empleados(df_equipo)
    opciones_responsables = obtener_opciones_responsables(df_equipo)
    tarjetas_iniciales = generar_tarjetas_equipo(df_equipo, df_vac)

    opciones_roles = [
        {'label': 'Head of Bidding', 'value': 'Head of Bidding'},
        {'label': 'Bidding Area Manager', 'value': 'Bidding Area Manager'},
        {'label': 'Bidding Technician', 'value': 'Bidding Technician'}
    ]

    opciones_sedes = [
        {'label': 'MAD (Quint)', 'value': 'MAD (Quint)'},
        {'label': 'BCN (T. Auditori)', 'value': 'BCN (T. Auditori)'},
        {'label': 'VALENCIA', 'value': 'VALENCIA'}
    ]

    # --- LÓGICA CONDICIONAL DE SEGURIDAD ---
    if rol == 'editor':
        panel_superior = html.Div([
            # BLOQUE IZQUIERDO: Añadir / Editar Personal
            html.Div([
                html.Div([
                    html.Span("Alta y Edición de Personal", style={'color': '#FFFFFF', 'backgroundColor': 'var(--text-border)', 'padding': '8px 16px', 'fontSize': '9px', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'borderRadius': '6px', 'marginRight': '16px'}),
                    dcc.Dropdown(id='drop-editar-id', options=opciones_empleados, placeholder="Cargar empleado existente...", style={'width': '300px'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '24px'}),
                
                html.Div([
                    html.Div([
                        html.Label("ID Empleado", className="etiqueta-dato"),
                        dcc.Input(id='input-id', placeholder='Alias...', className="input-filtro")
                    ], className="serveo-input-wrapper", style={'flex': '1'}),
                    
                    html.Div([
                        html.Label("Nombre Completo", className="etiqueta-dato"),
                        dcc.Input(id='input-nombre', placeholder='Nombre y apellidos', className="input-filtro")
                    ], className="serveo-input-wrapper", style={'flex': '2'}),
                    
                    html.Div([
                        html.Label("Perfil / Rol Operativo", className="etiqueta-dato"),
                        dcc.Dropdown(id='input-perfil', options=opciones_roles, placeholder='Selecciona nivel...', clearable=True, searchable=False)
                    ], className="serveo-input-wrapper", style={'flex': '2'}),
                ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '16px'}),

                html.Div([
                    html.Div([
                        html.Label("Sede / Centro", className="etiqueta-dato", style={'color': 'var(--accent)'}),
                        dcc.Dropdown(id='input-sede', options=opciones_sedes, placeholder='Sede de trabajo...', clearable=True, searchable=False)
                    ], className="serveo-input-wrapper", style={'flex': '1'}),

                    html.Div([
                        html.Label("Reporta a (Head Assigned)", className="etiqueta-dato", id="label-responsable"),
                        dcc.Dropdown(
                            id='input-responsable', 
                            options=opciones_responsables, 
                            placeholder='Selecciona Manager...', 
                            clearable=True,
                            disabled=False
                        )
                    ], className="serveo-input-wrapper", style={'flex': '2'}),
                ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '16px'}),

                html.Div([
                    html.Div([
                        html.Label("Vac. Pendientes (Año Ant.)", className="etiqueta-dato"),
                        dcc.Input(id='input-vac-pasado', type='number', placeholder='Días...', className="input-filtro")
                    ], className="serveo-input-wrapper", style={'flex': '1'}),
                    
                    html.Div([
                        html.Label("Vac. Asignadas (Este Año)", className="etiqueta-dato"),
                        dcc.Input(id='input-vac-este', type='number', placeholder='Días...', className="input-filtro")
                    ], className="serveo-input-wrapper", style={'flex': '1'}),
                    
                    html.Div(style={'flex': '1'}),
                ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '24px'}),
                
                html.Button('💾 Guardar / Actualizar Empleado', id='btn-anadir', n_clicks=0, className="btn-serveo-primario", style={'float': 'right'})
                
            ], className="serveo-panel-accion", style={'flex': '2', 'marginBottom': '0'}),

            # BLOQUE DERECHO: Eliminar Personal
            html.Div([
                html.Div("Baja de Personal", style={'color': '#FFFFFF', 'backgroundColor': 'var(--semantic-negative)', 'padding': '8px 16px', 'fontSize': '9px', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'marginBottom': '24px', 'borderRadius': '6px', 'display': 'inline-block'}),
                
                html.Div([
                    html.Label("Seleccionar para dar de baja:", className="etiqueta-dato"),
                    dcc.Dropdown(id='drop-eliminar-id', options=opciones_empleados, placeholder="Busca por ID o Nombre...")
                ], className="serveo-input-wrapper", style={'marginBottom': '24px'}),
                
                html.Button('🗑️ Eliminar del Sistema', id='btn-eliminar', n_clicks=0, className="btn-serveo-negativo", style={'width': '100%'})
                
            ], className="serveo-panel-accion", style={'flex': '1', 'marginBottom': '0'})
            
        ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '32px'})
    else:
        # PANTALLA MODO LECTOR (Invisible para no ensuciar la UX)
        panel_superior = html.Div(style={'display': 'none'})


    return html.Div([
        html.H3("Directorio del Equipo Técnico", className="serveo-titulo-pagina"),
        
        panel_superior,
        
        html.Div(id='mensaje-equipo', style={'marginBottom': '24px', 'fontWeight': 'bold', 'fontFamily': 'var(--font-family)', 'fontSize': '13px'}),
        
        html.H3("Estructura Organizativa", className="serveo-titulo-seccion"),
        html.Div(id='contenedor-tarjetas-equipo', children=tarjetas_iniciales)

    ], style={'paddingBottom': '40px'})


def register_callbacks(app):
    
    @app.callback(
        [Output('input-responsable', 'disabled'),
         Output('input-responsable', 'placeholder'),
         Output('input-responsable', 'options')],
        [Input('input-perfil', 'value')]
    )
    def ajustar_campo_responsable(rol_seleccionado):
        _, _, df_eq, _, _ = obtener_datos_eficiente(force_reload=False)
        opciones_heads = obtener_opciones_responsables(df_eq)
        
        if not rol_seleccionado:
            return False, "Selecciona primero un rol...", opciones_heads
        
        if "Head of Bidding" in str(rol_seleccionado):
            return True, "No requerido (Nivel de Dirección)", []
        else:
            return False, "Selecciona el Head of Bidding a cargo...", opciones_heads


    @app.callback(
        [Output('contenedor-tarjetas-equipo', 'children'),
         Output('drop-eliminar-id', 'options'),
         Output('drop-editar-id', 'options'),
         Output('mensaje-equipo', 'children'),
         Output('mensaje-equipo', 'style'),
         Output('input-id', 'value'),
         Output('input-nombre', 'value'),
         Output('input-perfil', 'value'),
         Output('input-sede', 'value'),
         Output('input-responsable', 'value'),
         Output('drop-eliminar-id', 'value'),
         Output('drop-editar-id', 'value'),
         Output('input-vac-pasado', 'value'),
         Output('input-vac-este', 'value')],
        [Input('btn-anadir', 'n_clicks'),
         Input('btn-eliminar', 'n_clicks'),
         Input('drop-editar-id', 'value')],
        [State('input-id', 'value'),
         State('input-nombre', 'value'),
         State('input-perfil', 'value'),
         State('input-sede', 'value'),
         State('input-responsable', 'value'),
         State('drop-eliminar-id', 'value'),
         State('input-vac-pasado', 'value'),
         State('input-vac-este', 'value')]
    )
    def gestionar_equipo(btn_add, btn_del, edit_id, i_id, i_nom, i_perf, i_sede, i_resp, del_id, i_vac_p, i_vac_e):
        trigger = ctx.triggered_id
        if not trigger:
            raise dash.exceptions.PreventUpdate

        _, _, df_eq, df_vac, error_sistema = obtener_datos_eficiente(force_reload=False)
        estilo_mensaje = {'marginBottom': '24px', 'fontWeight': 'bold', 'fontFamily': 'var(--font-family)', 'fontSize': '13px'}

        if error_sistema:
            estilo_msg = estilo_mensaje.copy()
            estilo_msg['color'] = 'var(--semantic-negative)'
            return [dash.no_update]*3 + [error_sistema, estilo_msg] + [dash.no_update]*9

        ret = [dash.no_update] * 14

        if trigger == 'drop-editar-id':
            if edit_id and edit_id in df_eq['ID_Tecnico'].values:
                fila_editar = df_eq[df_eq['ID_Tecnico'] == edit_id].iloc[0]
                ret[5] = fila_editar['ID_Tecnico']
                ret[6] = fila_editar['Nombre']
                ret[7] = fila_editar['Perfil Técnico']
                ret[8] = fila_editar.get('Sede', 'MAD (Quint)')
                ret[9] = fila_editar.get('Responsable', '')
                
                ret[12] = fila_editar.get('Vac_Pasado', '')
                ret[13] = fila_editar.get('Vac_Este', '')
                
                ret[3] = f"✏️ Modo Edición: Editando los datos de {fila_editar['Nombre']}. Modifica los campos y pulsa Guardar."
                ret[4] = {'color': 'var(--accent)', 'marginBottom': '24px', 'fontWeight': 'bold'}
            else:
                ret[5], ret[6], ret[7], ret[8], ret[9] = "", "", None, None, None
                ret[12], ret[13] = "", ""
                ret[3], ret[4] = "", estilo_mensaje
            return tuple(ret)

        exito = False

        if trigger == 'btn-anadir':
            if not i_id or not i_nom or not i_perf or not i_sede:
                ret[4] = {'color': 'var(--semantic-negative)', 'marginBottom': '24px', 'fontWeight': 'bold'}
                ret[3] = "⚠️ El ID, Nombre, Perfil y Sede son campos obligatorios."
                return tuple(ret)
                
            if "Head of Bidding" not in str(i_perf) and not i_resp:
                ret[4] = {'color': 'var(--semantic-negative)', 'marginBottom': '24px', 'fontWeight': 'bold'}
                ret[3] = "⚠️ Error: BAMs y Técnicos deben tener un Head of Bidding asignado."
                return tuple(ret)

            val_responsable = "" if "Head of Bidding" in str(i_perf) else i_resp

            val_vac_p = float(i_vac_p) if i_vac_p else 0.0
            val_vac_e = float(i_vac_e) if i_vac_e else 0.0

            columnas_texto = ['ID_Tecnico', 'Nombre', 'Perfil Técnico', 'Responsable', 'Sede']
            for col in columnas_texto:
                if col not in df_eq.columns: df_eq[col] = ""
                df_eq[col] = df_eq[col].astype(object)

            if str(i_id).strip() in df_eq['ID_Tecnico'].astype(str).values:
                mask = df_eq['ID_Tecnico'].astype(str) == str(i_id).strip()
                df_eq.loc[mask, 'Nombre'] = str(i_nom).strip()
                df_eq.loc[mask, 'Perfil Técnico'] = str(i_perf).strip()
                df_eq.loc[mask, 'Sede'] = str(i_sede).strip()
                df_eq.loc[mask, 'Responsable'] = val_responsable
                df_eq.loc[mask, 'Vac_Pasado'] = val_vac_p
                df_eq.loc[mask, 'Vac_Este'] = val_vac_e
                
                ret[3] = f"💾 ¡Datos de {i_nom} actualizados correctamente!"
            else:
                nueva_fila = pd.DataFrame([{
                    'ID_Tecnico': str(i_id).strip(), 
                    'Nombre': str(i_nom).strip(), 
                    'Perfil Técnico': str(i_perf).strip(), 
                    'Horas_Jornada': 8.0,
                    'Responsable': val_responsable,
                    'Sede': str(i_sede).strip(),
                    'Vac_Pasado': val_vac_p,
                    'Vac_Este': val_vac_e
                }])
                df_eq = pd.concat([df_eq, nueva_fila], ignore_index=True)
                ret[3] = f"✅ Personal {i_nom} dado de alta correctamente en la sede {i_sede}."
                
            ret[4] = {'color': 'var(--semantic-positive)', 'marginBottom': '24px', 'fontWeight': 'bold'}
            ret[5], ret[6], ret[7], ret[8], ret[9], ret[11] = "", "", None, None, None, None
            ret[12], ret[13] = "", ""
            exito = True

        elif trigger == 'btn-eliminar':
            if not del_id:
                ret[4] = {'color': 'var(--semantic-negative)', 'marginBottom': '24px', 'fontWeight': 'bold'}
                ret[3] = "⚠️ Selecciona un empleado para dar de baja."
                return tuple(ret)
                
            if str(del_id).strip() in df_eq['ID_Tecnico'].astype(str).values:
                nombre_borrado = df_eq[df_eq['ID_Tecnico'].astype(str) == str(del_id).strip()]['Nombre'].values[0]
                df_eq = df_eq[df_eq['ID_Tecnico'].astype(str) != str(del_id).strip()]
                
                ret[3] = f"🗑️ Empleado {nombre_borrado} eliminado correctamente del sistema."
                ret[4] = {'color': 'var(--semantic-positive)', 'marginBottom': '24px', 'fontWeight': 'bold'}
                ret[10] = None
                exito = True
            else:
                ret[4] = {'color': 'var(--semantic-negative)', 'marginBottom': '24px', 'fontWeight': 'bold'}
                ret[3] = "⚠️ ID no encontrado."

        if exito:
            guardado_exitoso, msg_sistema = guardar_sqlite_centralizado(df_eq_new=df_eq)
            if not guardado_exitoso:
                ret[4] = {'color': 'var(--semantic-negative)', 'marginBottom': '24px', 'fontWeight': 'bold'}
                ret[3] = msg_sistema
                return tuple(ret)
            
            _, _, df_eq_fresco, df_vac_fresco, _ = obtener_datos_eficiente(force_reload=True)
            
            ret[0] = generar_tarjetas_equipo(df_eq_fresco, df_vac_fresco)
            opc_nuevas = generar_opciones_empleados(df_eq_fresco)
            ret[1] = opc_nuevas
            ret[2] = opc_nuevas

        return tuple(ret)