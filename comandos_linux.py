# ~/.telegram_bot_skills/comandos_linux.py
"""
Skill comandos Linux - Ejecuta comandos de sistema en lenguaje natural
Ejecuta AUTOMÁTICAMENTE los comandos, no solo los sugiere
"""

import subprocess
import os
import re
from pathlib import Path

# Directorio base para operaciones seguras
BASE_DIR = os.path.expanduser("~")

# Comandos comunes con sus descripciones y comandos reales
COMANDOS_NATURALES = {
    # ===== SISTEMA =====
    "memoria ram": "free -h",
    "memoria libre": "free -h",
    "ram disponible": "free -h",
    "swap": "free -h | grep Swap",
    "espacio disco": "df -h",
    "disco duro": "df -h",
    "almacenamiento": "df -h",
    "procesos": "ps aux --sort=-%cpu | head -20",
    "programas ejecutándose": "ps aux | head -20",
    "cpu": "top -bn1 | head -5",
    "carga del sistema": "uptime",
    "kernel": "uname -r",
    "versión del sistema": "cat /etc/os-release | head -5",
    "arquitectura": "uname -m",
    "tiempo encendido": "uptime -p",
    "usuarios conectados": "who",
    "quién soy": "whoami",
    "historial comandos": "history | tail -20",
    "fecha y hora": "date '+%Y-%m-%d %H:%M:%S'",
    
    # ===== ARCHIVOS Y CARPETAS =====
    "archivos ocultos": "ls -la | grep '^\\\\.'",
    "archivos grandes": "find . -type f -size +100M -exec ls -lh {} \\; 2>/dev/null | head -20",
    "archivos modificados hoy": "find . -type f -newermt 'today' -ls 2>/dev/null | head -20",
    "archivos recientes": "ls -lt | head -20",
    "directorio actual": "pwd",
    "árbol directorios": "tree -L 2 2>/dev/null | head -30 || ls -R | head -50",
    
    # ===== RED =====
    "mi ip pública": "curl -s ifconfig.me 2>/dev/null || echo 'No hay internet'",
    "mi ip local": "ip addr show | grep 'inet ' | grep -v 127.0.0.1 | head -1",
    "conexiones red": "ss -tuln",
    "puertos abiertos": "ss -tuln",
    "wifi conectado": "iwgetid 2>/dev/null || nmcli -t -f NAME connection show --active 2>/dev/null | head -1",
    "redes wifi disponibles": "nmcli device wifi list 2>/dev/null || echo 'Ejecuta: nmcli dev wifi list'",
    "ping a google": "ping -c 4 google.com 2>/dev/null | tail -3",
    
    # ===== HARDWARE =====
    "hardware": "lscpu | head -10",
    "discos": "lsblk",
    "discos montados": "df -h",
    "usb conectados": "lsusb 2>/dev/null || echo 'Ejecuta: lsusb'",
    "pci dispositivos": "lspci | head -10",
    "temperatura cpu": "sensors 2>/dev/null | grep -i 'core' | head -5 || echo 'Instala lm-sensors'",
    
    # ===== PROCESOS =====
    "procesos por cpu": "ps aux --sort=-%cpu | head -15",
    "procesos por memoria": "ps aux --sort=-%mem | head -15",
    "mi shell": "echo $SHELL",
    "variables de entorno": "env | head -20",
    
    # ===== BÚSQUEDA =====
    "últimos logs": "journalctl -n 20 --no-pager 2>/dev/null || tail -20 /var/log/syslog 2>/dev/null",
    "servicios activos": "systemctl list-units --type=service --state=running | head -15",
}

def ejecutar_comando_seguro(comando):
    """Ejecuta comando con validación de seguridad y timeout"""
    try:
        # Comandos peligrosos no permitidos en skill
        peligrosos = [
            "rm -rf /", "rm -rf /*", "dd if=", "mkfs", "format",
            ":(){", "chmod 777 /", "sudo", "su -", "passwd"
        ]
        for p in peligrosos:
            if p in comando.lower():
                return "⚠️ Comando peligroso no permitido por seguridad"
        
        # Verificar que no intente salir del directorio base peligrosamente
        if ".." in comando and "cd" not in comando and "ls" not in comando:
            # Permitir ls con .. pero no otros comandos
            if not comando.startswith("ls"):
                return "⚠️ No se permite salir del directorio base con '..'"
        
        resultado = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15,
            executable='/bin/bash',
            cwd=BASE_DIR
        )
        
        salida = resultado.stdout or resultado.stderr
        if not salida:
            return "✅ Comando ejecutado sin salida"
        
        # Limitar tamaño para no saturar Telegram
        if len(salida) > 1500:
            salida = salida[:1500] + "\n... (truncado)"
        
        # Formatear respuesta bonita
        return f"📟 `{comando}`\n```\n{salida}\n```"
        
    except subprocess.TimeoutExpired:
        return "⏰ El comando tardó demasiado (>15 segundos)"
    except Exception as e:
        return f"❌ Error: {e}"

def listar_contenido(ruta, detallado=False):
    """Lista el contenido de un directorio"""
    try:
        # Expandir ruta
        if ruta.startswith("~/"):
            ruta = os.path.expanduser(ruta)
        elif not ruta.startswith("/"):
            # Si es nombre simple, asumir subdirectorio del home
            ruta = os.path.join(BASE_DIR, ruta)
        
        if not os.path.exists(ruta):
            return f"❌ La ruta '{ruta}' no existe"
        
        if os.path.isfile(ruta):
            return f"📄 `{ruta}` es un archivo, no un directorio"
        
        if detallado or "detallado" in texto_lower:
            comando = f"ls -la '{ruta}'"
        else:
            comando = f"ls '{ruta}'"
        
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=5)
        salida = resultado.stdout or resultado.stderr
        
        if not salida:
            return f"📁 Directorio `{ruta}` vacío"
        
        if len(salida) > 1500:
            salida = salida[:1500] + "\n... (truncado)"
        
        return f"📁 **Contenido de `{ruta}`:**\n```\n{salida}\n```"
        
    except Exception as e:
        return f"❌ Error listando: {e}"

def buscar_archivos(nombre):
    """Busca archivos por nombre"""
    try:
        comando = f"find {BASE_DIR} -name '*{nombre}*' -type f 2>/dev/null | head -15"
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=10)
        salida = resultado.stdout
        
        if not salida:
            return f"❌ No encontré archivos con '{nombre}'"
        
        return f"🔍 **Archivos encontrados:**\n```\n{salida}\n```"
    except Exception as e:
        return f"❌ Error buscando: {e}"

def match(texto):
    """Detecta si es un comando de sistema para ejecutar"""
    texto_lower = texto.lower()
    
    # Palabras clave que indican comando de sistema
    palabras_clave = [
        "muestra", "lista", "dime", "cuánto", "cuanta", "qué", "cómo", "cuál",
        "archivos", "carpetas", "directorio", "procesos", "memoria", "ram",
        "disco", "red", "usuario", "cpu", "kernel", "sistema", "hardware",
        "espacio", "almacenamiento", "programas", "ejecutando", "corriendo",
        "ip", "wifi", "conexión", "puertos", "logs", "servicios"
    ]
    
    # Detectar si es un comando
    es_comando = any(p in texto_lower for p in palabras_clave)
    
    # Excluir preguntas que debería responder la IA
    preguntas_ia = [
        "qué significa", "cómo funciona", "para qué sirve", "explica",
        "por qué", "cuál es la diferencia", "qué es"
    ]
    if any(p in texto_lower for p in preguntas_ia):
        return False
    
    # Comandos directos que empiezan con palabras específicas
    comandos_directos = ["ls ", "ps ", "df ", "free ", "top ", "uptime ", "who ", "pwd"]
    if any(texto_lower.startswith(c) for c in comandos_directos):
        return True
    
    return es_comando

def run(texto, contexto):
    """Ejecuta el comando apropiado automáticamente"""
    global texto_lower
    texto_lower = texto.lower()
    
    # ===== COMANDOS DIRECTOS (el usuario escribe el comando) =====
    if texto_lower.startswith(("ls ", "ps ", "df ", "free ", "top ", "uptime ", "who ", "pwd", "date")):
        return ejecutar_comando_seguro(texto)
    
    # ===== BÚSQUEDA DE ARCHIVOS =====
    if "buscar" in texto_lower and ("archivo" in texto_lower or "fichero" in texto_lower):
        nombre = texto_lower.split("buscar")[-1].strip()
        for p in ["el archivo", "el fichero", "archivo llamado", "fichero llamado", "llamado"]:
            nombre = nombre.replace(p, "")
        nombre = nombre.strip().strip('"').strip("'")
        if nombre:
            return buscar_archivos(nombre)
    
    # ===== LISTAR DIRECTORIO =====
    if any(p in texto_lower for p in ["lista", "archivos", "carpetas", "qué hay en"]):
        # Extraer ruta
        ruta = "."
        palabras = texto.split()
        for i, p in enumerate(palabras):
            if p.lower() in ["de", "en", "carpeta", "directorio"] and i+1 < len(palabras):
                ruta = palabras[i+1]
                break
        
        # Limpiar ruta
        ruta = ruta.strip('"').strip("'")
        detallado = "detallado" in texto_lower or "todos" in texto_lower or "incluyendo ocultos" in texto_lower or "-la" in texto_lower
        
        return listar_contenido(ruta, detallado)
    
    # ===== BUSCAR EN COMANDOS_NATURALES =====
    for frase, comando in COMANDOS_NATURALES.items():
        if frase in texto_lower:
            return ejecutar_comando_seguro(comando)
    
    # ===== PROCESOS (con opciones específicas) =====
    if "procesos" in texto_lower or "programas" in texto_lower:
        if "cpu" in texto_lower or "más cpu" in texto_lower:
            comando = "ps aux --sort=-%cpu | head -15"
        elif "memoria" in texto_lower or "más memoria" in texto_lower:
            comando = "ps aux --sort=-%mem | head -15"
        else:
            comando = "ps aux | head -15"
        return ejecutar_comando_seguro(comando)
    
    # ===== MEMORIA =====
    if "memoria" in texto_lower or "ram" in texto_lower:
        if "libre" in texto_lower or "disponible" in texto_lower:
            comando = "free -h | grep -E 'Mem|Swap'"
        else:
            comando = "free -h"
        return ejecutar_comando_seguro(comando)
    
    # ===== ESPACIO EN DISCO =====
    if any(p in texto_lower for p in ["espacio", "disco", "almacenamiento"]):
        if "humano" in texto_lower or "h" in texto_lower:
            comando = "df -h"
        else:
            comando = "df -h"
        return ejecutar_comando_seguro(comando)
    
    # ===== RED =====
    if "ip" in texto_lower:
        if "pública" in texto_lower or "publica" in texto_lower or "externo" in texto_lower:
            comando = "curl -s ifconfig.me 2>/dev/null || echo 'No hay internet'"
        else:
            comando = "ip addr show | grep 'inet ' | grep -v 127.0.0.1"
        return ejecutar_comando_seguro(comando)
    
    if "wifi" in texto_lower:
        if "disponibles" in texto_lower:
            comando = "nmcli device wifi list 2>/dev/null || echo 'Ejecuta: nmcli dev wifi list'"
        else:
            comando = "iwgetid 2>/dev/null || nmcli -t -f NAME connection show --active 2>/dev/null | head -1"
        return ejecutar_comando_seguro(comando)
    
    # ===== Si no se pudo determinar, devolver None para que la IA lo procese =====
    return None

