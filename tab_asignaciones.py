from dash import html, dcc, Input, Output, State, ctx, ALL
import dash
import pandas as pd
from utils.data_manager import obtener_datos_eficiente, guardar_sqlite_centralizado, parsear_fecha_es
from utils.icons import icono
from datetime import datetime

# Textos exactos confirmados
COL_CODIGO = 'Código de Licitación'
COL_NOMBRE = 'Nombre de la Licitación'

# ==========================================================
# ESTILOS DE APOYO (estilo Salesforce / Lightning, look Serveo)
# ==========================================================

ESTILO_TARJETA = {
    'backgroundColor': '#FFFFFF',
    'border': '1px solid #e5e5e5',
    'borderRadius': 'var(--radius-container)',
    'boxShadow': '0 1px 2px rgba(71, 71, 81, 0.05)',
    'overflow': 'hidden'
}

ESTILO_BADGE_ETAPA = {
    'Pendiente Asignar': {'color': '#a86100', 'backgroundColor': '#fdf0dd'},
    'En estudio': {'color': '#9a3412', 'backgroundColor': '#ffe1d0'},
    'Estudio previo': {'color': '#4b327f', 'backgroundColor': '#ece4fb'},
}

ETAPAS = ['Pendiente Asignar', 'En estudio', 'Estudio previo']


def formatear_presupuesto(valor):
    """Convierte un número a texto con separador de miles español (1.234.567)."""
    if valor is None or valor == "" or pd.isna(valor):
        return ""
    try:
        num = float(str(valor).replace('.', '').replace(',', '.')) if isinstance(valor, str) else float(valor)
    except (ValueError, TypeError):
        return ""
    if num == 0:
        return ""
    return f"{num:,.0f}".replace(",", ".")


def limpiar_presupuesto(texto):
    """Convierte el texto con separador de miles ('1.234.567') de vuelta a float."""
    if texto is None or str(texto).strip() == "":
        return None
    limpio = str(texto).strip().replace('.', '').replace('€', '').replace(' ', '')
    limpio = limpio.replace(',', '.')
    try:
        return float(limpio)
    except (ValueError, TypeError):
        return None


def limpiar_numero_decimal(texto):
    """Convierte un texto con coma o punto decimal (sin separador de miles) a float. Para horas."""
    if texto is None or str(texto).strip() == "":
        return None
    limpio = str(texto).strip().replace(',', '.')
    try:
        return float(limpio)
    except (ValueError, TypeError):
        return None


def badge_etapa(etapa):
    estilo = ESTILO_BADGE_ETAPA.get(etapa, {'color': '#5c5c5c', 'backgroundColor': '#f3f3f3'})
    return html.Span(etapa or 'Sin etapa', style={
        **estilo, 'fontSize': '10px', 'fontWeight': '800', 'borderRadius': '4px',
        'padding': '2px 8px', 'textTransform': 'uppercase', 'letterSpacing': '0.02em',
        'flex': 'none', 'whiteSpace': 'nowrap'
    })


def fila_licitacion(row, codigo_seleccionado):
    cod = str(row.get(COL_CODIGO, ''))
    nombre = str(row.get(COL_NOMBRE, 'Sin nombre'))
    cliente = str(row.get('Cliente', '')) or '—'
    etapa = str(row.get('Etapa', '')) or 'Pendiente Asignar'
    fin = str(row.get('Fecha de Fin', '')) or 'TBD'
    activo = cod == codigo_seleccionado

    return html.Div([
        html.Div([
            html.Span(cod, style={'fontSize': '12px', 'fontWeight': '700', 'color': 'var(--accent)'}),
            badge_etapa(etapa)
        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'gap': '8px'}),
        html.Div(nombre, style={
            'fontSize': '13px', 'fontWeight': '600', 'color': 'var(--text-border)', 'marginTop': '4px',
            'lineHeight': '1.35', 'display': '-webkit-box', 'WebkitLineClamp': '2',
            'WebkitBoxOrient': 'vertical', 'overflow': 'hidden'
        }),
        html.Div([
            html.Span(cliente, style={
                'fontSize': '12px', 'color': 'var(--gray-66)', 'whiteSpace': 'nowrap',
                'overflow': 'hidden', 'textOverflow': 'ellipsis'
            }),
            html.Span(f"Fin {fin}", style={'fontSize': '11px', 'color': 'var(--gray-b3)', 'whiteSpace': 'nowrap'})
        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'gap': '8px', 'marginTop': '4px'})
    ],
        id={'type': 'fila-licitacion', 'index': cod},
        n_clicks=0,
        style={
            'padding': '12px 16px',
            'borderBottom': '1px solid #f4f4f4',
            'cursor': 'pointer',
            'backgroundColor': 'rgba(255, 78, 0, 0.06)' if activo else '#FFFFFF',
            'borderLeft': '3px solid var(--accent)' if activo else '3px solid transparent'
        }
    )


def campo(label, componente, color_label=None, flex='1'):
    estilo_label = {'color': color_label} if color_label else {}
    return html.Div([
        html.Label(label, className="etiqueta-dato", style=estilo_label),
        componente
    ], className="serveo-input-wrapper", style={'flex': flex})


def layout(rol='lector', codigo_seleccionado=None):
    df_bbdd, df_cron, df_eq, df_vac, error_sistema = obtener_datos_eficiente(force_reload=False)

    # --- Alias de equipo (igual que antes) ---
    opciones_equipo, opciones_bam = [], []
    if not df_eq.empty:
        col_id = 'ID_Tecnico' if 'ID_Tecnico' in df_eq.columns else ('ID_Técnico' if 'ID_Técnico' in df_eq.columns else 'Nombre')
        col_nom = 'Nombre' if 'Nombre' in df_eq.columns else df_eq.columns[0]
        df_eq[col_nom] = df_eq[col_nom].astype(str).str.strip()
        df_eq[col_id] = df_eq[col_id].astype(str).str.strip()

        for _, row in df_eq.iterrows():
            nombre_real = row[col_nom]
            alias_visual = row[col_id]
            if pd.isna(nombre_real) or nombre_real == 'nan':
                continue
            if pd.isna(alias_visual) or alias_visual == 'nan' or not alias_visual:
                alias_visual = nombre_real

            opcion = {'label': alias_visual, 'value': nombre_real}
            perfil = str(row.get('Perfil Técnico', '')).strip()
            if perfil == 'Bidding Area Manager':
                opciones_bam.append(opcion)
            elif perfil == 'Bidding Technician':
                opciones_equipo.append(opcion)
            else:
                opciones_equipo.append(opcion)
                opciones_bam.append(opcion)

    opciones_etapa_drop = [{'label': i, 'value': i} for i in ETAPAS]

    # --- Licitaciones activas (cronograma) para la lista lateral ---
    if not df_cron.empty and COL_CODIGO in df_cron.columns:
        df_lista = df_cron.copy()
        for c in [COL_CODIGO, COL_NOMBRE, 'Cliente', 'Etapa', 'Fecha de Fin']:
            if c not in df_lista.columns:
                df_lista[c] = ""
        df_lista['Fecha de Fin'] = pd.to_datetime(df_lista['Fecha de Fin'].apply(parsear_fecha_es), errors='coerce').dt.strftime('%d/%m/%Y').fillna("TBD")
        registros_lista = df_lista.to_dict('records')
    else:
        registros_lista = []

    if codigo_seleccionado is None and registros_lista:
        codigo_seleccionado = str(registros_lista[0].get(COL_CODIGO, ''))

    # --- Datos de la licitación seleccionada para precargar el panel de detalle ---
    draft = {}
    if codigo_seleccionado and not df_cron.empty:
        fila = df_cron[df_cron[COL_CODIGO].astype(str) == str(codigo_seleccionado)]
        if not fila.empty:
            draft = fila.iloc[0].to_dict()

    fc_limpia = parsear_fecha_es(draft.get('Fecha de Creación')) if draft else None
    ff_limpia = parsear_fecha_es(draft.get('Fecha de Fin')) if draft else None

    es_editor = rol == 'editor'

    # ==========================================================
    # HEADER DE PÁGINA
    # ==========================================================
    header = html.Div([
        html.Div([
            html.Div([
                html.Img(src=icono('licitacion'), style={
                    'width': '42px', 'height': '42px', 'borderRadius': '8px', 'background': 'var(--accent)',
                    'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'padding': '11px',
                    'boxSizing': 'border-box', 'flex': 'none'
                }),
                html.Div([
                    html.Div("Asignación de licitaciones", style={'fontSize': '12px', 'color': 'var(--gray-66)', 'fontWeight': '600'}),
                    html.Div("Activación y parámetros", style={'fontSize': '20px', 'fontWeight': '700', 'color': 'var(--text-border)', 'lineHeight': '1.2'})
                ])
            ], style={'display': 'flex', 'alignItems': 'center', 'gap': '13px'}),

            html.Button(
                ['＋ Nueva licitación'], id='btn-modo-nueva', n_clicks=0,
                className="btn-serveo-primario", style={'display': 'block' if es_editor else 'none'}
            )
        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'padding': '14px 18px'})
    ], style=ESTILO_TARJETA)

    # ==========================================================
    # COLUMNA IZQUIERDA — LISTA DE LICITACIONES
    # ==========================================================
    lista_panel = html.Div([
        html.Div([
            html.Div("Licitaciones", style={'fontSize': '14px', 'fontWeight': '700', 'color': 'var(--text-border)'}),
            html.Span(f"{len(registros_lista)}", style={
                'fontSize': '11px', 'fontWeight': '700', 'color': 'var(--gray-66)',
                'backgroundColor': 'var(--card-divider)', 'borderRadius': '10px', 'padding': '2px 9px'
            })
        ], style={'padding': '12px 16px', 'borderBottom': '1px solid #f0f0f0', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}),

        html.Div([
            dcc.Input(
                id='lista-asig-buscar', type='text', placeholder='Buscar licitación…',
                className="input-filtro", style={'width': '100%'}
            ),
            dcc.Dropdown(
                id='lista-asig-filtro-etapa', options=opciones_etapa_drop,
                placeholder='Etapa', multi=True,
                style={'marginTop': '8px'}
            )
        ], style={'padding': '10px 16px', 'borderBottom': '1px solid #f0f0f0'}, className="serveo-input-wrapper"),

        html.Div(
            id='lista-asig-contenedor',
            children=[fila_licitacion(r, codigo_seleccionado) for r in registros_lista],
            style={'maxHeight': '640px', 'overflowY': 'auto'}
        )
    ], style={**ESTILO_TARJETA, 'width': '360px', 'flex': 'none'})

    # ==========================================================
    # COLUMNA DERECHA — PANEL DE DETALLE / FORMULARIO
    # ==========================================================
    cabecera_detalle = html.Div([
        html.Div([
            html.Div([
                html.Span(f"LICITACIÓN · {codigo_seleccionado or 'Nueva'}", style={
                    'fontSize': '11px', 'fontWeight': '700', 'color': 'var(--gray-66)', 'letterSpacing': '0.03em'
                }),
            ]),
            html.Div(
                str(draft.get(COL_NOMBRE, '')) or 'Selecciona o crea una licitación',
                id='detalle-asig-titulo',
                style={'fontSize': '18px', 'fontWeight': '700', 'color': 'var(--text-border)', 'marginTop': '4px'}
            ),
            html.Div(
                str(draft.get('Cliente', '')) or '',
                id='detalle-asig-cliente',
                style={'fontSize': '13px', 'color': 'var(--gray-66)', 'marginTop': '3px'}
            )
        ])
    ], style={'padding': '16px 20px', 'borderBottom': '1px solid #f0f0f0'})

    cuerpo_detalle = html.Div([
        # --- Selector de licitación (alta nueva o edición directa por código) ---
        html.Div([
            campo("Cargar licitación activa (editar)", dcc.Dropdown(
                id='drop-editar-lic',
                options=[{'label': f"{r[COL_CODIGO]} - {r.get(COL_NOMBRE, '')}", 'value': str(r[COL_CODIGO])} for r in registros_lista],
                value=codigo_seleccionado, placeholder="Selecciona licitación activa…", clearable=True
            ), flex='2'),
            campo("Buscar en BBDD (alta nueva)", html.Div([
                dcc.Input(id='input-act-lic', type='text', placeholder="Código/nombre nuevo…", list='sugerencias-licitaciones', className="input-filtro", style={'width': '100%'}),
                html.Datalist(id='sugerencias-licitaciones', children=[])
            ]), flex='2'),
        ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '16px'}),

        html.Div("Detalles de la licitación", style={
            'fontSize': '13px', 'fontWeight': '700', 'color': 'var(--text-border)',
            'paddingBottom': '9px', 'borderBottom': '1px solid #f0f0f0', 'marginBottom': '14px'
        }),

        html.Div([
            campo("Etapa (obligatorio)", dcc.Dropdown(id='drop-act-etapa', options=opciones_etapa_drop, value=draft.get('Etapa'), placeholder="Selecciona etapa…"), color_label='var(--accent)'),
            campo("Manager (BAM)", dcc.Dropdown(id='drop-act-bam', options=opciones_bam, value=draft.get('BAM') or None, clearable=True)),
        ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '14px'}),

        html.Div([
            campo("Técnico 1", dcc.Dropdown(id='drop-act-t1', options=opciones_equipo, value=draft.get('Técnico 1') or None, clearable=True)),
            campo("Técnico 2", dcc.Dropdown(id='drop-act-t2', options=opciones_equipo, value=draft.get('Técnico 2') or None, clearable=True)),
            campo("Técnico 3", dcc.Dropdown(id='drop-act-t3', options=opciones_equipo, value=draft.get('Técnico 3') or None, clearable=True)),
        ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '14px'}),

        html.Div([
            campo("Fecha de creación", dcc.DatePickerSingle(id='date-act-fcreacion', display_format='YYYY-MM-DD', placeholder='Selecciona…', date=fc_limpia.strftime('%Y-%m-%d') if fc_limpia is not None and pd.notna(fc_limpia) else None, style={'width': '100%'})),
            campo("Fecha de fin (vencimiento)", dcc.DatePickerSingle(id='date-act-ffin', display_format='YYYY-MM-DD', placeholder='Selecciona…', date=ff_limpia.strftime('%Y-%m-%d') if ff_limpia is not None and pd.notna(ff_limpia) else None, style={'width': '100%'})),
            campo("Horas estimadas (técnicos)", dcc.Input(id='input-act-horas', type='text', inputMode='numeric', placeholder='Horas…', value=draft.get('Horas de Licitación'), className="input-filtro")),
            campo("Horas estimadas (BAM)", dcc.Input(id='input-act-horas-bam', type='text', inputMode='numeric', placeholder='Horas…', value=draft.get('Horas de Licitación BAM'), className="input-filtro"), color_label='var(--accent)'),
        ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '14px'}),

        html.Div([
            campo("Presupuesto (€)", dcc.Input(id='input-act-presupuesto', type='text', inputMode='numeric', placeholder='Importe en euros…', value=formatear_presupuesto(draft.get('Presupuesto')), className="input-filtro"), flex='1'),
            html.Div(style={'flex': '3'}),
        ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '14px'}),

        html.Div([
            campo("Personas involucradas (externos/otros)", dcc.Input(id='input-involucrados', type='text', placeholder='Nombres separados por comas…', value=draft.get('Personas involucradas'), className="input-filtro", style={'width': '100%'})),
            campo("Comentario / notas (opcional)", dcc.Input(id='input-act-comentario', type='text', placeholder='Añade un comentario…', value=draft.get('Comentario'), className="input-filtro", style={'width': '100%'})),
        ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '20px'}),

        html.Div([
            html.Button('💾 Guardar / Activar', id='btn-activar', n_clicks=0, className="btn-serveo-primario", style={'display': 'inline-block' if es_editor else 'none'}),
            html.Button('🗑️ Eliminar esta licitación', id='btn-eliminar', n_clicks=0, className="btn-serveo-negativo", style={'display': 'inline-block' if es_editor else 'none', 'marginLeft': '12px'}),
        ], style={'marginBottom': '20px'}),

        html.Div(error_sistema, id='msj-interaccion', style={'fontWeight': 'bold', 'fontFamily': 'var(--font-family)', 'fontSize': '13px', 'color': 'var(--semantic-negative)', 'marginBottom': '14px'}),

        html.Div([
            html.Label("Informe generado (copiar para email)", className="etiqueta-dato", style={'color': 'var(--accent)'}),
            dcc.Textarea(id='area-informe', readOnly=True, style={
                'width': '100%', 'height': '160px', 'fontFamily': 'var(--font-family)', 'fontSize': '12px',
                'padding': '12px', 'borderRadius': '6px', 'border': '1px solid var(--card-divider)',
                'backgroundColor': '#FAFAFA', 'color': 'var(--text-border)'
            })
        ])
    ], style={'padding': '18px 20px'})

    detalle_panel = html.Div([cabecera_detalle, cuerpo_detalle], style={**ESTILO_TARJETA, 'flex': '1', 'minWidth': '0'})

    return html.Div([
        dcc.Store(id='asig-codigo-seleccionado', data=codigo_seleccionado),
        html.H3("Activación y Asignación de Licitaciones", className="serveo-titulo-pagina", style={'display': 'none'}),
        header,
        html.Div([lista_panel, detalle_panel], style={'display': 'flex', 'gap': '16px', 'alignItems': 'flex-start', 'marginTop': '16px'})
    ], style={'paddingBottom': '40px'})


def register_callbacks(app):

    # ----------------------------------------------------------------
    # 1b. Botón "Nueva licitación" del header: limpia el formulario
    #     y deja la app lista para una alta desde cero
    # ----------------------------------------------------------------
    @app.callback(
        [Output('asig-codigo-seleccionado', 'data', allow_duplicate=True),
         Output('drop-editar-lic', 'value', allow_duplicate=True),
         Output('input-act-lic', 'value', allow_duplicate=True),
         Output('drop-act-etapa', 'value', allow_duplicate=True),
         Output('drop-act-bam', 'value', allow_duplicate=True),
         Output('drop-act-t1', 'value', allow_duplicate=True),
         Output('drop-act-t2', 'value', allow_duplicate=True),
         Output('drop-act-t3', 'value', allow_duplicate=True),
         Output('date-act-fcreacion', 'date', allow_duplicate=True),
         Output('date-act-ffin', 'date', allow_duplicate=True),
         Output('input-act-horas', 'value', allow_duplicate=True),
         Output('input-act-horas-bam', 'value', allow_duplicate=True),
         Output('input-act-presupuesto', 'value', allow_duplicate=True),
         Output('input-involucrados', 'value', allow_duplicate=True),
         Output('input-act-comentario', 'value', allow_duplicate=True),
         Output('area-informe', 'value', allow_duplicate=True),
         Output('msj-interaccion', 'children', allow_duplicate=True)],
        Input('btn-modo-nueva', 'n_clicks'),
        prevent_initial_call=True
    )
    def iniciar_modo_alta(n_clicks):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        return None, None, "", None, None, None, None, None, None, None, "", "", "", "", "", "", ""

    # ----------------------------------------------------------------
    # 2. Selección de licitación en la lista lateral (clic en una fila)
    # ----------------------------------------------------------------
    @app.callback(
        Output('asig-codigo-seleccionado', 'data', allow_duplicate=True),
        Input({'type': 'fila-licitacion', 'index': ALL}, 'n_clicks'),
        State({'type': 'fila-licitacion', 'index': ALL}, 'id'),
        prevent_initial_call=True
    )
    def seleccionar_licitacion(n_clicks_list, ids_list):
        trigger = ctx.triggered_id
        if not trigger or not isinstance(trigger, dict):
            raise dash.exceptions.PreventUpdate
        # Evita disparos en el primer render (todos los n_clicks en 0)
        if not any(n_clicks_list):
            raise dash.exceptions.PreventUpdate
        return trigger.get('index')

# ----------------------------------------------------------------
    # 2. Refrescar la lista lateral (buscador + filtro de etapa)
    #    y refrescar el panel de detalle cuando cambia la selección
    # ----------------------------------------------------------------
    @app.callback(
        [Output('lista-asig-contenedor', 'children'),
         Output('detalle-asig-titulo', 'children', allow_duplicate=True),
         Output('detalle-asig-cliente', 'children', allow_duplicate=True),
         Output('drop-editar-lic', 'value', allow_duplicate=True),
         Output('drop-act-etapa', 'value', allow_duplicate=True),
         Output('drop-act-bam', 'value', allow_duplicate=True),
         Output('drop-act-t1', 'value', allow_duplicate=True),
         Output('drop-act-t2', 'value', allow_duplicate=True),
         Output('drop-act-t3', 'value', allow_duplicate=True),
         Output('date-act-fcreacion', 'date', allow_duplicate=True),
         Output('date-act-ffin', 'date', allow_duplicate=True),
         Output('input-act-horas', 'value', allow_duplicate=True),
         Output('input-act-horas-bam', 'value', allow_duplicate=True),
         Output('input-act-presupuesto', 'value', allow_duplicate=True),
         Output('input-involucrados', 'value', allow_duplicate=True),
         Output('input-act-comentario', 'value', allow_duplicate=True),
         Output('area-informe', 'value', allow_duplicate=True), # <-- Agregado como salida
         Output('msj-interaccion', 'children', allow_duplicate=True)],
        [Input('asig-codigo-seleccionado', 'data'),
         Input('lista-asig-buscar', 'value'),
         Input('lista-asig-filtro-etapa', 'value')],
        prevent_initial_call=True
    )
    def refrescar_lista_y_detalle(codigo_sel, texto_buscar, etapas_filtro):
        df_bbdd, df_cron, _, _, _ = obtener_datos_eficiente(force_reload=False)

        # --- Reconstruir lista filtrada ---
        if not df_cron.empty and COL_CODIGO in df_cron.columns:
            df_lista = df_cron.copy()
            for c in [COL_CODIGO, COL_NOMBRE, 'Cliente', 'Etapa', 'Fecha de Fin']:
                if c not in df_lista.columns:
                    df_lista[c] = ""

            if texto_buscar:
                mask = (df_lista[COL_CODIGO].astype(str).str.contains(texto_buscar, case=False, na=False)) | \
                       (df_lista[COL_NOMBRE].astype(str).str.contains(texto_buscar, case=False, na=False))
                df_lista = df_lista[mask]

            if etapas_filtro:
                if isinstance(etapas_filtro, str):
                    etapas_filtro = [etapas_filtro]
                df_lista = df_lista[df_lista['Etapa'].isin(etapas_filtro)]

            df_lista['Fecha de Fin'] = pd.to_datetime(df_lista['Fecha de Fin'].apply(parsear_fecha_es), errors='coerce').dt.strftime('%d/%m/%Y').fillna("TBD")
            registros_lista = df_lista.to_dict('records')
        else:
            registros_lista = []

        filas = [fila_licitacion(r, codigo_sel) for r in registros_lista]

        # --- Recargar el panel de detalle según la licitación seleccionada ---
        # ret_vacio incluye un string vacío extra para el 'area-informe' y otro para limpiar 'msj-interaccion'
        ret_vacio = ("Selecciona o crea una licitación", "", None, None, None, None, None, None, None, None, "", "", "", "", "", "", "")
        if not codigo_sel or df_cron.empty:
            return (filas, *ret_vacio)

        fila = df_cron[df_cron[COL_CODIGO].astype(str) == str(codigo_sel)]
        if fila.empty:
            return (filas, *ret_vacio)

        r = fila.iloc[0]
        fc_limpia = parsear_fecha_es(r.get('Fecha de Creación'))
        ff_limpia = parsear_fecha_es(r.get('Fecha de Fin'))

        # --- Limpieza de variables para construir el reporte pre-cargado ---
        t1_val = str(r.get('Técnico 1', '')).strip() if pd.notna(r.get('Técnico 1')) else ""
        t2_val = str(r.get('Técnico 2', '')).strip() if pd.notna(r.get('Técnico 2')) else ""
        t3_val = str(r.get('Técnico 3', '')).strip() if pd.notna(r.get('Técnico 3')) else ""
        bam_clean = str(r.get('BAM', '')).strip() if pd.notna(r.get('BAM')) else ""
        comentario_val = str(r.get('Comentario', '')).strip() if pd.notna(r.get('Comentario')) else ""
        invol_clean = str(r.get('Personas involucradas', '')).strip() if pd.notna(r.get('Personas involucradas')) else ""
        
        fcreacion_str = fc_limpia.strftime('%Y-%m-%d') if pd.notna(fc_limpia) else 'TBD'
        ffin_str = ff_limpia.strftime('%Y-%m-%d') if pd.notna(ff_limpia) else 'TBD'
        
        horas_tec = r.get('Horas de Licitación', 0)
        horas_bam = r.get('Horas de Licitación BAM', 0)
        if pd.isna(horas_tec) or horas_tec == "": horas_tec = 0
        if pd.isna(horas_bam) or horas_bam == "": horas_bam = 0

        presupuesto_val = r.get('Presupuesto', 0)
        if pd.isna(presupuesto_val) or presupuesto_val == "": presupuesto_val = 0

        # --- Generación automática del informe de lectura ---
        informe_generado = (
            f"📌 ACTUALIZACIÓN DE ASIGNACIÓN (SERVEO)\n"
            f"--------------------------------------------------\n"
            f"Código: {codigo_sel}\n"
            f"Nombre: {str(r.get(COL_NOMBRE, 'Sin nombre'))}\n"
            f"Cliente: {str(r.get('Cliente', ''))}\n\n"
            f"📋 ESTATUS OPERATIVO:\n"
            f"Etapa Actual: {r.get('Etapa', 'Pendiente Asignar')}\n"
            f"BAM Responsable: {bam_clean if bam_clean else 'Pendiente'}\n"
            f"Técnicos: {', '.join([t for t in [t1_val, t2_val, t3_val] if t]) or 'Pendiente'}\n"
            f"Apoyo/Involucrados: {invol_clean if invol_clean else 'Ninguno'}\n\n"
            f"⏳ PLANIFICACIÓN TÉCNICA:\n"
            f"Fechas: {fcreacion_str} al {ffin_str}\n"
            f"Horas Estimadas: {horas_tec}h (Técnicos) / {horas_bam}h (BAM)\n"
            f"Presupuesto: {presupuesto_val:,.0f} €\n\n"
            f"💬 NOTAS ADICIONALES:\n"
            f"{comentario_val if comentario_val else 'Ninguna'}\n"
            f"--------------------------------------------------"
        )

        return (
            filas,
            str(r.get(COL_NOMBRE, 'Sin nombre')),
            str(r.get('Cliente', '')),
            codigo_sel,
            r.get('Etapa') or None,
            r.get('BAM') or None,
            r.get('Técnico 1') or None,
            r.get('Técnico 2') or None,
            r.get('Técnico 3') or None,
            fc_limpia.strftime('%Y-%m-%d') if pd.notna(fc_limpia) else None,
            ff_limpia.strftime('%Y-%m-%d') if pd.notna(ff_limpia) else None,
            r.get('Horas de Licitación', ''),
            r.get('Horas de Licitación BAM', ''),
            formatear_presupuesto(r.get('Presupuesto', '')),
            r.get('Personas involucradas', ''),
            r.get('Comentario', ''),
            informe_generado, # <-- Retornado al final de la tupla
            "" # Limpia cualquier mensaje de error de una licitación anterior
        )

    # ----------------------------------------------------------------
    # 3. Autocompletado de BBDD para alta de nueva licitación
    # ----------------------------------------------------------------
    @app.callback(
        Output('sugerencias-licitaciones', 'children'),
        Input('input-act-lic', 'value'),
        prevent_initial_call=True
    )
    def buscar_en_bbdd(search_value):
        df_bbdd, df_cron, _, _, _ = obtener_datos_eficiente(force_reload=False)
        if df_bbdd.empty or COL_CODIGO not in df_bbdd.columns:
            return []

        codigos_activos = df_cron[COL_CODIGO].dropna().tolist() if not df_cron.empty else []
        df_disp = df_bbdd[~df_bbdd[COL_CODIGO].isin(codigos_activos)]

        if search_value:
            mask = (df_disp[COL_CODIGO].astype(str).str.contains(search_value, case=False, na=False, regex=False)) | \
                   (df_disp[COL_NOMBRE].astype(str).str.contains(search_value, case=False, na=False, regex=False))
            df_disp = df_disp[mask]

        return [html.Option(value=f"{row[COL_CODIGO]} - {row.get(COL_NOMBRE, '')}") for _, row in df_disp.head(40).iterrows()]

    # ----------------------------------------------------------------
    # 4. Al elegir/escribir una licitación nueva en el buscador BBDD,
    #    precarga sus datos base en el formulario (modo alta).
    #    No toca 'asig-codigo-seleccionado' para no disparar el refresco
    #    de la lista, que pisaría estos valores recién cargados.
    # ----------------------------------------------------------------
    @app.callback(
        [Output('drop-act-etapa', 'value', allow_duplicate=True),
         Output('date-act-fcreacion', 'date', allow_duplicate=True),
         Output('date-act-ffin', 'date', allow_duplicate=True),
         Output('input-act-horas', 'value', allow_duplicate=True),
         Output('input-act-horas-bam', 'value', allow_duplicate=True),
         Output('input-act-presupuesto', 'value', allow_duplicate=True),
         Output('drop-act-bam', 'value', allow_duplicate=True),
         Output('drop-act-t1', 'value', allow_duplicate=True),
         Output('drop-act-t2', 'value', allow_duplicate=True),
         Output('drop-act-t3', 'value', allow_duplicate=True),
         Output('input-involucrados', 'value', allow_duplicate=True),
         Output('input-act-comentario', 'value', allow_duplicate=True),
         Output('detalle-asig-titulo', 'children', allow_duplicate=True),
         Output('detalle-asig-cliente', 'children', allow_duplicate=True),
         Output('drop-editar-lic', 'value', allow_duplicate=True)],
        Input('input-act-lic', 'value'),
        prevent_initial_call=True
    )
    def poblar_formulario_alta(val_nuevo):
        if not val_nuevo or " - " not in val_nuevo:
            raise dash.exceptions.PreventUpdate

        df_bbdd, _, _, _, _ = obtener_datos_eficiente(force_reload=False)
        cod_lic = val_nuevo.split(" - ")[0].strip()
        fila = df_bbdd[df_bbdd[COL_CODIGO] == cod_lic]
        if fila.empty:
            raise dash.exceptions.PreventUpdate

        r = fila.iloc[0]
        fc_limpia = parsear_fecha_es(r.get('Fecha de Creación'))
        ff_limpia = parsear_fecha_es(r.get('Fecha de Fin'))

        return (
            None,
            fc_limpia.strftime('%Y-%m-%d') if pd.notna(fc_limpia) else None,
            ff_limpia.strftime('%Y-%m-%d') if pd.notna(ff_limpia) else None,
            r.get('Horas de Licitación', ''),
            r.get('Horas de Licitación BAM', ''),
            formatear_presupuesto(r.get('Presupuesto', '')),
            "", "", "", "", "", "",
            str(r.get(COL_NOMBRE, 'Sin nombre')),
            str(r.get('Cliente', '')),
            None  # drop-editar-lic: deja de apuntar a una licitación activa, estamos en modo alta
        )

    # ----------------------------------------------------------------
    # 5. Guardar / Activar / Eliminar la licitación del panel de detalle
    # ----------------------------------------------------------------
    @app.callback(
        [Output('msj-interaccion', 'children'),
         Output('msj-interaccion', 'style'),
         Output('area-informe', 'value', allow_duplicate=True),
         Output('asig-codigo-seleccionado', 'data', allow_duplicate=True),
         Output('input-act-lic', 'value', allow_duplicate=True)],
        [Input('btn-activar', 'n_clicks'),
         Input('btn-eliminar', 'n_clicks')],
        [State('input-act-lic', 'value'),
         State('drop-editar-lic', 'value'),
         State('drop-act-etapa', 'value'),
         State('drop-act-bam', 'value'),
         State('drop-act-t1', 'value'),
         State('drop-act-t2', 'value'),
         State('drop-act-t3', 'value'),
         State('input-involucrados', 'value'),
         State('date-act-fcreacion', 'date'),
         State('date-act-ffin', 'date'),
         State('input-act-horas', 'value'),
         State('input-act-horas-bam', 'value'),
         State('input-act-presupuesto', 'value'),
         State('input-act-comentario', 'value'),
         State('asig-codigo-seleccionado', 'data')],
        prevent_initial_call=True
    )
    def gestor_maestro_funnel(n_activar, n_eliminar, cod_lic_input, edit_lic_input, etapa, bam_val, t1, t2, t3,
                               involucrados_val, high_fcreacion, high_ffin, high_horas, high_horas_bam,
                               high_presupuesto, comentario_input, codigo_actual):
        trigger = ctx.triggered_id
        if not trigger:
            raise dash.exceptions.PreventUpdate

        df_bbdd, df_cron, df_eq, df_vac, error_sistema = obtener_datos_eficiente(force_reload=False)
        estilo_msg = {'fontWeight': 'bold', 'fontFamily': 'var(--font-family)', 'fontSize': '13px', 'marginBottom': '14px'}

        if error_sistema:
            estilo_msg['color'] = 'var(--semantic-negative)'
            return error_sistema, estilo_msg, dash.no_update, dash.no_update, dash.no_update

        cols_necesarias = [COL_CODIGO, COL_NOMBRE, 'Cliente', 'Fecha de Creación', 'Fecha de Fin',
                            'Horas de Licitación', 'Horas de Licitación BAM', 'Presupuesto', 'BAM', 'Técnico 1', 'Técnico 2',
                            'Técnico 3', 'Personas involucradas', 'Etapa', 'Comentario']
        for col in cols_necesarias:
            if col not in df_cron.columns:
                df_cron[col] = ""

        def depurar_celda(valor):
            if pd.isna(valor) or valor is None or str(valor).strip() == "" or str(valor).strip().lower() == "none":
                return ""
            return str(valor).strip()

        # ============== GUARDAR / ACTIVAR ==============
        if trigger == 'btn-activar':
            if not cod_lic_input and not edit_lic_input:
                estilo_msg['color'] = 'var(--semantic-negative)'
                return "⚠️ Selecciona una licitación (Nueva o Activa).", estilo_msg, dash.no_update, dash.no_update, dash.no_update

            if not etapa:
                estilo_msg['color'] = 'var(--semantic-negative)'
                return "⚠️ La etapa es un campo obligatorio.", estilo_msg, dash.no_update, dash.no_update, dash.no_update

            cod_lic = str(edit_lic_input).strip() if edit_lic_input else str(cod_lic_input).split(" - ")[0].strip()

            t1_val, t2_val, t3_val, bam_clean = depurar_celda(t1), depurar_celda(t2), depurar_celda(t3), depurar_celda(bam_val)
            comentario_val = depurar_celda(comentario_input)
            invol_clean = depurar_celda(involucrados_val)
            hay_tecnicos = bool(t1_val or t2_val or t3_val)

            if etapa != 'Pendiente Asignar' and not hay_tecnicos and not bam_clean:
                estilo_msg['color'] = 'var(--semantic-negative)'
                return f"⚠️ La etapa '{etapa}' exige asignar al menos un BAM o un Técnico.", estilo_msg, dash.no_update, dash.no_update, dash.no_update

            # --- VALIDACIÓN DE TIPOS DE DATOS ANTES DE GUARDAR ---
            horas_tec_num = limpiar_numero_decimal(high_horas)
            if high_horas and str(high_horas).strip() != "" and horas_tec_num is None:
                estilo_msg['color'] = 'var(--semantic-negative)'
                return f"⚠️ 'Horas estimadas (técnicos)' debe ser un número (escribiste: \"{high_horas}\").", estilo_msg, dash.no_update, dash.no_update, dash.no_update
            if horas_tec_num is not None and horas_tec_num < 0:
                estilo_msg['color'] = 'var(--semantic-negative)'
                return "⚠️ 'Horas estimadas (técnicos)' no puede ser un número negativo.", estilo_msg, dash.no_update, dash.no_update, dash.no_update

            horas_bam_num = limpiar_numero_decimal(high_horas_bam)
            if high_horas_bam and str(high_horas_bam).strip() != "" and horas_bam_num is None:
                estilo_msg['color'] = 'var(--semantic-negative)'
                return f"⚠️ 'Horas estimadas (BAM)' debe ser un número (escribiste: \"{high_horas_bam}\").", estilo_msg, dash.no_update, dash.no_update, dash.no_update
            if horas_bam_num is not None and horas_bam_num < 0:
                estilo_msg['color'] = 'var(--semantic-negative)'
                return "⚠️ 'Horas estimadas (BAM)' no puede ser un número negativo.", estilo_msg, dash.no_update, dash.no_update, dash.no_update

            presupuesto_num = limpiar_presupuesto(high_presupuesto)
            if high_presupuesto and str(high_presupuesto).strip() != "" and presupuesto_num is None:
                estilo_msg['color'] = 'var(--semantic-negative)'
                return f"⚠️ 'Presupuesto' debe ser un importe numérico (escribiste: \"{high_presupuesto}\").", estilo_msg, dash.no_update, dash.no_update, dash.no_update
            if presupuesto_num is not None and presupuesto_num < 0:
                estilo_msg['color'] = 'var(--semantic-negative)'
                return "⚠️ 'Presupuesto' no puede ser un importe negativo.", estilo_msg, dash.no_update, dash.no_update, dash.no_update

            fc_valida = parsear_fecha_es(high_fcreacion) if high_fcreacion else None
            if high_fcreacion and pd.isna(fc_valida):
                estilo_msg['color'] = 'var(--semantic-negative)'
                return f"⚠️ 'Fecha de creación' no es una fecha válida (\"{high_fcreacion}\").", estilo_msg, dash.no_update, dash.no_update, dash.no_update

            ff_valida = parsear_fecha_es(high_ffin) if high_ffin else None
            if high_ffin and pd.isna(ff_valida):
                estilo_msg['color'] = 'var(--semantic-negative)'
                return f"⚠️ 'Fecha de fin' no es una fecha válida (\"{high_ffin}\").", estilo_msg, dash.no_update, dash.no_update, dash.no_update

            if fc_valida is not None and ff_valida is not None and not pd.isna(fc_valida) and not pd.isna(ff_valida):
                if ff_valida.date() < fc_valida.date():
                    estilo_msg['color'] = 'var(--semantic-negative)'
                    return "⚠️ 'Fecha de fin' no puede ser anterior a 'Fecha de creación'.", estilo_msg, dash.no_update, dash.no_update, dash.no_update

            if etapa == 'Pendiente Asignar':
                t1_val = t2_val = t3_val = bam_clean = ""

            is_update = cod_lic in df_cron[COL_CODIGO].astype(str).values

            if is_update:
                mask = df_cron[COL_CODIGO].astype(str) == cod_lic
                df_cron.loc[mask, 'Etapa'] = etapa
                df_cron.loc[mask, 'BAM'] = bam_clean
                df_cron.loc[mask, 'Técnico 1'] = t1_val
                df_cron.loc[mask, 'Técnico 2'] = t2_val
                df_cron.loc[mask, 'Técnico 3'] = t3_val
                df_cron.loc[mask, 'Personas involucradas'] = invol_clean
                df_cron.loc[mask, 'Comentario'] = comentario_val
                df_cron.loc[mask, 'Fecha de Creación'] = str(high_fcreacion).strip() if high_fcreacion else ""
                df_cron.loc[mask, 'Fecha de Fin'] = str(high_ffin).strip() if high_ffin else ""
                df_cron.loc[mask, 'Horas de Licitación'] = horas_tec_num if horas_tec_num is not None else ""
                df_cron.loc[mask, 'Horas de Licitación BAM'] = horas_bam_num if horas_bam_num is not None else ""
                df_cron.loc[mask, 'Presupuesto'] = presupuesto_num if presupuesto_num is not None else ""

                nom_proy = str(df_cron.loc[mask, COL_NOMBRE].values[0])
                cliente = str(df_cron.loc[mask, 'Cliente'].values[0]) if 'Cliente' in df_cron.columns else ""
                mensaje = f"💾 ¡Datos de la licitación {cod_lic} actualizados!"
            else:
                fila_virgen = df_bbdd[df_bbdd[COL_CODIGO].astype(str) == cod_lic].copy()
                if fila_virgen.empty:
                    estilo_msg['color'] = 'var(--semantic-negative)'
                    return "⚠️ Error: Ese código no existe en BBDD.", estilo_msg, dash.no_update, dash.no_update, dash.no_update

                nom_proy = str(fila_virgen.iloc[0].get(COL_NOMBRE, 'Sin Nombre'))
                cliente = str(fila_virgen.iloc[0].get('Cliente', 'Sin Cliente'))

                fila_virgen['Etapa'] = etapa
                fila_virgen['BAM'] = bam_clean
                fila_virgen['Técnico 1'], fila_virgen['Técnico 2'], fila_virgen['Técnico 3'] = t1_val, t2_val, t3_val
                fila_virgen['Personas involucradas'] = invol_clean
                fila_virgen['Comentario'] = comentario_val
                if 'Cliente' not in fila_virgen.columns:
                    fila_virgen['Cliente'] = ""
                fila_virgen['Fecha de Creación'] = str(high_fcreacion).strip() if high_fcreacion else ""
                fila_virgen['Fecha de Fin'] = str(high_ffin).strip() if high_ffin else ""
                fila_virgen['Horas de Licitación'] = horas_tec_num if horas_tec_num is not None else ""
                fila_virgen['Horas de Licitación BAM'] = horas_bam_num if horas_bam_num is not None else ""
                fila_virgen['Presupuesto'] = presupuesto_num if presupuesto_num is not None else ""

                df_cron = pd.concat([df_cron, fila_virgen], ignore_index=True)
                mensaje = f"🚀 ¡Licitación {cod_lic} inyectada al Funnel Operativo!"

            informe_generado = (
                f"📌 ACTUALIZACIÓN DE ASIGNACIÓN (SERVEO)\n"
                f"--------------------------------------------------\n"
                f"Código: {cod_lic}\n"
                f"Nombre: {nom_proy}\n"
                f"Cliente: {cliente}\n\n"
                f"📋 ESTATUS OPERATIVO:\n"
                f"Etapa Actual: {etapa}\n"
                f"BAM Responsable: {bam_clean if bam_clean else 'Pendiente'}\n"
                f"Técnicos: {', '.join([t for t in [t1_val, t2_val, t3_val] if t]) or 'Pendiente'}\n"
                f"Apoyo/Involucrados: {invol_clean if invol_clean else 'Ninguno'}\n\n"
                f"⏳ PLANIFICACIÓN TÉCNICA:\n"
                f"Fechas: {high_fcreacion if high_fcreacion else 'TBD'} al {high_ffin if high_ffin else 'TBD'}\n"
                f"Horas Estimadas: {horas_tec_num if horas_tec_num is not None else 0}h (Técnicos) / {horas_bam_num if horas_bam_num is not None else 0}h (BAM)\n"
                f"Presupuesto: {(presupuesto_num or 0):,.0f} €\n\n"
                f"💬 NOTAS ADICIONALES:\n"
                f"{comentario_val if comentario_val else 'Ninguna'}\n"
                f"--------------------------------------------------"
            )

            guardado_exitoso, msg_sistema = guardar_sqlite_centralizado(df_cron_new=df_cron)
            if not guardado_exitoso:
                estilo_msg['color'] = 'var(--semantic-negative)'
                return msg_sistema, estilo_msg, dash.no_update, dash.no_update, dash.no_update

            estilo_msg['color'] = 'var(--semantic-positive)'
            return mensaje, estilo_msg, informe_generado, cod_lic, ""

        # ============== ELIMINAR ==============
        elif trigger == 'btn-eliminar':
            if not codigo_actual:
                estilo_msg['color'] = 'var(--semantic-negative)'
                return "⚠️ No hay ninguna licitación seleccionada para eliminar.", estilo_msg, dash.no_update, dash.no_update, dash.no_update

            cod_lic = str(codigo_actual).strip()
            existe = cod_lic in df_cron[COL_CODIGO].astype(str).values
            if not existe:
                estilo_msg['color'] = 'var(--semantic-negative)'
                return "⚠️ Esta licitación todavía no está activa, no hay nada que eliminar.", estilo_msg, dash.no_update, dash.no_update, dash.no_update

            df_cron = df_cron[df_cron[COL_CODIGO].astype(str) != cod_lic]
            guardado_exitoso, msg_sistema = guardar_sqlite_centralizado(df_cron_new=df_cron)

            if not guardado_exitoso:
                estilo_msg['color'] = 'var(--semantic-negative)'
                return msg_sistema, estilo_msg, dash.no_update, dash.no_update, dash.no_update

            estilo_msg['color'] = 'var(--semantic-negative)'
            return f"🗑️ ¡Licitación {cod_lic} devuelta a BBDD!", estilo_msg, "", None, ""

        raise dash.exceptions.PreventUpdate