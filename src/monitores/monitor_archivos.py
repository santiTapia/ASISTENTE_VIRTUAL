# src/monitores/monitor_archivos.py
# ATENCIÓN: NO EJECUTAR ESTE SCRIPT HASTA DESPUÉS DEL MAPEO INICIAL.
# Este es el "Vigilante" en tiempo real que mantiene la DB actualizada.

import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

# Importamos nuestras herramientas
try:
    from src import gestor_db
    from src import utils
    from src.config_scanner import (
        CARPETAS_RAIZ_A_ESCANEAR, 
        CARPETAS_IGNORADAS, EXTENSIONES_IGNORADAS,
        EXTENSIONES_PERMITIDAS
    )
    
except ImportError:
    # Fallback por si la ruta de importación falla
    import gestor_db
    import utils
    # Necesitamos las mismas listas de seguridad

def estimar_tokens(ruta_archivo):
    """Calcula el peso en tokens solo para archivos permitidos."""
    try:
        path_obj = Path(ruta_archivo)
        ext = path_obj.suffix.lower()
        
        # 1. Solo calcular si la extensión está en la lista de PERMITIDAS
        if ext not in EXTENSIONES_PERMITIDAS:
            return 0 
        
        # 2. Si es una extensión permitida, estimar el peso
        tamano = os.path.getsize(ruta_archivo)
        return int(tamano / 4) # Regla: 1 token ~= 4 caracteres
    except:
        return 0

class GestorEventosHandler(FileSystemEventHandler):
    # ... (El método __init__ y es_ruta_segura se mantienen igual) ...
    def __init__(self):
        super().__init__()
        self.carpetas_ignoradas = CARPETAS_IGNORADAS
        self.extensiones_ignoradas = EXTENSIONES_IGNORADAS

    def es_ruta_segura(self, ruta_str):
        # ... (Usa la versión corregida que te di antes) ...
        ruta_path = Path(ruta_str)
        extension = ruta_path.suffix.lower()
        filename = ruta_path.name

        # CRITERIO DE PORTABILIDAD: Ignorar archivos temporales (Windows/Linux)
        if (extension in self.extensiones_ignoradas or 
            filename.startswith("~$") or      # Windows Office temps
            filename.startswith("~") or       # Otros bloqueos de Windows
            filename.startswith(".")):        # Archivos ocultos/temporales en Linux/macOS
            return False
    
        partes_ruta = set(Path(ruta_str).parts)
        if not self.carpetas_ignoradas.isdisjoint(partes_ruta): return False
        return True

    def procesar_evento(self, ruta_str, tipo_evento):
        if not self.es_ruta_segura(ruta_str): return

        path_obj = Path(ruta_str)
        if not path_obj.exists(): return # Si fue borrado muy rápido

        print(f"Monitor: {tipo_evento} -> {path_obj.name}")
        
        # 1. Calcular datos extendidos
        hash_val = utils.calcular_hash_archivo(path_obj)
        peso = os.path.getsize(path_obj)
        tokens = estimar_tokens(path_obj)
        
        # 2. Insertar en Activos (Inventario)
        if hash_val:
            gestor_db.insertar_activo_completo(
                ruta=ruta_str,
                nombre=path_obj.name,
                ext=path_obj.suffix.lower(),
                peso=peso,
                tokens_est=tokens,
                hash_val=hash_val
            )
            
            # 3. Registrar la Acción (Diario de a Bordo) - Buscamos el ID recién creado/actualizado para vincularlo
            activo = gestor_db.get_activo_por_ruta(ruta_str)
            if activo:
                id_activo = activo[0] # Asumiendo que ID es la primera columna
                gestor_db.insertar_registro_accion(
                    tipo=f"ARCHIVO_{tipo_evento}", # CREADO o MODIFICADO
                    contexto=path_obj.name,
                    id_activo=id_activo
                )

    def on_created(self, event):
        if not event.is_directory: self.procesar_evento(event.src_path, "CREADO")

    def on_modified(self, event):
        if not event.is_directory: self.procesar_evento(event.src_path, "MODIFICADO")

# Añade el bloque if __name__ == "__main__" para probarlo
if __name__ == "__main__":
    # iniciar_monitor_archivos() # Descomentar para probar
    pass