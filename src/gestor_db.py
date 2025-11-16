# gestor_db.py
# Este script contiene todas las funciones para interactuar con la DB SQLite.

import sqlite3
from pathlib import Path

# Definimos la ruta de la base de datos de forma robusta.
# Path(__file__).parent apunta a 'src/'. .parent otra vez apunta a la raíz del proyecto.
DB_PATH = Path(__file__).parent.parent / "memoria.db" 

# La base de datos ahora SIEMPRE se creará en:
# C:\Users\santi\Desktop\PROYECTOS\Asistente_Local\memoria.db

# Reemplaza la función completa inicializar_base_de_datos() en src/gestor_db.py

def inicializar_base_de_datos():
    """
    Inicializa la conexión y crea las tablas Activos y Registros.
    """
    conn = None
    print(f"Inicializando base de datos en: {DB_PATH}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Tabla Activos (Inventario de archivos)
        print("Creando tabla 'Activos'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Activos (
                ID_Activo INTEGER PRIMARY KEY,
                Ruta_Absoluta TEXT UNIQUE NOT NULL,
                Tipo_Activo TEXT,
                Extension TEXT,
                Hash_Contenido TEXT,
                Etiquetas TEXT,
                Fecha_Creacion_DB DATETIME DEFAULT CURRENT_TIMESTAMP,
                Fecha_Modificacion_DB DATETIME DEFAULT CURRENT_TIMESTAMP,
                Estado_Chroma TEXT DEFAULT 'Pendiente'
            )
        """)
        
        # 2. Tabla Registros (Diario de a Bordo)
        print("Creando tabla 'Registros' (Diario de a Bordo)...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Registros (
                ID_Registro INTEGER PRIMARY KEY,
                ID_Activo INTEGER,
                Tipo_Accion TEXT NOT NULL,
                Detalle TEXT NOT NULL,
                Etiquetas TEXT,
                Fecha_Registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                -- Definimos la relación con Activos (FK)
                FOREIGN KEY (ID_Activo) REFERENCES Activos(ID_Activo)
            )
        """)

        conn.commit()
        print("Base de datos inicializada correctamente.")
    except sqlite3.Error as e:
        print(f"Error al inicializar la base de datos: {e}")
    finally:
        if conn:
            conn.close()

# --- (Aquí irán el resto de funciones: insertar_activo, buscar_registro, etc.) ---

if __name__ == "__main__":
    # Si ejecutamos este archivo directamente, inicializa la DB.
    inicializar_base_de_datos()

# --- HASTA AQUI CODIGO BASE 0 INICIO, SEGUIDAMENTE; FUNCIONES "BRAZOS" ---

def conectar_db():
    """
    Función de ayuda para conectarse a la DB y devolver la conexión.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
    except sqlite3.Error as e:
        print(f"Error de conexión a SQLite: {e}")
    return conn

def get_activo_por_ruta(ruta_abs):
    """
    Busca un activo por su ruta absoluta.
    Devuelve la fila del activo si existe, o None si no existe.
    """
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Activos WHERE Ruta_Absoluta = ?", (ruta_abs,))
            activo = cursor.fetchone()  # fetchone() devuelve una fila o None
            conn.close()
            return activo
        except sqlite3.Error as e:
            print(f"Error al buscar activo por ruta: {e}")
            conn.close()
    return None

def insertar_o_actualizar_activo(ruta_abs_str, tipo_activo, extension, hash_contenido):
    """
    Función inteligente para gestionar un Activo.
    1. Comprueba si el activo (por su ruta) ya existe.
    2. Si NO existe, lo crea.
    3. Si SÍ existe, comprueba si el Hash ha cambiado.
    4. Si el Hash cambió, actualiza el hash y la fecha de modificación.
    """
    conn = conectar_db()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        
        # 1. Comprobar si existe
        cursor.execute("SELECT ID_Activo, Hash_Contenido FROM Activos WHERE Ruta_Absoluta = ?", (ruta_abs_str,))
        activo_existente = cursor.fetchone()

        if activo_existente is None:
            # 2. Si NO existe, lo insertamos
            print(f"Insertando nuevo Activo: {ruta_abs_str}")
            # (Aquí es donde llamaremos al LLM para generar etiquetas)
            etiquetas_ia = "pendiente" # Por ahora, lo dejamos pendiente
            
            cursor.execute("""
                INSERT INTO Activos (Ruta_Absoluta, Tipo_Activo, Extension, Hash_Contenido, Etiquetas, Estado_Chroma)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ruta_abs_str, tipo_activo, extension, hash_contenido, etiquetas_ia, 'Pendiente'))
            
        else:
            # 3. Si SÍ existe, comprobamos el Hash
            id_activo_existente, hash_existente = activo_existente
            
            if hash_existente != hash_contenido:
                # 4. Si el Hash cambió, lo actualizamos
                print(f"Actualizando Activo (hash cambiado): {ruta_abs_str}")
                cursor.execute("""
                    UPDATE Activos
                    SET Hash_Contenido = ?, Fecha_Modificacion_DB = CURRENT_TIMESTAMP, Estado_Chroma = 'Pendiente'
                    WHERE ID_Activo = ?
                """, (hash_contenido, id_activo_existente))
            # else:
                # Si el hash es el mismo, no hacemos nada.
                # print(f"Activo sin cambios: {ruta_abs_str}")
                pass

        conn.commit()
    except sqlite3.Error as e:
        print(f"Error al insertar/actualizar activo: {e}")
    finally:
        conn.close()

# Añadir al final de src/gestor_db.py

def insertar_registro(id_activo, tipo_accion, detalle, etiquetas=None):
    """
    Inserta una entrada en la tabla Registros (Diario de a Bordo).
    """
    conn = conectar_db()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        
        # ID_Activo puede ser NULL al inicio, ya que la conexión la hará el LLM después
        cursor.execute("""
            INSERT INTO Registros (ID_Activo, Tipo_Accion, Detalle, Etiquetas)
            VALUES (?, ?, ?, ?)
        """, (id_activo, tipo_accion, detalle, etiquetas))
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error al insertar registro: {e}")
    finally:
        if conn:
            conn.close()