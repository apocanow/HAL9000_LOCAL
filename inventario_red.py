# ~/.telegram_bot_skills/inventario_red.py
"""
Skill para consultar el inventario de equipos de la red local
Lee desde un archivo de texto con formato: "nombre tiene la IP x.x.x.x"
"""

import os
import re

# Ruta del archivo de inventario
INVENTARIO_FILE = os.path.expanduser("~/inventario_red.txt")

def cargar_inventario():
    """Carga el inventario desde el archivo de texto"""
    inventario = {}
    
    if not os.path.exists(INVENTARIO_FILE):
        return None
    
    try:
        with open(INVENTARIO_FILE, 'r', encoding='utf-8') as f:
            for linea in f:
                linea = linea.strip()
                if not linea:
                    continue
                
                # Buscar patrones: "nombre tiene la IP x.x.x.x" o "nombre está en x.x.x.x"
                patrones = [
                    r'([A-Za-z0-9\s]+?)\s+(?:tiene la IP|tiene IP|IP|está en|es)\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)',
                    r'([A-Za-z0-9\s]+?)\s+-\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)',
                ]
                
                for patron in patrones:
                    match = re.search(patron, linea, re.IGNORECASE)
                    if match:
                        nombre = match.group(1).strip()
                        ip = match.group(2).strip()
                        inventario[nombre.lower()] = ip
                        break
                
                # Formato simple: "nombre: x.x.x.x"
                if ':' in linea and not match:
                    partes = linea.split(':', 1)
                    if len(partes) == 2:
                        nombre = partes[0].strip()
                        ip = partes[1].strip()
                        if re.match(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', ip):
                            inventario[nombre.lower()] = ip
        
        return inventario
    except Exception as e:
        print(f"Error cargando inventario: {e}")
        return None

def match(texto):
    """Detecta si pregunta por equipos de la red"""
    texto_lower = texto.lower()
    
    # Palabras clave que indican consulta de inventario
    palabras_clave = [
        "ip", "dirección ip", "qué ip", "cuál es la ip", "como se llama",
        "equipo", "servidor", "router", "máquina", "dispositivo",
        "dónde está", "donde esta", "que ip tiene"
    ]
    
    # También detectar si menciona algún nombre conocido (se verá en run)
    return any(p in texto_lower for p in palabras_clave)

def run(texto, contexto):
    """Consulta el inventario"""
    inventario = cargar_inventario()
    
    if inventario is None:
        return "❌ No encontré el archivo de inventario.\n📁 Crea `~/inventario_red.txt` con el formato:\n`nombre tiene la IP 192.168.1.x`"
    
    texto_lower = texto.lower()
    
    # ===== LISTAR TODO EL INVENTARIO =====
    if any(p in texto_lower for p in ["lista inventario", "todos los equipos", "todos los servidores", "inventario completo", "qué equipos tengo"]):
        if not inventario:
            return "📭 El inventario está vacío"
        
        # Ordenar por nombre
        equipos = sorted(inventario.items())
        
        respuesta = "📡 **Inventario de red:**\n\n"
        for nombre, ip in equipos:
            respuesta += f"• **{nombre.capitalize()}** → `{ip}`\n"
        
        respuesta += f"\n📊 Total: {len(equipos)} equipos"
        return respuesta
    
    # ===== BUSCAR IP POR NOMBRE =====
    # Buscar qué equipo tiene cierta IP
    ip_match = re.search(r'([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', texto_lower)
    if ip_match:
        ip_buscar = ip_match.group(1)
        for nombre, ip in inventario.items():
            if ip == ip_buscar:
                return f"🔍 La IP `{ip}` pertenece a **{nombre.capitalize()}**"
        return f"❌ No encontré ningún equipo con la IP `{ip_buscar}`"
    
    # ===== BUSCAR NOMBRE (normalizado) =====
    # Extraer posibles nombres del texto
    palabras = texto_lower.split()
    
    # Primero buscar coincidencias exactas con nombres del inventario
    for nombre, ip in inventario.items():
        if nombre in texto_lower:
            return f"🔍 **{nombre.capitalize()}** → `{ip}`"
    
    # Buscar por palabras sueltas (ej: "dime ip de proxmox")
    for palabra in palabras:
        if len(palabra) > 2:  # Ignorar palabras muy cortas
            for nombre, ip in inventario.items():
                if palabra in nombre or nombre in palabra:
                    return f"🔍 **{nombre.capitalize()}** → `{ip}`"
    
    # ===== SUGERENCIA SI NO ENCUENTRA =====
    return f"❌ No encontré información sobre '{texto}'\n\n📋 **Equipos disponibles:**\n" + "\n".join([f"• {n.capitalize()}" for n in list(inventario.keys())[:10]])

