import pandas as pd
import datetime
import numpy as np
import os
import sys

# Detectar si estamos ejecutando desde el .exe compilado o desde Python normal
if getattr(sys, 'frozen', False):
    directorio_base = os.path.dirname(sys.executable)
else:
    directorio_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARCHIVO_EXCEL = os.path.join(directorio_base, "cronograma.xlsx")


def formato_fecha_es(fecha):
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    return f"{fecha.day} {meses[fecha.month - 1]}"

def leer_excel():
    """Lectura centralizada y limpieza automatizada de cabeceras."""
    try:
        with pd.ExcelFile(ARCHIVO_EXCEL, engine='openpyxl') as xls:
            hojas = {sheet.lower().strip(): sheet for sheet in xls.sheet_names}
            
            df_maestro = pd.read_excel(xls, sheet_name=hojas.get('cronograma')) if 'cronograma' in hojas else pd.DataFrame()
            df_eq = pd.read_excel(xls, sheet_name=hojas.get('equipo')) if 'equipo' in hojas else pd.DataFrame()
            df_vac = pd.read_excel(xls, sheet_name=hojas.get('vacaciones')) if 'vacaciones' in hojas else pd.DataFrame()
            
            # Guardianes de espacios en blanco invisibles
            if not df_maestro.empty: df_maestro.columns = df_maestro.columns.str.strip()
            if not df_eq.empty: df_eq.columns = df_eq.columns.str.strip()
            if not df_vac.empty: df_vac.columns = df_vac.columns.str.strip()
            
            return df_maestro, df_eq, df_vac
    except Exception as e:
        print(f"Error en data_manager: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def procesar_cronograma(df_base):
    if df_base.empty:
        return df_base, []

    # 1. Asegurar que Pandas entiende las fechas correctamente
    df_base['Creacion_dt'] = pd.to_datetime(df_base['Fecha de Creación'], format='%d/%m/%Y', errors='coerce')
    df_base['Fin_dt'] = pd.to_datetime(df_base['Fecha de Fin'], errors='coerce')
    
    # 2. ORDENAR TODO EL DATAFRAME AQUÍ, justo después de entender las fechas
    df_base = df_base.sort_values(by='Fin_dt', ascending=True)

    # 3. Crear el Hito_Fin para todas las filas (fundamental para que el color naranja aparezca en ambas tablas)
    df_base['Hito_Fin'] = df_base['Fin_dt'].apply(lambda x: formato_fecha_es(x.date()) if pd.notnull(x) else "")

    # 4. Formatear visualmente para la pantalla
    df_base['Fecha de Creación'] = df_base['Creacion_dt'].dt.strftime('%d/%m/%Y')
    df_base['Fecha de Fin'] = df_base['Fin_dt'].dt.strftime('%d/%m/%Y')
    
    # Formatear divisa, manejando posibles valores nulos si la fila es nueva
    df_base['Presupuesto'] = df_base['Presupuesto'].apply(
        lambda x: f"{float(x):,.0f} €".replace(",", ".") if pd.notnull(x) and str(x).strip() != "" else ""
    )

    # 5. Calcular FTEs
    def calcular_fte_diario(row):
        if pd.isnull(row['Creacion_dt']) or pd.isnull(row['Fin_dt']):
            return 0.0
        start = row['Creacion_dt'].date()
        end = row['Fin_dt'].date()
        if start > end: return 0.0
        
        dias_lab = max(1, np.busday_count(start, end + datetime.timedelta(days=1)))
        
        horas = row.get('Horas de Licitación', 0)
        if pd.isnull(horas): horas = 0
            
        return round(float(horas) / (dias_lab * 8), 2)

    df_base['FTE_Diario'] = df_base.apply(calcular_fte_diario, axis=1)

    # 6. Desplegar columnas del calendario
    hoy = datetime.date.today()
    lista_dias_obj = [hoy + datetime.timedelta(days=i) for i in range(61)]
    columnas_calendario_nombres = []
    
    for dia in lista_dias_obj:
        col_name = formato_fecha_es(dia)
        columnas_calendario_nombres.append(col_name)
        es_laborable = dia.weekday() < 5
        
        def asignar_fte_dia(row):
            if pd.isnull(row['Creacion_dt']) or pd.isnull(row['Fin_dt']): return 0.0
            if row['Creacion_dt'].date() <= dia <= row['Fin_dt'].date() and es_laborable:
                return row['FTE_Diario']
            return 0.0
            
        df_base[col_name] = df_base.apply(asignar_fte_dia, axis=1)

    return df_base, columnas_calendario_nombres
def guardar_asignacion(cod_licitacion, tec1, tec2, tec3):
    """Guarda la asignación únicamente en la pestaña operativa 'cronograma'."""
    try:
        with pd.ExcelFile(ARCHIVO_EXCEL, engine='openpyxl') as xls:
            df_bbdd = pd.read_excel(xls, sheet_name='bbdd')
            df_cron = pd.read_excel(xls, sheet_name='cronograma')
            df_eq = pd.read_excel(xls, sheet_name='equipo')
            df_vac = pd.read_excel(xls, sheet_name='vacaciones')

        # 1. Asegurar estructura de la pestaña operativa
        if 'Código de Licitación' not in df_cron.columns:
            df_cron['Código de Licitación'] = ""
            
        columnas_tecnicos = ['Técnico 1', 'Técnico 2', 'Técnico 3']
        for col in columnas_tecnicos:
            if col not in df_cron.columns:
                df_cron[col] = ""
            df_cron[col] = df_cron[col].astype(object) # Forzar texto

        # 2. Buscar si la licitación ya tiene fila en cronograma
        indice = df_cron.index[df_cron['Código de Licitación'] == cod_licitacion].tolist()
        
        if indice:
            # Si existe, actualizamos esa fila
            idx = indice[0]
        else:
            # Si es la primera vez que se le asigna alguien, creamos la fila
            idx = len(df_cron)
            df_cron.at[idx, 'Código de Licitación'] = cod_licitacion

        # 3. Inyectar técnicos
        df_cron.at[idx, 'Técnico 1'] = tec1 if tec1 else ""
        df_cron.at[idx, 'Técnico 2'] = tec2 if tec2 else ""
        df_cron.at[idx, 'Técnico 3'] = tec3 if tec3 else ""

        # 4. Sobrescribir conservando todas las pestañas intactas
        with pd.ExcelWriter(ARCHIVO_EXCEL, engine='openpyxl', mode='w') as writer:
            df_bbdd.to_excel(writer, sheet_name='bbdd', index=False)
            df_cron.to_excel(writer, sheet_name='cronograma', index=False)
            df_eq.to_excel(writer, sheet_name='equipo', index=False)
            df_vac.to_excel(writer, sheet_name='vacaciones', index=False)
            
        return True, "Asignación guardada correctamente."
        
    except PermissionError:
        return False, "⚠️ ERROR: El archivo Excel está abierto. Ciérralo y vuelve a intentarlo."
    except Exception as e:
        return False, f"Error inesperado: {e}"
    

def sincronizar_vacaciones(datos_tabla):
    """Sobrescribe la pestaña de vacaciones asegurando la integridad estructural."""
    try:
        columnas_maestras = ['ID_Tecnico', 'Nombre', 'Fecha_Inicio', 'Fecha_Fin', 'Tipo_Ausencia']
        if not datos_tabla:
            df_vac = pd.DataFrame(columns=columnas_maestras)
        else:
            df_vac = pd.DataFrame(datos_tabla)
            for col in columnas_maestras:
                if col not in df_vac.columns:
                    df_vac[col] = ""
            df_vac = df_vac[columnas_maestras]

        # Leer el resto de pestañas para preservarlas
        with pd.ExcelFile(ARCHIVO_EXCEL, engine='openpyxl') as xls:
            df_bbdd = pd.read_excel(xls, sheet_name='bbdd')
            df_cron = pd.read_excel(xls, sheet_name='cronograma')
            df_eq = pd.read_excel(xls, sheet_name='equipo')
            
        # Escritura limpia completa
        with pd.ExcelWriter(ARCHIVO_EXCEL, engine='openpyxl', mode='w') as writer:
            df_bbdd.to_excel(writer, sheet_name='bbdd', index=False)
            df_cron.to_excel(writer, sheet_name='cronograma', index=False)
            df_eq.to_excel(writer, sheet_name='equipo', index=False)
            df_vac.to_excel(writer, sheet_name='vacaciones', index=False)
            
        return True, "Sincronizado"
    except PermissionError:
        return False, "⚠️ ERROR: El archivo Excel está abierto. Ciérralo para poder guardar los cambios."
    except Exception as e:
        return False, f"⚠️ ERROR INESPERADO: {str(e)}"