# gestor_db.py
# Este script contiene todas las funciones para interactuar con la DB SQLite.

import sqlite3
from pathlib import Path

# Path(__file__).parent apunta a 'src/'. .parent otra vez apunta a la raíz del proyecto.
# C:\Users\santi\Desktop\PROYECTOS\Asistente_Local\memoria.db

DB_PATH = Path(__file__).parent.parent / "memoria.db" 

# --- 1. FUNCIONES AUXILIARES (NO PERDER ESTAS) ---

def conectar_db():
    """Crea la conexión a SQLite."""
    try:
        return sqlite3.connect(DB_PATH)
    except sqlite3.Error as e:
        print(f"Error crítico SQLite: {e}")
        return None

def get_activo_por_ruta(ruta_abs):
    """
    Busca un activo por su ruta. Vital para que el monitor sepa si existe.
    Devuelve la tupla completa (ID, Ruta, ...).
    El ID_Activo es el índice [0].
    """
    conn = conectar_db()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Activos WHERE Ruta_Absoluta = ?", (str(ruta_abs),))
        activo = cursor.fetchone()
        return activo
    except Exception as e:
        print(f"Error buscando activo: {e}")
        return None
    finally:
        conn.close()

# --- 2. INICIALIZACIÓN DE TABLAS (ESTRUCTURA 2.0) ---

def inicializar_base_de_datos():
    """
    Inicializa la conexión y crea las tablas Activos y Registros.
    """
    conn = None
    print(f"Inicializando base de datos en: {DB_PATH}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # TABLA 1: ACTIVOS (Inventario)
        print("Creando tabla 'Activos'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Activos (
            ID_Activo INTEGER PRIMARY KEY AUTOINCREMENT,
            Ruta_Absoluta TEXT UNIQUE NOT NULL,
            Nombre_Archivo TEXT,
            Extension TEXT,
            Tipo_Activo TEXT,      -- 'Archivo', 'Programa', 'Email'
            
            -- Metadatos de Peso y Recursos
            Peso_Bytes INTEGER,        -- Para filtrar archivos gigantes
            Estimacion_Tokens INTEGER, -- Para que el LLM sepa si le cabe en memoria
            
            -- Inteligencia
            Resumen_Ejecutivo TEXT,    -- Resumen breve para búsquedas rápidas
            Etiquetas_Confirmadas TEXT,-- Tags aprobados por el usuario
            
            -- Control de Cambios
            Hash_Contenido TEXT,
            Fecha_Modificacion_DB DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- Estado del RAG
            Estado_Procesamiento TEXT DEFAULT 'Pendiente' -- 'Pendiente', 'Indexado', 'Error'
        )
        """)
        
        # 2. Tabla Registros (Diario de a Bordo)
        print("Creando tabla 'Registros' (Diario de a Bordo)...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Registros (
                ID_Registro INTEGER PRIMARY KEY AUTOINCREMENT,
                Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            
                Tipo_Evento TEXT NOT NULL,  -- 'FOCO', 'MODIFICADO', 'CREADO', 'LLM_QUERY'
                Contexto_Crudo TEXT,        -- Ej: 'AutoCAD - Plano.dwg'
            
                -- El Enlace (Linker)
                ID_Activo_Asociado INTEGER, -- Puede ser NULL al principio
                Confianza_Enlace TEXT,      -- 'ALTA', 'MEDIA', 'NULA'
                Etiquetas TEXT,
            
                FOREIGN KEY (ID_Activo_Asociado) REFERENCES Activos(ID_Activo)
            )
        """)

            # 3. TABLA PROGRAMAS (Nuevo: Contexto de Software)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Programas_Conocidos (
                Nombre_Proceso TEXT PRIMARY KEY, -- Ej: 'acad.exe'
                Nombre_Comercial TEXT,           -- Ej: 'AutoCAD 2024'
                Descripcion_Contextual TEXT,     -- Ej: 'Software de diseño CAD...'
                Categoria TEXT                   -- 'Diseño', 'Ofimática', 'Sistema'
            )
        """)

        conn.commit()
        print("Base de datos inicializada correctamente.")
    except sqlite3.Error as e:
        print(f"Error al inicializar la base de datos: {e}")
    finally:
        if conn:
            conn.close()

# --- 3. FUNCIONES DE INSERCIÓN (ACTUAL CON 2.0) ---

def insertar_activo_completo(ruta, nombre, ext, peso, tokens_est, hash_val):
    """
    Inserta o actualiza un activo con TODOS los datos nuevos (tokens, peso).
    Reemplaza a la antigua 'insertar_o_actualizar_activo'.
    """
    conn = conectar_db()
    if not conn: return
    try:
        cursor = conn.cursor()
        # Usamos INSERT OR REPLACE para actualizar si ya existe la ruta. (Requiere que Ruta_Absoluta sea UNIQUE, que lo es)
        cursor.execute("""
            INSERT OR REPLACE INTO Activos (
                Ruta_Absoluta, Nombre_Archivo, Extension, Peso_Bytes, 
                Estimacion_Tokens, Hash_Contenido, Fecha_Modificacion_DB, Estado_Procesamiento
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, "Pendiente")
                ON CONFLICT(Ruta_Absoluta) DO UPDATE SET
                Hash_Contenido = excluded.Hash_Contenido,
                Peso_Bytes = excluded.Peso_Bytes,
                Estimacion_Tokens = excluded.Estimacion_Tokens,
                Fecha_Modificacion_DB = CURRENT_TIMESTAMP,
                Estado_Procesamiento = 'Pendiente'
        """, (str(ruta), nombre, ext, peso, tokens_est, hash_val))
        conn.commit()
    except Exception as e:
        print(f"Error insertando activo completo: {e}")
    finally:
        conn.close()

def insertar_registro_accion(tipo, contexto, id_activo=None):
    conn = conectar_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Registros (Tipo_Evento, Contexto_Crudo, ID_Activo_Asociado)
            VALUES (?, ?, ?)
        """, (tipo, contexto, id_activo))
        conn.commit()
    except Exception as e:
        print(f"Error DB (Registro): {e}")
    finally:
        conn.close()

# En src/gestor_db.py (Añadir al final)

def obtener_registros_recientes(limite=10):
    """
    Recupera los últimos 'limite' registros de acciones para el contexto del LLM.
    """
    conn = conectar_db()
    if not conn: return "No hay historial disponible."
    
    try:
        cursor = conn.cursor()
        # Se ordena por Timestamp (el más reciente primero)
        cursor.execute("""
            SELECT Timestamp, Tipo_Evento, Contexto_Crudo, ID_Activo_Asociado 
            FROM Registros 
            ORDER BY Timestamp DESC 
            LIMIT ?
        """, (limite,))
        registros = cursor.fetchall()
        
        # Formatear la salida para que el LLM la lea fácilmente
        salida_formateada = []
        for reg in reversed(registros): # Los revertimos para que el LLM lea la historia en orden cronológico
            salida_formateada.append(f"[{reg[0]}] Evento: {reg[1]}, Detalle: '{reg[2]}', Activo ID: {reg[3]}")
            
        return "\n".join(salida_formateada)
    except Exception as e:
        return f"Error al obtener registros recientes: {e}"
    finally:
        conn.close()

# En src/gestor_db.py (Añadir al final)

def get_activo_por_id(activo_id):
    """
    Busca un activo por su ID. Útil para obtener la ficha completa de un archivo.
    """
    conn = conectar_db()
    if not conn: return None
    
    try:
        conn.row_factory = sqlite3.Row # Para poder acceder a las columnas por nombre
        cursor = conn.cursor()
        # Seleccionamos todas las columnas, incluyendo el Resumen_Ejecutivo
        cursor.execute("SELECT * FROM Activos WHERE ID_Activo = ?", (activo_id,))
        activo = cursor.fetchone()
        
        if activo:
            # Convertimos la fila a un diccionario para un fácil acceso en Python
            return dict(activo)
        return None
    except Exception as e:
        print(f"Error al buscar activo por ID: {e}")
        return None
    finally:
        conn.close()

# En src/gestor_db.py (Añadir al final)

def get_activo_por_id(activo_id):
    """
    Busca un activo por su ID. Útil para obtener la ficha completa de un archivo.
    """
    conn = conectar_db()
    if not conn: return None
    
    try:
        conn.row_factory = sqlite3.Row # Para poder acceder a las columnas por nombre
        cursor = conn.cursor()
        # Seleccionamos todas las columnas, incluyendo el Resumen_Ejecutivo
        cursor.execute("SELECT * FROM Activos WHERE ID_Activo = ?", (activo_id,))
        activo = cursor.fetchone()
        
        if activo:
            # Convertimos la fila a un diccionario para un fácil acceso en Python
            return dict(activo)
        return None
    except Exception as e:
        print(f"Error al buscar activo por ID: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    # Si ejecutamos este archivo directamente, inicializa la DB.
    inicializar_base_de_datos()

# ---------------------------------------------------------------------------------------------------------------------
