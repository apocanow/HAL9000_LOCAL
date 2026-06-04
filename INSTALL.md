# 🤖 HAL9000 LOCAL - Guía de Instalación

**HAL9000 LOCAL** es un asistente inteligente con IA local, voz y memoria semántica que se ejecuta como un bot de Telegram.

---

## 📋 Requisitos del Sistema

### Hardware Mínimo
- **CPU**: Intel/AMD con soporte SSE4 (2011+) o ARM64
- **RAM**: 4 GB mínimo (8 GB recomendado)
- **Almacenamiento**: 10 GB libres

### Software Requerido
- Python 3.10+
- Git
- Audio (ALSA/Pulseaudio)

---

## 🐧 Instalación en ARCH LINUX

### 1. Actualizar el Sistema
```bash
sudo pacman -Syu
```

### 2. Instalar Dependencias del Sistema
```bash
sudo pacman -S python python-pip base-devel git alsa-utils ffmpeg
```

### 3. Crear Directorio del Proyecto
```bash
mkdir -p ~/HAL9000_LOCAL
cd ~/HAL9000_LOCAL
git clone https://github.com/apocanow/HAL9000_LOCAL.git .
```

### 4. Crear Entorno Virtual
```bash
python -m venv venv
source venv/bin/activate
```

### 5. Instalar Dependencias Python
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

#### Si `requirements.txt` no existe, instala manualmente:
```bash
pip install python-telegram-bot ollama chromadb sentence-transformers faster-whisper duckduckgo-search requests
```

### 6. Instalar Ollama (IA Local)
```bash
# Descargar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Iniciar servicio
ollama serve &

# Descargar modelo en otra terminal
ollama pull phi3:mini
```

### 7. Instalar Piper (Text-to-Speech)
```bash
# Instalar desde AUR (recomendado)
yay -S piper-tts

# O compilar desde fuente
git clone https://github.com/rhasspy/piper.git
cd piper/src/cpp
cmake .
make
sudo make install
```

### 8. Descargar Modelo de Voz Español
```bash
mkdir -p ~/HAL9000
cd ~/HAL9000
wget https://github.com/rhasspy/piper/releases/download/2023.11.14-1/es_ES-davefx-medium.onnx
```

### 9. Configurar Bot de Telegram
1. Habla con [@BotFather](https://t.me/botfather) en Telegram
2. Crea un nuevo bot y obtén el TOKEN
3. Edita `0_ASISTENTE_CODEGIT_VOZ.py`:

```python
TOKEN = "tu_token_aqui"
PIPER_MODEL = "/home/tu_usuario/HAL9000/es_ES-davefx-medium.onnx"
```

### 10. Ejecutar el Bot
```bash
cd ~/HAL9000_LOCAL
source venv/bin/activate
python 0_ASISTENTE_CODEGIT_VOZ.py
```

---

## 🐧 Instalación en DEBIAN (11, 12)

### 1. Actualizar el Sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Instalar Dependencias del Sistema
```bash
sudo apt install -y python3.10 python3.10-venv python3-pip python3-dev \
    build-essential git alsa-utils ffmpeg libsndfile1 portaudio19-dev
```

### 3. Crear Directorio del Proyecto
```bash
mkdir -p ~/HAL9000_LOCAL
cd ~/HAL9000_LOCAL
git clone https://github.com/apocanow/HAL9000_LOCAL.git .
```

### 4. Crear Entorno Virtual
```bash
python3.10 -m venv venv
source venv/bin/activate
```

### 5. Instalar Dependencias Python
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

#### Si `requirements.txt` no existe:
```bash
pip install python-telegram-bot ollama chromadb sentence-transformers faster-whisper duckduckgo-search requests
```

### 6. Instalar Ollama
```bash
# Descargar e instalar
curl -fsSL https://ollama.ai/install.sh | sh

# Iniciar servicio
ollama serve &

# Descargar modelo (en otra terminal)
ollama pull phi3:mini
```

### 7. Instalar Piper (Text-to-Speech)
```bash
# Opción 1: Desde repositorio (si está disponible)
sudo apt install -y piper

# Opción 2: Compilar desde fuente
git clone https://github.com/rhasspy/piper.git
cd piper/src/cpp
sudo apt install -y cmake build-essential
cmake .
make
sudo make install
```

### 8. Descargar Modelo de Voz Español
```bash
mkdir -p ~/HAL9000
cd ~/HAL9000
wget https://github.com/rhasspy/piper/releases/download/2023.11.14-1/es_ES-davefx-medium.onnx
```

### 9. Configurar Bot de Telegram
1. Habla con [@BotFather](https://t.me/botfather) en Telegram
2. Crea un nuevo bot y obtén el TOKEN
3. Edita `0_ASISTENTE_CODEGIT_VOZ.py`:

```python
TOKEN = "tu_token_aqui"
PIPER_MODEL = "/home/tu_usuario/HAL9000/es_ES-davefx-medium.onnx"
```

### 10. Ejecutar el Bot
```bash
cd ~/HAL9000_LOCAL
source venv/bin/activate
python 0_ASISTENTE_CODEGIT_VOZ.py
```

---

## 📋 Configuración Avanzada

### Variables de Entorno
```bash
# .env (crear en el directorio del proyecto)
TELEGRAM_TOKEN=tu_token_aqui
OLLAMA_MODEL=phi3:mini
PIPER_MODEL=/home/usuario/HAL9000/es_ES-davefx-medium.onnx
```

### Crear Archivos de Configuración
```bash
# Base de datos de memoria
~/.telegram_bot_memoria.db

# Personalidad del bot
~/.telegram_bot_personalidad.json

# Skills personalizados
~/.telegram_bot_skills/
  ├── tiempo.py
  ├── noticias.py
  ├── comandos_linux.py
  └── tu_skill_personalizado.py
```

### Ejemplo de Skill Personalizado
Crea `~/.telegram_bot_skills/mi_skill.py`:

```python
def match(texto):
    """Devuelve True si esta skill puede manejar el texto"""
    return "palabra_clave" in texto.lower()

def run(texto, contexto):
    """Ejecuta la skill"""
    return "Tu respuesta personalizada aquí"
```

---

## 🚀 Uso Básico

### Comandos Principales

| Comando | Descripción |
|---------|-------------|
| `/start` | Mostrar ayuda |
| `/aprender clave = valor` | Guardar información en memoria |
| `/recordar texto` | Buscar en memoria |
| `/lista` | Ver todo lo que sabe |
| `/olvidar clave` | Borrar información |
| `/comando ls -la` | Ejecutar comando Linux |
| `/personalidad campo = valor` | Cambiar personalidad del bot |

### Ejemplos de Uso

```
Usuario: "¿qué tiempo hace en Barcelona?"
HAL9000: 🌤️ Barcelona: ☀️ +24°C, viento 10km/h

Usuario: "noticias de inteligencia artificial"
HAL9000: 📰 **Noticias sobre 'inteligencia artificial':**
         1. Nuevo modelo de IA revolucionario...

Usuario: /aprender mi color favorito = azul
HAL9000: ✅ Aprendido: mi color favorito = azul

Usuario: /recordar color favorito
HAL9000: 🧠 Recordatorio encontrado (similitud: 89.0%)
         💬 Valor: azul
```

---

## 🐛 Solución de Problemas

### Ollama no inicia
```bash
# Verificar si está ejecutándose
ps aux | grep ollama

# Reiniciar manualmente
ollama serve

# Verificar conexión
curl http://localhost:11434/api/tags
```

### Whisper falla
```bash
# Verificar audio
arecord -l

# Descargar modelo manualmente
python3 -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu')"
```

### Piper no genera voz
```bash
# Verificar ALSA
aplay -l

# Probar Piper directamente
echo "Hola mundo" | piper --model ~/HAL9000/es_ES-davefx-medium.onnx --output_file test.wav
aplay test.wav
```

### Error de permisos en ChromaDB
```bash
chmod -R 755 ~/.telegram_bot_*
```

---

## 📊 Características Principales

✨ **Características Activas:**
- 🎤 Transcripción de voz (Whisper)
- 🔊 Síntesis de voz (Piper TTS)
- 🧠 IA local (Ollama + Phi3:mini)
- 📚 Búsqueda en documentos (RAG con ChromaDB)
- 💾 Memoria híbrida semántica (SQLite + embeddings)
- 📰 Búsqueda de noticias (DuckDuckGo)
- 🌤️ Información meteorológica (wttr.in)
- 📁 Gestión de archivos
- 💻 Ejecución de comandos Linux
- 📦 Sistema de skills modulares
- 🛡️ Confirmación de comandos peligrosos

---

## 📚 Estructura del Proyecto

```
HAL9000_LOCAL/
├── 0_ASISTENTE_CODEGIT_VOZ.py    # Bot principal
├── INSTALL.md                      # Esta guía
├── PROYECTO.md                     # Descripción del proyecto
├── README.md                       # Readme básico
├── RESUMEN.txt                     # Flujo del sistema
├── SKILLS.README                   # Info de skills
└── skills/
    ├── tiempo.py                   # Weather information
    ├── noticias.py                 # News fetching
    ├── comandos_linux.py           # Linux commands
    └── inventario_red.py           # Network inventory
```

---

## 🔧 Mantenimiento

### Limpiar Base de Datos de Memoria
```bash
rm ~/.telegram_bot_memoria.db
```

### Actualizar Modelos
```bash
source ~/HAL9000_LOCAL/venv/bin/activate
ollama pull phi3:mini
```

### Logs del Bot
```bash
tail -f ~/.telegram_bot.log
```

---

## 📖 Documentación Adicional

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Ollama Modelos](https://ollama.ai)
- [Whisper](https://github.com/openai/whisper)
- [Piper TTS](https://github.com/rhasspy/piper)
- [ChromaDB](https://www.trychroma.com/)

---

## 📝 Licencia

Este proyecto es de código abierto. Úsalo libremente.

---

## 💬 Soporte

Si tienes problemas:
1. Revisa el archivo `PROYECTO.md` para más contexto
2. Verifica los logs del sistema
3. Abre un issue en GitHub

**¡Disfruta tu asistente inteligente local! 🤖**
