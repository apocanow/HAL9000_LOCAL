"""
Skill para noticias de Inteligencia Artificial
"""

from duckduckgo_search import DDGS

def match(texto):
    texto = texto.lower()
    return any(p in texto for p in ["noticias ia", "inteligencia artificial noticias", "ai news", "noticias de ia"])

def run(texto, contexto):
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.news("inteligencia artificial", max_results=5))
            
            if not resultados:
                return "❌ No encontré noticias de IA"
            
            texto_respuesta = "🧠 **Noticias de Inteligencia Artificial:**\n\n"
            for i, r in enumerate(resultados, 1):
                texto_respuesta += f"{i}. **{r['title']}**\n"
                texto_respuesta += f"   {r['body'][:100]}...\n\n"
            
            return texto_respuesta
    except Exception as e:
        return f"❌ Error: {e}"

