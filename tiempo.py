# ~/.telegram_bot_skills/tiempo.py
"""
Skill para consultar el tiempo atmosférico (actual y pronóstico)
"""

import requests
import json
import os
import re
from datetime import datetime, timedelta

UBICACIONES_FILE = os.path.expanduser("~/.telegram_bot_ubicaciones.json")

# Ubicaciones por defecto
UBICACIONES_DEFECTO = {
    "default": "Barcelona",
    "casa": "Vilaller",
    "trabajo": "Barcelona"
}

def cargar_ubicaciones():
    if os.path.exists(UBICACIONES_FILE):
        try:
            with open(UBICACIONES_FILE, 'r') as f:
                return json.load(f)
        except:
            return UBICACIONES_DEFECTO.copy()
    return UBICACIONES_DEFECTO.copy()

def match(texto):
    texto = texto.lower()
    palabras = [
        "tiempo", "clima", "temperatura", "lluvia", "qué tiempo", 
        "cómo está el clima", "qué temperatura hace", "va a llover",
        "lloverá", "pronóstico", "va a hacer", "mañana", "pasado mañana"
    ]
    return any(p in texto for p in palabras)

def obtener_tiempo_actual(ciudad):
    """Obtiene el tiempo actual - formato CORTO que SÍ funciona"""
    try:
        # Este formato funciona perfectamente
        url = f"https://wttr.in/{ciudad}?format=3"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            datos = response.text.strip()
            if datos and "Unknown" not in datos:
                return datos
        return None
    except Exception as e:
        print(f"Error en tiempo actual: {e}")
        return None

def obtener_pronostico_simple(ciudad):
    """
    Obtiene pronóstico para mañana usando el formato estándar
    (sin format=3, dejando que wttr.in devuelva texto)
    """
    try:
        # Usamos la URL normal, wttr.in devuelve texto formateado
        url = f"https://wttr.in/{ciudad}?lang=es&days=2"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return None
        
        texto = response.text
        
        # Buscar la línea de mañana en el texto
        lineas = texto.split('\n')
        
        # Variables para guardar
        manana_temperatura = None
        manana_condicion = None
        
        for i, linea in enumerate(lineas):
            # Buscar "Mañana:" o "Tomorrow:" en español
            if 'Mañana' in linea or 'Tomorrow' in linea:
                # La siguiente línea suele tener la temperatura
                if i + 1 < len(lineas):
                    siguiente = lineas[i + 1]
                    # Extraer temperatura (ej: "🌡️ 15..25°C")
                    temp_match = re.search(r'🌡️\s*([\d\.]+\.\.[\d\.]+°C)', siguiente)
                    if temp_match:
                        manana_temperatura = temp_match.group(1)
                    
                    # Buscar condición del clima (🌧️, ☀️, etc.)
                    cond_match = re.search(r'([🌧️☀️⛅☁️🌦️⛈️]+)\s*(.+)', siguiente)
                    if cond_match:
                        manana_condicion = cond_match.group(1)
                
                break
        
        # Si encontramos algo, devolverlo
        if manana_temperatura or manana_condicion:
            resultado = f"🌤️ **Mañana en {ciudad}:** "
            if manana_condicion:
                resultado += f"{manana_condicion} "
            if manana_temperatura:
                resultado += f"{manana_temperatura}"
            return resultado
        
        # Si no, intentar método alternativo
        return obtener_pronostico_alternativo(ciudad)
        
    except Exception as e:
        print(f"Error en pronóstico: {e}")
        return None

def obtener_pronostico_alternativo(ciudad):
    """
    Método alternativo usando el servicio v2 de wttr.in
    """
    try:
        # Usar API JSON de wttr.in (más fiable)
        url = f"https://wttr.in/{ciudad}?format=j1&lang=es"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        # El pronóstico está en weather
        if 'weather' in data and len(data['weather']) > 1:
            manana = data['weather'][1]  # Día 1 = mañana
            
            # Extraer datos
            fecha = manana.get('date', '')
            temp_max = manana.get('maxtempC', '')
            temp_min = manana.get('mintempC', '')
            descripcion = manana.get('hourly', [{}])[0].get('lang_es', [{}])[0].get('value', '')
            
            # Emoji según descripción
            emoji = "🌤️"
            if "lluvia" in descripcion.lower():
                emoji = "🌧️"
            elif "soleado" in descripcion.lower():
                emoji = "☀️"
            elif "nublado" in descripcion.lower():
                emoji = "☁️"
            
            if temp_max and temp_min:
                return f"{emoji} **Mañana en {ciudad}:** {descripcion} {temp_min}°C a {temp_max}°C"
            elif temp_max:
                return f"{emoji} **Mañana en {ciudad}:** {descripcion} {temp_max}°C"
        
        return None
    except Exception as e:
        print(f"Error en método alternativo: {e}")
        return None

def detectar_pregunta_lluvia(texto):
    """Detecta si pregunta específicamente por lluvia"""
    texto = texto.lower()
    return any(p in texto for p in ["va a llover", "lloverá", "habrá lluvia", "llueve mañana"])

def extraer_ciudad(texto, ubicaciones):
    """Extrae la ciudad del texto del usuario"""
    texto_lower = texto.lower()
    
    # Buscar ubicaciones guardadas
    for nombre, ubicacion in ubicaciones.items():
        if nombre in texto_lower and nombre != "default":
            return ubicacion
    
    # Buscar después de "en"
    palabras = texto.split()
    for i, p in enumerate(palabras):
        if p.lower() in ["en", "de", "para"] and i+1 < len(palabras):
            posible = palabras[i+1].capitalize()
            if len(posible) > 2:
                return posible
    
    # Usar ubicación por defecto
    return ubicaciones.get("default", "Barcelona")

def run(texto, contexto):
    """Ejecuta la consulta del tiempo"""
    ubicaciones = cargar_ubicaciones()
    ciudad = extraer_ciudad(texto, ubicaciones)
    pregunta_lluvia = detectar_pregunta_lluvia(texto)
    es_futuro = "mañana" in texto.lower() or "pasado" in texto.lower()
    
    # ===== PRONÓSTICO PARA MAÑANA =====
    if "mañana" in texto.lower():
        pronostico = obtener_pronostico_simple(ciudad)
        
        if pronostico:
            # Si pregunta específicamente por lluvia
            if pregunta_lluvia:
                if "lluv" in pronostico.lower() or "🌧️" in pronostico:
                    return f"☔ **Sí, se espera lluvia mañana en {ciudad}.**\n{pronostico}"
                else:
                    return f"☀️ **No, no se espera lluvia mañana en {ciudad}.**\n{pronostico}"
            return pronostico
        else:
            return f"❌ No pude obtener el pronóstico para {ciudad}"
    
    # ===== TIEMPO ACTUAL =====
    tiempo_actual = obtener_tiempo_actual(ciudad)
    
    if tiempo_actual:
        if pregunta_lluvia:
            if "rain" in tiempo_actual.lower() or "lluv" in tiempo_actual.lower():
                return f"☔ **Sí, está lloviendo en {ciudad} ahora mismo.**\n🌤️ {tiempo_actual}"
            else:
                return f"☀️ **No, no está lloviendo en {ciudad} ahora.**\n🌤️ {tiempo_actual}"
        return f"🌤️ {tiempo_actual}"
    
    return f"❌ No encontré información para '{ciudad}'"



