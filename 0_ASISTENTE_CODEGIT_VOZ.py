#!/usr/bin/env python3
"""
Asistente de Telegram con Voz, RAG, Memoria Semántica y Skills.
FASE 4: Agente local con web search, creación de archivos, comandos avanzados
"""

import subprocess
import tempfile
import os
import json
import re
import shlex
import time
import sqlite3
import requests
from datetime import datetime
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from faster_whisper import WhisperModel
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
import ollama
from duckduckgo_search import DDGS

# ========= CONFIGURACIÓN =========
TOKEN = "TOKENTELEGRAM"

# Modelo de Ollama (local) - usa el que tengas instalado
OLLAMA_MODEL = "phi3:mini"

# Ruta del modelo de voz Piper
PIPER_MODEL = "/home/rorshach/HAL9000/es_ES-davefx-medium.onnx"

# Archivos de memoria
MEMORIA_DB = os.path.expanduser("~/.telegram_bot_memoria.db")
PERSONALIDAD_FILE = os.path.expanduser("~/.telegram_bot_personalidad.json")
RAG_PATH = os.path.expanduser("~/HAL9000/rag_db")

# Carpeta de skills
SKILLS_DIR = os.path.expanduser("~/.telegram_bot_skills")

# Directorio base para crear archivos
BASE_DIR = os.path.expanduser("~")

# Comandos peligrosos que requieren confirmación
COMANDOS_PELIGROSOS = ["rm", "mv", "dd", "mkfs", "format", "shred", "wipe", "kill", "pkill", "chmod", "chown"]

# Comandos permitidos (los seguros se ejecutan sin confirmación)
COMANDOS_SEGUROS = [
    "ls", "pwd", "date", "whoami", "echo", "cat", "df", "free", "ps", 
    "uptime", "uname", "du", "find", "grep", "wc", "head", "tail", "tree",
    "mkdir", "touch", "cp", "ln"
]

# ========= INICIALIZAR MODELOS =========
print("🧠 Cargando modelo de embeddings...")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
embedder = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Modelo de embeddings listo")

# ========= MEMORIA SEMÁNTICA CON MIGRACIÓN AUTOMÁTICA =========
def init_memoria_db():
    """Inicializa la base de datos SQLite para memoria semántica con migración automática"""
    conn = sqlite3.connect(MEMORIA_DB)
    cursor = conn.cursor()
    
    # Verificar si la tabla existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memoria'")
    tabla_existe = cursor.fetchone()
    
    if tabla_existe:
        # Verificar las columnas existentes
        cursor.execute("PRAGMA table_info(memoria)")
        columnas = [col[1] for col in cursor.fetchall()]
        
        # Migrar si falta usuario_id
        if 'usuario_id' not in columnas:
            print("⚠️ Migrando base de datos: añadiendo columna usuario_id...")
            cursor.execute("ALTER TABLE memoria ADD COLUMN usuario_id TEXT DEFAULT 'default'")
            cursor.execute("UPDATE memoria SET usuario_id = 'default' WHERE usuario_id IS NULL")
            conn.commit()
            print("✅ Migración completada")
        
        # Migrar si embedding es TEXT (ya lo es)
        if 'embedding' not in columnas:
            print("⚠️ Error: tabla memoria sin columna embedding")
            conn.close()
            # Recrear la base de datos
            conn = sqlite3.connect(MEMORIA_DB)
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS memoria")
            cursor.execute("DROP TABLE IF EXISTS memoria_fts")
            conn.commit()
            # Crear tabla nueva
            cursor.execute('''
                CREATE TABLE memoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clave TEXT NOT NULL,
                    valor TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    usuario_id TEXT DEFAULT 'default'
                )
            ''')
            conn.commit()
    else:
        # Crear tabla nueva
        cursor.execute('''
            CREATE TABLE memoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clave TEXT NOT NULL,
                valor TEXT NOT NULL,
                embedding TEXT NOT NULL,
                fecha TEXT NOT NULL,
                usuario_id TEXT DEFAULT 'default'
            )
        ''')
    
    # Crear tabla FTS5 para búsqueda por keywords
    try:
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS memoria_fts USING fts5(
                clave, 
                valor, 
                content=memoria, 
                content_rowid=id
            )
        ''')
    except sqlite3.OperationalError as e:
        print(f"⚠️ Error creando FTS5: {e}")
        # Si falla, recrear
        cursor.execute("DROP TABLE IF EXISTS memoria_fts")
        cursor.execute('''
            CREATE VIRTUAL TABLE memoria_fts USING fts5(
                clave, 
                valor, 
                content=memoria, 
                content_rowid=id
            )
        ''')
    
    # Crear índices
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_usuario ON memoria(usuario_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_clave ON memoria(clave)')
    except sqlite3.OperationalError as e:
        print(f"⚠️ Nota: {e}")
    
    conn.commit()
    conn.close()
    print(f"✅ Base de datos memoria: {MEMORIA_DB}")

def obtener_embedding(texto):
    """Genera embedding para un texto"""
    return embedder.encode(texto).tolist()

def guardar_en_memoria(clave, valor, usuario_id="default"):
    """Guarda en memoria con embedding semántico"""
    conn = sqlite3.connect(MEMORIA_DB)
    cursor = conn.cursor()
    
    embedding = obtener_embedding(clave)
    embedding_json = json.dumps(embedding)
    fecha = datetime.now().isoformat()
    
    # Verificar si ya existe para este usuario
    cursor.execute('SELECT id FROM memoria WHERE clave = ? AND usuario_id = ?', (clave, usuario_id))
    existe = cursor.fetchone()
    
    if existe:
        # Actualizar existente
        cursor.execute('''
            UPDATE memoria SET valor = ?, embedding = ?, fecha = ?
            WHERE clave = ? AND usuario_id = ?
        ''', (valor, embedding_json, fecha, clave, usuario_id))
        # Actualizar FTS
        try:
            cursor.execute('UPDATE memoria_fts SET clave = ?, valor = ? WHERE rowid = ?', 
                          (clave, valor, existe[0]))
        except:
            pass
    else:
        # Insertar nuevo
        cursor.execute('''
            INSERT INTO memoria (clave, valor, embedding, fecha, usuario_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (clave, valor, embedding_json, fecha, usuario_id))
        # Insertar en FTS
        nuevo_id = cursor.lastrowid
        try:
            cursor.execute('INSERT INTO memoria_fts(rowid, clave, valor) VALUES(?, ?, ?)', 
                          (nuevo_id, clave, valor))
        except:
            pass
    
    conn.commit()
    conn.close()
    return True

def buscar_en_memoria(pregunta, usuario_id="default", umbral=0.6):
    """Búsqueda híbrida: semántica + keywords"""
    conn = sqlite3.connect(MEMORIA_DB)
    cursor = conn.cursor()
    
    # Búsqueda por keywords usando FTS5
    resultados_keyword = []
    try:
        cursor.execute('''
            SELECT m.clave, m.valor
            FROM memoria m
            JOIN memoria_fts fts ON m.id = fts.rowid
            WHERE m.usuario_id = ? AND memoria_fts MATCH ?
            LIMIT 5
        ''', (usuario_id, pregunta))
        resultados_keyword = cursor.fetchall()
    except Exception as e:
        print(f"⚠️ Error en búsqueda FTS: {e}")
    
    # Búsqueda semántica
    cursor.execute('SELECT clave, valor, embedding FROM memoria WHERE usuario_id = ?', (usuario_id,))
    resultados = cursor.fetchall()
    conn.close()
    
    if not resultados and not resultados_keyword:
        return None
    
    # Generar embedding de la pregunta
    pregunta_embedding = obtener_embedding(pregunta)
    
    # Calcular similitud semántica
    mejores = []
    for clave, valor, embedding_json in resultados:
        try:
            embedding = json.loads(embedding_json)
            similitud = calcular_similitud(pregunta_embedding, embedding)
            if similitud > umbral:
                mejores.append((similitud, clave, valor))
        except:
            continue
    
    # Combinar con resultados de keywords
    for clave, valor in resultados_keyword:
        encontrado = False
        for i, (sim, c, v) in enumerate(mejores):
            if c == clave:
                mejores[i] = (sim + 0.2, c, v)
                encontrado = True
                break
        if not encontrado:
            mejores.append((0.5, clave, valor))
    
    if not mejores:
        return None
    
    mejores.sort(reverse=True)
    mejor = mejores[0]
    
    return {
        "clave": mejor[1],
        "valor": mejor[2],
        "similitud": mejor[0]
    }

def calcular_similitud(v1, v2):
    """Calcula similitud coseno entre dos vectores"""
    import math
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0
    return dot_product / (norm1 * norm2)

def listar_memoria(usuario_id="default"):
    """Lista todas las claves guardadas por el usuario"""
    conn = sqlite3.connect(MEMORIA_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT clave, fecha FROM memoria WHERE usuario_id = ? ORDER BY fecha DESC', (usuario_id,))
    resultados = cursor.fetchall()
    conn.close()
    return resultados

def eliminar_de_memoria(clave, usuario_id="default"):
    """Elimina una entrada de memoria por clave exacta"""
    conn = sqlite3.connect(MEMORIA_DB)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM memoria WHERE clave = ? AND usuario_id = ?', (clave, usuario_id))
    row = cursor.fetchone()
    if row:
        try:
            cursor.execute('DELETE FROM memoria_fts WHERE rowid = ?', (row[0],))
        except:
            pass
        cursor.execute('DELETE FROM memoria WHERE id = ?', (row[0],))
    
    afectadas = cursor.rowcount
    conn.commit()
    conn.close()
    return afectadas > 0

# ========= SKILLS MODULARES =========
class SkillManager:
    def __init__(self, skills_dir):
        self.skills_dir = skills_dir
        self.skills = []
        self._crear_directorio()
        self._cargar_skills()
    
    def _crear_directorio(self):
        Path(self.skills_dir).mkdir(parents=True, exist_ok=True)
        # Crear skill de ejemplo si no existe
        ejemplo_path = os.path.join(self.skills_dir, "ejemplo_skill.py")
        if not os.path.exists(ejemplo_path):
            with open(ejemplo_path, 'w', encoding='utf-8') as f:
                f.write('''"""
Ejemplo de skill para el asistente.
Las skills deben tener una función match() y una función run()
"""

def match(texto):
    """Devuelve True si esta skill puede manejar el texto"""
    return "ejemplo" in texto.lower()

def run(texto, contexto):
    """Ejecuta la skill. Recibe el texto y un contexto con funciones útiles"""
    return "Esto es un ejemplo de skill. Personalízala para tus necesidades."
''')
    
    def _cargar_skills(self):
        for archivo in os.listdir(self.skills_dir):
            if archivo.endswith('.py') and archivo != '__init__.py' and archivo != 'ejemplo_skill.py':
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(
                        archivo[:-3], 
                        os.path.join(self.skills_dir, archivo)
                    )
                    modulo = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(modulo)
                    if hasattr(modulo, 'match') and hasattr(modulo, 'run'):
                        self.skills.append({
                            'nombre': archivo[:-3],
                            'modulo': modulo,
                            'match': modulo.match,
                            'run': modulo.run
                        })
                        print(f"✅ Skill cargada: {archivo[:-3]}")
                except Exception as e:
                    print(f"⚠️ Error cargando skill {archivo}: {e}")
    
    def procesar(self, texto, contexto):
        for skill in self.skills:
            try:
                if skill['match'](texto):
                    return skill['run'](texto, contexto)
            except Exception as e:
                print(f"⚠️ Error en skill {skill['nombre']}: {e}")
        return None

# ========= FUNCIONES WEB (tiempo y noticias) =========
def buscar_noticias(consulta, max_resultados=5):
    """Busca noticias usando DuckDuckGo"""
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.news(consulta, max_results=max_resultados))
            if not resultados:
                return f"No encontré noticias sobre '{consulta}'."
            
            texto = f"📰 **Noticias sobre '{consulta}':**\n\n"
            for i, r in enumerate(resultados[:max_resultados], 1):
                texto += f"{i}. **{r['title']}**\n"
                texto += f"   📍 {r.get('source', 'fuente desconocida')} | 📅 {r.get('date', 'fecha desconocida')}\n"
                texto += f"   📝 {r['body'][:200]}...\n\n"
            return texto
    except Exception as e:
        return f"❌ Error buscando noticias: {e}"

def obtener_tiempo(ciudad):
    """Obtiene el tiempo actual de una ciudad usando wttr.in"""
    try:
        url = f"https://wttr.in/{ciudad}?format=3"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            datos = response.text.strip()
            if datos and "Unknown" not in datos:
                return f"🌤️ {datos}"
            else:
                return f"No encontré información del tiempo para '{ciudad}'"
        else:
            return f"No pude obtener el tiempo para '{ciudad}'"
    except Exception as e:
        return f"❌ Error obteniendo tiempo: {e}"

# ========= CREACIÓN Y LECTURA DE ARCHIVOS =========
def crear_archivo(ruta, contenido):
    """Crea un archivo con el contenido especificado"""
    try:
        ruta_completa = os.path.expanduser(ruta)
        
        # Verificar que la ruta esté dentro del directorio base
        abs_path = os.path.abspath(ruta_completa)
        base_abs = os.path.abspath(BASE_DIR)
        if not abs_path.startswith(base_abs):
            return f"❌ No puedo crear archivos fuera de {BASE_DIR}"
        
        # Crear directorios si no existen
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        
        # Escribir archivo
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(contenido)
        
        return f"✅ Archivo creado: `{abs_path}`\n📝 Tamaño: {len(contenido)} caracteres"
    except Exception as e:
        return f"❌ Error creando archivo: {e}"

def leer_archivo(ruta):
    """Lee el contenido de un archivo"""
    try:
        ruta_completa = os.path.expanduser(ruta)
        if not os.path.exists(ruta_completa):
            return f"❌ El archivo `{ruta}` no existe."
        
        if os.path.isdir(ruta_completa):
            return f"❌ `{ruta}` es un directorio, no un archivo."
        
        with open(ruta_completa, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Limitar tamaño para no saturar Telegram
        if len(contenido) > 3000:
            contenido = contenido[:3000] + "\n... (archivo truncado)"
        
        return f"📄 **Contenido de `{ruta}`:**\n```\n{contenido}\n```"
    except UnicodeDecodeError:
        return f"❌ No puedo leer `{ruta}` porque parece ser un archivo binario."
    except Exception as e:
        return f"❌ Error leyendo archivo: {e}"

def listar_directorio(ruta="."):
    """Lista el contenido de un directorio"""
    try:
        ruta_completa = os.path.expanduser(ruta)
        if not os.path.exists(ruta_completa):
            return f"❌ La ruta `{ruta}` no existe."
        
        if os.path.isfile(ruta_completa):
            return f"`{ruta}` es un archivo, no un directorio."
        
        items = os.listdir(ruta_completa)
        if not items:
            return f"📁 El directorio `{ruta}` está vacío."
        
        # Separar directorios y archivos
        dirs = [f"📁 {i}" for i in items if os.path.isdir(os.path.join(ruta_completa, i))]
        files = [f"📄 {i}" for i in items if os.path.isfile(os.path.join(ruta_completa, i))]
        
        todos = dirs + files
        # Limitar a 50 items
        if len(todos) > 50:
            todos = todos[:50]
            todos.append("... y más")
        
        resultado = f"📁 **Contenido de `{ruta}`:**\n" + "\n".join(todos)
        return resultado
    except Exception as e:
        return f"❌ Error listando directorio: {e}"

# ========= EJECUCIÓN DE COMANDOS CON VALIDACIÓN =========
def comando_es_peligroso(comando):
    """Detecta si un comando es peligroso"""
    comando_lower = comando.lower()
    partes = comando_lower.split()
    if not partes:
        return False
    
    cmd_base = partes[0]
    
    # Verificar si el comando base está en la lista de peligrosos
    if cmd_base in COMANDOS_PELIGROSOS:
        return True
    
    # Verificar casos especiales (rm -rf, etc.)
    if cmd_base == "rm" and ("-rf" in partes or "-r" in partes):
        return True
    
    return False

def ejecutar_comando(comando, confirmado=False):
    """Ejecuta un comando del sistema con validación de seguridad"""
    if not comando or not comando.strip():
        return "❌ Comando vacío"
    
    try:
        cmd_parts = shlex.split(comando)
    except:
        cmd_parts = comando.split()
    
    if not cmd_parts:
        return "❌ Comando vacío"
    
    # Verificar comando permitido
    cmd_base = cmd_parts[0]
    if cmd_base not in COMANDOS_SEGUROS and cmd_base not in COMANDOS_PELIGROSOS:
        return f"❌ Comando no permitido: `{cmd_base}`\nPermitidos: {', '.join(COMANDOS_SEGUROS + COMANDOS_PELIGROSOS)}"
    
    # Verificar peligrosidad
    if comando_es_peligroso(comando) and not confirmado:
        return f"⚠️ **COMANDO PELIGROSO DETECTADO**\n\nComando: `{comando}`\n\n⚠️ ¿Quieres ejecutarlo? Responde **sí** o **confirmo** para continuar."
    
    try:
        resultado = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=30)
        salida = resultado.stdout or resultado.stderr or "✅ Ejecutado sin salida."
        if len(salida) > 1900:
            salida = salida[:1900] + "\n... (truncado)"
        return f"```\n{salida}\n```"
    except subprocess.TimeoutExpired:
        return "⚠️ El comando tardó demasiado (30s límite)"
    except Exception as e:
        return f"⚠️ Error: {e}"

# ========= RAG =========
print("📚 Cargando base de conocimiento RAG...")
coleccion_rag = None
try:
    chroma = PersistentClient(path=RAG_PATH)
    coleccion_rag = chroma.get_collection("conocimiento")
    print(f"✅ RAG cargada con {coleccion_rag.count()} fragmentos")
except Exception as e:
    print(f"⚠️ No se pudo cargar RAG: {e}")
    print("   Para usar RAG, crea una base de conocimiento con ChromaDB")

def buscar_en_rag(pregunta, max_resultados=5):
    """Busca en la base de conocimiento RAG"""
    if coleccion_rag is None:
        return None
    try:
        query_embedding = embedder.encode(pregunta).tolist()
        resultados = coleccion_rag.query(
            query_embeddings=[query_embedding],
            n_results=max_resultados
        )
        if resultados['documents'] and len(resultados['documents'][0]) > 0:
            contexto = ""
            for i, doc in enumerate(resultados['documents'][0], 1):
                fuente = "desconocida"
                if resultados['metadatas'] and resultados['metadatas'][0] and i-1 < len(resultados['metadatas'][0]):
                    metadato = resultados['metadatas'][0][i-1]
                    if metadato and isinstance(metadato, dict):
                        fuente = metadato.get('source', 'desconocida')
                contexto += f"[Fuente: {fuente}]\n{doc[:600]}\n\n"
            return contexto
        return None
    except Exception as e:
        print(f"Error en RAG: {e}")
        return None

def mostrar_documentos_rag():
    """Muestra los documentos cargados en RAG al iniciar el bot"""
    if coleccion_rag is None:
        print("📚 RAG: No hay base de conocimiento cargada")
        return
    
    try:
        total = coleccion_rag.count()
        
        if total == 0:
            print("📚 RAG: Base de conocimiento vacía")
            return
        
        # Obtener todos los metadatos
        resultados = coleccion_rag.get(limit=total)
        
        if not resultados or 'metadatas' not in resultados:
            print("📚 RAG: No se pudieron leer los metadatos")
            return
        
        # Agrupar por source (nombre del archivo)
        documentos = {}
        for metadata in resultados['metadatas']:
            if metadata and 'source' in metadata:
                source = metadata['source']
                if source not in documentos:
                    documentos[source] = 0
                documentos[source] += 1
        
        if documentos:
            print("📚 **Documentos en RAG:**")
            for nombre, fragmentos in documentos.items():
                print(f"   • {nombre} ({fragmentos} fragmentos)")
            print(f"   📊 Total: {total} fragmentos de {len(documentos)} documentos")
        else:
            print("📚 RAG: Documentos cargados sin metadatos 'source'")
            print(f"   Total: {total} fragmentos")
            
    except Exception as e:
        print(f"⚠️ No se pudo listar documentos RAG: {e}")

# ========= WHISPER (voz a texto) =========
print("🎤 Cargando modelo de voz (Whisper base - español)...")
whisper_model = None
try:
    whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
    print("✅ Modelo de voz listo")
except Exception as e:
    print(f"⚠️ Error cargando Whisper: {e}")

def transcribir_audio(audio_path):
    if whisper_model is None:
        return "Error: modelo de voz no disponible"
    try:
        segments, _ = whisper_model.transcribe(audio_path, language="es", beam_size=5)
        texto = " ".join([seg.text for seg in segments])
        return texto.strip() if texto else ""
    except Exception as e:
        print(f"Error transcripción: {e}")
        return ""

# ========= PIPER TTS (texto a voz) =========
def hablar_frase(texto):
    if not texto or len(texto.strip()) == 0:
        return False
    
    texto = texto.strip()
    
    # Eliminar emojis y caracteres problemáticos
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    texto = emoji_pattern.sub('', texto)
    
    # Reemplazar caracteres problemáticos
    texto = texto.replace('`', "'")
    texto = texto.replace('"', ' ')
    texto = texto.replace('\\', ' ')
    texto = texto.replace('$', ' ')
    texto = texto.replace('\n', ' ')
    texto = texto.replace('¡', '')
    texto = texto.replace('¿', '')
    texto = texto.replace('*', ' ')
    texto = texto.replace('_', ' ')
    texto = texto.replace('[', ' ')
    texto = texto.replace(']', ' ')
    texto = texto.replace('(', ' ')
    texto = texto.replace(')', ' ')
    
    if len(texto) > 250:
        texto = texto[:247] + "..."
    
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            output_file = tmp.name
        
        texto_escapado = shlex.quote(texto)
        cmd = f'echo {texto_escapado} | piper --model {PIPER_MODEL} --output_file {output_file}'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"Error Piper: {result.stderr}")
            return False
        
        subprocess.run(f'aplay {output_file}', shell=True, check=True, capture_output=True, timeout=10)
        os.unlink(output_file)
        return True
        
    except subprocess.TimeoutExpired:
        print("Error TTS: Timeout en frase")
        return False
    except Exception as e:
        print(f"Error TTS: {e}")
        return False

def hablar(texto):
    if not texto or len(texto.strip()) == 0:
        return False
    
    # Dividir en frases más cortas para mejor pronunciación
    frases = re.split(r'(?<=[.!?;])\s+', texto)
    
    exito = True
    for i, frase in enumerate(frases):
        frase = frase.strip()
        if frase and len(frase) > 5:
            if not hablar_frase(frase):
                exito = False
            time.sleep(0.15)
    
    return exito

# ========= PERSONALIDAD =========
PERSONALIDAD_DEFECTO = {
    "nombre": "HAL9000",
    "rol": "asistente personal experto en Linux",
    "rasgos": "inteligente, preciso, útil y amigable",
    "idioma": "español",
    "instrucciones_adicionales": """Responde de forma clara y concisa. Si no sabes algo, dilo honestamente.
Puedes ejecutar comandos Linux, crear archivos, buscar noticias y consultar el tiempo.
Si es necesario, pregunta confirmación antes de ejecutar comandos peligrosos."""
}

def cargar_personalidad():
    if os.path.exists(PERSONALIDAD_FILE):
        try:
            with open(PERSONALIDAD_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return PERSONALIDAD_DEFECTO.copy()
    return PERSONALIDAD_DEFECTO.copy()

def guardar_personalidad(personalidad):
    with open(PERSONALIDAD_FILE, 'w', encoding='utf-8') as f:
        json.dump(personalidad, f, ensure_ascii=False, indent=2)

def construir_system_prompt():
    p = cargar_personalidad()
    return f"""Eres {p['nombre']}, un {p['rol']} con personalidad {p['rasgos']}.
Hablas en {p['idioma']}.
{p['instrucciones_adicionales']}"""

# ========= IA HÍBRIDA =========
def detectar_intencion_simple(mensaje):
    """Detección simple de intenciones para comandos comunes"""
    mensaje_lower = mensaje.lower()
    
    # Noticias
    if any(palabra in mensaje_lower for palabra in ["noticias", "noticia", "últimas noticias", "qué pasó", "ha pasado"]):
        return "noticias"
    
    # Tiempo
    if any(palabra in mensaje_lower for palabra in ["tiempo", "clima", "temperatura", "lluvia", "qué tiempo", "cómo está"]):
        return "tiempo"
    
    # Crear archivo
    if any(palabra in mensaje_lower for palabra in ["crea un archivo", "crear archivo", "escribe en", "guarda esto en"]):
        return "crear_archivo"
    
    # Leer archivo
    if any(palabra in mensaje_lower for palabra in ["lee el archivo", "muestra el archivo", "contenido de", "cat"]):
        return "leer_archivo"
    
    # Listar directorio
    if any(palabra in mensaje_lower for palabra in ["lista los archivos", "qué hay en", "contenido de la carpeta", "muestra la carpeta"]):
        return "listar_directorio"
    
    return None

def responder_ia(mensaje, contexto_rag=None, memoria=None):
    """Genera respuesta usando el modelo local"""
    system_prompt = construir_system_prompt()
    
    if contexto_rag:
        system_prompt += f"\n\n**Información de mi base de conocimiento:**\n{contexto_rag}"
    
    if memoria:
        system_prompt += f"\n\n**Recuerdo que me enseñaste:** {memoria['clave']} = {memoria['valor']}"
    
    try:
        respuesta = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': mensaje}
            ]
        )
        return respuesta['message']['content']
    except Exception as e:
        return f"❌ Error con la IA local: {e}\n\nVerifica que Ollama esté corriendo:\n`ollama serve`"

# ========= MANEJADORES DE TELEGRAM =========
# Diccionario para comandos pendientes de confirmación
comandos_pendientes = {}

async def start(update, context):
    personalidad = cargar_personalidad()
    await update.message.reply_text(
        f"🤖 **{personalidad['nombre']}** (Fase 4 - Agente Local Avanzado)\n\n"
        f"Soy tu {personalidad['rol']}.\n\n"
        "**✨ Novedades:**\n"
        "• 📰 Buscar noticias (ej: 'noticias de inteligencia artificial')\n"
        "• 🌤️ Consultar tiempo (ej: 'qué tiempo hace en Madrid')\n"
        "• 📝 Crear archivos (ej: 'crea un archivo ~/notas.txt con contenido X')\n"
        "• 📖 Leer archivos (ej: 'muestra el contenido de ~/notas.txt')\n"
        "• 📁 Listar directorios (ej: 'qué hay en Descargas')\n"
        "• 🛡️ Comandos peligrosos requieren confirmación\n"
        "• 🧠 Búsqueda híbrida en memoria (semántica + keywords)\n"
        "• 📦 Skills modulares (carpeta ~/.telegram_bot_skills/)\n\n"
        "**📝 Comandos de memoria:**\n"
        "/aprender clave = valor - Guardar información\n"
        "/recordar texto - Buscar por significado\n"
        "/lista - Ver todo lo que sé\n"
        "/olvidar clave - Borrar información\n\n"
        "**🔧 Otros comandos:**\n"
        "/comando cmd - Forzar ejecución\n"
        "/personalidad campo = valor - Cambiar mi personalidad",
        parse_mode='Markdown'
    )

async def cmd_aprender(update, context):
    texto = " ".join(context.args)
    if not texto or "=" not in texto:
        await update.message.reply_text(
            "❌ Uso: `/aprender clave = valor`\n\n"
            "Ejemplo: `/aprender mi color favorito = azul`",
            parse_mode='Markdown'
        )
        return
    clave, valor = texto.split("=", 1)
    clave, valor = clave.strip(), valor.strip()
    user_id = str(update.effective_user.id)
    guardar_en_memoria(clave, valor, user_id)
    await update.message.reply_text(f"✅ Aprendido:\n**{clave}** = `{valor}`", parse_mode='Markdown')

async def cmd_recordar(update, context):
    if not context.args:
        await update.message.reply_text(
            "❌ Uso: `/recordar texto`\n\n"
            "Ejemplo: `/recordar color favorito`",
            parse_mode='Markdown'
        )
        return
    pregunta = " ".join(context.args).strip()
    user_id = str(update.effective_user.id)
    resultado = buscar_en_memoria(pregunta, user_id)
    if resultado:
        similitud = resultado['similitud'] * 100
        await update.message.reply_text(
            f"🧠 **Recordatorio encontrado** (similitud: {similitud:.1f}%)\n\n"
            f"📌 **Clave:** {resultado['clave']}\n"
            f"💬 **Valor:** {resultado['valor']}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"❌ No recuerdo nada relacionado con *\"{pregunta}\"*", parse_mode='Markdown')

async def cmd_lista(update, context):
    user_id = str(update.effective_user.id)
    resultados = listar_memoria(user_id)
    if not resultados:
        await update.message.reply_text(
            "📭 No tengo nada en memoria.\n"
            "Usa `/aprender clave = valor` para enseñarme.",
            parse_mode='Markdown'
        )
        return
    
    lista = "\n".join([f"• `{clave}` (desde {fecha[:10]})" for clave, fecha in resultados[:20]])
    total = len(resultados)
    mensaje = f"📚 **Lo que sé ({total} items):**\n\n{lista}"
    if total > 20:
        mensaje += f"\n\n... y {total - 20} más."
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def cmd_olvidar(update, context):
    if not context.args:
        await update.message.reply_text("❌ Uso: `/olvidar clave`", parse_mode='Markdown')
        return
    clave = " ".join(context.args).strip()
    user_id = str(update.effective_user.id)
    if eliminar_de_memoria(clave, user_id):
        await update.message.reply_text(f"🗑️ Olvidado: **{clave}**", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ No encontré **{clave}**", parse_mode='Markdown')

async def cmd_comando(update, context):
    comando = " ".join(context.args)
    if not comando:
        await update.message.reply_text("❌ Uso: `/comando ls -la`", parse_mode='Markdown')
        return
    resultado = ejecutar_comando(comando, confirmado=True)
    await update.message.reply_text(f"📟 `{comando}`\n{resultado}", parse_mode='Markdown')
    hablar(resultado)

async def cmd_personalidad(update, context):
    texto = " ".join(context.args)
    if not texto or "=" not in texto:
        await update.message.reply_text(
            "❌ Uso: `/personalidad campo = valor`\n\n"
            "Campos: `nombre`, `rol`, `rasgos`, `idioma`, `instrucciones_adicionales`",
            parse_mode='Markdown'
        )
        return
    campo, valor = texto.split("=", 1)
    campo, valor = campo.strip(), valor.strip()
    personalidad = cargar_personalidad()
    if campo in personalidad:
        personalidad[campo] = valor
        guardar_personalidad(personalidad)
        await update.message.reply_text(f"✅ **{campo}** cambiado a: `{valor}`", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ Campo '{campo}' no válido.", parse_mode='Markdown')

async def manejar_texto(update, context):
    user_id = str(update.effective_user.id)
    texto = update.message.text
    
    # Verificar confirmaciones pendientes para comandos peligrosos
    if user_id in comandos_pendientes:
        pendiente = comandos_pendientes[user_id]
        if texto.lower() in ['sí', 'si', 'confirmo', 'yes', 'y', 'confirmar', 'vale', 'ok']:
            comando = pendiente['comando']
            del comandos_pendientes[user_id]
            resultado = ejecutar_comando(comando, confirmado=True)
            await update.message.reply_text(f"📟 `{comando}`\n{resultado}", parse_mode='Markdown')
            hablar(resultado)
            return
        else:
            del comandos_pendientes[user_id]
            await update.message.reply_text("❌ Comando cancelado.")
            return
    
    # Intentar con skills primero
    skill_manager = context.bot_data.get('skill_manager')
    if skill_manager:
        resultado_skill = skill_manager.procesar(texto, {
            'buscar_memoria': lambda t: buscar_en_memoria(t, user_id),
            'rag': buscar_en_rag,
            'ejecutar_comando': ejecutar_comando
        })
        if resultado_skill:
            await update.message.reply_text(resultado_skill)
            hablar(resultado_skill)
            return
    
    # Detectar intención simple
    intencion = detectar_intencion_simple(texto)
    
    if intencion == "noticias":
        # Extraer consulta
        consulta = texto.lower()
        for palabra in ["noticias", "noticia", "de", "sobre", "acerca de"]:
            consulta = consulta.replace(palabra, "")
        consulta = consulta.strip() or "actualidad"
        resultado = buscar_noticias(consulta)
        await update.message.reply_text(resultado, parse_mode='Markdown')
        hablar(resultado[:300])
        return
    
    elif intencion == "tiempo":
        # Extraer ciudad
        ciudad = texto.lower()
        for palabra in ["tiempo", "clima", "en", "de", "qué", "como", "cómo", "está", "hace", "el tiempo", "la temperatura"]:
            ciudad = ciudad.replace(palabra, "")
        ciudad = ciudad.strip() or "Madrid"
        resultado = obtener_tiempo(ciudad)
        await update.message.reply_text(resultado, parse_mode='Markdown')
        hablar(resultado)
        return
    
    elif intencion == "listar_directorio":
        # Extraer ruta
        ruta = texto.lower()
        for palabra in ["lista los archivos", "qué hay en", "contenido de la carpeta", "muestra la carpeta", "de", "en"]:
            ruta = ruta.replace(palabra, "")
        ruta = ruta.strip() or "."
        resultado = listar_directorio(ruta)
        await update.message.reply_text(resultado, parse_mode='Markdown')
        hablar(resultado[:300])
        return
    
    elif intencion == "leer_archivo":
        # Extraer ruta
        ruta = texto.lower()
        for palabra in ["lee el archivo", "muestra el archivo", "contenido de", "cat", "el archivo"]:
            ruta = ruta.replace(palabra, "")
        ruta = ruta.strip()
        if ruta:
            resultado = leer_archivo(ruta)
            await update.message.reply_text(resultado, parse_mode='Markdown')
            hablar(resultado[:300])
        else:
            await update.message.reply_text("❌ ¿Qué archivo quieres leer?")
        return
    
    elif intencion == "crear_archivo":
        await update.message.reply_text(
            "📝 Para crear un archivo, usa el formato:\n"
            "`crea un archivo ~/ruta/archivo.txt con contenido X`\n\n"
            "Ejemplo: `crea un archivo ~/prueba.txt con contenido Hola mundo`"
        )
        return
    
    # Si no hay intención específica, usar IA
    # Buscar en RAG
    contexto_rag = buscar_en_rag(texto)
    
    # Buscar en memoria
    memoria = buscar_en_memoria(texto, user_id)
    
    # Responder con IA
    respuesta = responder_ia(texto, contexto_rag, memoria)
    
    await update.message.reply_text(respuesta)
    hablar(respuesta)

async def manejar_voz(update, context):
    """Maneja mensajes de voz - CORREGIDO (no modifica update.message.text)"""
    if whisper_model is None:
        await update.message.reply_text("❌ El modelo de voz no está disponible.")
        return
    
    await update.message.reply_text("🎤 Escuchando...")
    try:
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            audio_path = tmp.name
        
        texto = transcribir_audio(audio_path)
        os.unlink(audio_path)
        
        if not texto:
            await update.message.reply_text("❌ No entendí el audio. ¿Puedes repetir?")
            return
        
        await update.message.reply_text(f"📝 Entendí: *\"{texto}\"*", parse_mode='Markdown')
        
        # ===== PROCESAR EL TEXTO DIRECTAMENTE (sin modificar update.message) =====
        user_id = str(update.effective_user.id)
        
        # Verificar confirmaciones pendientes para comandos peligrosos
        if user_id in comandos_pendientes:
            pendiente = comandos_pendientes[user_id]
            if texto.lower() in ['sí', 'si', 'confirmo', 'yes', 'y', 'confirmar', 'vale', 'ok']:
                comando = pendiente['comando']
                del comandos_pendientes[user_id]
                resultado = ejecutar_comando(comando, confirmado=True)
                await update.message.reply_text(f"📟 `{comando}`\n{resultado}", parse_mode='Markdown')
                hablar(resultado)
                return
            else:
                del comandos_pendientes[user_id]
                await update.message.reply_text("❌ Comando cancelado.")
                return
        
        # Intentar con skills primero
        skill_manager = context.bot_data.get('skill_manager')
        if skill_manager:
            resultado_skill = skill_manager.procesar(texto, {
                'buscar_memoria': lambda t: buscar_en_memoria(t, user_id),
                'rag': buscar_en_rag,
                'ejecutar_comando': ejecutar_comando
            })
            if resultado_skill:
                await update.message.reply_text(resultado_skill)
                hablar(resultado_skill)
                return
        
        # Detectar intención simple
        intencion = detectar_intencion_simple(texto)
        
        if intencion == "noticias":
            consulta = texto.lower()
            for palabra in ["noticias", "noticia", "de", "sobre", "acerca de"]:
                consulta = consulta.replace(palabra, "")
            consulta = consulta.strip() or "actualidad"
            resultado = buscar_noticias(consulta)
            await update.message.reply_text(resultado, parse_mode='Markdown')
            hablar(resultado[:300])
            return
        
        elif intencion == "tiempo":
            ciudad = texto.lower()
            for palabra in ["tiempo", "clima", "en", "de", "qué", "como", "cómo", "está", "hace", "el tiempo", "la temperatura"]:
                ciudad = ciudad.replace(palabra, "")
            ciudad = ciudad.strip() or "Madrid"
            resultado = obtener_tiempo(ciudad)
            await update.message.reply_text(resultado, parse_mode='Markdown')
            hablar(resultado)
            return
        
        elif intencion == "listar_directorio":
            ruta = texto.lower()
            for palabra in ["lista los archivos", "qué hay en", "contenido de la carpeta", "muestra la carpeta", "de", "en"]:
                ruta = ruta.replace(palabra, "")
            ruta = ruta.strip() or "."
            resultado = listar_directorio(ruta)
            await update.message.reply_text(resultado, parse_mode='Markdown')
            hablar(resultado[:300])
            return
        
        elif intencion == "leer_archivo":
            ruta = texto.lower()
            for palabra in ["lee el archivo", "muestra el archivo", "contenido de", "cat", "el archivo"]:
                ruta = ruta.replace(palabra, "")
            ruta = ruta.strip()
            if ruta:
                resultado = leer_archivo(ruta)
                await update.message.reply_text(resultado, parse_mode='Markdown')
                hablar(resultado[:300])
            else:
                await update.message.reply_text("❌ ¿Qué archivo quieres leer?")
            return
        
        elif intencion == "crear_archivo":
            await update.message.reply_text(
                "📝 Para crear un archivo, usa el formato:\n"
                "`crea un archivo ~/ruta/archivo.txt con contenido X`\n\n"
                "Ejemplo: `crea un archivo ~/prueba.txt con contenido Hola mundo`"
            )
            return
        
        # Si no hay intención específica, usar IA
        contexto_rag = buscar_en_rag(texto)
        memoria = buscar_en_memoria(texto, user_id)
        respuesta = responder_ia(texto, contexto_rag, memoria)
        
        await update.message.reply_text(respuesta)
        hablar(respuesta)
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# ========= MAIN =========
def main():
    # Inicializar base de datos de memoria
    init_memoria_db()
    
    # Inicializar skills
    skill_manager = SkillManager(SKILLS_DIR)
    
    personalidad = cargar_personalidad()
    print("=" * 60)
    print("🤖 ASISTENTE INTELIGENTE - FASE 4")
    print("=" * 60)
    print(f"📦 Modelo Ollama: {OLLAMA_MODEL}")
    print(f"🎤 Whisper: {'✅ disponible' if whisper_model else '❌ no disponible'}")
    print(f"🔊 Piper TTS: {PIPER_MODEL}")
    print(f"🎭 Personalidad: {personalidad['nombre']}")
    print(f"📚 RAG: {RAG_PATH} ({'✅' if coleccion_rag else '⚠️ no disponible'})")
    
    # Mostrar documentos en RAG
    if coleccion_rag:
        mostrar_documentos_rag()
    
    print(f"💾 Memoria semántica: {MEMORIA_DB}")
    print(f"📦 Skills disponibles: {len(skill_manager.skills)}")
    print(f"📁 Directorio base: {BASE_DIR}")
    print("=" * 60)
    print("✅ Bot listo para usar")
    print("✨ Características activas:")
    print("   • Noticias (DuckDuckGo)")
    print("   • Tiempo (wttr.in)")
    print("   • Crear/leer archivos")
    print("   • Listar directorios")
    print("   • Comandos Linux con confirmación")
    print("   • Memoria híbrida (semántica + keywords)")
    print("   • Skills modulares")
    print("=" * 60)
    
    app = Application.builder().token(TOKEN).build()
    
    # Guardar skill_manager en bot_data para acceso desde handlers
    app.bot_data['skill_manager'] = skill_manager
    app.bot_data['comandos_pendientes'] = comandos_pendientes
    
    # Handlers de comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("aprender", cmd_aprender))
    app.add_handler(CommandHandler("recordar", cmd_recordar))
    app.add_handler(CommandHandler("lista", cmd_lista))
    app.add_handler(CommandHandler("olvidar", cmd_olvidar))
    app.add_handler(CommandHandler("comando", cmd_comando))
    app.add_handler(CommandHandler("personalidad", cmd_personalidad))
    
    # Handlers de mensajes
    app.add_handler(MessageHandler(filters.VOICE, manejar_voz))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_texto))
    
    app.run_polling()

if __name__ == "__main__":
    main()

