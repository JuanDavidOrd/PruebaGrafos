"""
Gestor de sonidos para la aplicación.
Genera sonidos de muerte del burro.
"""
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl
from pathlib import Path
import os


class DonkeyAudioManager:
    """Gestor de efectos de sonido para el burro"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.death_sound = None
            self._initialized = True
            self._load_sounds()
    
    def _load_sounds(self):
        """Carga los archivos de sonido disponibles"""
        # Buscar sonido de muerte en la carpeta assets/sounds
        # Intentar múltiples rutas relativas y absolutas
        sound_paths = [
            Path(__file__).parent.parent / "assets" / "sounds" / "donkey_death.wav",
            Path(__file__).parent.parent / "assets" / "sounds" / "death.wav",
            Path.cwd() / "assets" / "sounds" / "donkey_death.wav",
            Path.cwd() / "assets" / "sounds" / "death.wav",
        ]
        
        for path in sound_paths:
            if path.exists():
                try:
                    self.death_sound = QSoundEffect()
                    self.death_sound.setSource(QUrl.fromLocalFile(str(path)))
                    if self.death_sound.status() == 0:  # 0 = Ok
                        break
                except Exception as e:
                    print(f"Error cargando sonido de {path}: {e}")
    
    def play_death_sound(self):
        """Reproduce el sonido de muerte del burro"""
        if self.death_sound:
            try:
                self.death_sound.play()
            except Exception as e:
                print(f"Error reproduciendo sonido de muerte: {e}")
    
    def has_death_sound(self) -> bool:
        """Verifica si hay un sonido de muerte cargado"""
        return self.death_sound is not None


def get_audio_manager() -> DonkeyAudioManager:
    """Obtiene la instancia del gestor de audio (singleton)"""
    return DonkeyAudioManager()
