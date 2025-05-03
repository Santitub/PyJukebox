# PyJukebox 🎵

Un reproductor de música en la terminal con interfaz de usuario intuitiva y soporte para múltiples formatos de audio.

![Python](https://img.shields.io/badge/python-3.6%2B-brightgreen)
![GPL-3.0 License](https://img.shields.io/badge/license-GPL%203.0-blue)

## Características ✨

- 🎵 Reproducción de múltiples formatos de audio (MP3, WAV, FLAC, OGG, M4A, AAC)
- 📁 Navegación por carpetas y archivos
- 🎮 Controles intuitivos con teclado y ratón
- 🔄 Modos de repetición (desactivado, canción actual, carpeta actual)
- 🔊 Control de volumen
- ⏩ Avance rápido y retroceso en la canción actual
- 🎨 Interfaz de usuario con colores y emojis
- 📊 Barra de progreso visual
- 🐭 Soporte para ratón y rueda de desplazamiento
- 🔍 Búsqueda rápida de canciones
- 💾 Guardado automático de preferencias
- 📝 Registro de errores y eventos

## Requisitos 📋

- Python 3.6 o superior
- VLC Media Player
- Biblioteca python-vlc
- Biblioteca rich (para la interfaz de usuario)

## Plataformas compatibles 🌍

PyJukebox funciona en las siguientes plataformas:
- **Windows**
- **Linux**
- **macOS**
- **Android** (Termux)

## Métodos de Instalación 🔧

### 1. Instalación usando Docker 🐳

Si prefieres usar Docker para ejecutar PyJukebox sin tener que instalar dependencias adicionales, sigue estos pasos:

#### 1.1 Construye la imagen Docker:

Navega a la carpeta del proyecto y construye la imagen de Docker:

```bash
docker build -t pyjukebox .
````

#### 1.2 Ejecuta el contenedor Docker:

Ejecuta el siguiente comando para lanzar el contenedor con acceso a tu sistema de archivos local y al dispositivo de sonido:

```bash
docker run -it --rm \
  -v /:/mnt/host \
  -e PULSE_SERVER=unix:${XDG_RUNTIME_DIR}/pulse/native \
  -v ${XDG_RUNTIME_DIR}/pulse/native:${XDG_RUNTIME_DIR}/pulse/native \
  -v ~/.config/pulse/cookie:/root/.config/pulse/cookie \
  --device /dev/snd \
  pyjukebox:latest
```

Este comando monta el sistema de archivos local (`/`) dentro del contenedor y permite que PyJukebox acceda a los archivos de música en tu PC.

---

### 2. Instalación Manual 🔨

Si prefieres instalar PyJukebox manualmente en tu máquina, sigue estos pasos:

#### 2.1 Instala VLC Media Player:

* **Linux**: `sudo apt install vlc`
* **Windows**: Descarga desde [videolan.org](https://www.videolan.org/vlc/)
* **macOS**: `brew install vlc`

#### 2.2 (Opcional) Crea y activa un entorno virtual:

Para evitar conflictos con otras dependencias del sistema, es recomendable usar un entorno virtual:

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

#### 2.3 Instala las dependencias de Python:

Instala las bibliotecas necesarias para que PyJukebox funcione correctamente:

```bash
pip install python-vlc rich
```

#### 2.4 Clona este repositorio:

Clona el repositorio de PyJukebox desde GitHub y navega a la carpeta del proyecto:

```bash
git clone https://github.com/tu-usuario/pyjukebox.git
cd pyjukebox
```

#### 2.5 Ejecuta el reproductor:

Lanza el reproductor de música:

```bash
python pyjukebox.py
```

---

## Uso 🎮

1. **Navegación:**

   * La interfaz te permitirá seleccionar tu directorio de música al inicio.
   * Puedes arrastrar una carpeta al iniciar el programa o seleccionarla desde la interfaz.
   * La navegación se realiza completamente desde la interfaz, sin necesidad de escribir comandos.

2. **Controles de navegación:**

   * Flechas arriba/abajo: Navegación rápida sin cooldown.
   * Rueda del ratón: Navegación con cooldown suave.
   * Enter: Abrir carpeta.
   * B: Volver atrás.

3. **Controles de reproducción:**

   * Espacio: Reproducir/Pausar.
   * N: Siguiente canción.
   * P: Canción anterior.
   * S: Detener.
   * Flechas izquierda/derecha: Avanzar/Retroceder 10 segundos.
   * +/-: Ajustar volumen.
   * R: Cambiar modo de repetición.

4. **Otros controles:**

   * Q: Salir del programa.
   * F: Buscar canción.

## Preferencias 💾

El programa guarda automáticamente las preferencias en `~/.pyjukebox/config.json`:

* Último directorio visitado.
* Volumen actual.
* Modo de repetición.
* Preferencias de visualización.

Los logs de la aplicación se guardan en `~/.pyjukebox/debug.log`.

## Licencia 📄

Este proyecto está bajo la Licencia **GPL-3.0**. Ver el archivo [LICENSE](./LICENSE) para más detalles.
