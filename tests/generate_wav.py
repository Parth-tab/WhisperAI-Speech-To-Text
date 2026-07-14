import wave
import os


def generate_float32_wav(filepath, duration_sec=1.0, sample_rate=16000):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with wave.open(filepath, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(4)  # 32-bit (4 bytes)
        wav_file.setframerate(sample_rate)
        # Note: standard wave module doesn't natively write float type headers, but it writes the bytes.
        # However, many soundfile/ffmpeg readers expect standard float IEEE if bits=32.
        # In our case we use soundfile in tests, let's write standard struct.pack('f') bytes.

        # We can also just use soundfile if it's installed (it is, because PyInstaller test uses it?
        # No, wait, `import soundfile as sf` was used in `profiling_test.py`.
        # If soundfile is available in profiling_test, maybe we can use it here too!
        pass


try:
    import soundfile as sf
    import numpy as np

    def generate(filepath, duration=1.0, sr=16000):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        audio = (np.sin(2 * np.pi * 440 * t)).astype(np.float32)
        sf.write(filepath, audio, sr, subtype="FLOAT")
except ImportError:

    def generate(filepath, duration=1.0, sr=16000):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        import wave
        import struct
        import math

        with wave.open(filepath, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(4)  # float32 is 4 bytes
            w.setframerate(sr)
            w.setcomptype("NONE", "not compressed")
            # The WAVE_FORMAT_IEEE_FLOAT is not strictly enforced by pure 'wave' python lib,
            # but soundfile might fail to read it if the header doesn't say float.
            # So let's just write raw 16-bit PCM (2 bytes) for maximum compatibility if soundfile fails.
            w.setsampwidth(2)
            for i in range(int(sr * duration)):
                value = int(32767.0 * math.sin(2.0 * math.pi * 440.0 * i / sr))
                w.writeframes(struct.pack("<h", value))


if __name__ == "__main__":
    generate(os.path.join(os.path.dirname(__file__), "data", "sample_dictation.wav"))
