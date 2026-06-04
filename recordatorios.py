# ~/.telegram_bot_skills/recordatorios.py
"""
Skill recordatorios - Guarda y recuerda cosas temporales
"""

import json
import os
from datetime import datetime

RECORDATORIOS_FILE = os.path.expanduser("~/.telegram_bot_recordatorios.json")

def cargar_recordatorios():
    if os.path.exists(RECORDATORIOS_FILE):
        with open(RECORDATORIOS_FILE, 'r') as f:
            return json.load(f)
    return []

def guardar_recordatorios(recordatorios):
    with open(RECORDATORIOS_FILE, 'w') as f:
        json.dump(recordatorios, f, indent=2)

def match(texto):
    texto = texto.lower()
    return any(p in texto for p in ["recuérdame", "recordar", "recordatorio", "avísame"])

def run(texto, contexto):
    texto_lower = texto.lower()
    
    # Guardar recordatorio
    if "recuérdame" in texto_lower or "recordar" in texto_lower:
        # Extraer el recordatorio
        for palabra in ["recuérdame", "recordar que", "recordar", "avísame"]:
            texto = texto.replace(palabra, "")
        recordatorio = texto.strip()
        
        if recordatorio:
            recordatorios = cargar_recordatorios()
            recordatorios.append({
                "texto": recordatorio,
                "fecha": datetime.now().isoformat(),
                "completado": False
            })
            guardar_recordatorios(recordatorios)
            return f"✅ Recordatorio guardado: \"{recordatorio}\""
    
    # Listar recordatorios
    if "mis recordatorios" in texto_lower or "qué tengo que" in texto_lower:
        recordatorios = cargar_recordatorios()
        pendientes = [r for r in recordatorios if not r["completado"]]
        
        if not pendientes:
            return "📭 No tienes recordatorios pendientes"
        
        lista = "\n".join([f"• {r['texto']}" for r in pendientes[:10]])
        return f"📋 **Recordatorios pendientes:**\n{lista}"
    
    return "❌ Uso: 'recuérdame comprar leche' o 'mis recordatorios'"

