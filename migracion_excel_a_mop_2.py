import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from pathlib import Path
import unicodedata
import numpy as np
from datetime import datetime
import sys

class MigracionDGAMOP:
    """
    Clase para migrar datos históricos de Excel DGA a PostgreSQL
    """
    
    # Mapeo de columnas Excel → PostgreSQL
    MAPEO_COLUMNAS = {
        'Código Obra': 'codigo_obra',
        'CÃ³digo Obra': 'codigo_obra',
        'Estado': 'estado',
        'Región': 'region',
        'RegiÃ³n': 'region',
        'Provincia': 'provincia',
        'Comuna': 'comuna',
        'UTM Norte (m)': 'utm_norte',
        'UTM Este (m)': 'utm_este',
        'Huso': 'huso',
        'Naturaleza': 'naturaleza',
        'Obra habilitada?': 'obra_habilitada',
        'Fecha Registro Obra': 'fecha_registro_obra',
        'Canal de transmisión': 'canal_transmision',
        'Canal de transmisiÃ³n': 'canal_transmision',
        'Fecha (dd/mm/yyyy)': 'fecha',
        'Hora Medición (24hh)': 'hora_medicion',
        'Hora MediciÃ³n (24hh)': 'hora_medicion',
        'Caudal (l/s)': 'caudal',
        'Totalizador (m3)': 'totalizador',
        'Nivel Freático (m)': 'nivel_freatico',
        'Nivel FreÃ¡tico (m)': 'nivel_freatico',
        'database': 'database'
    }
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.engine = None
        self.connection_string = None
    
    def crear_conexion(self):
        """Crea la conexión a PostgreSQL usando SQLAlchemy"""
        try:
            self.connection_string = (
                f"postgresql+psycopg2://{self.db_config['user']}:{self.db_config['password']}"
                f"@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
            )
            self.engine = create_engine(self.connection_string)
            print(f"OK - Conexion creada: {self.db_config['database']}")
            return True
        except Exception as e:
            print(f"ERROR - Error creando conexion: {e}")
            return False
    
    def normalize_value(self, x):
        """Normaliza un valor individual"""
        if pd.isna(x):
            return np.nan
        if isinstance(x, (int, float, np.number)):
            return float(x)
        s = str(x).strip().lower()
        s = ''.join(c for c in unicodedata.normalize('NFKD', s) 
                   if not unicodedata.combining(c))
        return s
    
    def normalize_df(self, df):
        """Normaliza todo el DataFrame"""
        return df.applymap(self.normalize_value)
    
    def obtener_columnas_tabla(self):
        """Obtiene las columnas de la tabla PostgreSQL"""
        try:
            schema = self.db_config.get('schema', 'public')
            tabla = self.db_config['tabla']
            
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database']
            )
            cursor = conn.cursor()
            
            query = f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = '{schema}' 
              AND table_name = '{tabla}'
            ORDER BY ordinal_position;
            """
            
            cursor.execute(query)
            columnas = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            return columnas
            
        except Exception as e:
            print(f"ERROR - Error obteniendo columnas de tabla: {e}")
            return None
    
    def subir_csv_a_postgres(self, ruta_csv):
        """
        Sube un CSV directamente a PostgreSQL usando COPY
        VERSIÓN CORREGIDA con validación y manejo robusto de errores
        """
        from pathlib import Path
        
        conn = None
        cursor = None
        ruta_csv_temp = None
        
        try:
            ruta_csv = Path(ruta_csv)
            if not ruta_csv.exists():
                print(f"ERROR - Archivo CSV no existe: {ruta_csv}")
                return False
            
            schema = self.db_config.get('schema', 'public')
            tabla = self.db_config['tabla']
            
            print(f"\n[BD] Subiendo CSV a PostgreSQL usando COPY...")
            print(f"   Archivo: {ruta_csv}")
            print(f"   Destino: {schema}.{tabla}")
            
            # 1. OBTENER COLUMNAS DE LA TABLA
            columnas_tabla = self.obtener_columnas_tabla()
            if not columnas_tabla:
                print("ERROR - No se pudieron obtener las columnas de la tabla")
                return False
            
            print(f"   Columnas en tabla: {len(columnas_tabla)}")
            print(f"   {columnas_tabla[:5]}...")
            
            # 2. LEER CSV Y VALIDAR COLUMNAS
            df_csv = pd.read_csv(ruta_csv)
            print(f"   Registros en CSV: {len(df_csv)}")
            print(f"   Columnas en CSV: {len(df_csv.columns)}")
            
            # 3. FILTRAR SOLO COLUMNAS QUE EXISTEN EN LA TABLA
            columnas_validas = [col for col in df_csv.columns 
                               if col in columnas_tabla and not col.startswith('_')]
            
            print(f"   Columnas válidas para importar: {len(columnas_validas)}")
            
            if not columnas_validas:
                print("ERROR - No hay columnas validas para importar")
                return False
            
            # 4. CREAR CSV TEMPORAL SOLO CON COLUMNAS VÁLIDAS
            df_limpio = df_csv[columnas_validas].copy()
            
            # CRÍTICO: Convertir todas las columnas datetime a string formato ISO (YYYY-MM-DD)
            for col in df_limpio.columns:
                if pd.api.types.is_datetime64_any_dtype(df_limpio[col]):
                    print(f"   Convirtiendo columna fecha: {col}")
                    df_limpio[col] = df_limpio[col].dt.strftime('%Y-%m-%d')
                    df_limpio[col] = df_limpio[col].replace('NaT', '')
            
            # Manejar columna hora_medicion (ya viene como string HH:MM:SS del procesamiento)
            if 'hora_medicion' in df_limpio.columns:
                print(f"   Validando columna hora_medicion...")
                # Reemplazar None/NaN con string vacío
                df_limpio['hora_medicion'] = df_limpio['hora_medicion'].fillna('')
            
            # Reemplazar NaN con None para PostgreSQL
            df_limpio = df_limpio.where(pd.notnull(df_limpio), None)
            
            ruta_csv_temp = ruta_csv.parent / f"temp_{ruta_csv.name}"
            df_limpio.to_csv(ruta_csv_temp, index=False, na_rep='')
            
            print(f"   CSV temporal creado: {ruta_csv_temp}")
            
            # DEBUG: Mostrar primeras 3 líneas del CSV para verificar formato
            print(f"\n   [DEBUG] Muestra del CSV temporal:")
            with open(ruta_csv_temp, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i < 3:  # Encabezado + 2 filas
                        print(f"      {line.strip()[:150]}...")
                    else:
                        break
            
            # 5. CONEXIÓN A POSTGRES
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database']
            )
            cursor = conn.cursor()
            
            # 6. CONTAR ANTES
            cursor.execute(f"SELECT COUNT(*) FROM {schema}.{tabla};")
            count_antes = cursor.fetchone()[0]
            print(f"   Registros ANTES: {count_antes}")
            
            # 7. EJECUTAR COPY
            columnas_str = ', '.join(columnas_validas)
            
            with open(ruta_csv_temp, 'r', encoding='utf-8') as f:
                next(f)  # Saltar encabezados
                
                copy_query = f"""
                COPY {schema}.{tabla} ({columnas_str})
                FROM STDIN 
                WITH (FORMAT CSV, DELIMITER ',', NULL '', ENCODING 'UTF8');
                """
                
                print(f"   Ejecutando COPY...")
                cursor.copy_expert(copy_query, f)
            
            # 8. COMMIT
            conn.commit()
            print(f"   OK - COMMIT exitoso")
            
            # 9. CONTAR DESPUÉS
            cursor.execute(f"SELECT COUNT(*) FROM {schema}.{tabla};")
            count_despues = cursor.fetchone()[0]
            insertados = count_despues - count_antes
            
            print(f"   Registros DESPUÉS: {count_despues}")
            print(f"   OK - {insertados} registros insertados")
            
            # 10. VERIFICACIÓN ADICIONAL (si hay filtro de fecha)
            if 'fecha' in columnas_validas:
                cursor.execute(f"""
                    SELECT MIN(fecha), MAX(fecha), COUNT(*) 
                    FROM {schema}.{tabla} 
                    WHERE fecha >= (SELECT MAX(fecha) - INTERVAL '60 days' FROM {schema}.{tabla});
                """)
                fecha_min, fecha_max, count_recientes = cursor.fetchone()
                print(f"   Últimos 60 días - Min: {fecha_min}, Max: {fecha_max}, Count: {count_recientes}")
            
            return True
            
        except Exception as e:
            print(f"ERROR - Error en carga CSV: {e}")
            import traceback
            traceback.print_exc()
            
            if conn:
                conn.rollback()
                print("   Rollback ejecutado")
            
            return False
            
        finally:
            # LIMPIEZA
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            
            # Eliminar CSV temporal solo si todo salió bien
            if ruta_csv_temp and ruta_csv_temp.exists():
                try:
                    ruta_csv_temp.unlink()
                    print(f"   CSV temporal eliminado")
                except:
                    print(f"   ⚠ No se pudo eliminar CSV temporal: {ruta_csv_temp}")
    
    def buscar_archivos_excel(self, ruta_base, año=None, mes=None, proyecto=None, codigos_obra_filtro=None):
        """Busca archivos Excel en la estructura de carpetas"""
        print("[BUSCAR] Buscando archivos Excel...")
        print(f"   Ruta base: {ruta_base}")
        if año:
            print(f"   Año filtro: {año}")
        if mes:
            print(f"   Mes filtro: {mes}")
        if proyecto:
            print(f"   Proyecto filtro: {proyecto}")
        if codigos_obra_filtro:
            print(f"   Filtro de obras: {', '.join(codigos_obra_filtro)}")
        
        ruta_base = Path(ruta_base)
        archivos_encontrados = []
        
        mapeo_carpetas_proyecto = {
            '2253': 'P5',
            '2366': 'P12',
            '2367': 'P22',
            '2368': 'P17'
        }
        
        for carpeta_proyecto in ruta_base.iterdir():
            if not carpeta_proyecto.is_dir():
                continue
            
            codigo_carpeta = carpeta_proyecto.name.split(' - ')[0]
            codigo_proyecto = mapeo_carpetas_proyecto.get(codigo_carpeta)
            
            if proyecto and codigo_proyecto != proyecto:
                continue
            
            print(f"\n[PROYECTO] Procesando proyecto: {carpeta_proyecto.name}")
            
            for carpeta_año in carpeta_proyecto.iterdir():
                if not carpeta_año.is_dir():
                    continue
                
                try:
                    año_carpeta = int(carpeta_año.name)
                except ValueError:
                    continue
                
                if año and año_carpeta != año:
                    continue
                
                for archivo in carpeta_año.iterdir():
                    if archivo.suffix in ['.xls', '.xlsx']:
                        nombre_archivo = archivo.stem.lower()
                        
                        if 'historia' in nombre_archivo:
                            mes_archivo = None
                        else:
                            partes = archivo.stem.split('.')
                            if len(partes) > 0:
                                try:
                                    mes_archivo = int(partes[0].strip())
                                except ValueError:
                                    mes_archivo = None
                            else:
                                mes_archivo = None
                        
                        if mes is not None:
                            if mes_archivo != mes:
                                continue
                        
                        # FILTRO POR CÓDIGO DE OBRA
                        if codigos_obra_filtro:
                            en_filtro = False
                            for codigo in codigos_obra_filtro:
                                if codigo.lower() in archivo.name.lower():
                                    en_filtro = True
                                    break
                            if not en_filtro:
                                continue
                        
                        info = {
                            'proyecto': codigo_proyecto,
                            'carpeta_proyecto': carpeta_proyecto.name,
                            'carpeta_pozo': 'NA', # Elimado en la estructura EC2
                            'año': año_carpeta,
                            'mes': mes_archivo,
                            'tipo': 'HISTORIA' if 'historia' in nombre_archivo else 'REPORTE'
                        }
                        
                        archivos_encontrados.append((archivo, info))
        
        print(f"\nOK - Total archivos encontrados: {len(archivos_encontrados)}")
        return archivos_encontrados
    
    def leer_excel(self, ruta_archivo, info_archivo):
        """Lee un archivo Excel y retorna DataFrame"""
        try:
            ext = ruta_archivo.suffix.lower()
            engine = 'xlrd' if ext == '.xls' else 'openpyxl'
            
            # Soporte para rutas largas en Windows (>260 caracteres)
            ruta_str = str(ruta_archivo.absolute())
            if sys.platform == "win32" and not ruta_str.startswith("\\\\?\\"):
                ruta_str = "\\\\?\\" + ruta_str
            
            df = pd.read_excel(ruta_str, skiprows=4, engine=engine)
            
            if df.empty:
                print(f"       ADVERTENCIA - Archivo vacio: {ruta_archivo.name}")
                
                # Intentar extraer codigo de obra del nombre del archivo
                import re
                codigo_encontrado = "DESCONOCIDO"
                # Patrón estándar OB-XXXX-XXX o RTU_XXX
                match = re.search(r'(OB-\d{4}-\d{3}|RTU_[A-Z]\d{2})', ruta_archivo.name, re.IGNORECASE)
                if match:
                    codigo_encontrado = match.group().upper()
                
                print(f"       -> Generando registro de control con 0s para {codigo_encontrado}")
                
                # Crear un registro dummy para el día 1 del mes correspondiente
                anio = info_archivo.get('año', 2026)
                mes = info_archivo.get('mes') or 1
                
                df_dummy = pd.DataFrame([{
                    'Código Obra': codigo_encontrado,
                    'Estado': 'Vacio (Auto)',
                    'Fecha (dd/mm/yyyy)': datetime(anio, mes, 1),
                    'Hora Medición (24hh)': '00:00:00',
                    'Caudal (l/s)': 0.0,
                    'Totalizador (m3)': 0.0,
                    'Nivel Freático (m)': 0.0,
                    'database': str(ruta_archivo)
                }])
                
                # Agregar metadatos internos
                df_dummy['_proyecto'] = info_archivo['proyecto']
                df_dummy['_año_carpeta'] = info_archivo['año']
                df_dummy['_tipo_archivo'] = info_archivo['tipo']
                
                return df_dummy
            
            df['database'] = str(ruta_archivo)
            df['_proyecto'] = info_archivo['proyecto']
            df['_año_carpeta'] = info_archivo['año']
            df['_tipo_archivo'] = info_archivo['tipo']
            
            return df
            
        except Exception as e:
            print(f"     ERROR leyendo {ruta_archivo.name}: {e}")
            return None
    
    def procesar_dataframe(self, df):
        """Procesa y limpia el DataFrame"""
        if 'Nro. Fila' in df.columns:
            df = df.drop('Nro. Fila', axis=1)
        
        columnas_renombrar = {}
        for col_original in df.columns:
            if col_original in self.MAPEO_COLUMNAS:
                columnas_renombrar[col_original] = self.MAPEO_COLUMNAS[col_original]
        
        df = df.rename(columns=columnas_renombrar)
        
        if 'fecha' not in df.columns:
            print(f"       ADVERTENCIA - No se encontro columna 'fecha'")
            return pd.DataFrame()
        
        # CONVERTIR TODAS LAS COLUMNAS DE FECHA (crítico para PostgreSQL)
        columnas_fecha = ['fecha', 'fecha_registro_obra']
        for col in columnas_fecha:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
        
        df = df.dropna(subset=['fecha', 'codigo_obra'])
        
        if df.empty:
            print("       ADVERTENCIA - DataFrame vacio después de limpiar")
            return df
        
        columnas_texto = ['estado', 'region', 'provincia', 'comuna', 'naturaleza', 
                         'obra_habilitada', 'canal_transmision']
        for col in columnas_texto:
            if col in df.columns:
                df[col] = df[col].apply(self.normalize_value)
        
        columnas_numericas = ['utm_norte', 'utm_este', 'caudal', 'totalizador', 'nivel_freatico']
        for col in columnas_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # CONVERTIR hora_medicion a formato TIME correcto (HH:MM:SS)
        if 'hora_medicion' in df.columns:
            # Puede venir como int (ej: 1230 = 12:30) o como string
            def convertir_hora(valor):
                if pd.isna(valor):
                    return None
                
                # Si es número (ej: 1230, 130, 0)
                if isinstance(valor, (int, float, np.number)):
                    hora_int = int(valor)
                    horas = hora_int // 100
                    minutos = hora_int % 100
                    return f"{horas:02d}:{minutos:02d}:00"
                
                # Si ya es string
                valor_str = str(valor).strip()
                
                # Si tiene formato HH:MM o HH:MM:SS
                if ':' in valor_str:
                    partes = valor_str.split(':')
                    if len(partes) == 2:
                        return f"{partes[0].zfill(2)}:{partes[1].zfill(2)}:00"
                    elif len(partes) == 3:
                        return f"{partes[0].zfill(2)}:{partes[1].zfill(2)}:{partes[2].zfill(2)}"
                
                # Si es número como string (ej: "1230")
                try:
                    hora_int = int(float(valor_str))
                    horas = hora_int // 100
                    minutos = hora_int % 100
                    return f"{horas:02d}:{minutos:02d}:00"
                except:
                    return None
            
            df['hora_medicion'] = df['hora_medicion'].apply(convertir_hora)
        
        return df
    
    def ejecutar_migracion(self, ruta_base, año=None, mes=None, proyecto=None, 
                          codigos_obra_filtro=None, subir_db=True, guardar_csv=True, ruta_csv=None):
        """Ejecuta el proceso completo de migración"""
        print("="*70)
        print("MIGRACION DGA MOP - EXCEL -> POSTGRESQL")
        print("="*70)
        
        try:
            if subir_db:
                if not self.crear_conexion():
                    return {'status': 'error', 'mensaje': 'Error creando conexión a BD'}
            
            archivos = self.buscar_archivos_excel(ruta_base, año, mes, proyecto, codigos_obra_filtro)
            
            if not archivos:
                return {
                    'status': 'warning',
                    'mensaje': 'No se encontraron archivos Excel'
                }
            
            print(f"\n[PROCESAR] Procesando {len(archivos)} archivos...")
            dataframes = []
            archivos_procesados = 0
            
            for archivo, info in archivos:
                print(f"\n   [ARCHIVO] {archivo.name}")
                
                df = self.leer_excel(archivo, info)
                
                if df is not None:
                    df_procesado = self.procesar_dataframe(df)
                    if not df_procesado.empty:
                        dataframes.append(df_procesado)
                        archivos_procesados += 1
                        print(f"       OK - {len(df_procesado)} registros")
            
            if not dataframes:
                return {
                    'status': 'error',
                    'mensaje': 'No se pudo procesar ningún archivo'
                }
            
            print(f"\n[UNIR] Consolidando {len(dataframes)} DataFrames...")
            df_consolidado = pd.concat(dataframes, ignore_index=True)
            print(f"   Total registros: {len(df_consolidado)}")
            
            if 'fecha' in df_consolidado.columns:
                fecha_min = df_consolidado['fecha'].min()
                fecha_max = df_consolidado['fecha'].max()
                print(f"\n[FECHAS] Rango de fechas:")
                print(f"   Min: {fecha_min}")
                print(f"   Max: {fecha_max}")
            
            antes_dup = len(df_consolidado)
            df_consolidado = df_consolidado.drop_duplicates(
                subset=['codigo_obra', 'fecha', 'hora_medicion'],
                keep='last'
            )
            duplicados = antes_dup - len(df_consolidado)
            
            if duplicados > 0:
                print(f"   Duplicados eliminados: {duplicados}")
            
            if not ruta_csv:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ruta_csv = f"./output/migracion_{timestamp}.csv"
            
            print(f"\n[GUARDAR] Guardando CSV...")
            Path(ruta_csv).parent.mkdir(parents=True, exist_ok=True)
            df_consolidado.to_csv(ruta_csv, index=False)
            print(f"   OK - CSV guardado: {ruta_csv}")
            
            # DIAGNÓSTICO: Verificar tipos de datos en CSV
            print(f"\n[DIAGNOSTICO] Diagnóstico de tipos de datos:")
            for col in ['fecha', 'fecha_registro_obra', 'hora_medicion']:
                if col in df_consolidado.columns:
                    tipo = df_consolidado[col].dtype
                    muestra = df_consolidado[col].dropna().head(3).tolist()
                    print(f"   {col}: {tipo} -> {muestra}")
            
            if subir_db:
                exito = self.subir_csv_a_postgres(ruta_csv)
                if not exito:
                    return {
                        'status': 'error',
                        'mensaje': 'Error subiendo a PostgreSQL',
                        'csv_guardado': ruta_csv
                    }
            
            print("\n" + "="*70)
            print("OK - MIGRACION COMPLETADA")
            print("="*70)
            
            return {
                'status': 'success',
                'mensaje': 'Migración completada exitosamente',
                'archivos_procesados': archivos_procesados,
                'registros_totales': len(df_consolidado),
                'duplicados_eliminados': duplicados,
                'csv_guardado': ruta_csv
            }
            
        except Exception as e:
            print(f"\nERROR - Error en migracion: {e}")
            import traceback
            traceback.print_exc()
            return {'status': 'error', 'mensaje': str(e)}


# EJEMPLO DE USO
if __name__ == "__main__":
    
    db_config = {
        'host': '3.147.102.192',
        'port': '5432',
        'user': 'postgres',
        'password': 'Quantica346',
        'database': 'thingsboard',
        'schema': 'normativa_dga',
        'tabla': 'dga_mop_mediciones'
    }
    
    # Ruta adaptada para la EC2 de Amazon (Ubuntu)
    RUTA_BASE = "/opt/quantica/EXTRACCIONES MOP"
    
    migrador = MigracionDGAMOP(db_config)
    
    # =====================================================================
    # EJEMPLO 1: MIGRAR UN MES ESPECÍFICO (MANUAL)
    # =====================================================================
    # print("\n[INICIO] Ejecutando migración masiva manual para Enero 2026...")
    #resultado = migrador.ejecutar_migracion(
     #    ruta_base=RUTA_BASE,
      #   año=2026,
       #  mes=2,
        # proyecto=None,            # Procesa todos los proyectos (P5, P12, P17, P22)
        # codigos_obra_filtro=None, # IMPORTANTE: None procesa todos los pozos encontrados
       #  subir_db=True,            # Sube los datos a PostgreSQL
       #  guardar_csv=True,         # Guarda un respaldo en CSV
       #  ruta_csv="./output/migracion_enero_2026_total.csv"
    #)
    
    # =====================================================================
    # EJEMPLO 2: MIGRAR EL MES ANTERIOR AUTOMÁTICAMENTE (CRONJOB)
    # =====================================================================
    import datetime
    hoy = datetime.date.today()
    primer_dia_mes_actual = hoy.replace(day=1)
    ultimo_dia_mes_anterior = primer_dia_mes_actual - datetime.timedelta(days=1)
    
    anio_procesar = ultimo_dia_mes_anterior.year
    mes_procesar = ultimo_dia_mes_anterior.month
    
    meses_str = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    nombre_mes = meses_str[mes_procesar - 1]
    
    ruta_csv_salida = f"./output/migracion_{nombre_mes}_{anio_procesar}_total.csv"
    
    print(f"\n[INICIO] Ejecutando migración masiva automática para {nombre_mes.capitalize()} {anio_procesar}...")
    resultado = migrador.ejecutar_migracion(
        ruta_base=RUTA_BASE,
        año=anio_procesar,
        mes=mes_procesar,
        proyecto=None,            # Procesa todos los proyectos
        codigos_obra_filtro=None, # Procesa todos los pozos encontrados
        subir_db=True,            # Sube los datos a PostgreSQL
        guardar_csv=True,         # Guarda un respaldo en CSV
        ruta_csv=ruta_csv_salida
    )
    
    # ---------------------------------------------------------------------
    print(f"\nRESULTADO FINAL:")
    for k, v in resultado.items():
        print(f"   {k}: {v}")
