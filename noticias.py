# ~/.telegram_bot_skills/noticias.py
"""
Skill para buscar noticias en internet usando DuckDuckGo
"""

import requests
import json
import os
from duckduckgo_search import DDGS

# Archivo para guardar categorías favoritas
CATEGORIAS_FILE = os.path.expanduser("~/.telegram_bot_categorias.json")

# Categorías por defecto
CATEGORIAS_DEFECTO = {
    "default": "tecnología",
    "favoritas": ["tecnología", "linux", "inteligencia artificial", "ciencia"]
}

def cargar_categorias():
    """Carga las categorías guardadas"""
    if os.path.exists(CATEGORIAS_FILE):
        try:
            with open(CATEGORIAS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return CATEGORIAS_DEFECTO.copy()
    return CATEGORIAS_DEFECTO.copy()

def guardar_categoria(nombre, valor):
    """Guarda una categoría personalizada"""
    categorias = cargar_categorias()
    categorias[nombre] = valor
    with open(CATEGORIAS_FILE, 'w', encoding='utf-8') as f:
        json.dump(categorias, f, ensure_ascii=False, indent=2)
    return True

def match(texto):
    """Detecta si es una consulta de noticias"""
    texto = texto.lower()
    palabras = [
        "noticias", "noticia", "últimas noticias", "qué pasó", "ha pasado",
        "news", "actualidad", "información sobre", "buscame noticias",
        "qué hay de nuevo", "eventos actuales"
    ]
    return any(p in texto for p in palabras)

def buscar_noticias(consulta, max_resultados=5):
    """Busca noticias usando DuckDuckGo"""
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.news(consulta, max_results=max_resultados))
            
            if not resultados:
                return None
            
            # Formatear resultados de forma bonita
            texto = f"📰 **Noticias sobre '{consulta}':**\n\n"
            for i, r in enumerate(resultados[:max_resultados], 1):
                titulo = r['title']
                fuente = r.get('source', 'fuente desconocida')
                fecha = r.get('date', 'fecha reciente')
                cuerpo = r['body'][:150] + "..." if len(r['body']) > 150 else r['body']
                
                texto += f"{i}. **{titulo}**\n"
                texto += f"   📍 {fuente} | 📅 {fecha}\n"
                texto += f"   📝 {cuerpo}\n\n"
            
            return texto
    except Exception as e:
        return f"❌ Error buscando noticias: {e}"

def run(texto, contexto):
    """Ejecuta la búsqueda de noticias"""
    texto_lower = texto.lower()
    categorias = cargar_categorias()
    
    # ===== NOTICIAS POR CATEGORÍA GUARDADA =====
    # Buscar si menciona una categoría favorita
    for categoria in categorias.get("favoritas", []):
        if categoria in texto_lower:
            return buscar_noticias(categoria)
    
    # ===== NOTICIAS POR TEMA ESPECÍFICO =====
    # Extraer el tema después de palabras clave
    tema = None
    palabras_clave = ["noticias de", "noticias sobre", "buscame noticias de", "qué pasa con", "actualidad de"]
    
    for p in palabras_clave:
        if p in texto_lower:
            tema = texto_lower.split(p)[-1].strip()
            break
    
    # Si no encontró con palabras clave, buscar último tema
    if not tema:
        # Eliminar palabras genéricas
        tema = texto_lower
        for p in ["noticias", "noticia", "de", "sobre", "acerca", "buscame", "dime", "cuéntame"]:
            tema = tema.replace(p, "")
        tema = tema.strip()
    
    # Si el tema es muy corto o vacío, usar categoría por defecto
    if not tema or len(tema) < 2 or tema in ["hoy", "ahora", "actuales", "recientes"]:
        tema = categorias.get("default", "tecnología")
    
    return buscar_noticias(tema)

