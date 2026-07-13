import numpy as np
import time
import pyautogui
import pyperclip
import string
from src.asr.engine import ASREngine
from src.llm.engine import LLMEngine
from src.utils.text_cleaner import pre_filter_text
from src.config.manager import ConfigManager

class AIPipeline:
    def __init__(self, asr_engine: ASREngine, llm_engine: LLMEngine, config_manager: ConfigManager = None):
        self.asr_engine = asr_engine
        self.llm_engine = llm_engine
        self.config_manager = config_manager or ConfigManager()

    def process_audio(self, audio_data: np.ndarray, context: str = "", profile_id: str = "general") -> str:
        if len(audio_data) == 0:
            print("[Pipeline] No audio data provided.")
            return ""
            
        dictionary = self.config_manager.get("dictionary", [])
        
        print("[Pipeline] Starting ASR transcription...")
        is_whisper = self.config_manager.get("whisper_mode", False)
        trim_db = self.config_manager.get("whisper_trim_db", -55.0) if is_whisper else -40.0
        rms_min = self.config_manager.get("whisper_rms_min", 0.003) if is_whisper else 0.01
        
        raw_text = self.asr_engine.transcribe(
            audio_data, 
            dictionary=dictionary,
            whisper_mode=is_whisper,
            trim_db=trim_db,
            rms_min=rms_min
        )
        print(f"[Pipeline] Raw transcription: '{raw_text}'")
        
        # Strip whitespace and check length
        if not raw_text or len(raw_text.strip()) < 2:
            print("[Pipeline] Transcript empty. Bypassing LLM.")
            return ""  # DO NOT call the LLM formatter
            
        print("[Pipeline] Running regex cleaner...")
        regex_cleaned = pre_filter_text(raw_text)
        print(f"[Pipeline] Regex cleaned: '{regex_cleaned}'")
        
        if not regex_cleaned:
            print("[Pipeline] Regex cleaned text is empty. Aborting.")
            return ""

        # Snippets check
        snippets = self.config_manager.get("snippets", {})
        clean_lower = regex_cleaned.lower().strip()
        match_key = clean_lower.translate(str.maketrans('', '', string.punctuation))
        
        if match_key in snippets:
            print(f"[Pipeline] Snippet match found for '{match_key}'. Bypassing LLM.")
            return snippets[match_key]

        # Command Mode check
        if clean_lower.startswith("command"):
            print("[Pipeline] Command Mode triggered.")
            command_text = regex_cleaned
            
            old_cb = pyperclip.paste()
            
            import uuid
            marker = str(uuid.uuid4())
            # Fast clipboard polling instead of fixed sleep
            pyperclip.copy(marker)
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.hotkey('ctrl', 'c')
            
            selected_text = ""
            for _ in range(50):
                try:
                    selected_text = pyperclip.paste()
                    if selected_text != marker:
                        break
                except Exception:
                    pass
                time.sleep(0.01)
                
            if selected_text == marker:
                selected_text = ""
            
            print("[Pipeline] Running LLM Command Mode...")
            final_text = self.llm_engine.execute_command(command_text, selected_text, context)
            print(f"[Pipeline] Command result: '{final_text}'")
            return final_text
            
        # Code Mode check
        if profile_id == "technical":
            print("[Pipeline] Technical context detected. Applying syntax map...")
            from src.utils.syntax_map import apply_syntax_map
            regex_cleaned = apply_syntax_map(regex_cleaned)
            print(f"[Pipeline] Syntax mapped: '{regex_cleaned}'")
            
        print("[Pipeline] Running LLM cleanup...")
        final_text = self.llm_engine.clean_text(regex_cleaned, context, profile_id)
        print(f"[Pipeline] Final text: '{final_text}'")
        
        return final_text
