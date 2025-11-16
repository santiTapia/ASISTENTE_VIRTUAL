# src/utils.py
# Herramientas genéricas que usarán varios scripts.

import hashlib

def calcular_hash_archivo(ruta_archivo):
    """
    Calcula el hash SHA-256 de un archivo.
    Leemos el archivo en "chunks" (trozos) para no agotar la
    RAM si es un archivo muy grande (ej. un vídeo o un .blend).
    """
    h = hashlib.sha256()
    
    try:
        with open(ruta_archivo, 'rb') as file:  # 'rb' = leer en modo binario
            while True:
                # Leemos en trozos de 64kb
                chunk = file.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()  # Devuelve la firma como texto
        
    except FileNotFoundError:
        print(f"Error (hash): Archivo no encontrado en {ruta_archivo}")
        return None
    except PermissionError:
        print(f"Error (hash): No hay permisos para leer {ruta_archivo}")
        return None
    except Exception as e:
        print(f"Error (hash) desconocido en {ruta_archivo}: {e}")
        return None