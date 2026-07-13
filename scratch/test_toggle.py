import sys
import os
import time

# Add root directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.audio.capture import AudioCaptureEngine

def test_toggles():
    print("Initializing engine...")
    engine = AudioCaptureEngine(use_vad=False)
    
    for i in range(3):
        print(f"Toggle {i+1}: Start recording")
        engine.start_recording()
        time.sleep(1)
        print(f"Toggle {i+1}: Stop recording")
        engine.stop_recording()
        time.sleep(1)
        
    print("Test complete.")

if __name__ == "__main__":
    test_toggles()
