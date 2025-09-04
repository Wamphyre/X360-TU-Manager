import subprocess
import re
import os
import platform
import sys

# Detect XexTool.exe path regardless of case sensitivity
def encontrar_xextool():
    # Get the directory where this script is running from
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        base_dir = sys._MEIPASS
    else:
        # Running as normal Python script
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check multiple possible locations
    possible_paths = [
        # PyInstaller _internal directory
        os.path.join(base_dir, "xextool", "XexTool.exe"),
        # Current directory
        os.path.join("xextool", "XexTool.exe"),
        os.path.join("XexTool", "XexTool.exe"),
        # Relative to script location
        os.path.join(base_dir, "..", "xextool", "XexTool.exe"),
    ]
    
    for posible in possible_paths:
        if os.path.exists(posible):
            return os.path.abspath(posible)
    
    raise FileNotFoundError("XexTool.exe not found")

# Lazy cache for XexTool path
XEXTOOL_PATH_CACHE = None

def get_xextool_path():
    global XEXTOOL_PATH_CACHE
    if XEXTOOL_PATH_CACHE and os.path.exists(XEXTOOL_PATH_CACHE):
        return XEXTOOL_PATH_CACHE
    XEXTOOL_PATH_CACHE = encontrar_xextool()
    return XEXTOOL_PATH_CACHE

def obtener_media_id(ruta_xex):
    """Get only MediaID (function kept for compatibility)"""
    info = obtener_info_juego(ruta_xex)
    return info["media_id"] if info else None

def obtener_info_juego(ruta_xex):
    """Get MediaID and TitleID from XEX file"""
    # Auto-detect operating system and build appropriate command
    system = platform.system().lower()
    
    try:
        xextool_path = get_xextool_path()
    except FileNotFoundError:
        print("[ERROR] XexTool.exe not found. Place it under xextool/ and retry.")
        return None

    if system == "windows":
        # Windows: Run XexTool.exe natively
        cmd = [xextool_path, "-l", ruta_xex]
        print(f"[INFO] Running on Windows - executing XexTool natively")
    else:
        # Linux/macOS: Use Wine to run XexTool.exe
        cmd = ["wine", xextool_path, "-l", ruta_xex]
        print(f"[INFO] Running on {system.title()} - using Wine to execute XexTool")
    
    try:
        salida = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        texto = salida.decode(errors="ignore")
        
        # Search for MediaID
        media_match = re.search(r"Media ID:\s*([0-9A-F]{8})", texto, re.IGNORECASE)
        media_id = media_match.group(1).upper() if media_match else None
        
        # Search for TitleID
        title_match = re.search(r"Title ID:\s*([0-9A-F]{8})", texto, re.IGNORECASE)
        title_id = title_match.group(1).upper() if title_match else None
        
        if media_id or title_id:
            return {
                "media_id": media_id,
                "title_id": title_id
            }
            
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Running xextool: {e.output.decode(errors='ignore')}")
        if system != "windows":
            print(f"[ERROR] Make sure Wine is installed on {system.title()}")
    except FileNotFoundError as e:
        if system != "windows":
            print(f"[ERROR] Wine not found. Please install Wine on {system.title()}")
        else:
            print(f"[ERROR] XexTool.exe not found or not executable on Windows")
    return None
