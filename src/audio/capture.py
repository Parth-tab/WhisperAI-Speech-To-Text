import sounddevice as sd
import numpy as np
import collections
import queue
import scipy.signal
import ctypes
from PySide6.QtCore import QThread, Signal
from src.audio.vad import VADEngine

class AudioWorker(QThread):
    connection_successful = Signal()
    recording_failed = Signal(str)
    audio_chunk_ready = Signal(object) # np.ndarray
    audio_level_changed = Signal(float)
    recording_stopped = Signal(object) # np.ndarray

    def __init__(self, use_vad=True, vad_threshold=0.5):
        super().__init__()
        self.use_vad = use_vad
        self.vad_threshold = vad_threshold
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.full_audio = collections.deque(maxlen=30000)
        self._resample_buffer = np.array([], dtype=np.float32)
        
    def stop(self):
        self.is_recording = False
        
    def run(self):
        # 1. Initialize COM Apartment for this background thread
        try:
            ctypes.windll.ole32.CoInitializeEx(None, 0)
        except Exception as e:
            print(f"Warning: CoInitializeEx failed: {e}")

        try:
            # 2. Refresh PortAudio cache natively off the UI thread
            # Avoid re-initializing to prevent GIL deadlocks/UI freezes with Bluetooth devices.
            # sd._terminate()
            # sd._initialize()

            # 3. Find precise COM Communications Device
            comm_device_name = None
            try:
                from src import helper
                comm_device_name = helper._get_windows_default_communications_device_name()
            except Exception as e:
                print(f"Failed to get COM comm device: {e}")

            is_bluetooth_hfp = False
            if comm_device_name:
                is_bluetooth_hfp = True
            else:
                device_idx = sd.default.device[0]
                if device_idx is not None and device_idx >= 0:
                    device_info = sd.query_devices(device_idx, "input")
                    device_name = device_info.get("name", "").lower()
                    if any(k in device_name for k in ["hands-free", "ag audio", "bluetooth", "bth", "headset", "earbuds", "airpods"]):
                        is_bluetooth_hfp = True

            # 4. Host API Cascade with Safe 16kHz
            target_apis = ['WASAPI', 'DirectSound', 'MME']
            working_stream = None
            working_sr = None
            in_channels = 1
            
            for api_name in target_apis:
                hostapi_idx = None
                for i, api in enumerate(sd.query_hostapis()):
                    if api_name in api["name"]:
                        hostapi_idx = i
                        break
                
                if hostapi_idx is None:
                    continue
                    
                api_info = sd.query_hostapis(hostapi_idx)
                device_idx = None
                
                if comm_device_name:
                    for dev_id in api_info['devices']:
                        dev = sd.query_devices(dev_id)
                        if comm_device_name in dev['name'] or dev['name'] in comm_device_name:
                            device_idx = dev_id
                            break
                
                if device_idx is None:
                    device_idx = api_info.get("default_input_device")
                    
                if device_idx is None or device_idx < 0:
                    continue
                    
                device_info = sd.query_devices(device_idx)
                in_channels = 1
                out_channels = int(device_info.get("max_output_channels", 0))
                out_device_idx = None
                
                if is_bluetooth_hfp:
                    for dev_id in api_info['devices']:
                        dev = sd.query_devices(dev_id)
                        if dev.get('max_output_channels', 0) > 0:
                            if comm_device_name and (comm_device_name in dev['name'] or dev['name'] in comm_device_name):
                                out_device_idx = dev_id
                                break
                            elif any(k in dev['name'].lower() for k in ["hands-free", "ag audio", "bluetooth", "bth", "headset", "earbuds", "airpods"]):
                                out_device_idx = dev_id
                                break
                    if out_device_idx is None:
                        out_device_idx = api_info.get("default_output_device")
                        
                    if out_device_idx is not None and out_device_idx >= 0:
                        out_dev_info = sd.query_devices(out_device_idx)
                        out_channels = int(out_dev_info.get("max_output_channels", 0))
                
                sample_rates = [16000, 48000, 8000]
                
                hostapi_name = api_info.get('name', '')
                stream_settings = None
                if 'Windows WASAPI' in hostapi_name:
                    stream_settings = sd.WasapiSettings(exclusive=False)
                    
                for test_sr in sample_rates:
                    try:
                        def _audio_callback(indata, outdata, frames, time_info, status):
                            if outdata is not None:
                                outdata.fill(0) # Absolute silence lock
                            if self.is_recording:
                                self.audio_queue.put(indata.copy())

                        if is_bluetooth_hfp and out_channels > 0 and out_device_idx is not None and out_device_idx >= 0:
                            stream = sd.Stream(
                                device=(device_idx, out_device_idx),
                                samplerate=test_sr,
                                channels=(1, 1),
                                dtype="int16",
                                blocksize=0,
                                callback=_audio_callback,
                                extra_settings=stream_settings,
                            )
                        else:
                            def _input_callback(indata, frames, time_info, status):
                                if self.is_recording:
                                    self.audio_queue.put(indata.copy())
                                    
                            stream = sd.InputStream(
                                device=device_idx,
                                samplerate=test_sr,
                                channels=1,
                                dtype="int16",
                                blocksize=0,
                                callback=_input_callback,
                                extra_settings=stream_settings,
                            )
                            
                        working_stream = stream
                        working_sr = test_sr
                        break
                    except Exception as e:
                        print(f"[AudioWorker] Fallback warning: Failed {hostapi_name} at {test_sr}Hz - {e}")
                        continue
                        
                if working_stream is not None:
                    break
                    
            if working_stream is None:
                raise RuntimeError("No compatible audio API/device/samplerate combination found.")
                
            self.connection_successful.emit()
            self.is_recording = True
            
            vad_engine = None
            if self.use_vad:
                vad_engine = VADEngine(sample_rate=16000, min_silence_duration_ms=4000)
                vad_engine.threshold = self.vad_threshold
                
            with working_stream:
                while self.is_recording:
                    try:
                        chunk = self.audio_queue.get(timeout=0.1)
                        
                        audio_float32 = chunk.astype(np.float32) / 32768.0
                        if audio_float32.ndim > 1 and audio_float32.shape[1] > 1:
                            audio_mono = audio_float32.mean(axis=1)
                        elif audio_float32.ndim > 1:
                            audio_mono = audio_float32[:, 0]
                        else:
                            audio_mono = audio_float32
                            
                        self.full_audio.append(audio_mono)
                        
                        rms = np.sqrt(np.mean(audio_mono**2))
                        self.audio_level_changed.emit(float(rms))
                        self.audio_chunk_ready.emit(audio_mono)
                        
                        if vad_engine:
                            if working_sr == 48000:
                                vad_chunk = audio_mono[::3]
                            elif working_sr == 8000:
                                vad_chunk = scipy.signal.resample(audio_mono, len(audio_mono) * 2)
                            else:
                                vad_chunk = audio_mono
                                
                            self._resample_buffer = np.concatenate([self._resample_buffer, vad_chunk])
                            
                            while len(self._resample_buffer) >= 512:
                                out_chunk = self._resample_buffer[:512]
                                self._resample_buffer = self._resample_buffer[512:]
                                if vad_engine.process_chunk(out_chunk):
                                    print("[AudioWorker] VAD silence timeout reached.")
                                    self.is_recording = False
                                    break
                    except queue.Empty:
                        continue
                        
            # Stream exited cleanly
            if len(self.full_audio) > 0:
                final_audio = np.concatenate(list(self.full_audio))
                if working_sr != 16000:
                    num_samples = int(len(final_audio) * 16000 / working_sr)
                    final_audio = scipy.signal.resample(final_audio, num_samples).astype(np.float32)
                    
                if len(final_audio) < 16000 * 0.5:
                    final_audio = np.array([], dtype=np.float32)
            else:
                final_audio = np.array([], dtype=np.float32)
                
            self.recording_stopped.emit(final_audio)
            
        except Exception as e:
            print(f"[AudioWorker] Fatal error: {e}")
            self.recording_failed.emit(str(e))
        finally:
            try:
                ctypes.windll.ole32.CoUninitialize()
            except Exception:
                pass
