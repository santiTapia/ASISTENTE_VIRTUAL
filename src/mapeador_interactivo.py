# src/mapeador_interactivo.py
# Versión 2 del mapeador. Este script es INTERACTIVO.
# Te preguntará qué hacer con archivos desconocidos.

from pathlib import Path
import os
import time

# Importamos nuestras propias herramientas
try:
    from src import gestor_db
    from src import utils
except ImportError:
    # Esto es por si lo ejecutamos de forma diferente
    import gestor_db
    import utils

# --- 1. LISTAS DE SEGURIDAD Y ÁMBITO ---

# (Pega aquí las listas CARPETAS_IGNORADAS, EXTENSIONES_IGNORADAS
# y EXTENSIONES_PERMITIDAS que definimos arriba)

from src.config_scanner import CARPETAS_RAIZ_A_ESCANEAR, CARPETAS_IGNORADAS, EXTENSIONES_IGNORADAS, EXTENSIONES_PERMITIDAS

# --- 3. LÓGICA DEL "PUESTO DE CONTROL" ---
# Este diccionario guardará tus decisiones para no preguntarte 1000 veces por la misma extensión (ej. .pdf)

DECISIONES_CACHE = {}

def manejar_decision_archivo(ruta_path, extension):
    """
    El "Puesto de Control" interactivo.
    Se activa cuando una extensión no es conocida.
    """
    # Primero, revisamos si ya hemos tomado una decisión para esta extensión
    if extension in DECISIONES_CACHE:
        return DECISIONES_CACHE[extension] # 'procesar_siempre' o 'ignorar_siempre'

    print("\n" + "="*50)
    print("🚦 PUESTO DE CONTROL 🚦")
    print(f"He encontrado un archivo con una extensión desconocida:")
    print(f"  Archivo: {ruta_path}")
    print(f"  Extensión: {extension}")
    print("\n¿Qué quieres hacer?")
    print("---")
    print("[1] Indexar (Solo este archivo)")
    print("    (Se añadirá a la DB memoria.db para que el asistente lo conozca)")
    print("[2] Ignorar (Solo este archivo)")
    print("    (No se tocará. El asistente nunca sabrá que existe)")
    print("---")
    print("[3] Indexar SIEMPRE (Todos los archivos '*.{ext}')".format(ext=extension[1:]))
    print("    (Añade esta extensión a la 'Whitelist' para el resto del escaneo)")
    print("[4] Ignorar SIEMPRE (Todos los archivos '*.{ext}')".format(ext=extension[1:]))
    print("    (Añade esta extensión a la 'Blacklist' para el resto del escaneo)")
    
    while True:
        choice = input(f"Tu decisión para '{extension}' (1-4): ")
        
        if choice == '1':
            return 'procesar_una_vez'
        elif choice == '2':
            return 'ignorar_una_vez'
        elif choice == '3':
            # Guardamos la decisión en caché y procesamos esta vez
            DECISIONES_CACHE[extension] = 'procesar_siempre'
            print(f"✅ OK. Todos los archivos '{extension}' se procesarán.")
            return 'procesar_siempre'
        elif choice == '4':
            # Guardamos la decisión en caché e ignoramos esta vez
            DECISIONES_CACHE[extension] = 'ignorar_siempre'
            print(f"❌ OK. Todos los archivos '{extension}' se ignorarán.")
            return 'ignorar_siempre'
        else:
            print("Opción no válida. Por favor, introduce un número del 1 al 4.")

def procesar_archivo_en_db(ruta_path, ruta_str, extension):
    """
    Función de ayuda para hashear e insertar/actualizar el activo.
    """
    hash_archivo = utils.calcular_hash_archivo(ruta_path)
    if hash_archivo:
        gestor_db.insertar_o_actualizar_activo(
            ruta_abs_str = ruta_str,
            tipo_activo = "Archivo", # TODO: Inferir mejor el tipo
            extension = extension,
            hash_contenido = hash_archivo
        )
        return 1 # 1 archivo procesado
    return 0 # 0 archivos procesados (error de hash)

def mapear_carpetas_raiz_interactivo():
    """
    Función principal que recorre las carpetas raíz
    y usa el "Puesto de Control".
    """
    print("Iniciando mapeo INTERACTIVO de activos...")
    archivos_procesados = 0
    archivos_ignorados = 0

    gestor_db.inicializar_base_de_datos()

    for ruta_raiz in CARPETAS_RAIZ_A_ESCANEAR:
        if not ruta_raiz.exists():
            print(f"ADVERTENCIA: La carpeta raíz '{ruta_raiz}' no existe. Saltando.")
            continue
        
        print(f"--- Escaneando '{ruta_raiz}' ---")
        
        for dirpath, dirnames, filenames in os.walk(str(ruta_raiz), topdown=True):
            
            # 1. FILTRO DE CARPETAS (BLACKLIST)
            # Comparamos los nombres de las carpetas en la ruta actual
            partes_ruta = set(Path(dirpath).parts)
            if not CARPETAS_IGNORADAS.isdisjoint(partes_ruta):
                # print(f"Ignorando carpeta (Blacklist): {dirpath}")
                dirnames[:] = [] # No entrar en subcarpetas
                filenames[:] = [] # Ignorar archivos aquí
                continue

            for filename in filenames:
                
                ruta_absoluta_path = Path(dirpath) / filename
                ruta_absoluta_str = str(ruta_absoluta_path)
                extension = ruta_absoluta_path.suffix.lower()

                # Ignorar archivos sin extensión
                if not extension:
                    archivos_ignorados += 1
                    continue
                
                # 2. FILTRO DE EXTENSIONES (BLACKLIST)
                if extension in EXTENSIONES_IGNORADAS:
                    archivos_ignorados += 1
                    continue
                
                # (Pequeño ajuste para ignorar temporales de Office)
                if filename.startswith("~$"):
                    archivos_ignorados += 1
                    continue
                
                # 3. FILTRO DE EXTENSIONES (WHITELIST)
                if extension in EXTENSIONES_PERMITIDAS:
                    # Procesar en silencio
                    archivos_procesados += procesar_archivo_en_db(ruta_absoluta_path, ruta_absoluta_str, extension)
                    continue

                # 4. PUESTO DE CONTROL (GREYLIST / DESCONOCIDOS)
                # Si llegamos aquí, no es Blacklist ni Whitelist
                decision = manejar_decision_archivo(ruta_absoluta_path, extension)
                
                if decision in ('procesar_una_vez', 'procesar_siempre'):
                    archivos_procesados += procesar_archivo_en_db(ruta_absoluta_path, ruta_absoluta_str, extension)
                else:
                    # (decisión es 'ignorar_una_vez' o 'ignorar_siempre')
                    archivos_ignorados += 1

    print("--- Mapeo Completado ---")
    print(f"Total de activos procesados/actualizados: {archivos_procesados}")
    print(f"Total de archivos ignorados (Seguridad/Ruido): {archivos_ignorados}")


# --- EJECUCIÓN ---
if __name__ == "__main__":
    inicio = time.time()
    mapear_carpetas_raiz_interactivo()
    fin = time.time()
    print(f"El mapeo tomó {fin - inicio:.2f} segundos.")
    print("\nDecisiones tomadas en esta sesión:")
    print(DECISIONES_CACHE)