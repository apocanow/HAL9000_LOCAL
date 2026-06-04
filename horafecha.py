# ~/.telegram_bot_skills/horafecha.py
"""
Skill hora y fecha - Información de tiempo
"""

from datetime import datetime
import locale

# Intentar configurar locale en español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except:
        pass

def match(texto):
    texto = texto.lower()
    palabras = ["qué hora", "hora es", "qué día", "fecha", "hoy es", "día es", "fecha actual"]
    return any(p in texto for p in palabras)

def run(texto, contexto):
    ahora = datetime.now()
    
    if "hora" in texto.lower():
        return f"🕐 Son las **{ahora.strftime('%H:%M')}**"
    
    if "fecha" in texto.lower() or "día" in texto.lower():
        return f"📅 Hoy es **{ahora.strftime('%A %d de %B de %Y')}**"
    
    return f"🕐 **{ahora.strftime('%H:%M')}** - 📅 **{ahora.strftime('%A %d de %B')}**"


