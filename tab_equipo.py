from dash import html, dcc, dash_table, Input, Output, State, ctx
import dash
import pandas as pd
from utils.data_manager import leer_excel, ARCHIVO_EXCEL

def generar_opciones_borrado(df_equipo):
    """Genera las opciones para el desplegable de eliminar basado en los datos reales."""
    if df_equipo.empty:
        return []
    return [{'label': f"{row['ID_Tecnico']} - {row['Nombre']}", 'value': row['ID_Tecnico']} 
            for _, row in df_equipo.iterrows() if pd.notna(row.get('ID_Tecnico'))]

def obtener_opciones_responsables(df_equipo):
    """Filtra y devuelve los BAMs disponibles para ser asignados como responsables."""
    if df_equipo.empty:
        return []
    # Filtrar por rol de Manager (BAM)
    bams = df_equipo[df_equipo['Perfil Técnico'].astype(str).str.contains('Manager', case=False, na=False)]
    return [{'label': row['Nombre'], 'value': row['Nombre']} for _, row in bams.iterrows()]


# --- RENDERS DE TARJETAS AGRUPADAS POR RESPONSABLE (JERARQUÍA COHESIVA) ---
def generar_tarjetas_equipo(df_equipo):
    """Construye la estructura del equipo organizada por Responsables / BAMs."""
    if df_equipo.empty:
        return html.Div("No hay técnicos registrados en el directorio.", 
                        style={'color': 'var(--gray-b3)', 'fontFamily': 'var(--font-family)', 'fontStyle': 'italic', 'padding': '16px'})

    df_temp = df_equipo.copy()
    
    # Separamos en dos grupos: Líderes (BAM) y Técnicos con responsable
    df_bams = df_temp[df_temp['Perfil Técnico'].astype(str).str.contains('Manager', case=False, na=False)]
    df_tecnicos = df_temp[~df_temp['Perfil Técnico'].astype(str).str.contains('Manager', case=False, na=False)]

    # Función auxiliar para pintar la tarjeta física individual de cualquier empleado
    def construir_tarjeta_individual(row, es_bam=False):
        tec_id = row.get('ID_Tecnico', 'TEC-XX')
        nombre = row.get('Nombre', 'Técnico')
        rol = row.get('Perfil Técnico', 'Sin Rol Definido')
        horas = row.get('Horas_Jornada', 8)
        
        color_badge = '#4383F0' if es_bam else '#FF4E00'
        bg_badge = 'rgba(67, 131, 240, 0.1)' if es_bam else 'rgba(255, 78, 0, 0.1)'

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
                    'color': color_badge, 'backgroundColor': bg_badge,
                    'padding': '3px 8px', 'borderRadius': 'var(--radius-pill)',
                    'fontSize': '9px', 'fontWeight': '700', 'textTransform': 'uppercase', 'letterSpacing': '0.5px'
                })
            ], style={'marginBottom': '12px'}),
            
            html.Div([
                html.Span("Jornada", style={'fontSize': '11px', 'color': 'var(--gray-66)'}),
                html.Span(f"{horas}h/día", style={'fontSize': '12px', 'fontWeight': '700', 'color': 'var(--color-title)'})
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'borderTop': '1px solid var(--card-divider)', 'paddingTop': '8px'})
            
        ], className="card-serveo", style={'marginBottom': '0', 'boxShadow': '0 4px 12px rgba(71, 71, 81, 0.02)', 'padding': '16px', 'backgroundColor': '#FFFFFF'})

    bloques_jerarquicos = []

    # 1. Iteramos por cada BAM para crear su sección y meter a sus técnicos asignados
    for _, bam_row in df_bams.iterrows():
        bam_nombre = bam_row['Nombre']
        
        # Filtrar los técnicos que dependen de este BAM concreto
        mis_tecnicos = df_tecnicos[df_tecnicos['Responsable'] == bam_nombre]
        
        grid_tecnicos = html.Div(
            [construir_tarjeta_individual(t_row, es_bam=False) for _, t_row in mis_tecnicos.iterrows()],
            style={
                'display': 'grid',
                'gridTemplateColumns': 'repeat(auto-fill, minmax(240px, 1fr))',
                'gap': '16px',
                'marginTop': '12px'
            }
        ) if not mis_tecnicos.empty else html.Div("Este mánager no tiene técnicos asignados todavía.", style={'color': 'var(--gray-b3)', 'fontStyle': 'italic', 'fontSize': '12px', 'marginTop': '12px'})

        # Contenedor del grupo del Mánager (Módulo visual delimitado)
        bloque_grupo = html.Div([
            # Cabecera del grupo (La tarjeta del Líder BAM de forma destacada)
            html.Div([
                html.Div([
                    html.Span("Área / Cuentas de:", style={'fontSize': '10px', 'color': 'var(--gray-66)', 'textTransform': 'uppercase', 'fontWeight': 'bold', 'display': 'block'}),
                    html.Span(bam_nombre, style={'fontSize': '18px', 'fontWeight': '700', 'color': 'var(--color-title)'})
                ]),
                html.Div([
                    html.Span(f"LÍDER BAM (#{bam_row.get('ID_Tecnico')})", style={'fontSize': '9px', 'backgroundColor': 'rgba(67,131,240,0.15)', 'color': '#4383F0', 'padding': '4px 8px', 'borderRadius': '4px', 'fontWeight': 'bold', 'marginRight': '12px'}),
                    html.Span(f"{len(mis_tecnicos)} Técnicos a cargo", style={'fontSize': '11px', 'color': 'var(--gray-66)', 'fontWeight': '600'})
                ], style={'display': 'flex', 'alignItems': 'center'})
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'borderBottom': '2px solid var(--text-border)', 'paddingBottom': '12px', 'marginBottom': '16px'}),
            
            # Sub-grid de sus técnicos dependientes
            grid_tecnicos
            
        ], style={'backgroundColor': '#FAFAFA', 'border': '1px solid var(--card-divider)', 'borderRadius': 'var(--radius-container)', 'padding': '24px', 'marginBottom': '32px'})
        
        bloques_jerarquicos.append(bloque_grupo)

    # 2. Capturar huérfanos (Técnicos que tengan un responsable no existente o vacío por error)
    nombres_bam = df_bams['Nombre'].tolist()
    tecnicos_huerfanos = df_tecnicos[~df_tecnicos['Responsable'].isin(nombres_bam) | df_tecnicos['Responsable'].isna()]
    
    if not tecnicos_huerfanos.empty:
        bloque_huerfanos = html.Div([
            html.Div("Personal Pendiente de Asignación de Responsable", style={'fontSize': '13px', 'fontWeight': '700', 'color': 'var(--semantic-negative)', 'borderBottom': '1px solid var(--semantic-negative)', 'paddingBottom': '6px', 'marginBottom': '16px'}),
            html.Div([construir_tarjeta_individual(h_row, es_bam=False) for _, h_row in tecnicos_huerfanos.iterrows()],
                     style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fill, minmax(240px, 1fr))', 'gap': '16px'})
        ], style={'backgroundColor': 'rgba(219,86,58,0.03)', 'border': '1px dashed var(--semantic-negative)', 'borderRadius': 'var(--radius-container)', 'padding': '24px', 'marginBottom': '32px'})
        bloques_jerarquicos.append(bloque_huerfanos)

    return html.Div(bloques_jerarquicos)


def layout():
    _, df_equipo, _ = leer_excel()
    
    opciones_borrar = generar_opciones_borrado(df_equipo)
    opciones_responsables = obtener_opciones_responsables(df_equipo)
    tarjetas_iniciales = generar_tarjetas_equipo(df_equipo)

    opciones_roles = [
        {'label': 'Business Area Manager', 'value': 'Business Area Manager'},
        {'label': 'Bidding Technician', 'value': 'Bidding Technician'}
    ]

    return html.Div([
        html.H3("Directorio del Equipo Técnico", className="serveo-titulo-pagina"),
        
        # --- PANEL DE CONTROL DUAL ---
        html.Div([
            
            # BLOQUE IZQUIERDO: Añadir Técnico (Con lógica de Responsable añadida)
            html.Div([
                html.Div("Dar de Alta Nuevo Técnico", style={'color': '#FFFFFF', 'backgroundColor': 'var(--text-border)', 'padding': '8px 16px', 'fontSize': '9px', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'marginBottom': '24px', 'borderRadius': '6px', 'display': 'inline-block'}),
                
                # Fila de Inputs Principal
                html.Div([
                    html.Div([
                        html.Label("ID Técnico", className="etiqueta-dato"),
                        dcc.Input(id='input-id', placeholder='Ej. TEC-01', className="input-filtro")
                    ], className="serveo-input-wrapper", style={'flex': '1'}),
                    
                    html.Div([
                        html.Label("Nombre Completo", className="etiqueta-dato"),
                        dcc.Input(id='input-nombre', placeholder='Nombre y apellidos', className="input-filtro")
                    ], className="serveo-input-wrapper", style={'flex': '2'}),
                    
                    html.Div([
                        html.Label("Perfil / Rol", className="etiqueta-dato"),
                        dcc.Dropdown(id='input-perfil', options=opciones_roles, placeholder='Selecciona rol...', clearable=True, searchable=False)
                    ], className="serveo-input-wrapper", style={'flex': '2'}),
                ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '16px'}),

                # Segunda Fila de Inputs: Horas y NUEVO CAMPO Responsable
                html.Div([
                    html.Div([
                        html.Label("Horas/Día", className="etiqueta-dato"),
                        dcc.Input(id='input-horas', placeholder='Ej. 8', type='number', className="input-filtro")
                    ], className="serveo-input-wrapper", style={'flex': '1'}),

                    html.Div([
                        html.Label("Responsable Asignado (Obligatorio para Técnicos)", className="etiqueta-dato", id="label-responsable"),
                        dcc.Dropdown(
                            id='input-responsable', 
                            options=opciones_responsables, 
                            placeholder='Selecciona el BAM a cargo...', 
                            clearable=True,
                            disabled=False
                        )
                    ], className="serveo-input-wrapper", style={'flex': '2'}),
                ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '24px'}),
                
                html.Button('Añadir al Equipo', id='btn-anadir', n_clicks=0, className="btn-serveo-primario", style={'float': 'right'})
                
            ], className="serveo-panel-accion", style={'flex': '2', 'marginBottom': '0'}),

            # BLOQUE DERECHO: Eliminar Técnico
            html.Div([
                html.Div("Baja de Técnico", style={'color': '#FFFFFF', 'backgroundColor': 'var(--semantic-negative)', 'padding': '8px 16px', 'fontSize': '9px', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'marginBottom': '24px', 'borderRadius': '6px', 'display': 'inline-block'}),
                
                html.Div([
                    html.Label("Seleccionar para eliminar:", className="etiqueta-dato"),
                    dcc.Dropdown(id='drop-eliminar-id', options=opciones_borrar, placeholder="Busca por ID o Nombre...")
                ], className="serveo-input-wrapper", style={'marginBottom': '24px'}),
                
                html.Button('Eliminar del Sistema', id='btn-eliminar', n_clicks=0, className="btn-serveo-negativo", style={'width': '100%'})
                
            ], className="serveo-panel-accion", style={'flex': '1', 'marginBottom': '0'})
            
        ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '32px'}),
        
        # Chivato de notificaciones
        html.Div(id='mensaje-equipo', style={'marginBottom': '24px', 'fontWeight': 'bold', 'fontFamily': 'var(--font-family)', 'fontSize': '13px'}),
        
        # --- SECCIÓN DE ORGANIGRAMA / TARJETAS VISUALES ---
        html.H3("Estructura Operativa del Equipo", className="serveo-titulo-seccion"),
        html.Div(id='contenedor-tarjetas-equipo', children=tarjetas_iniciales)

    ], style={'paddingBottom': '40px'})


def register_callbacks(app):
    # --- CALLBACK 1: COMPORTAMIENTO DINÁMICO DEL DESPLEGABLE RESPONSABLE ---
    @app.callback(
        [Output('input-responsable', 'disabled'),
         Output('input-responsable', 'placeholder'),
         Output('input-responsable', 'value')],
        [Input('input-perfil', 'value')]
    )
    def ajustar_campo_responsable(rol_seleccionado):
        """Bloquea o desbloquea el campo responsable según el tipo de rol."""
        if not rol_seleccionado:
            return False, "Selecciona primero un rol...", None
        
        if "Manager" in str(rol_seleccionado):
            # Es un BAM, no requiere ni puede tener responsable asignado
            return True, "No requerido (Es un perfil BAM corporativo)", None
        
        return False, "Selecciona el BAM a cargo...", None


    # --- CALLBACK 2: GESTIÓN INTEGRAL (ALTA/BAJA/EXCEL) ---
    @app.callback(
        [Output('contenedor-tarjetas-equipo', 'children'),
         Output('drop-eliminar-id', 'options'),
         Output('input-responsable', 'options'), # <-- Actualizar dropdown de la interfaz al meter nuevos BAMs
         Output('mensaje-equipo', 'children'),
         Output('mensaje-equipo', 'style'),
         Output('input-id', 'value'),
         Output('input-nombre', 'value'),
         Output('input-perfil', 'value'),
         Output('input-horas', 'value'),
         Output('drop-eliminar-id', 'value')],
        [Input('btn-anadir', 'n_clicks'),
         Input('btn-eliminar', 'n_clicks')],
        [State('input-id', 'value'),
         State('input-nombre', 'value'),
         State('input-perfil', 'value'),
         State('input-horas', 'value'),
         State('input-responsable', 'value'),
         State('drop-eliminar-id', 'value')]
    )
    def gestionar_equipo(btn_add, btn_del, i_id, i_nom, i_perf, i_hor, i_resp, del_id):
        trigger = ctx.triggered_id
        if not trigger:
            raise dash.exceptions.PreventUpdate

        _, df_eq, _ = leer_excel()
        mensaje = ""
        estilo_mensaje = {'marginBottom': '24px', 'fontWeight': 'bold', 'fontFamily': 'var(--font-family)', 'fontSize': '13px'}

        c_id, c_nom, c_perf, c_hor, c_del = dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # ====================
        # ACCIÓN: AÑADIR
        # ====================
        if trigger == 'btn-anadir':
            if not i_id or not i_nom or not i_perf:
                estilo_mensaje['color'] = 'var(--semantic-negative)'
                return dash.no_update, dash.no_update, dash.no_update, "⚠️ El ID, Nombre y Perfil son campos obligatorios.", estilo_mensaje, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
                
            # Regla de Negocio: Si no es BAM, obligatoriamente tiene que definir a su mánager
            if "Manager" not in str(i_perf) and not i_resp:
                estilo_mensaje['color'] = 'var(--semantic-negative)'
                return dash.no_update, dash.no_update, dash.no_update, "⚠️ Campo obligatorio: Los Técnicos deben tener un Responsable (BAM) asignado.", estilo_mensaje, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

            if not df_eq.empty and i_id in df_eq['ID_Tecnico'].astype(str).values:
                estilo_mensaje['color'] = 'var(--semantic-negative)'
                return dash.no_update, dash.no_update, dash.no_update, f"⚠️ Error: El ID {i_id} ya existe.", estilo_mensaje, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

            # Si es un BAM, guardamos el campo vacío (o un guión limpio) en la columna Responsable del Excel
            val_responsable = "" if "Manager" in str(i_perf) else i_resp

            nueva_fila = pd.DataFrame([{
                'ID_Tecnico': i_id, 
                'Nombre': i_nom, 
                'Perfil Técnico': i_perf, 
                'Horas_Jornada': i_hor,
                'Responsable': val_responsable # Guardado del nuevo campo
            }])
            
            df_eq = pd.concat([df_eq, nueva_fila], ignore_index=True)
            mensaje = f"✅ Técnico {i_nom} dado de alta y asignado correctamente."
            estilo_mensaje['color'] = 'var(--semantic-positive)'
            c_id, c_nom, c_perf, c_hor = "", "", None, ""

        # ====================
        # ACCIÓN: ELIMINAR
        # ====================
        elif trigger == 'btn-eliminar':
            if not del_id:
                estilo_mensaje['color'] = 'var(--semantic-negative)'
                return dash.no_update, dash.no_update, dash.no_update, "⚠️ Selecciona un técnico del desplegable para eliminar.", estilo_mensaje, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
                
            if del_id in df_eq['ID_Tecnico'].astype(str).values:
                df_eq = df_eq[df_eq['ID_Tecnico'].astype(str) != str(del_id)]
                mensaje = f"💾 Técnico con ID {del_id} eliminado del directorio."
                estilo_mensaje['color'] = 'var(--semantic-positive)'
                c_del = None
            else:
                estilo_mensaje['color'] = 'var(--semantic-negative)'
                mensaje = "⚠️ ID no encontrado."

        # ====================
        # GUARDADO SEGURO MULTI-PESTAÑA
        # ====================
        try:
            with pd.ExcelFile(ARCHIVO_EXCEL, engine='openpyxl') as xls:
                df_bbdd = pd.read_excel(xls, sheet_name='bbdd') if 'bbdd' in xls.sheet_names else pd.DataFrame()
                df_cron = pd.read_excel(xls, sheet_name='cronograma') if 'cronograma' in xls.sheet_names else pd.DataFrame()
                df_vac = pd.read_excel(xls, sheet_name='vacaciones') if 'vacaciones' in xls.sheet_names else pd.DataFrame()

            with pd.ExcelWriter(ARCHIVO_EXCEL, engine='openpyxl', mode='w') as writer:
                if not df_bbdd.empty: df_bbdd.to_excel(writer, sheet_name='bbdd', index=False)
                df_cron.to_excel(writer, sheet_name='cronograma', index=False)
                df_eq.to_excel(writer, sheet_name='equipo', index=False) # Escribe los datos con la col 'Responsable'
                df_vac.to_excel(writer, sheet_name='vacaciones', index=False)
                
        except PermissionError:
            mensaje = "⚠️ ERROR: El archivo Excel está abierto. Ciérralo y vuelve a intentarlo."
            estilo_mensaje['color'] = 'var(--semantic-negative)'
            _, df_eq, _ = leer_excel()

        # Re-renderizado reactivo de la UI
        html_tarjetas_actualizadas = generar_tarjetas_equipo(df_eq)
        nuevas_opciones_borrado = generar_opciones_borrado(df_eq)
        nuevas_opciones_responsables = obtener_opciones_responsables(df_eq)

        return (html_tarjetas_actualizadas, nuevas_opciones_borrado, nuevas_opciones_responsables, 
                mensaje, estilo_mensaje, c_id, c_nom, c_perf, c_hor, c_del)