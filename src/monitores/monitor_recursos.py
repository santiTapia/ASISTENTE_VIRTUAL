# src/monitores/monitor_recursos.py
import psutil
import time
from src import gestor_db

# Umbrales para generar una alerta (ajustables)
UMBRAL_CPU = 85.0
UMBRAL_RAM = 90.0
INTERVALO_CHEQUEO = 10 # Segundos

def obtener_proceso_principal():
    """Identifica el proceso con mayor consumo de CPU."""
    try:
        # psutil.process_iter es portable en Linux y Windows
        # Atributos: CPU, Memoria, Nombre
        procs = sorted(
            (p for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent'])),
            key=lambda p: p.info['cpu_percent'],
            reverse=True
        )
        # Devolvemos el nombre del proceso y su % de CPU
        if procs and procs[0].info['cpu_percent'] > 5.0:
            return procs[0].info['name'], procs[0].info['cpu_percent']
        return "N/A", 0
    except Exception as e:
        print(f"Error al obtener procesos: {e}")
        return "N/A", 0

def iniciar_monitor_recursos():
    print("🚀 Iniciando Monitor de Recursos...")
    while True:
        cpu_uso = psutil.cpu_percent(interval=None)
        ram_uso = psutil.virtual_memory().percent
        proceso_top, cpu_proceso = obtener_proceso_principal()
        
        alerta = False
        contexto = ""

        if cpu_uso > UMBRAL_CPU or ram_uso > UMBRAL_RAM:
            alerta = True
            
            # Generar el mensaje detallado para la DB
            contexto = (
                f"ALERTA_RECURSOS: CPU={cpu_uso:.1f}%, RAM={ram_uso:.1f}%. "
                f"Proceso principal: {proceso_top} ({cpu_proceso:.1f}%)."
            )
            
            # Registrar la alerta en la DB (para que el LLM la lea)
            gestor_db.insertar_registro_accion(
                tipo="ALERTA_RECURSOS", 
                contexto=contexto, 
                id_activo=None
            )
            print(f"🚨 ALERTA REGISTRADA: {contexto}")

        # Aquí irá la lógica futura para pausar el LLM pesado si hay una alerta
        # Por ahora, solo registra.

        time.sleep(INTERVALO_CHEQUEO)

if __name__ == "__main__":
    iniciar_monitor_recursos()