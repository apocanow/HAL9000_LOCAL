# 🤖 HAL9000_LOCAL - Descripción del Proyecto

## 📌 ¿Qué es HAL9000_LOCAL?

**HAL9000_LOCAL** es un asistente inteligente personal con IA completamente local, basado en Telegram. Combina múltiples tecnologías de IA y machine learning para crear un asistente versátil, privado y sin depender de servicios en la nube.

---

## 🎯 Objetivo Principal

Proporcionar un **asistente de IA completo que funciona 100% localmente**, respetando la privacidad del usuario, sin enviar datos a servidores externos (excepto búsquedas opcionales de noticias y clima).

---

## 🏗️ Arquitectura del Sistema

### Componentes Principales

```
┌─────────────────────────────────────────────┐
│         TELEGRAM (Interfaz)                 │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│  PROCESAMIENTO DE ENTRADA                   │
│  ├─ Transcripción: Whisper (voz→texto)     │
│  ├─ Normalización de texto                  │
│  └─ Detección de intención                  │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│  SISTEMA DE SKILLS (Respuesta rápida)       │
│  ├─ 🌤️ Tiempo (wttr.in)                     │
│  ├─ 📰 Noticias (DuckDuckGo)                │
│  ├─ 💻 Comandos Linux                       │
│  ├─ 🧮 Calculadora                          │
│  └─ 📁 Gestión de archivos                  │
└──────────────┬──────────────────────────────┘
               │
        ┌──────┴─────────────────┐
        │ ¿Hizo match?           │
        ├──────┬────────────────┤
        │ SÍ   │ NO             │
        ▼      ▼                ▼
    RESPUESTA RÁPIDA ──────┐    │
                           ▼
                ┌─────────────────────┐
                │  BÚSQUEDA EN MEMORIA│
                │  (SQLite + FTS5)    │
                └──────────┬──────────┘
                           ▼
                ┌─────────────────────┐
                │  BÚSQUEDA EN RAG    │
                │  (ChromaDB)         │
                └──────────┬──────────┘
                           ▼
                ┌─────────────────────┐
                │  IA LOCAL (Ollama)  │
                │  Modelo: Phi3:mini  │
                └──────────┬──────────┘
                           ▼
                ┌─────────────────────┐
                │  Generación texto   │
                └──────────┬──────────┘
                           ▼
                ┌─────────────────────┐
                │  TTS (Piper)        │
                │  Voz en español     │
                └─────────────────────┘
```

---

## 🔧 Tecnologías Utilizadas

| Componente | Tecnología | Propósito |
|-----------|-----------|----------|
| **Bot** | python-telegram-bot | Interface con Telegram |
| **IA** | Ollama + Phi3:mini | Generación de respuestas |
| **Voz→Texto** | Whisper (OpenAI) | Transcripción de audio |
| **Texto→Voz** | Piper TTS | Síntesis de voz en español |
| **Memoria** | SQLite + FTS5 | Base de datos local |
| **Búsqueda Semántica** | Sentence Transformers | Embeddings (384 dim) |
| **RAG** | ChromaDB | Indexación de documentos |
| **Noticias** | DuckDuckGo Search | Búsqueda sin rastreo |
| **Clima** | wttr.in | API pública sin autenticación |

---

## 💡 Características Principales

### 1. 🎤 Voz Conversacional
- Transcripción de audio en tiempo real (Whisper)
- Síntesis de voz en español (Piper TTS)
- Reconocimiento de intención automático

### 2. 🧠 Memoria Semántica Híbrida
- **SQLite**: Almacenamiento persistente
- **FTS5**: Búsqueda por palabras clave
- **Embeddings**: Búsqueda por significado
- **Combinación**: Resultados más precisos

### 3. 📚 RAG (Retrieval-Augmented Generation)
- Indexación de documentos PDF/TXT
- Búsqueda de contexto relevante
- Respuestas basadas en conocimiento personalizado

### 4. 📦 Sistema de Skills Modulares
Permite agregar funcionalidades rápidamente sin modificar el bot principal:

```python
# Estructura de un skill
def match(texto):
    return "palabra_clave" in texto.lower()

def run(texto, contexto):
    return "respuesta instantánea"
```

### 5. 🛡️ Seguridad
- Confirmación de comandos peligrosos
- Restricción de directorios
- Validación de entrada
- Aislamiento por usuario

### 6. 🌐 Completamente Privado
- **100% local** (excepto búsquedas opcionales)
- No envía datos personales a la nube
- Histórico almacenado localmente
- Control total del usuario

---

## 📊 Flujo de Procesamiento

### Ejemplo Práctico: "¿Qué tiempo hace en Barcelona?"

```
1. ENTRADA (Telegram)
   └─ Usuario envía mensaje de voz o texto

2. TRANSCRIPCIÓN (Whisper)
   └─ Convierte voz a: "¿qué tiempo hace en Barcelona?"

3. DETECCIÓN DE SKILL
   └─ Sistema detecta palabra clave: "tiempo"
   └─ Match de skill "tiempo.py"

4. EJECUCIÓN SKILL (Rápido)
   └─ Llama API wttr.in
   └─ Respuesta: "Barcelona: ☀️ +24°C, viento 10km/h"
   └─ Tiempo: ~1.5 segundos ⚡

5. SÍNTESIS DE VOZ
   └─ Piper genera audio en español
   └─ Envía a Telegram

6. RESPUESTA USUARIO
   └─ Recibe texto + audio
   └─ Lee mensaje en voz alta
```

### Flujo Alternativo: "¿Me enseñaste algo sobre programación?"

```
1. ENTRADA
   └─ Pregunta: "¿Me enseñaste algo sobre programación?"

2. INTENTAR SKILL
   └─ No hay match con skills → continuar

3. BUSCAR EN MEMORIA
   └─ Búsqueda semántica + keywords
   └─ Encuentra: "lenguaje favorito = Python"
   └─ Similitud: 89%

4. BUSCAR EN RAG
   └─ Documento indexado encontrado
   └─ Contexto sobre Python

5. GENERAR CON IA (Ollama)
   └─ Input: pregunta + memoria + RAG
   └─ Output: "Tu lenguaje favorito es Python. Según..."
   └─ Tiempo: ~3-6 segundos

6. SÍNTESIS + RESPUESTA
   └─ Convierte a voz
   └─ Envía usuario
```

---

## 🎮 Comandos Disponibles

### Memoria
| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `/aprender` | Guardar información | `/aprender mi ciudad = Madrid` |
| `/recordar` | Buscar en memoria | `/recordar ciudad donde vivo` |
| `/lista` | Ver todo lo memorizado | `/lista` |
| `/olvidar` | Borrar información | `/olvidar mi ciudad` |

### Sistema
| Comando | Descripción |
|---------|-------------|
| `/start` | Mostrar ayuda |
| `/comando` | Ejecutar comando Linux |
| `/personalidad` | Cambiar personalidad del bot |

### Conversación Natural
- "¿Qué tiempo hace?" → Skill de clima
- "Noticias de IA" → Skill de noticias
- "¿Quién soy?" → Búsqueda en memoria
- Cualquier otra pregunta → IA local

---

## 📁 Estructura de Archivos

```
~/.telegram_bot_memoria.db          # Base de datos SQLite
~/.telegram_bot_personalidad.json   # Configuración del bot
~/.telegram_bot_skills/             # Skills personalizadas
  ├── tiempo.py
  ├── noticias.py
  ├── comandos_linux.py
  └── inventario_red.py

~/HAL9000/
├── rag_db/                         # Base de datos ChromaDB
└── es_ES-davefx-medium.onnx       # Modelo de voz

HAL9000_LOCAL/
├── 0_ASISTENTE_CODEGIT_VOZ.py    # Bot principal
├── INSTALL.md                     # Guía de instalación
├── PROYECTO.md                    # Este archivo
├── README.md                       # Readme
├── RESUMEN.txt                    # Flujo visual
└── [skills individuales]
```

---

## 🚀 Casos de Uso

### 1. **Asistente Personal**
- Gestionar tareas y recordatorios
- Responder preguntas personalizadas
- Mantener base de conocimiento privada

### 2. **Desarrollador/SysAdmin**
- Ejecutar comandos Linux desde Telegram
- Consultar estado del sistema
- Buscar información en documentación indexada

### 3. **Estudiante**
- Guardar apuntes en memoria
- Buscar información por significado
- Generar respuestas a preguntas

### 4. **Privacidad Total**
- Sin envío de datos a cloud
- Control total del almacenamiento
- Sin rastreo de actividad

---

## 📊 Rendimiento

| Operación | Tiempo | Notas |
|-----------|--------|-------|
| Skill (tiempo/noticias) | 1-2s | Respuesta instantánea |
| IA + Memoria | 3-6s | Con búsqueda semántica |
| Transcripción voz | 2-3s | Whisper base (CPU) |
| Síntesis voz | 1-2s | Piper TTS |
| **Total (voz→voz)** | **~8-15s** | Incluyendo I/O |

### Requisitos de Recursos
- **CPU**: ~20-30% durante IA
- **RAM**: ~800MB (Ollama) + ~400MB (app)
- **Almacenamiento**: ~500MB modelos + ~100MB por 1000 memorias

---

## 🔐 Privacidad y Seguridad

✅ **Lo que ES privado:**
- Datos de memoria (SQLite local)
- Conversaciones (no se envían a servidores)
- Documentos RAG (indexados localmente)
- Comandos ejecutados

⚠️ **Lo que NO es privado:**
- Búsquedas de clima (wttr.in - sin rastreo)
- Búsquedas de noticias (DuckDuckGo - sin rastreo)
- Conexión con Telegram (necesaria para recibir mensajes)

---

## 🛠️ Personalización

### Agregar Skills Personalizadas
1. Crear archivo en `~/.telegram_bot_skills/mi_skill.py`
2. Implementar `match()` y `run()`
3. Reiniciar bot - cargará automáticamente

### Cambiar Personalidad
```bash
/personalidad nombre = Mi Asistente
/personalidad rol = experto en matemáticas
/personalidad rasgos = preciso, educado, ingenioso
```

### Indexar Documentos en RAG
```bash
python cargar_pdf.py documento.pdf
```

---

## 🎓 Aprendizaje y Desarrollo

### Para Desarrolladores
- Código modular y bien documentado
- Sistema de plugins fácil de extender
- Ejemplos de skills incluidos
- Logs detallados para debugging

### Para Usuarios
- Interface intuitiva (Telegram)
- Comandos simples y naturales
- Respuestas por voz y texto
- Memoria que aprende de ti

---

## 🚀 Próximas Mejoras Planificadas

- [ ] Soporte para múltiples modelos Ollama
- [ ] Caché inteligente de embeddings
- [ ] Interfaz web alternativa
- [ ] Sincronización entre dispositivos
- [ ] Más modelos de voz regional
- [ ] Plugin store para skills
- [ ] Analytics locales

---

## 📝 Licencia

Este proyecto es software libre. Úsalo, modifícalo y comparte libremente.

---

## 🤝 Contribuir

Se aceptan:
- Skills nuevas
- Mejoras de rendimiento
- Documentación
- Reportes de bugs

---

## 💬 Contacto y Soporte

- **GitHub**: [apocanow/HAL9000_LOCAL](https://github.com/apocanow/HAL9000_LOCAL)
- **Issues**: Reporta bugs y sugerencias
- **Documentación**: Ver `INSTALL.md` y `RESUMEN.txt`

---

## 🎉 ¡Disfruta tu asistente inteligente local!

**HAL9000_LOCAL** te brinda todo el poder de la IA moderna con la privacidad que mereces.

```
    🤖
   [██]  Asistente IA 100% Local
   [██]  Privado • Rápido • Inteligente
   [██]  Powered by Ollama + Telegram
    ▔▔
```
