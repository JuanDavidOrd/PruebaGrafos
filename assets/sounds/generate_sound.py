"""
Script para generar un archivo WAV de sonido de muerte del burro.
"""
import wave
import struct
import math

def generate_donkey_death_sound(filename="donkey_death.wav", duration=2.0, sample_rate=44100):
    """
    Genera un archivo WAV con un sonido de muerte del burro.
    Usa una frecuencia decreciente (slide) que simula un "ehhhhhhh" descendente.
    """
    
    num_samples = int(sample_rate * duration)
    
    # Abrir archivo WAV para escribir
    with wave.open(filename, 'wb') as wav_file:
        # Configurar parámetros: 1 canal (mono), 2 bytes por muestra, sample_rate Hz
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        # Generar muestras
        for i in range(num_samples):
            # Tiempo normalizado (0 a 1)
            t = i / sample_rate
            progress = t / duration  # 0 a 1 mientras avanza el sonido
            
            # Frecuencia descendente: comienza en 300 Hz y baja a 100 Hz
            start_freq = 300.0
            end_freq = 100.0
            freq = start_freq + (end_freq - start_freq) * progress
            
            # Generar onda sinusoidal con decay (amplitud disminuye)
            amplitude = 0.8 * (1.0 - progress)  # Fade out
            
            # Añadir un poco de ruido para hacerlo más "orgánico"
            import random
            noise = random.uniform(-0.1, 0.1) * (1.0 - progress)
            
            # Calcular muestra
            sample = amplitude * math.sin(2.0 * math.pi * freq * t) + noise
            
            # Limitar a rango de -1 a 1
            sample = max(-1.0, min(1.0, sample))
            
            # Convertir a entero de 16 bits
            sample_int = int(sample * 32767)
            
            # Escribir en formato little-endian
            wav_file.writeframes(struct.pack('<h', sample_int))
    
    print(f"Archivo de sonido creado: {filename}")


if __name__ == "__main__":
    import os
    # Obtener la ruta del directorio actual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(current_dir, "donkey_death.wav")
    generate_donkey_death_sound(output_file)
