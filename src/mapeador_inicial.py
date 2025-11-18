# src/mapeador_inicial.py
# NO SIRVE AHORA ---------------- APARCADO PARA CUANDO SE NECESITE - SUSTITUIDO POR MAPEADOR INTERACTIVO 17/11/25 -------------------------
# Este script se ejecuta UNA VEZ para escanear tus carpetas
# y poblar la base de datos 'Activos' por primera vez.

from pathlib import Path  # ¡La clave de la portabilidad!
import os
import time

# Importamos nuestras propias herramientas
# (Usamos 'src.' porque estamos dentro de la carpeta 'src')
from src import gestor_db
from src import utils

# --- CONFIGURACIÓN DE SEGURIDAD Y ÁMBITO ---

# 1. RAÍCES DE BÚSQUEDA (¡PORTÁTIL!)
# Aquí definimos DÓNDE buscar. Usamos Path.home() para
# que funcione en Windows (C:\Users\santi) y Linux (/home/santi)
CARPETAS_RAIZ_A_ESCANEAR = [
    Path.home() / "Documents",
    Path.home() / "Desktop",
    Path.home() / "Downloads"
    # Añade aquí más carpetas raíz si lo necesitas
    # Path("C:/Proyectos") # Ejemplo de ruta absoluta si es necesario
]

# 2. BLACKLIST DE CARPETAS (SEGURIDAD Y RUIDO)
# Nombres de carpetas que ignoraremos SIEMPRE.
CARPETAS_IGNORADAS = {
    ".venv", "__pycache__", "node_modules", ".git",
    "AppData", "Application Data", "$Recycle.Bin"
}

# 3. BLACKLIST DE EXTENSIONES (SEGURIDAD Y RUIDO)
EXTENSIONES_IGNORADAS = {
    ".tmp", ".log", ".dll", ".sys", ".ini", ".exe", ".msi",
    ".lnk", ".key", ".pem", ".token", ".env" # Seguridad
}

# --- FIN DE LA CONFIGURACIÓN ---


def mapear_carpetas_raiz():
    """
    Función principal que recorre las carpetas raíz y procesa cada archivo.
    """
    print("Iniciando mapeo inicial de activos...")
    archivos_procesados = 0
    archivos_ignorados = 0

    # Primero, nos aseguramos de que la DB existe
    gestor_db.inicializar_base_de_datos()

    for ruta_raiz in CARPETAS_RAIZ_A_ESCANEAR:
        # Verificamos que la carpeta raíz exista
        if not ruta_raiz.exists():
            print(f"ADVERTENCIA: La carpeta raíz '{ruta_raiz}' no existe. Saltando.")
            continue
        
        print(f"--- Escaneando '{ruta_raiz}' ---")
        
        # os.walk es la mejor herramienta para recorrer carpetas recursivamente
        for dirpath, dirnames, filenames in os.walk(str(ruta_raiz)):
            
            # 1. FILTRO DE CARPETAS (SEGURIDAD)
            # Si estamos en una carpeta de la Blacklist, no seguimos
            if any(nombre_carpeta in CARPETAS_IGNORADAS for nombre_carpeta in dirpath.split(os.sep)):
                # print(f"Ignorando carpeta (Blacklist): {dirpath}")
                dirnames[:] = [] # Le decimos a os.walk que no entre en subcarpetas
                filenames[:] = [] # Ignoramos archivos en esta carpeta
                continue

            # 2. PROCESO DE ARCHIVOS
            for filename in filenames:
                
                # Obtenemos la ruta absoluta de forma portátil
                ruta_absoluta_path = Path(dirpath) / filename
                ruta_absoluta_str = str(ruta_absoluta_path)
                
                # 3. FILTRO DE EXTENSIONES (SEGURIDAD/RUIDO)
                extension = ruta_absoluta_path.suffix.lower()
                
                if extension in EXTENSIONES_IGNORADAS:
                    archivos_ignorados += 1
                    continue
                
                # 4. OBTENCIÓN DE DATOS
                # Si el archivo pasa los filtros, obtenemos su "firma"
                hash_archivo = utils.calcular_hash_archivo(ruta_absoluta_path)
                
                if hash_archivo is None:
                    # (utils.py ya habrá impreso el error, ej. 'Permiso denegado')
                    archivos_ignorados += 1
                    continue

                # 5. INSERCIÓN EN LA BASE DE DATOS
                # ¡Aquí usamos la función que creamos antes!
                gestor_db.insertar_o_actualizar_activo(
                    ruta_abs_str = ruta_absoluta_str,
                    tipo_activo = "Archivo", # Podríamos hacerlo más inteligente luego
                    extension = extension,
                    hash_contenido = hash_archivo
                )
                archivos_procesados += 1
                
                if archivos_procesados % 100 == 0:
                    print(f"Procesados {archivos_procesados} archivos...")

    print("--- Mapeo Completado ---")
    print(f"Total de activos procesados/actualizados: {archivos_procesados}")
    print(f"Total de archivos ignorados (Seguridad/Ruido): {archivos_ignorados}")


# Esto permite que ejecutemos este script directamente desde la terminal
if __name__ == "__main__":
    inicio = time.time()
    mapear_carpetas_raiz()
    fin = time.time()
    print(f"El mapeo tomó {fin - inicio:.2f} segundos.")