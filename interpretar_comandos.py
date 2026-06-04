# ~/.telegram_bot_skills/interpretar_comandos.py
"""
Skill para interpretar y EJECUTAR comandos complejos en lenguaje natural
"""

import re
import subprocess
import os

# Directorio base para operaciones seguras
BASE_DIR = os.path.expanduser("~")

def ejecutar_comando_seguro(comando):
    """Ejecuta comando con validación"""
    try:
        # Verificar que no salga del directorio base
        if ".." in comando and not comando.startswith("cd"):
            return "❌ No se permite salir del directorio base"
        
        resultado = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if resultado.returncode == 0:
            salida = resultado.stdout or "✅ Comando ejecutado correctamente"
            return f"✅ **Ejecutado:** `{comando}`\n```\n{salida[:500]}\n```"
        else:
            error = resultado.stderr or "Error desconocido"
            return f"❌ **Error en:** `{comando}`\n```\n{error[:500]}\n```"
    except subprocess.TimeoutExpired:
        return "⏰ El comando tardó demasiado"
    except Exception as e:
        return f"❌ Error: {e}"

def match(texto):
    """Detecta comandos para ejecutar automáticamente"""
    texto = texto.lower()
    
    # Comandos que queremos ejecutar automáticamente
    comandos_auto = [
        "crea carpeta", "crea directorio", "nueva carpeta",
        "borra archivo", "elimina archivo", "elimina carpeta",
        "mueve", "copia", "renombra"
    ]
    
    # Si el usuario está escribiendo un comando manual (empieza con mkdir, rm, etc.)
    if texto.startswith(("mkdir", "rm", "cp", "mv", "touch", "cat >")):
        return True
    
    return any(c in texto for c in comandos_auto)

def run(texto, contexto):
    """Ejecuta el comando automáticamente"""
    texto_lower = texto.lower()
    
    # Si el usuario ya escribió un comando (empieza con mkdir, rm, etc.)
    if texto_lower.startswith(("mkdir", "rm", "cp", "mv", "touch")):
        # Ejecutar directamente
        return ejecutar_comando_seguro(texto)
    
    # ===== CREAR CARPETA =====
    if any(p in texto_lower for p in ["crea carpeta", "crea directorio", "nueva carpeta"]):
        # Extraer nombre de la carpeta
        nombre = texto_lower
        for p in ["crea carpeta", "crea directorio", "nueva carpeta", "la carpeta", "el directorio"]:
            nombre = nombre.replace(p, "")
        nombre = nombre.strip()
        
        # Limpiar nombre (quitar comillas, espacios)
        nombre = nombre.strip('"').strip("'").strip()
        
        if not nombre:
            return "❌ ¿Qué nombre quieres para la carpeta?"
        
        # Si no tiene ruta, crear en ~/
        if not nombre.startswith("/") and not nombre.startswith("~/"):
            ruta = os.path.expanduser(f"~/{nombre}")
        else:
            ruta = os.path.expanduser(nombre)
        
        comando = f"mkdir -p '{ruta}'"
        return ejecutar_comando_seguro(comando)
    
    # ===== ELIMINAR ARCHIVO/CARPETA =====
    if any(p in texto_lower for p in ["borra archivo", "elimina archivo", "elimina carpeta"]):
        nombre = texto_lower
        for p in ["borra archivo", "elimina archivo", "elimina carpeta", "el archivo", "la carpeta"]:
            nombre = nombre.replace(p, "")
        nombre = nombre.strip().strip('"').strip("'").strip()
        
        if not nombre:
            return "❌ ¿Qué quieres eliminar?"
        
        # Verificar si es carpeta o archivo
        if "carpeta" in texto_lower or "directorio" in texto_lower:
            return f"⚠️ ¿Seguro que quieres eliminar la carpeta '{nombre}'? Responde 'sí' o 'confirmo'"
        else:
            return f"⚠️ ¿Seguro que quieres eliminar el archivo '{nombre}'? Responde 'sí' o 'confirmo'"
    
    # ===== MOVER =====
    if "mueve" in texto_lower and "a" in texto_lower:
        match = re.search(r'mueve\s+(\S+)\s+a\s+(\S+)', texto_lower)
        if match:
            origen, destino = match.groups()
            comando = f"mv '{origen}' '{destino}'"
            return ejecutar_comando_seguro(comando)
    
    # ===== COPIAR =====
    if "copia" in texto_lower and "a" in texto_lower:
        match = re.search(r'copia\s+(\S+)\s+a\s+(\S+)', texto_lower)
        if match:
            origen, destino = match.groups()
            comando = f"cp '{origen}' '{destino}'"
            return ejecutar_comando_seguro(comando)
    
    return None

