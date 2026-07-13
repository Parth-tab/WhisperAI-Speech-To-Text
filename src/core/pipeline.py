import numpy as np
import time
import pyautogui
import pyperclip
import string
from src.asr.engine import ASREngine
from src.llm.engine import LLMEngine
from src.utils.text_cleaner import pre_filter_text
from src.config.manager import ConfigManager

from dataclasses import dataclass

@dataclass
class PipelineContext:
    audio_data: np.ndarray
    context_str: str
    profile_id: str
    pid: int
    text: str = ""
    is_terminal: bool = False

class PipelineStage:
    def process(self, ctx: PipelineContext, config: ConfigManager, asr: ASREngine, llm: LLMEngine):
        pass

class ASRStage(PipelineStage):
    def process(self, ctx: PipelineContext, config: ConfigManager, asr: ASREngine, llm: LLMEngine):
        if len(ctx.audio_data) == 0:
            ctx.is_terminal = True
            return
            
        dictionary = config.get("dictionary", [])
        is_whisper = config.get("whisper_mode", False)
        trim_db = config.get("whisper_trim_db", -55.0) if is_whisper else -40.0
        rms_min = config.get("whisper_rms_min", 0.003) if is_whisper else 0.01
        
        ctx.text = asr.transcribe(
            ctx.audio_data, 
            dictionary=dictionary,
            whisper_mode=is_whisper,
            trim_db=trim_db,
            rms_min=rms_min
        )
        if not ctx.text or len(ctx.text.strip()) < 2:
            ctx.is_terminal = True

class RegexStage(PipelineStage):
    def process(self, ctx: PipelineContext, config: ConfigManager, asr: ASREngine, llm: LLMEngine):
        ctx.text = pre_filter_text(ctx.text)
        if not ctx.text:
            ctx.is_terminal = True

class SnippetStage(PipelineStage):
    def process(self, ctx: PipelineContext, config: ConfigManager, asr: ASREngine, llm: LLMEngine):
        snippets = config.get("snippets", {})
        clean_lower = ctx.text.lower().strip()
        match_key = clean_lower.translate(str.maketrans('', '', string.punctuation))
        if match_key in snippets:
            ctx.text = snippets[match_key]
            ctx.is_terminal = True

class CommandModeStage(PipelineStage):
    def process(self, ctx: PipelineContext, config: ConfigManager, asr: ASREngine, llm: LLMEngine):
        clean_lower = ctx.text.lower().strip()
        if clean_lower.startswith("command"):
            import uuid
            marker = str(uuid.uuid4())
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
                
            ctx.text = llm.execute_command(ctx.text, selected_text, ctx.context_str)
            ctx.is_terminal = True

class CodeModeStage(PipelineStage):
    def process(self, ctx: PipelineContext, config: ConfigManager, asr: ASREngine, llm: LLMEngine):
        if ctx.profile_id == "technical":
            from src.utils.syntax_map import apply_syntax_map
            from src.injection.ide_bridge import ide_bridge
            ctx.text = apply_syntax_map(ctx.text)
            ctx.text = ide_bridge.process_file_tags(ctx.text, ctx.pid)

class BacktrackStage(PipelineStage):
    def process(self, ctx: PipelineContext, config: ConfigManager, asr: ASREngine, llm: LLMEngine):
        from src.utils.backtrack_detector import backtrack_detector
        ctx.text = backtrack_detector.process(ctx.text)

class LLMCleanupStage(PipelineStage):
    def process(self, ctx: PipelineContext, config: ConfigManager, asr: ASREngine, llm: LLMEngine):
        ctx.text = llm.clean_text(ctx.text, ctx.context_str, ctx.profile_id)

class AIPipeline:
    def __init__(self, asr_engine: ASREngine, llm_engine: LLMEngine, config_manager: ConfigManager = None):
        self.asr_engine = asr_engine
        self.llm_engine = llm_engine
        self.config_manager = config_manager or ConfigManager()
        self.stages = [
            ASRStage(),
            RegexStage(),
            SnippetStage(),
            CommandModeStage(),
            CodeModeStage(),
            BacktrackStage(),
            LLMCleanupStage()
        ]

    def process_audio(self, audio_data: np.ndarray, context: str = "", profile_id: str = "general", pid: int = 0) -> str:
        ctx = PipelineContext(
            audio_data=audio_data,
            context_str=context,
            profile_id=profile_id,
            pid=pid
        )
        
        for stage in self.stages:
            stage.process(ctx, self.config_manager, self.asr_engine, self.llm_engine)
            if ctx.is_terminal:
                break
                
        return ctx.text
