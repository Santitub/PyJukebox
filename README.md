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
- Biblioteca `python-vlc`
- Biblioteca `rich` (para la interfaz de usuario)

## Instalación 🔧

1. Instala VLC Media Player:
   - Linux: `sudo apt install vlc`
   - Windows: Descarga desde [videolan.org](https://www.videolan.org/vlc/)
   - macOS: `brew install vlc`

2. (Opcional) Crea y activa un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
````

3. Instala las dependencias de Python:

```bash
pip install python-vlc rich
```

4. Clona este repositorio:

```bash
git clone https://github.com/tu-usuario/pyjukebox.git
cd pyjukebox
```

## Uso 🎮

1. Ejecuta el reproductor:

```bash
python pyjukebox.py
```

2. Navegación:

   * La interfaz te permitirá seleccionar tu directorio de música al inicio
   * Puedes arrastrar una carpeta al iniciar el programa o seleccionarla desde la interfaz
   * La navegación se realiza completamente desde la interfaz, sin necesidad de escribir comandos

3. Controles de navegación:

   * Flechas arriba/abajo: Navegación rápida sin cooldown
   * Rueda del ratón: Navegación con cooldown suave
   * Enter: Abrir carpeta
   * B: Volver atrás

4. Controles de reproducción:

   * Espacio: Reproducir/Pausar
   * N: Siguiente canción
   * P: Canción anterior
   * S: Detener
   * Flechas izquierda/derecha: Avanzar/Retroceder 10 segundos
   * +/-: Ajustar volumen
   * R: Cambiar modo de repetición

5. Otros controles:

   * Q: Salir del programa
   * F: Buscar canción

## Preferencias 💾

El programa guarda automáticamente las preferencias en `~/.pyjukebox/config.json`:

* Último directorio visitado
* Volumen actual
* Modo de repetición
* Preferencias de visualización

Los logs de la aplicación se guardan en `~/.pyjukebox/debug.log`

## Licencia 📄

Este proyecto está bajo la Licencia **GPL-3.0**. Ver el archivo [LICENSE](./LICENSE) para más detalles.
