# src/monitores/monitor_archivos.py
# ATENCIÓN: NO EJECUTAR ESTE SCRIPT HASTA DESPUÉS DEL MAPEO INICIAL.
# Este es el "Vigilante" en tiempo real que mantiene la DB actualizada.

import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

# Importamos nuestras herramientas
try:
    from src import gestor_db
    from src import utils
    from src.mapeador_interactivo import CARPETAS_RAIZ_A_ESCANEAR, CARPETAS_IGNORADAS, EXTENSIONES_IGNORADAS
except ImportError:
    # Fallback por si la ruta de importación falla
    import gestor_db
    import utils
    # Necesitamos las mismas listas de seguridad

    CARPETAS_RAIZ_A_ESCANEAR = [
    Path.home() / "Documentos",
    Path.home() / "Escritorio",
    Path.home() / "Descargas",
    Path("C:/escaner"),
    Path("G:/.shortcut-targets-by-id/1-hEFmLDxi7ep0x5rdxfSq4hpV6YEOQOM/CARPETA PROYECTOS WP/2022/22_0001 AMARE NOVO SANTI PETRI/15 SEGURIDAD Y SALUD/09 CONTROL HORARIO"),
    Path("G:/.shortcut-targets-by-id/1-hEFmLDxi7ep0x5rdxfSq4hpV6YEOQOM/CARPETA PROYECTOS WP/2022/22_0001 AMARE NOVO SANTI PETRI/15 SEGURIDAD Y SALUD/18 UNIFORMIDAD"),
    Path("G:/.shortcut-targets-by-id/1-hEFmLDxi7ep0x5rdxfSq4hpV6YEOQOM/CARPETA PROYECTOS WP/2022/22_0001 AMARE NOVO SANTI PETRI/23 AUXILIAR")
    ]
    CARPETAS_IGNORADAS = {".venv", "AppData"}
    EXTENSIONES_IGNORADAS = {".tmp", ".log"}

class GestorEventosHandler(FileSystemEventHandler):
    """
    Clase que define qué hacer cuando Watchdog detecta un evento.
    """

    def __init__(self):
        super().__init__()
        # Usamos las listas de seguridad del mapeador
        self.carpetas_ignoradas = CARPETAS_IGNORADAS
        self.extensiones_ignoradas = EXTENSIONES_IGNORADAS

    def es_ruta_segura(self, ruta_str):
        """
        Comprueba si una ruta está en la Blacklist de carpetas o extensiones.
        """
        ruta_path = Path(ruta_str)
        
        # 1. Comprobar extensiones y nombre de archivo
        extension = ruta_path.suffix.lower()
        filename = ruta_path.name # 👈 ¡La corrección! Obtenemos el nombre aquí.
        
        # Ignoramos la extensión y los temporales de Office
        if extension in self.extensiones_ignoradas or filename.startswith("~$"):
            return False
            
        # 2. Comprobar carpetas
        partes_ruta = set(Path(ruta_str).parts)
        if not self.carpetas_ignoradas.isdisjoint(partes_ruta):
            return False
            
        return True

    def on_created(self, event):
        """
        Se llama cuando un archivo o carpeta es creado.
        """
        if event.is_directory or not self.es_ruta_segura(event.src_path):
            return
            
        print(f"Monitor: Archivo CREADO detectado: {event.src_path}")
        # Lógica para añadir a la DB
        ruta_str = str(event.src_path)
        hash_archivo = utils.calcular_hash_archivo(ruta_str)
        if hash_archivo:
            gestor_db.insertar_o_actualizar_activo(
                ruta_abs_str=ruta_str,
                tipo_activo="Archivo",
                extension=Path(ruta_str).suffix.lower(),
                hash_contenido=hash_archivo
            )
        # TODO: Añadir lógica de "Caja Fuerte" aquí

    def on_modified(self, event):
        """
        Se llama cuando un archivo es modificado.
        """
        if event.is_directory or not self.es_ruta_segura(event.src_path):
            return

        print(f"Monitor: Archivo MODIFICADO detectado: {event.src_path}")
        # Es la misma función, ya que "insertar_o_actualizar" actualiza el hash
        ruta_str = str(event.src_path)
        hash_archivo = utils.calcular_hash_archivo(ruta_str)
        if hash_archivo:
            gestor_db.insertar_o_actualizar_activo(
                ruta_abs_str=ruta_str,
                tipo_activo="Archivo",
                extension=Path(ruta_str).suffix.lower(),
                hash_contenido=hash_archivo
            )
        # TODO: Añadir lógica de "Caja Fuerte" (versionado)

    def on_deleted(self, event):
        """
        Se llama cuando un archivo o carpeta es eliminado.
        """
        if event.is_directory or not self.es_ruta_segura(event.src_path):
            return
            
        print(f"Monitor: Archivo ELIMINADO detectado: {event.src_path}")
        # TODO: Crear una función en gestor_db.py para "desactivar" un activo
        # gestor_db.desactivar_activo_por_ruta(event.src_path)
        pass

    def on_moved(self, event):
        """
        Se llama cuando un archivo o carpeta es renombrado o movido.
        """
        if event.is_directory or not self.es_ruta_segura(event.dest_path):
            return
            
        print(f"Monitor: Archivo MOVIDO/RENOMBRADO: {event.src_path} -> {event.dest_path}")
        # TODO: Crear una función en gestor_db.py para "actualizar_ruta_activo"
        # gestor_db.actualizar_ruta_activo(event.src_path, event.dest_path)
        pass

def iniciar_monitor_archivos():
    """
    Función principal para configurar e iniciar los observadores de Watchdog.
    """
    print("Iniciando monitor de archivos en tiempo real...")
    event_handler = GestorEventosHandler()
    observer = Observer()
    
    # Creamos un observador para CADA carpeta raíz
    for ruta_raiz in CARPETAS_RAIZ_A_ESCANEAR:
        if ruta_raiz.exists():
            observer.schedule(event_handler, str(ruta_raiz), recursive=True)
            print(f"Vigilando -> {ruta_raiz}")
        else:
            print(f"ADVERTENCIA: No se puede vigilar '{ruta_raiz}'. No existe.")

    observer.start()
    try:
        while True:
            # Mantenemos el script vivo, durmiendo
            time.sleep(60) # Comprueba estado cada minuto
    except KeyboardInterrupt:
        # Si paramos el script (Ctrl+C)
        observer.stop()
    observer.join()

if __name__ == "__main__":
    print("Este script no debe ejecutarse directamente.")
    print("El 'main.py' (Orquestador) será el encargado de lanzarlo.")
    # iniciar_monitor_archivos() # No lo iniciamos por defecto