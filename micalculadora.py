# ~/.telegram_bot_skills/micalculadora.py
"""
Skill calculadora - Realiza operaciones matemáticas básicas
"""

import re

def match(texto):
    """Detecta si es una operación matemática"""
    texto = texto.lower()
    operadores = ["suma", "resta", "multiplica", "divide", "más", "menos", "por", "entre", "+", "-", "*", "/"]
    return any(op in texto for op in operadores) and any(c.isdigit() for c in texto)

def run(texto, contexto):
    """Ejecuta la operación matemática"""
    texto = texto.lower()
    
    # Limpiar texto
    texto = texto.replace("cuánto es", "").replace("cuanto es", "")
    texto = texto.replace("calcula", "").replace("calcular", "")
    texto = texto.replace("dime", "").replace("", "")
    texto = texto.strip()
    
    # Buscar operación
    patrones = [
        (r'(\d+)\s*(?:suma|\+|\s*más\s*)\s*(\d+)', lambda a,b: a+b, "suma"),
        (r'(\d+)\s*(?:resta|\-|\s*menos\s*)\s*(\d+)', lambda a,b: a-b, "resta"),
        (r'(\d+)\s*(?:multiplica|\*|\s*por\s*)\s*(\d+)', lambda a,b: a*b, "multiplicación"),
        (r'(\d+)\s*(?:divide|/|\s*entre\s*)\s*(\d+)', lambda a,b: a/b if b!=0 else "error", "división"),
    ]
    
    for patron, func, nombre in patrones:
        match = re.search(patron, texto)
        if match:
            a = float(match.group(1))
            b = float(match.group(2))
            resultado = func(a, b)
            if resultado == "error":
                return "❌ No se puede dividir entre cero"
            return f"🧮 **{nombre.capitalize()}:** {int(a) if a.is_integer() else a} {nombre} {int(b) if b.is_integer() else b} = {int(resultado) if resultado.is_integer() else resultado:.2f}"
    
    return "❌ No entendí la operación. Ejemplos: '2 + 2', '10 entre 5'"


