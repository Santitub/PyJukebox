import os
import platform
import subprocess
import vlc
from pathlib import Path
import shutil
import threading
import time
import json
import re
import curses
import curses.ascii
import logging
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text

# Configurar logging
logging.basicConfig(
    filename='debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Definir colores
COLOR_PAIRS = {
    'TITLE': 1,      # Amarillo sobre negro
    'STATUS': 2,     # Verde sobre negro
    'SELECTED': 3,   # Blanco sobre azul
    'NORMAL': 4,     # Blanco sobre negro
    'PROGRESS': 5,   # Cian sobre negro
    'CONTROLS': 6,   # Magenta sobre negro
    'ERROR': 7,      # Rojo sobre negro
}

class VLCInstaller:
    @staticmethod
    def install_vlc():
        system = platform.system().lower()
        try:
            if system == 'linux':
                if 'termux' in os.environ.get('PREFIX', ''):
                    # Termux (Android)
                    print("Instalando VLC para Termux...")
                    result = subprocess.run(['pkg', 'install', 'vlc', '-y'], capture_output=True, text=True)
                    if result.returncode != 0:
                        print("Error al instalar VLC en Termux. Por favor, instálalo manualmente.")
                        return False
                else:
                    # Linux
                    print("Instalando VLC para Linux...")
                    if os.path.exists('/usr/bin/apt'):
                        result = subprocess.run(['sudo', 'apt', 'update'], capture_output=True, text=True)
                        if result.returncode != 0:
                            print("Error al actualizar repositorios. Por favor, instala VLC manualmente.")
                            return False
                        result = subprocess.run(['sudo', 'apt', 'install', 'vlc', '-y'], capture_output=True, text=True)
                    elif os.path.exists('/usr/bin/pacman'):
                        result = subprocess.run(['sudo', 'pacman', '-S', 'vlc', '--noconfirm'], capture_output=True, text=True)
                    elif os.path.exists('/usr/bin/dnf'):
                        result = subprocess.run(['sudo', 'dnf', 'install', 'vlc', '-y'], capture_output=True, text=True)
                    else:
                        print("No se pudo determinar el gestor de paquetes. Por favor, instala VLC manualmente.")
                        return False
                    
                    if result.returncode != 0:
                        print("Error al instalar VLC. Por favor, instálalo manualmente.")
                        return False
            elif system == 'windows':
                print("Por favor, instala VLC manualmente desde https://www.videolan.org/vlc/")
                return False
            elif system == 'darwin':  # macOS
                print("Instalando VLC para macOS...")
                result = subprocess.run(['brew', 'install', 'vlc'], capture_output=True, text=True)
                if result.returncode != 0:
                    print("Error al instalar VLC con Homebrew. Por favor, instálalo manualmente.")
                    return False
            return True
        except Exception as e:
            print(f"Error durante la instalación: {str(e)}")
            return False

    @staticmethod
    def check_vlc_installed():
        # Primero verificar si vlc está en el PATH
        if shutil.which('vlc'):
            return True
            
        system = platform.system().lower()
        if system == 'linux':
            if 'termux' in os.environ.get('PREFIX', ''):
                return os.path.exists('/data/data/com.termux/files/usr/bin/vlc')
            return os.path.exists('/usr/bin/vlc')
        elif system == 'windows':
            # Verificar múltiples ubicaciones comunes en Windows
            possible_paths = [
                'C:\\Program Files\\VideoLAN\\VLC\\vlc.exe',
                'C:\\Program Files (x86)\\VideoLAN\\VLC\\vlc.exe',
                os.path.expanduser('~\\AppData\\Local\\Programs\\VLC\\vlc.exe')
            ]
            return any(os.path.exists(path) for path in possible_paths)
        elif system == 'darwin':
            # Verificar múltiples ubicaciones comunes en macOS
            possible_paths = [
                '/Applications/VLC.app',
                os.path.expanduser('~/Applications/VLC.app'),
                '/opt/homebrew/bin/vlc',
                '/usr/local/bin/vlc'
            ]
            return any(os.path.exists(path) for path in possible_paths)
        return False

class MP3Player:
    def __init__(self, stdscr):
        logging.info("Inicializando reproductor MP3")
        self.stdscr = stdscr
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.current_song = None
        self.is_playing = False
        self.last_directory = None
        self.songs = []
        self.folders = []
        self.current_song_index = 0
        self.repeat_mode = 0  # 0: desactivada, 1: repetir canción, 2: repetir carpeta
        self.volume = 50
        self.player.audio_set_volume(self.volume)
        self.supported_extensions = ['*.mp3', '*.wav', '*.flac', '*.ogg', '*.m4a', '*.aac']
        self.console = Console()
        self.current_path = None
        self.parent_path = None
        self.load_preferences()
        self.selected_index = 0
        self.max_items_per_page = 10
        self.current_page = 0
        self.init_colors()
        self.error_message = None
        self.error_timer = 0
        self.key_pressed = False
        logging.info("Reproductor MP3 inicializado correctamente")

    def init_colors(self):
        """Inicializar los pares de colores"""
        curses.start_color()
        curses.init_pair(COLOR_PAIRS['TITLE'], curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(COLOR_PAIRS['STATUS'], curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_PAIRS['SELECTED'], curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(COLOR_PAIRS['NORMAL'], curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(COLOR_PAIRS['PROGRESS'], curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_PAIRS['CONTROLS'], curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(COLOR_PAIRS['ERROR'], curses.COLOR_RED, curses.COLOR_BLACK)

    def format_time(self, seconds):
        """Formatear tiempo en segundos a MM:SS"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def draw_progress_bar(self, y, x, width, progress, color_pair):
        """Dibujar una barra de progreso con estilo"""
        # Caracteres Unicode para la barra de progreso
        chars = [' ', '▏', '▎', '▍', '▌', '▋', '▊', '▉', '█']
        
        # Calcular la posición exacta
        exact_position = progress * width
        full_blocks = int(exact_position)
        partial_block = int((exact_position - full_blocks) * 8)
        
        # Dibujar la barra
        self.stdscr.addstr(y, x, '[')
        self.stdscr.addstr(y, x + 1, '█' * full_blocks, curses.color_pair(color_pair))
        if full_blocks < width - 2:
            self.stdscr.addstr(y, x + 1 + full_blocks, chars[partial_block], curses.color_pair(color_pair))
            self.stdscr.addstr(y, x + 1 + full_blocks + 1, ' ' * (width - 2 - full_blocks - 1))
        self.stdscr.addstr(y, x + width - 1, ']')

    def sanitize_filename(self, filename):
        """Limpiar caracteres especiales del nombre del archivo para la visualización"""
        cleaned = re.sub(r'[^\w\s\-\.]', ' ', filename)
        return cleaned[:40] + '...' if len(cleaned) > 40 else cleaned

    def load_preferences(self):
        """Cargar preferencias del usuario"""
        try:
            config_path = os.path.expanduser('~/.mp3player_config.json')
            logging.debug(f"Intentando cargar preferencias desde: {config_path}")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    prefs = json.load(f)
                    self.volume = prefs.get('volume', 50)
                    self.repeat_mode = prefs.get('repeat_mode', 0)
                    self.last_directory = prefs.get('last_directory', None)
                    self.player.audio_set_volume(self.volume)
                logging.info("Preferencias cargadas correctamente")
            else:
                # Initialize with default values
                self.volume = 50
                self.repeat_mode = 0
                self.last_directory = None
                self.player.audio_set_volume(self.volume)
                logging.info("No se encontró archivo de preferencias, usando valores por defecto")
        except Exception as e:
            error_msg = f"Error al cargar preferencias: {str(e)}"
            logging.error(error_msg)
            self.show_error("❌ Error al cargar preferencias", log_error=True)
            # Ensure default values are set even if there's an error
            self.volume = 50
            self.repeat_mode = 0
            self.last_directory = None
            self.player.audio_set_volume(self.volume)

    def save_preferences(self):
        """Guardar preferencias del usuario"""
        try:
            config_path = os.path.expanduser('~/.mp3player_config.json')
            logging.debug(f"Guardando preferencias en: {config_path}")
            prefs = {
                'volume': self.volume,
                'repeat_mode': self.repeat_mode,
                'last_directory': self.last_directory
            }
            with open(config_path, 'w') as f:
                json.dump(prefs, f)
            logging.info("Preferencias guardadas correctamente")
        except Exception as e:
            error_msg = f"Error al guardar preferencias: {str(e)}"
            logging.error(error_msg)
            self.show_error("❌ Error al guardar preferencias", log_error=True)

    def load_directory(self, directory):
        """Cargar contenido del directorio especificado"""
        try:
            logging.info(f"Intentando cargar directorio: {directory}")
            if not os.path.isdir(directory):
                error_msg = f"Directorio no válido: {directory}"
                self.show_error("❌ Directorio no válido", log_error=True)
                logging.error(error_msg)
                return False

            self.songs = []
            self.folders = []
            self.current_path = directory
            self.parent_path = os.path.dirname(directory)

            # Cargar carpetas
            for item in os.listdir(directory):
                full_path = os.path.join(directory, item)
                if os.path.isdir(full_path):
                    self.folders.append(full_path)

            # Cargar canciones
            for ext in self.supported_extensions:
                found = list(Path(directory).glob(ext))
                self.songs.extend(found)
                logging.debug(f"Encontrados {len(found)} archivos con extensión {ext}")
            
            self.songs = [str(song) for song in self.songs]
            self.folders.sort()
            self.songs.sort()
            
            self.last_directory = directory
            self.save_preferences()
            logging.info(f"Se cargaron {len(self.songs)} canciones y {len(self.folders)} carpetas correctamente")
            return True
        except Exception as e:
            error_msg = f"Error al cargar directorio {directory}: {str(e)}"
            self.show_error("❌ Error al cargar directorio", log_error=True)
            logging.error(error_msg)
            return False

    def show_error(self, message, duration=3, log_error=True):
        """Mostrar un mensaje de error temporal y registrarlo en el log"""
        self.error_message = message
        self.error_timer = time.time() + duration
        if log_error:
            logging.error(f"{message} - Canción actual: {self.current_song}")

    def clear_error(self):
        """Limpiar el mensaje de error"""
        self.error_message = None
        self.error_timer = 0

    def draw_interface(self):
        """Dibujar la interfaz completa"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Título
        title = "🎵 Reproductor MP3 🎵"
        self.stdscr.addstr(0, (width - len(title)) // 2, title, 
                          curses.color_pair(COLOR_PAIRS['TITLE']) | curses.A_BOLD)
        
        # Ruta actual
        if self.current_path:
            path_display = f"📁 {os.path.basename(self.current_path)}"
            if len(path_display) > width - 2:
                path_display = path_display[:width-5] + "..."
            self.stdscr.addstr(2, 0, path_display, curses.color_pair(COLOR_PAIRS['STATUS']))
        
        # Estado actual
        status = "▶️ Reproduciendo" if self.is_playing else "⏸️ Pausado" if self.current_song else "⏹️ Detenido"
        if self.current_song:
            status += f": {self.sanitize_filename(os.path.basename(self.current_song))}"
        self.stdscr.addstr(3, 0, status, curses.color_pair(COLOR_PAIRS['STATUS']))
        
        # Volumen y modo repetición
        volume_bar = "🔊 " + "█" * (self.volume // 10) + "░" * (10 - self.volume // 10)
        repeat_status = {
            0: "🔁 Desactivado",
            1: "🔂 Repetir canción",
            2: "🔄 Repetir carpeta"
        }[self.repeat_mode]
        self.stdscr.addstr(4, 0, f"{volume_bar} | {repeat_status}", 
                          curses.color_pair(COLOR_PAIRS['STATUS']))
        
        # Mensaje de error si existe
        if self.error_message and time.time() < self.error_timer:
            self.stdscr.addstr(5, 0, self.error_message, 
                             curses.color_pair(COLOR_PAIRS['ERROR']))
        
        # Lista de carpetas y canciones
        list_y = 7 if self.error_message else 6
        self.stdscr.addstr(list_y, 0, "📁 Carpetas y canciones:", 
                          curses.color_pair(COLOR_PAIRS['TITLE']))
        
        # Calcular índices para la paginación
        total_items = len(self.folders) + len(self.songs)
        start_idx = self.current_page * self.max_items_per_page
        end_idx = min(start_idx + self.max_items_per_page, total_items)
        
        # Mostrar carpetas y canciones
        for i in range(start_idx, end_idx):
            y = list_y + 2 + (i - start_idx)
            prefix = "→" if i == self.selected_index else " "
            
            if i < len(self.folders):
                # Es una carpeta
                folder_name = os.path.basename(self.folders[i])
                display_name = f"📁 {folder_name}"
            else:
                # Es una canción
                song_idx = i - len(self.folders)
                song_name = self.sanitize_filename(os.path.basename(self.songs[song_idx]))
                display_name = f"🎵 {song_name}"
            
            if i == self.selected_index:
                self.stdscr.addstr(y, 0, f"{prefix} {display_name}", 
                                 curses.color_pair(COLOR_PAIRS['SELECTED']))
            else:
                self.stdscr.addstr(y, 0, f"{prefix} {display_name}", 
                                 curses.color_pair(COLOR_PAIRS['NORMAL']))
        
        # Barra de progreso
        if self.is_playing and self.player.is_playing():
            try:
                length = self.player.get_length() / 1000
                current = self.player.get_time() / 1000
                
                if length > 0 and current >= 0:
                    progress = min(1.0, max(0.0, current / length))
                    self.draw_progress_bar(height - 6, 0, width, progress, COLOR_PAIRS['PROGRESS'])
                    time_str = f"{self.format_time(current)} / {self.format_time(length)}"
                    self.stdscr.addstr(height - 5, (width - len(time_str)) // 2, time_str,
                                     curses.color_pair(COLOR_PAIRS['PROGRESS']))
            except Exception as e:
                logging.error(f"Error al actualizar la barra de progreso: {str(e)}")
        
        # Controles
        controls = [
            "🎮 Controles:",
            "↑/↓: Navegar  ␣: Reproducir/Pausar  Enter: Abrir carpeta",
            "←/→: Avanzar/Retroceder  +/-: Volumen",
            "N: Siguiente  P: Anterior  S: Detener",
            "R: Modo repetición  Q: Salir  B: Volver atrás"
        ]
        for i, control in enumerate(controls):
            self.stdscr.addstr(height - len(controls) + i, 0, control,
                             curses.color_pair(COLOR_PAIRS['CONTROLS']))
        
        self.stdscr.refresh()

    def handle_input(self, key):
        """Manejar entrada del usuario"""
        total_items = len(self.folders) + len(self.songs)
        
        # Ignorar teclas de repetición rápidas solo para navegación
        current_time = time.time()
        if not hasattr(self, 'last_key_time'):
            self.last_key_time = 0
            self.last_key = None
            self.key_pressed = False
        
        # Para las flechas de navegación (arriba/abajo)
        if key in (curses.KEY_UP, curses.KEY_DOWN):
            if key == curses.KEY_UP and self.selected_index > 0:
                self.selected_index -= 1
                if self.selected_index < self.current_page * self.max_items_per_page:
                    self.current_page -= 1
            elif key == curses.KEY_DOWN and self.selected_index < total_items - 1:
                self.selected_index += 1
                if self.selected_index >= (self.current_page + 1) * self.max_items_per_page:
                    self.current_page += 1
        # Para las flechas de búsqueda (izquierda/derecha)
        elif key in (curses.KEY_LEFT, curses.KEY_RIGHT):
            if self.is_playing:
                if not self.key_pressed:  # Solo si la tecla no estaba presionada
                    self.key_pressed = True
                    self.last_key = key
                    self.last_key_time = current_time
                    if key == curses.KEY_LEFT:
                        self.seek(-10)
                    elif key == curses.KEY_RIGHT:
                        self.seek(10)
        elif key == -1:  # Tecla liberada
            self.key_pressed = False
        elif key == ord(' '):
            if self.selected_index >= len(self.folders):  # Es una canción
                song_idx = self.selected_index - len(self.folders)
                if song_idx == self.current_song_index and self.is_playing:
                    self.pause()
                else:
                    if self.is_playing and song_idx != self.current_song_index:
                        self.stop()
                        time.sleep(0.1)
                    self.play(song_idx)
        elif key == ord('\n'):  # Enter
            if self.selected_index < len(self.folders):  # Es una carpeta
                self.load_directory(self.folders[self.selected_index])
                self.selected_index = 0
                self.current_page = 0
        elif key == ord('b'):  # Volver atrás
            if self.parent_path:
                self.load_directory(self.parent_path)
                self.selected_index = 0
                self.current_page = 0
        elif key == ord('+'):
            self.set_volume(min(100, self.volume + 10))
        elif key == ord('-'):
            self.set_volume(max(0, self.volume - 10))
        elif key == ord('r'):
            self.toggle_repeat()
        elif key == ord('n'):
            self.next_song()
        elif key == ord('p'):
            self.previous_song()
        elif key == ord('s'):
            self.stop()
        elif key == ord('q'):
            return False
        
        return True

    def play(self, index=None):
        """Reproducir la canción actual o la especificada por índice"""
        if self.songs:
            if index is not None and 0 <= index < len(self.songs):
                self.current_song_index = index
                self.selected_index = index
                logging.info(f"Seleccionada canción {index}: {self.songs[index]}")
            if not self.is_playing:
                try:
                    # Detener la reproducción actual si existe
                    if self.player.is_playing():
                        self.player.stop()
                        time.sleep(0.2)  # Pausa más larga para asegurar que se detiene
                    
                    # Verificar si el archivo existe y es accesible
                    if not os.path.exists(self.songs[self.current_song_index]):
                        error_msg = f"El archivo no existe: {self.songs[self.current_song_index]}"
                        self.show_error("❌ El archivo no existe", log_error=True)
                        logging.error(error_msg)
                        return
                    
                    if not os.access(self.songs[self.current_song_index], os.R_OK):
                        error_msg = f"Sin permisos para leer el archivo: {self.songs[self.current_song_index]}"
                        self.show_error("❌ Sin permisos para leer el archivo", log_error=True)
                        logging.error(error_msg)
                        return
                    
                    media = self.instance.media_new(self.songs[self.current_song_index])
                    self.player.set_media(media)
                    
                    # Configurar opciones de decodificación
                    media.add_option('--no-audio-time-stretch')
                    media.add_option('--no-video-time-stretch')
                    media.add_option('--no-audio-resample')
                    media.add_option('--file-caching=1000')  # Aumentar el caché
                    media.add_option('--network-caching=1000')  # Aumentar el caché de red
                    
                    self.player.play()
                    logging.debug(f"Iniciando reproducción de: {self.songs[self.current_song_index]}")
                    
                    # Esperar un momento para que VLC inicie la reproducción
                    time.sleep(0.5)
                    
                    # Verificar si la reproducción comenzó correctamente
                    if not self.player.is_playing():
                        # Intentar una segunda vez con más tiempo de espera
                        time.sleep(0.5)
                        if not self.player.is_playing():
                            error_msg = f"Error al reproducir el archivo: {self.songs[self.current_song_index]}"
                            self.show_error("❌ Error al reproducir el archivo", log_error=True)
                            logging.error(error_msg)
                            return
                    
                    self.is_playing = True
                    self.current_song = self.songs[self.current_song_index]
                    self.clear_error()
                    logging.info(f"Reproducción iniciada correctamente: {self.current_song}")
                except Exception as e:
                    error_msg = f"Error al reproducir {self.songs[self.current_song_index]}: {str(e)}"
                    self.show_error(f"❌ Error: {str(e)}", log_error=True)
                    logging.error(error_msg)
            else:
                self.player.play()
                self.clear_error()
                logging.info("Reproducción reanudada")

    def pause(self):
        """Pausar la canción actual"""
        if self.is_playing:
            self.player.pause()
            self.is_playing = False
            logging.info("Reproducción pausada")

    def stop(self):
        """Detener la canción actual"""
        self.player.stop()
        self.is_playing = False
        logging.info("Reproducción detenida")

    def next_song(self):
        """Reproducir la siguiente canción en la lista"""
        if self.songs:
            self.current_song_index = (self.current_song_index + 1) % len(self.songs)
            self.selected_index = self.current_song_index
            logging.info(f"Pasando a siguiente canción: {self.songs[self.current_song_index]}")
            self.stop()
            self.play()

    def previous_song(self):
        """Reproducir la canción anterior en la lista"""
        if self.songs:
            self.current_song_index = (self.current_song_index - 1) % len(self.songs)
            self.selected_index = self.current_song_index
            logging.info(f"Volviendo a canción anterior: {self.songs[self.current_song_index]}")
            self.stop()
            self.play()

    def toggle_repeat(self):
        """Cambiar entre los modos de repetición"""
        self.repeat_mode = (self.repeat_mode + 1) % 3
        logging.info(f"Modo repetición: {['Desactivado', 'Repetir canción', 'Repetir carpeta'][self.repeat_mode]}")

    def set_volume(self, volume):
        """Ajustar el volumen (0-100)"""
        try:
            volume = max(0, min(100, int(volume)))
            self.volume = volume
            self.player.audio_set_volume(volume)
            logging.info(f"Volumen ajustado a {volume}%")
        except ValueError:
            logging.error("Error: El volumen debe ser un número entre 0 y 100")

    def seek(self, seconds):
        """Avanzar/retroceder en la canción actual"""
        if self.is_playing:
            try:
                current_time = self.player.get_time()
                if current_time < 0:  # Si hay un error en la obtención del tiempo
                    logging.warning("Error al obtener el tiempo actual, intentando recuperar...")
                    time.sleep(0.1)  # Pequeña pausa para permitir que VLC se recupere
                    current_time = self.player.get_time()
                
                new_time = max(0, current_time + (seconds * 1000))
                self.player.set_time(int(new_time))
                logging.debug(f"Posición ajustada a {new_time/1000:.1f} segundos")
                
                # Verificar si la posición se actualizó correctamente
                time.sleep(0.1)
                if abs(self.player.get_time() - new_time) > 1000:  # Si la diferencia es mayor a 1 segundo
                    logging.warning("La posición no se actualizó correctamente, intentando recuperar...")
                    self.player.set_time(int(new_time))  # Intentar nuevamente
            except Exception as e:
                logging.error(f"Error al ajustar la posición: {str(e)}")
                self.show_error("❌ Error al ajustar la posición", log_error=True)

def monitor_playback(player):
    """Monitorear la reproducción y manejar la reproducción continua"""
    logging.info("Iniciando monitor de reproducción")
    last_error_time = 0
    error_count = 0
    max_retries = 3
    
    while True:
        try:
            if player.is_playing and not player.player.is_playing() and player.player.get_time() > 0:
                current_time = time.time()
                
                # Verificar si hay errores de decodificación
                if current_time - last_error_time < 5:  # Si hubo un error recientemente
                    error_count += 1
                    if error_count >= max_retries:  # Si hay demasiados errores seguidos
                        logging.error(f"Demasiados errores de reproducción ({error_count}), intentando recuperar...")
                        player.stop()
                        time.sleep(0.5)
                        
                        # Intentar reproducir la siguiente canción
                        if player.repeat_mode == 1:  # Repetir canción actual
                            logging.debug("Intentando reproducir la misma canción nuevamente")
                            player.play()
                        else:  # Repetir carpeta o modo desactivado
                            logging.debug("Pasando a siguiente canción después de error")
                            player.next_song()
                        
                        error_count = 0
                else:
                    error_count = 0
                
                last_error_time = current_time
                logging.debug("Detectado fin de reproducción")
                time.sleep(1)
                
                # Manejar los diferentes modos de repetición
                if player.repeat_mode == 1:  # Repetir canción actual
                    logging.debug("Repitiendo canción actual")
                    player.play()
                elif player.repeat_mode == 2:  # Repetir carpeta
                    logging.debug("Pasando a siguiente canción en la carpeta")
                    player.next_song()
                else:  # Modo desactivado
                    logging.debug("Pasando a siguiente canción")
                    player.next_song()
        except Exception as e:
            logging.error(f"Error en el monitor de reproducción: {str(e)}")
            time.sleep(1)  # Esperar antes de reintentar
        
        time.sleep(0.1)

def main(stdscr):
    logging.info("Iniciando aplicación")
    # Configurar curses
    curses.curs_set(0)  # Ocultar cursor
    stdscr.keypad(True)  # Habilitar teclas especiales
    curses.cbreak()  # Modo cbreak para mejor manejo de teclas
    stdscr.nodelay(True)  # Hacer getch() no bloqueante
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)  # Habilitar eventos del ratón
    
    # Verificar si VLC está instalado
    if not VLCInstaller.check_vlc_installed():
        logging.warning("VLC no encontrado, intentando instalación automática")
        stdscr.clear()
        stdscr.addstr(0, 0, "VLC no encontrado. Intentando instalar...", 
                     curses.color_pair(COLOR_PAIRS['STATUS']))
        stdscr.refresh()
        if not VLCInstaller.install_vlc():
            error_msg = "No se pudo instalar VLC automáticamente"
            logging.error(error_msg)
            stdscr.clear()
            stdscr.addstr(0, 0, "❌ No se pudo instalar VLC. Por favor, instálalo manualmente.",
                         curses.color_pair(COLOR_PAIRS['ERROR']))
            stdscr.addstr(1, 0, "Presiona cualquier tecla para salir...",
                         curses.color_pair(COLOR_PAIRS['ERROR']))
            stdscr.refresh()
            stdscr.getch()
            return

    player = MP3Player(stdscr)
    
    # Obtener el directorio inicial
    stdscr.clear()
    stdscr.addstr(0, 0, "📁 Ingresa la ruta a tu directorio de música: ",
                 curses.color_pair(COLOR_PAIRS['TITLE']))
    stdscr.refresh()
    curses.echo()
    music_dir = stdscr.getstr().decode('utf-8')
    curses.noecho()
    logging.info(f"Directorio de música ingresado: {music_dir}")
    
    if not music_dir and player.last_directory and os.path.exists(player.last_directory):
        music_dir = player.last_directory
        logging.info(f"Usando último directorio conocido: {music_dir}")
    elif not music_dir:
        # If no directory is provided and no valid last_directory exists, use home directory
        music_dir = os.path.expanduser("~")
        logging.info(f"Usando directorio home como predeterminado: {music_dir}")
    
    if not player.load_directory(music_dir):
        stdscr.clear()
        stdscr.addstr(0, 0, "❌ No se pudo cargar el directorio.",
                     curses.color_pair(COLOR_PAIRS['ERROR']))
        stdscr.addstr(1, 0, "Presiona cualquier tecla para salir...",
                     curses.color_pair(COLOR_PAIRS['ERROR']))
        stdscr.refresh()
        stdscr.getch()
        return

    # Iniciar el hilo de monitoreo de reproducción
    threading.Thread(target=monitor_playback, args=(player,), daemon=True).start()
    logging.info("Monitor de reproducción iniciado")

    # Bucle principal
    logging.info("Iniciando bucle principal")
    last_update = time.time()
    last_progress = 0
    last_mouse_time = 0
    mouse_cooldown = 0.1  # Cooldown para la rueda del ratón en segundos
    
    while True:
        current_time = time.time()
        
        if (current_time - last_update >= 0.2 or 
            (player.is_playing and abs(player.player.get_time()/1000 - last_progress) >= 1)):
            player.draw_interface()
            last_update = current_time
            if player.is_playing:
                last_progress = player.player.get_time()/1000
        
        key = stdscr.getch()
        if key == curses.KEY_MOUSE:
            try:
                _, x, y, _, bstate = curses.getmouse()
                if bstate & curses.BUTTON4_PRESSED:  # Rueda arriba
                    if current_time - last_mouse_time >= mouse_cooldown:
                        player.handle_input(curses.KEY_UP)
                        last_mouse_time = current_time
                elif bstate & curses.BUTTON5_PRESSED:  # Rueda abajo
                    if current_time - last_mouse_time >= mouse_cooldown:
                        player.handle_input(curses.KEY_DOWN)
                        last_mouse_time = current_time
            except:
                pass
        elif key != -1 or player.key_pressed:  # Procesar también cuando la tecla está presionada
            if not player.handle_input(key):
                break
        
        time.sleep(0.02)

    player.stop()
    player.save_preferences()
    logging.info("Aplicación finalizada correctamente")

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except Exception as e:
        logging.critical(f"Error fatal: {str(e)}", exc_info=True)