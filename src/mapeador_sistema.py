# src/mapeador_sistema.py
import platform
import psutil
import sqlite3
from pathlib import Path
from src import gestor_db

def obtener_info_sistema():
    """Recopila CPU, RAM, OS y GPU."""
    info = {
        "Sistema": platform.system(),
        "Version": platform.release(),
        "Nombre_PC": platform.node(),
        "CPU": platform.processor(),
        "RAM_Total_GB": round(psutil.virtual_memory().total / (1024**3), 2)
    }
    return info

def registrar_programas_comunes():
    """
    Inserta una base de conocimiento inicial sobre programas comunes.
    El LLM usará esto para saber qué estás haciendo.
    """
    programas = [
        ("acad.exe", "AutoCAD", "Diseño y dibujo técnico 2D/3D", "CAD"),
        ("freecad.exe", "FreeCAD", "Modelado paramétrico 3D Open Source", "CAD"),
        ("blender.exe", "Blender", "Modelado 3D, renderizado y animación", "3D"),
        ("code.exe", "VS Code", "Editor de código y desarrollo", "Dev"),
        ("chrome.exe", "Google Chrome", "Navegador Web", "Internet"),
        ("firefox.exe", "Mozilla Firefox", "Navegador Web", "Internet"),
        ("excel.exe", "Microsoft Excel", "Hojas de cálculo y datos", "Ofimática"),
        ("soffice.bin", "LibreOffice", "Suite ofimática Open Source", "Ofimática"),
    ]
    
    conn = gestor_db.conectar_db()
    cursor = conn.cursor()
    print("Registrando diccionario de programas...")
    for prog in programas:
        try:
            cursor.execute("INSERT OR IGNORE INTO Programas_Conocidos VALUES (?,?,?,?)", prog)
        except:
            pass
    conn.commit()
    conn.close()

def generar_ficha_tecnica_md():
    """Crea el archivo System_Specs.md en la Bóveda."""
    info = obtener_info_sistema()
    ruta_boveda = Path(__file__).parent.parent / "Boveda_MD"
    ruta_boveda.mkdir(exist_ok=True)
    
    contenido = "# Ficha Técnica del PC\n\n"
    for k, v in info.items():
        contenido += f"- **{k}:** {v}\n"
        
    with open(ruta_boveda / "System_Specs.md", "w", encoding="utf-8") as f:
        f.write(contenido)
    
    print("Ficha técnica generada en Boveda_MD/System_Specs.md")

if __name__ == "__main__":
    gestor_db.inicializar_base_de_datos()
    registrar_programas_comunes()
    generar_ficha_tecnica_md()