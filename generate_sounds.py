import wave
import math
import struct
import os

def write_tone(filename, freq=440, duration=0.5, volume=0.5, wave_type='sine'):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)

    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)

        for i in range(n_samples):
            t = float(i) / sample_rate
            if wave_type == 'sine':
                value = math.sin(2.0 * math.pi * freq * t)
            elif wave_type == 'square':
                value = 1.0 if math.sin(2.0 * math.pi * freq * t) > 0 else -1.0
            elif wave_type == 'saw':
                 value = 2.0 * (t * freq - math.floor(t * freq + 0.5))

            # Apply envelope (simple decay)
            decay = 1.0 - (i / n_samples)

            data = int(value * volume * decay * 32767.0)
            f.writeframes(struct.pack('<h', data))

def generate_daily_double(filename):
    # Ascending 'laser' sound
    sample_rate = 44100
    duration = 2.0
    n_samples = int(sample_rate * duration)

    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)

        for i in range(n_samples):
            t = float(i) / sample_rate
            # Frequency sweep 400 -> 1200
            freq = 400 + (800 * t / duration)
            value = math.sin(2.0 * math.pi * freq * t * 5) # *5 for wobble

            data = int(value * 0.5 * 32767.0)
            f.writeframes(struct.pack('<h', data))

os.makedirs('static/assets/audio', exist_ok=True)

# Buzz In (Medium Tone)
write_tone('static/assets/audio/buzz.wav', freq=440, duration=0.5)

# Correct (High Ding)
write_tone('static/assets/audio/correct.wav', freq=880, duration=0.8)

# Incorrect (Low Buzz)
write_tone('static/assets/audio/incorrect.wav', freq=150, duration=0.5, wave_type='square')

# Time's Up (Three beeps - simulating one)
write_tone('static/assets/audio/times_up.wav', freq=800, duration=0.2)

# Daily Double
generate_daily_double('static/assets/audio/daily_double.wav')

print("Sounds generated.")
