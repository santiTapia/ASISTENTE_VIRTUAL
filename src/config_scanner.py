# src/config_scanner.py
from pathlib import Path

# --- 1. RUTAS RAÍZ A ESCANEAR (Dinamismo PC Trabajo vs Casa) ---
# Puedes comentar/descomentar según el PC donde estés, o añadir lógica
# para detectar el nombre del PC.

CARPETAS_RAIZ_A_ESCANEAR = [
    Path.home() / "Desktop",
    Path.home() / "Downloads",
    Path("C:/escaner"),
    # Rutas específicas de tu trabajo (OJO: Verifica que la unidad G: existe)
    Path("G:/.shortcut-targets-by-id/1-hEFmLDxi7ep0x5rdxfSq4hpV6YEOQOM/CARPETA PROYECTOS WP/2022/22_0001 AMARE NOVO SANTI PETRI/15 SEGURIDAD Y SALUD/09 CONTROL HORARIO"),
    Path("G:/.shortcut-targets-by-id/1-hEFmLDxi7ep0x5rdxfSq4hpV6YEOQOM/CARPETA PROYECTOS WP/2022/22_0001 AMARE NOVO SANTI PETRI/15 SEGURIDAD Y SALUD/18 UNIFORMIDAD"),
    Path("G:/.shortcut-targets-by-id/1-hEFmLDxi7ep0x5rdxfSq4hpV6YEOQOM/CARPETA PROYECTOS WP/2022/22_0001 AMARE NOVO SANTI PETRI/23 AUXILIAR")
]

# --- 2. BLACKLIST DE CARPETAS (Ignorar SIEMPRE) ---
CARPETAS_IGNORADAS = {
    # -- WINDOWS --
    "Windows", "Program Files", "Program Files (x86)", "ProgramData",
    "AppData", "Local Settings", "Application Data",
    "$Recycle.Bin", "System Volume Information", "Recovery", "Config.Msi",
    "PerfLogs", "Microsoft", "!WGUA.Bin",
    
    # -- LINUX (Portabilidad) --
    "usr", "bin", "etc", "var", "proc", "sys", "dev", "run", "snap",
    ".config", ".local", ".cache", ".gnupg", ".ssh",
    
    # -- DESARROLLO / GIT --
    ".venv", "venv", "env", "__pycache__", "node_modules", ".git", ".vscode", 
    ".idea", "build", "dist", "target", "bower_components", "jspm_packages",
    
    # -- OTROS / NUBE / CACHÉ --
    ".dropbox.cache", ".stversions", "Temp", "tmp", "cache", "thumbnails",
    "Cache", "Code Cache", "GPUCache"
}

# --- 3. BLACKLIST DE EXTENSIONES (Ignorar SIEMPRE) ---
EXTENSIONES_IGNORADAS = {
    # -- SEGURIDAD (Claves y Secretos) --
    ".key", ".pem", ".token", ".env", ".secret", ".pfx", ".crt", ".cer",
    "id_rsa", "known_hosts", ".htpasswd", ".netrc",
    
    # -- SISTEMA / BINARIOS / EJECUTABLES --
    ".dll", ".sys", ".exe", ".msi", ".bat", ".sh", ".com", ".vbs", ".cmd",
    ".lnk", ".ini", ".dat", ".bin", ".iso", ".vmdk", ".vdi", ".img",
    ".reg", ".rec", ".pf", ".swp", ".class", ".backup", ".p12", ".user", ".vsidx", 
    ".v2", ".sln", ".pdb", ".cache", ".settings", ".up2date", ".dpb", ".cat", 
    ".inf", ".gpd", ".cfg"
    
    # -- BASES DE DATOS (Evitar bucles) --
    ".db", ".sqlite", ".sqlite3", ".mdb", ".accdb", ".db-journal", ".ldb",
    
    # -- CACHÉ / TEMPORALES / LOGS --
    ".tmp", ".log", ".temp", ".swp", ".bak", ".old", "thumbs.db", "desktop.ini",
    ".ds_store", # Mac
    "~$", # Temporales de Office (prefijo)
    
    # -- PYTHON COMPILADO --
    ".pyc", ".pyo", ".pyd",
    
    # -- CAD (Archivos de Bloqueo - ¡IMPORTANTE!) --
    ".dwl", ".dwl2", # Archivos de lock de AutoCAD, son ruido puro.
    ".bak", ".sv$",  # Backups automáticos de CAD (pueden llenar el disco)

    # -- MULTIMEDIA --
    ".3g2", ".3gp", ".mp4", ".mpeg", ".mpg", ".flv", ".avi", ".wma", ".wmv",
    
    # -- OTROS --
    ".err", ".rdp", ".gp3", ".gp", ".lock",
}

# --- 4. WHITELIST DE EXTENSIONES (Procesar SIEMPRE) ---
EXTENSIONES_PERMITIDAS = {
    # -- CONOCIMIENTO / TEXTO --
    ".md", ".txt", ".rst", ".adoc",
    
    # -- CÓDIGO --
    ".py", ".json", ".toml", ".css", ".html", ".js", ".ts", ".sql", ".xml", ".yaml", ".yml",
    ".c", ".cpp", ".cs", ".java", ".config", ".ico", ".resx", ".csproj", ".props", ".targets",
    
    # -- CAD / 3D --
    ".fcstd", ".blend", ".dwg", ".dxf", ".rvt", ".rfa", ".ifc", ".stl", ".obj",
    ".pc3", ".ctb", ".pzh", ".3dm", ".sat", ".skp",
    
    # -- IMÁGENES (Activos visuales) --
    ".svg", ".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff",

    # -- MULTIMEDIA -- 
    ".aep", ".ai", ".aif", ".ait", ".eps", ".exif", ".jpe", ".gif",
    
    # -- OFIMÁTICA --
    ".ods", ".odt", ".odp", ".eml", ".mbox", ".xlsx", ".docx", ".pptx", ".pdf", ".csv",
    ".docb", ".docm", ".dotm", ".dotx", ".potm", ".potx", ".ppam", ".ppsm", ".ppsx", 
    ".pptm", ".rtf", ".text", ".wps", ".xls", ".xlsb", ".xlsm", ".xltm", ".xltx",

    # -- COMPRESIÓN ARCHIVOS -- 
     ".7z", ".rar",
}