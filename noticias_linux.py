"""
Skill para noticias específicas de Linux
"""

from duckduckgo_search import DDGS

def match(texto):
    texto = texto.lower()
    return any(p in texto for p in ["noticias linux", "linux noticias", "qué hay de linux", "novedades linux"])

def run(texto, contexto):
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.news("Linux open source", max_results=5))
            
            if not resultados:
                return "❌ No encontré noticias de Linux"
            
            texto_respuesta = "🐧 **Noticias de Linux:**\n\n"
            for i, r in enumerate(resultados, 1):
                texto_respuesta += f"{i}. **{r['title']}**\n"
                texto_respuesta += f"   {r['body'][:100]}...\n\n"
            
            return texto_respuesta
    except Exception as e:
        return f"❌ Error: {e}"

