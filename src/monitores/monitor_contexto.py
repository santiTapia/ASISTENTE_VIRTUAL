# src/monitores/monitor_contexto.py
# Este script vigila la ventana activa y registra el contexto en la DB.

import time
import pygetwindow as gw # Librería para obtener la ventana activa

# Importamos las herramientas de la base de datos
try:
    from src import gestor_db
except ImportError:
    # Fallback si se ejecuta de forma independiente
    import gestor_db 

# Tiempo de espera entre comprobaciones (en segundos).
# Un valor bajo es más preciso, un valor alto consume menos CPU.
TIEMPO_ENTRE_CHEQUEOS = 5

def obtener_ventana_activa():
    """
    Obtiene el título de la ventana activa del sistema.
    """
    try:
        # Intenta obtener la ventana en primer plano (funciona en la mayoría de OS)
        ventana = gw.get_active_window()
        
        if ventana:
            # Filtramos títulos inútiles (ej. la barra de tareas o el escritorio)
            titulo = ventana.title
            if titulo and titulo.strip() not in ["", "Desktop", "Program Manager"]:
                return titulo.strip()
                
    except Exception as e:
        # print(f"Error al obtener ventana activa: {e}")
        pass
        
    return "DESCONOCIDO o INACTIVO"

def iniciar_monitor_contexto():
    """
    Bucle principal del monitor de contexto.
    """
    print("Iniciando monitor de contexto...")
    ultimo_titulo = ""
    
    # Nos aseguramos de que la DB esté lista antes de empezar
    gestor_db.inicializar_base_de_datos()

    try:
        while True:
            titulo_actual = obtener_ventana_activa()
            
            # Solo registramos si el título ha cambiado (la acción ha cambiado)
            if titulo_actual and titulo_actual != ultimo_titulo:
                
                print(f"Contexto cambiado: -> {titulo_actual}")
                
                # 1. Insertamos el nuevo registro en la DB
                gestor_db.insertar_registro_accion(
                    tipo='FOCO_VENTANA', # Acción clave para el asistente
                    contexto=titulo_actual,
                    id_activo=None # Lo dejamos en NULL. El LLM lo vinculará después.
                )
                
                # 2. Actualizamos el último título
                ultimo_titulo = titulo_actual
            
            # Esperamos para reducir el consumo de CPU
            time.sleep(TIEMPO_ENTRE_CHEQUEOS)

    except KeyboardInterrupt:
        print("\nMonitor de Contexto detenido por el usuario.")
    except Exception as e:
        print(f"Error crítico en monitor_contexto: {e}")


if __name__ == "__main__":
    # Si ejecutamos este archivo directamente para probarlo:
    iniciar_monitor_contexto()