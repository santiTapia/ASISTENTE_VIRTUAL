# src/gestor_ollama.py
import requests
import json
from src import gestor_db
from pathlib import Path

# --- CONFIGURACIÓN DE MODELOS (Necesitarás tener Ollama corriendo) ---
URL_OLLAMA = "http://localhost:11434/api/generate"
MODELO_LIGERO = "mistral:latest" # Ejemplo de 7B/8B
MODELO_PESADO = "mixtral:latest" # Ejemplo de 24B/70B

# --- RUTAS DE CONTEXTO ---
RUTA_SISTEMA_SPECS = Path(__file__).parent.parent / "Boveda_MD" / "System_Specs.md"

def obtener_contexto_llm(tipo_consulta, activo_id=None):
    """
    Ensambla el contexto completo: Global + Específico.
    """
    contexto_global = ""
    # 1. Leer la "Pre-memoria" (Ficha Técnica del PC)
    if RUTA_SISTEMA_SPECS.exists():
        contexto_global = RUTA_SISTEMA_SPECS.read_text(encoding="utf-8")
    
    # 2. Obtener Historial de Registros
    # (Futura función que busca las últimas 20 acciones del usuario en la DB)
    historial_reciente = gestor_db.obtener_registros_recientes(limite=10) # Aún por definir en gestor_db.py
    
    # 3. Obtener Datos del Activo Específico (si aplica)
    contexto_activo = ""
    if activo_id:
        activo = gestor_db.get_activo_por_id(activo_id) # Aún por definir en gestor_db.py
        if activo:
            # Aquí iría el código RAG para buscar los chunks relevantes
            contexto_activo = f"Activo en Foco: {activo['Nombre_Archivo']} | Resumen: {activo['Resumen_Ejecutivo']}"

    return f"FICHA TÉCNICA:\n{contexto_global}\n\nHISTORIAL RECIENTE:\n{historial_reciente}\n\nFOCO ACTUAL:\n{contexto_activo}"

def llm_query(prompt, modelo):
    """Función genérica para hacer la llamada a Ollama."""
    try:
        payload = {
            "model": modelo,
            "prompt": prompt,
            "stream": False # Usamos modo síncrono por ahora
        }
        response = requests.post(URL_OLLAMA, json=payload, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        return data['response']
        
    except requests.exceptions.RequestException as e:
        return f"Error de conexión con Ollama ({modelo}): {e}"
        
def llm_ligero_query(prompt, activo_id=None):
    """Consulta rápida para triage y comandos."""
    contexto = obtener_contexto_llm("ligero", activo_id)
    prompt_final = f"Contexto: {contexto}\n\nInstrucción: {prompt}"
    return llm_query(prompt_final, MODELO_LIGERO)

def llm_pesado_query(prompt, activo_id):
    """
    Consulta pesada para RAG e indexación.
    Aquí iría la lógica para consultar al monitor de recursos antes de llamar.
    """
    # Lógica de seguridad: Si monitor_recursos dice que el PC está ocupado, espera.
    # Por ahora, solo llama.
    
    contexto = obtener_contexto_llm("pesado", activo_id)
    prompt_final = f"Contexto Detallado para RAG: {contexto}\n\nInstrucción Rigurosa: {prompt}"
    return llm_query(prompt_final, MODELO_PESADO)
    
if __name__ == "__main__":
    # Prueba simple:
    print(llm_ligero_query("¿Cuál es el modelo de lenguaje que estás utilizando ahora?"))