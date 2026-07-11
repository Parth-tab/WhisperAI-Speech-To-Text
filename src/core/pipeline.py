import numpy as np
from src.asr.engine import ASREngine
from src.llm.engine import LLMEngine
from src.utils.text_cleaner import pre_filter_text

class AIPipeline:
    def __init__(self, asr_engine: ASREngine, llm_engine: LLMEngine):
        self.asr_engine = asr_engine
        self.llm_engine = llm_engine

    def process_audio(self, audio_data: np.ndarray, context: str = "") -> str:
        if len(audio_data) == 0:
            print("[Pipeline] No audio data provided.")
            return ""
            
        print("[Pipeline] Starting ASR transcription...")
        raw_text = self.asr_engine.transcribe(audio_data)
        print(f"[Pipeline] Raw transcription: '{raw_text}'")
        
        if not raw_text:
            print("[Pipeline] Transcription empty. Aborting.")
            return ""
            
        print("[Pipeline] Running regex cleaner...")
        regex_cleaned = pre_filter_text(raw_text)
        print(f"[Pipeline] Regex cleaned: '{regex_cleaned}'")
        
        if not regex_cleaned:
            print("[Pipeline] Regex cleaned text is empty. Aborting.")
            return ""
            
        print("[Pipeline] Running LLM cleanup...")
        final_text = self.llm_engine.clean_text(regex_cleaned, context)
        print(f"[Pipeline] Final text: '{final_text}'")
        
        return final_text
