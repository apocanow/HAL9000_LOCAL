# ~/.telegram_bot_skills/moneda.py
"""
Skill moneda - Conversión de divisas (requiere internet)
"""

import re
import requests

def match(texto):
    texto = texto.lower()
    return " a " in texto and any(c in texto for c in ["eur", "usd", "dolar", "euro", "peso", "real"])

def run(texto, contexto):
    # Buscar patrón: "100 eur a usd"
    patron = r'(\d+(?:\.\d+)?)\s*(\w+)\s*a\s*(\w+)'
    match = re.search(patron, texto.lower())
    
    if not match:
        return "❌ Formato: '100 eur a usd' o '50 dólares a euros'"
    
    cantidad = float(match.group(1))
    desde = match.group(2)
    hasta = match.group(3)
    
    # Mapear nombres comunes
    mapa = {
        "eur": "EUR", "euro": "EUR", "euros": "EUR",
        "usd": "USD", "dolar": "USD", "dólar": "USD", "dolares": "USD",
        "brl": "BRL", "real": "BRL", "reales": "BRL",
        "ars": "ARS", "peso": "ARS", "pesos": "ARS",
        "mxn": "MXN", "peso mexicano": "MXN"
    }
    
    desde_code = mapa.get(desde, desde.upper())
    hasta_code = mapa.get(hasta, hasta.upper())
    
    try:
        # API gratuita sin clave
        url = f"https://api.exchangerate-api.com/v4/latest/{desde_code}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            tasa = data['rates'].get(hasta_code)
            
            if tasa:
                resultado = cantidad * tasa
                return f"💱 **{cantidad} {desde_code}** = **{resultado:.2f} {hasta_code}**"
        
        return "❌ No pude obtener la tasa de cambio"
    except:
        return "❌ Error consultando moneda. ¿Tienes internet?"

