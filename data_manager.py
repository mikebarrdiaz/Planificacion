import pandas as pd
import datetime
import numpy as np
import os
import sys
import warnings
import sqlite3

# Detectar si estamos ejecutando desde el .exe compilado o desde Python normal
if getattr(sys, 'frozen', False):
    directorio_base = os.path.dirname(sys.executable)
else:
    directorio_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- ARQUITECTURA SQLITE ---
ARCHIVO_DB = os.path.join(directorio_base, "cronograma_Government.db")

# =====================================================================
# 1. MOTOR DE CACHÉ EN RAM Y LECTURA CENTRALIZADA
# =====================================================================
_DATA_CACHE = {
    'df_bbdd': None,
    'df_cron': None,
    'df_eq': None,
    'df_vac': None,
    'error': ""
}

# --- CACHÉ DE CALENDARIOS (Búsqueda Ultrarrápida O(1)) ---
_CALENDARIOS_CACHE = None

def obtener_datos_eficiente(force_reload=False):
    global _DATA_CACHE
    if force_reload or _DATA_CACHE['df_bbdd'] is None:
        _DATA_CACHE['df_bbdd'], _DATA_CACHE['df_cron'], _DATA_CACHE['df_eq'], _DATA_CACHE['df_vac'], _DATA_CACHE['error'] = leer_archivos_robusto()
    return _DATA_CACHE['df_bbdd'], _DATA_CACHE['df_cron'], _DATA_CACHE['df_eq'], _DATA_CACHE['df_vac'], _DATA_CACHE['error']

def obtener_calendarios(force_reload=False):
    """Extrae los calendarios provinciales y los convierte en diccionarios de alta velocidad."""
    global _CALENDARIOS_CACHE
    if not force_reload and _CALENDARIOS_CACHE is not None:
        return _CALENDARIOS_CACHE

    _CALENDARIOS_CACHE = {}
    try:
        conexion = sqlite3.connect(ARCHIVO_DB)
        tablas_sedes = [
            ('MAD (Quint)', 'calendario_madrid_2026'), 
            ('BCN (T. Auditori)', 'calendario_barcelona_2026'), 
            ('VALENCIA', 'calendario_valencia_2026')
        ]
        for sede, tabla in tablas_sedes:
            try:
                df = pd.read_sql(f"SELECT * FROM {tabla}", conexion)
                if not df.empty and 'fecha' in df.columns:
                    df['fecha'] = df['fecha'].apply(parsear_fecha_es).dt.date
                    # Diccionario {fecha: horas_laborables} para evitar .loc de Pandas
                    _CALENDARIOS_CACHE[sede] = dict(zip(df['fecha'], df['horas_laborables']))
            except sqlite3.OperationalError:
                pass # Si la tabla no existe aún, se usará el fallback genérico
    except Exception:
        pass
    finally:
        if 'conexion' in locals():
            conexion.close()
            
    return _CALENDARIOS_CACHE

def leer_archivos_robusto():
    try:
        conexion = sqlite3.connect(ARCHIVO_DB)
        
        def leer_tabla_segura(nombre_tabla):
            try:
                df = pd.read_sql(f"SELECT * FROM {nombre_tabla}", conexion)
                if not df.empty:
                    df.columns = df.columns.astype(str).str.strip()
                return df
            except sqlite3.OperationalError:
                return pd.DataFrame()

        df_bbdd = leer_tabla_segura('bbdd')
        if not df_bbdd.empty and 'Código de Licitación' in df_bbdd.columns:
            df_bbdd['Código de Licitación'] = df_bbdd['Código de Licitación'].astype(str).str.strip()

        df_cron = leer_tabla_segura('cronograma')
        if not df_cron.empty and 'Código de Licitación' in df_cron.columns:
            df_cron['Código de Licitación'] = df_cron['Código de Licitación'].astype(str).str.strip()

        df_eq = leer_tabla_segura('equipo')
        df_vac = leer_tabla_segura('vacaciones')

        return df_bbdd, df_cron, df_eq, df_vac, ""
        
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), f"⚠️ ERROR SQL: {e}"
    finally:
        if 'conexion' in locals():
            conexion.close()

def leer_excel():
    _, df_cron, df_eq, df_vac, _ = obtener_datos_eficiente()
    return df_cron, df_eq, df_vac

# =====================================================================
# 2. ESCRITURA Y SINCRONIZACIÓN DESDE EXCEL EXTERNO
# =====================================================================
def actualizar_bbdd_desde_excel(ruta_excel):
    global _DATA_CACHE, _CALENDARIOS_CACHE
    if not os.path.exists(ruta_excel):
        return False, f"⚠️ No se encontró el archivo Excel en la ruta: {ruta_excel}"
    
    try:
        df_excel = pd.read_excel(ruta_excel)
        
        for col in ['Código de Licitación', 'Nombre de la Licitación']:
            if col in df_excel.columns:
                df_excel[col] = df_excel[col].astype(str).str.strip()
                
        if 'Presupuesto' in df_excel.columns:
            df_excel['Presupuesto'] = pd.to_numeric(df_excel['Presupuesto'], errors='coerce').fillna(0.0)

        conexion = sqlite3.connect(ARCHIVO_DB)
        df_excel.to_sql('bbdd', con=conexion, if_exists='replace', index=False)
        conexion.close()
        
        # Purgamos cachés
        _DATA_CACHE = {'df_bbdd': None, 'df_cron': None, 'df_eq': None, 'df_vac': None, 'error': ""}
        _CALENDARIOS_CACHE = None
        obtener_datos_eficiente(force_reload=True)
        obtener_calendarios(force_reload=True)
        
        return True, "🚀 Tabla de Licitaciones (BBDD) actualizada correctamente desde el Excel."
    except Exception as e:
        return False, f"❌ Error crítico procesando el archivo Excel: {str(e)}"

def guardar_sqlite_centralizado(df_cron_new=None, df_eq_new=None, df_vac_new=None):
    try:
        conexion = sqlite3.connect(ARCHIVO_DB)
        
        # Blindaje estructural: Forzar fechas limpias ISO en SQLite antes de volcar
        if df_cron_new is not None: 
            df_cron_write = df_cron_new.copy()
            for col in ['Fecha de Creación', 'Fecha de Fin']:
                if col in df_cron_write.columns:
                    df_cron_write[col] = df_cron_write[col].apply(parsear_fecha_es).dt.strftime('%Y-%m-%d').fillna("")
            df_cron_write.to_sql('cronograma', con=conexion, if_exists='replace', index=False)
            
        if df_eq_new is not None: 
            df_eq_new.to_sql('equipo', con=conexion, if_exists='replace', index=False)
            
        if df_vac_new is not None: 
            df_vac_write = df_vac_new.copy()
            for col in ['Fecha_Inicio', 'Fecha_Fin']:
                if col in df_vac_write.columns:
                    df_vac_write[col] = df_vac_write[col].apply(parsear_fecha_es).dt.strftime('%Y-%m-%d').fillna("")
            df_vac_write.to_sql('vacaciones', con=conexion, if_exists='replace', index=False)
            
        obtener_datos_eficiente(force_reload=True)
        return True, "💾 Cambios guardados correctamente."
    except Exception as e:
        return False, f"⚠️ Error al guardar en BBDD: {e}"
    finally:
        if 'conexion' in locals():
            conexion.close()

def sincronizar_vacaciones(datos_tabla):
    df_vac = pd.DataFrame(datos_tabla) if datos_tabla else pd.DataFrame(columns=['ID_Tecnico', 'Nombre', 'Fecha_Inicio', 'Fecha_Fin', 'Tipo_Ausencia'])
    return guardar_sqlite_centralizado(df_vac_new=df_vac)

# =====================================================================
# 3. TRANSFORMACIONES ESPECÍFICAS DE NEGOCIO (CALCULO MAESTRO FTE)
# =====================================================================
def parsear_fecha_es(val):
    """
    Motor ultra-robusto de traducción de fechas en español. 
    Intercepta NaT, marcas de tiempo mixtas, formatos europeos (DD/MM) e inputs descriptivos.
    Silencia los warnings de Pandas detectando el formato ISO.
    """
    if pd.isna(val) or val is None:
        return pd.NaT
    if isinstance(val, (datetime.datetime, datetime.date)):
        return pd.to_datetime(val)
    
    s = str(val).strip().lower()
    if not s or s in ['nan', 'none', 'nat', '<na>']:
        return pd.NaT
    
    # Limpieza de colas horarias (ej: '2026-06-13 00:00:00' -> '2026-06-13')
    if " " in s and (s.count("-") == 2 or s.count("/") == 2) and ":" in s:
        s = s.split(" ")[0]

    # Mapeo unificado para entrada humana en castellano
    meses = {
        'enero': '01', 'ene': '01',
        'febrero': '02', 'feb': '02',
        'marzo': '03', 'mar': '03',
        'abril': '04', 'abr': '04',
        'mayo': '05', 'may': '05',
        'junio': '06', 'jun': '06',
        'julio': '07', 'jul': '07',
        'agosto': '08', 'ago': '08',
        'septiembre': '09', 'sep': '09', 'setiembre': '09', 'set': '09',
        'octubre': '10', 'oct': '10',
        'noviembre': '11', 'nov': '11',
        'diciembre': '12', 'dic': '12'
    }
    
    # Intérprete para textos complejos estilo "8 de junio de 2026"
    if " de " in s:
        partes = [p.strip() for p in s.split(" de ") if p.strip()]
        if len(partes) == 3:
            dia, mes_txt, anio = partes[0], partes[1], partes[2]
            mes_num = meses.get(mes_txt, mes_txt)
            s = f"{dia}-{mes_num}-{anio}"
    else:
        # Reemplazo directo para cadenas del tipo '08-junio-2026'
        for mes_txt, mes_num in meses.items():
            if mes_txt in s:
                s = s.replace(mes_txt, mes_num)
                break
                
    try:
        # DETECCIÓN DINÁMICA DE FORMATO:
        # Si la cadena empieza por 4 dígitos (Ej: "2026-06-13"), es formato ISO.
        if len(s) >= 8 and s[:4].isdigit() and s[4] in ['-', '/']:
            return pd.to_datetime(s, errors='coerce') # Sin dayfirst para evitar el warning
        else:
            # Si empieza por el día (Ej: "13/06/2026" o "13-06-2026"), forzamos lectura europea
            return pd.to_datetime(s, dayfirst=True, errors='coerce')
    except Exception:
        return pd.NaT

def formato_fecha_es(fecha):
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    return f"{fecha.day} {meses[fecha.month - 1]}"

def obtener_horas_dia(fecha, sede, dict_cals):
    """Devuelve las horas laborables de un día según el calendario de la sede."""
    if sede in dict_cals and fecha in dict_cals[sede]:
        return float(dict_cals[sede][fecha])
    # Fallback si no hay calendario o falta el día: 8h L-V, 0h S-D
    return 8.0 if fecha.weekday() < 5 else 0.0

def procesar_cronograma(df_base):
    if df_base.empty:
        return df_base, []

    # 1. Traer diccionarios de equipo y calendarios
    _, _, df_eq, _, _ = obtener_datos_eficiente()
    dict_cals = obtener_calendarios()
    
    # Mapeo de Empleado -> Sede (Soporta búsqueda por Nombre o ID)
    dict_sede = {}
    if not df_eq.empty:
        for _, r in df_eq.iterrows():
            sede = str(r.get('Sede', 'MAD (Quint)')).strip()
            if not sede or sede == 'nan': sede = 'MAD (Quint)'
            if pd.notna(r.get('Nombre')): dict_sede[str(r['Nombre']).strip()] = sede
            if pd.notna(r.get('ID_Tecnico')): dict_sede[str(r['ID_Tecnico']).strip()] = sede

    # 2. Corrección y parseo blindado mediante motor personalizado
    with warnings.catch_warnings():
        warnings.simplefilter("ignore") 
        df_base['Creacion_dt'] = df_base['Fecha de Creación'].apply(parsear_fecha_es)
        df_base['Fin_dt'] = df_base['Fecha de Fin'].apply(parsear_fecha_es)
    
    df_base = df_base.sort_values(by='Fin_dt', ascending=True)
    df_base['Hito_Fin'] = df_base['Fin_dt'].apply(lambda x: formato_fecha_es(x.date()) if pd.notnull(x) else "")

    df_base['Presupuesto'] = df_base['Presupuesto'].apply(
        lambda x: f"{float(x):,.0f} €".replace(",", ".") if pd.notnull(x) and str(x).strip() != "" else ""
    )

    # --- 3. CÁLCULO DE FTE CRUZADO CON CALENDARIOS PROVINCIALES ---
    def calcular_metricas_proyecto(row):
        if pd.isnull(row['Creacion_dt']) or pd.isnull(row['Fin_dt']):
            return pd.Series({'FTE_Base': 0.0, 'Sedes_Asignadas': ['MAD (Quint)']})
        
        start = row['Creacion_dt'].date()
        end = row['Fin_dt'].date()
        if start > end: 
            return pd.Series({'FTE_Base': 0.0, 'Sedes_Asignadas': ['MAD (Quint)']})
        
        # Averiguamos qué sedes están implicadas en este proyecto
        assigned = [str(row.get(col, '')).strip() for col in ['BAM', 'Técnico 1', 'Técnico 2', 'Técnico 3']]
        assigned = [t for t in assigned if t and t.lower() != 'nan']
        
        sedes_implicadas = [dict_sede.get(t, 'MAD (Quint)') for t in assigned]
        if not sedes_implicadas: sedes_implicadas = ['MAD (Quint)']

        # Sumamos las horas de todos los integrantes durante el proyecto
        horas_disponibles_equipo = 0.0
        curr_date = start
        while curr_date <= end:
            for s in sedes_implicadas:
                horas_disponibles_equipo += obtener_horas_dia(curr_date, s, dict_cals)
            curr_date += datetime.timedelta(days=1)
            
        # Promedio de horas por persona para el cálculo de FTE (Equivalencia a 1 persona)
        horas_promedio_persona = max(1.0, horas_disponibles_equipo / len(sedes_implicadas))

        # Horas totales necesarias para el proyecto
        h_tec = row.get('Horas de Licitación', 0)
        h_tec = 0 if pd.isnull(h_tec) or str(h_tec).strip() == "" else float(h_tec)
        h_bam = row.get('Horas de Licitación BAM', 0)
        h_bam = 0 if pd.isnull(h_bam) or str(h_bam).strip() == "" else float(h_bam)
        horas_totales_req = h_tec + h_bam
        
        # FTE Base (Carga / Capacidad real de la sede en esas fechas)
        fte_base = round(horas_totales_req / horas_promedio_persona, 4)
        return pd.Series({'FTE_Base': fte_base, 'Sedes_Asignadas': sedes_implicadas})

    metricas = df_base.apply(calcular_metricas_proyecto, axis=1)
    df_base['FTE_Base'] = metricas['FTE_Base']
    df_base['Sedes_Asignadas'] = metricas['Sedes_Asignadas']

    # --- 4. INYECCIÓN DEL FTE EN LOS 60 DÍAS (RESPETANDO FESTIVOS) ---
    hoy = datetime.date.today()
    lista_dias_obj = [hoy + datetime.timedelta(days=i) for i in range(61)]
    columnas_calendario_nombres = []
    
    for dia in lista_dias_obj:
        col_name = formato_fecha_es(dia)
        columnas_calendario_nombres.append(col_name)
        
        def asignar_fte_dia(row):
            if pd.isnull(row['Creacion_dt']) or pd.isnull(row['Fin_dt']): return 0.0
            if row['Creacion_dt'].date() <= dia <= row['Fin_dt'].date():
                
                # Leemos la capacidad promedio del equipo para ESTE DÍA concreto
                sedes = row['Sedes_Asignadas']
                horas_hoy_promedio = sum(obtener_horas_dia(dia, s, dict_cals) for s in sedes) / len(sedes)
                
                if horas_hoy_promedio > 0:
                    # Ajuste fino: Si hoy se trabajan 4h en vez de 8h, asignamos la mitad del FTE
                    return round(row['FTE_Base'] * (horas_hoy_promedio / 8.0), 2)
            return 0.0
            
        df_base[col_name] = df_base.apply(asignar_fte_dia, axis=1)
        
    # ─── FIX: CONVERTIR LISTA A TEXTO PARA QUE DASH NO CRASHEE ───
    if 'Sedes_Asignadas' in df_base.columns:
        df_base['Sedes_Asignadas'] = df_base['Sedes_Asignadas'].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))

    return df_base, columnas_calendario_nombres