# 🔧 Guía de Instalación - HAL9000_LOCAL

Instalación paso a paso para diferentes distribuciones Linux.

---

## 📋 Requisitos del Sistema

### Hardware Mínimo
- **CPU**: Intel/AMD con SSE4 (2011+) o ARM64
- **RAM**: 4GB (8GB recomendado)
- **Almacenamiento**: 10GB libres
- **Audio**: ALSA o PulseAudio

### Software Requerido
- **Python**: 3.10+
- **Git**: Para clonar el repositorio
- **Conexión**: Internet para descargar modelos

---

## 🐧 Instalación en ARCH LINUX

### 1. Actualizar Sistema

```bash
sudo pacman -Syu
```

### 2. Instalar Dependencias del Sistema

```bash
sudo pacman -S python python-pip base-devel git alsa-utils ffmpeg
```

### 3. Clonar Repositorio

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
pip install python-telegram-bot ollama chromadb sentence-transformers faster-whisper duckduckgo-search requests
```

### 6. Instalar Ollama (IA Local)

```bash
# Descargar e instalar
curl -fsSL https://ollama.ai/install.sh | sh

# Iniciar servicio en background
ollama serve &

# Descargar modelo (en otra terminal)
ollama pull phi3:mini

# Verificar
curl http://localhost:11434/api/tags
```

### 7. Instalar Piper TTS

```bash
# Opción 1: Desde AUR (recomendado)
yay -S piper-tts

# Opción 2: Compilar desde fuente
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

### 9. Obtener Token de Telegram

1. Abre [BotFather en Telegram](https://t.me/botfather)
2. Escribe `/newbot`
3. Sigue las instrucciones y obtén el TOKEN

### 10. Configurar Bot

Edita `0_ASISTENTE_CODEGIT_VOZ.py`:

```python
TOKEN = "tu_token_aqui"
PIPER_MODEL = "/home/tu_usuario/HAL9000/es_ES-davefx-medium.onnx"
```

### 11. Ejecutar Bot

```bash
cd ~/HAL9000_LOCAL
source venv/bin/activate
python 0_ASISTENTE_CODEGIT_VOZ.py
```

✅ El bot está listo cuando ves: `Bot iniciado correctamente`

---

## 🐧 Instalación en DEBIAN/UBUNTU

### 1. Actualizar Sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Instalar Dependencias del Sistema

```bash
sudo apt install -y python3.10 python3.10-venv python3-pip python3-dev \
    build-essential git alsa-utils ffmpeg libsndfile1 portaudio19-dev
```

### 3. Clonar Repositorio

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

### 7. Instalar Piper TTS

```bash
# Opción 1: Desde repositorio
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

### 9-11. Obtener Token, Configurar y Ejecutar

Sigue los pasos 9-11 de la sección Arch Linux arriba.

---

## 📋 Configuración Avanzada

### Variables de Entorno

Crea `.env` en el directorio del proyecto:

```bash
TELEGRAM_TOKEN=tu_token_aqui
OLLAMA_MODEL=phi3:mini
OLLAMA_HOST=http://localhost:11434
PIPER_MODEL=/home/usuario/HAL9000/es_ES-davefx-medium.onnx
PIPER_DEVICE=cpu
```

### Directorios de Configuración

Los archivos se guardan en `~/.telegram_bot_*`:

```bash
# Base de datos de memoria
~/.telegram_bot_memoria.db

# Configuración de personalidad
~/.telegram_bot_personalidad.json

# Skills personalizados
~/.telegram_bot_skills/
  ├── tiempo.py
  ├── noticias.py
  ├── comandos_linux.py
  └── tu_skill.py
```

### Crear Skill Personalizado

Crea `~/.telegram_bot_skills/mi_skill.py`:

```python
def match(texto):
    """Devuelve True si esta skill puede manejar el texto"""
    return "palabra_clave" in texto.lower()

def run(texto, contexto):
    """Ejecuta la skill"""
    return "Tu respuesta personalizada"
```

El bot cargará automáticamente el skill en el reinicio.

---

## 🔧 Ejecutar como Servicio Systemd

Para ejecutar automáticamente al iniciar el sistema:

### 1. Crear Archivo de Servicio

```bash
sudo nano /etc/systemd/system/hal9000.service
```

### 2. Añadir Contenido

```ini
[Unit]
Description=HAL9000 Local AI Assistant
After=network.target

[Service]
Type=simple
User=tu_usuario
WorkingDirectory=/home/tu_usuario/HAL9000_LOCAL
ExecStart=/home/tu_usuario/HAL9000_LOCAL/venv/bin/python /home/tu_usuario/HAL9000_LOCAL/0_ASISTENTE_CODEGIT_VOZ.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 3. Habilitar y Iniciar

```bash
sudo systemctl daemon-reload
sudo systemctl enable hal9000
sudo systemctl start hal9000

# Ver estado
sudo systemctl status hal9000

# Ver logs
journalctl -u hal9000 -f
```

---

## 🐛 Solución de Problemas

### Ollama No Inicia

```bash
# Verificar si está ejecutándose
ps aux | grep ollama

# Reiniciar manualmente
ollama serve

# Verificar conexión
curl http://localhost:11434/api/tags

# Si no responde
pkill -f "ollama serve"
ollama serve &
```

### Whisper Falla

```bash
# Verificar audio
arecord -l

# Descargar modelo manualmente
python3 -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu')"

# Probar grabación
arecord -d 3 test.wav
```

### Piper No Genera Voz

```bash
# Verificar ALSA
aplay -l

# Probar Piper directamente
echo "Hola mundo" | piper --model ~/HAL9000/es_ES-davefx-medium.onnx --output_file test.wav
aplay test.wav

# Si no hay sonido, revisar volumen
amixer set Master 100%
```

### ChromaDB Error de Permisos

```bash
chmod -R 755 ~/.telegram_bot_*
```

### Problema: "No module named 'telegram'"

```bash
# Verificar que el venv está activado
source venv/bin/activate

# Reinstalar dependencias
pip install --upgrade python-telegram-bot

# Verificar instalación
python -c "import telegram; print(telegram.__version__)"
```

### Problema: Token de Telegram Inválido

```bash
# Verificar formato del token
# Debe ser: 123456789:ABCdefGHIjklMNOpqrSTuvWXYZ1234567890

# Si es correcto, verificar permisos en BotFather
# El bot debe estar activo y no en modo prueba
```

### Problema: Ollama Lento

```bash
# Verificar recursos disponibles
free -h
top -p $(pgrep -f "ollama serve" | head -1)

# Opciones:
# 1. Usar modelo más ligero: ollama pull orca-mini
# 2. Aumentar RAM disponible
# 3. Usar GPU si está disponible: CUDA_VISIBLE_DEVICES=0 ollama serve
```

---

## 🔄 Actualizar Componentes

### Actualizar Ollama

```bash
# Actualizar instalación
curl -fsSL https://ollama.ai/install.sh | sh

# Actualizar modelo
ollama pull phi3:mini
```

### Actualizar Dependencias Python

```bash
cd ~/HAL9000_LOCAL
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Actualizar Código del Bot

```bash
cd ~/HAL9000_LOCAL
git pull origin main
```

---

## 📊 Verificación Post-Instalación

Ejecuta estos comandos para verificar todo funciona:

```bash
# Python
python --version  # 3.10+

# Ollama
ollama list  # Debe mostrar phi3:mini

# Piper
which piper  # Debe mostrar path

# Telegram bot
python -c "from telegram.ext import Application; print('OK')"

# Base de datos
test -f ~/.telegram_bot_memoria.db && echo "DB exists" || echo "DB will be created"
```

---

## 🎯 Próximos Pasos

1. ✅ Instalación completa
2. 📖 Lee [Descripción del Proyecto](PROJECT.md)
3. 🚀 Consulta [Uso Básico](../README.md#-uso-básico)
4. 🛠️ Crea [Skills Personalizados](DEVELOPMENT.md)
5. 📊 Entiende el [Flujo del Sistema](FLOW.md)

---

## ❓ ¿Problemas?

1. Revisa [Troubleshooting](TROUBLESHOOTING.md)
2. Consulta logs: `tail -f ~/.telegram_bot.log`
3. Abre un [issue en GitHub](https://github.com/apocanow/HAL9000_LOCAL/issues)

---

**¡Instalación completa! Ahora disfruta tu asistente IA local. 🤖**
