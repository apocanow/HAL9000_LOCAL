"""
Ejemplo de skill para el asistente.
Las skills deben tener una función match() y una función run()
"""

def match(texto):
    """Devuelve True si esta skill puede manejar el texto"""
    return "ejemplo" in texto.lower()

def run(texto, contexto):
    """Ejecuta la skill. Recibe el texto y un contexto con: memoria, rag, comandos"""
    return "Esto es un ejemplo de skill. Personalízala para tus necesidades."
