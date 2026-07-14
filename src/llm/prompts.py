class PromptBuilder:
    def __init__(self):
        self.base_rules = (
            "You are an expert text editor. Process raw voice dictation and output ONLY the user's final, intended text.\n\n"
            "RULES:\n"
            "1. Filler words (um, uh) have been pre-removed. Focus on grammar, capitalization, and punctuation.\n"
            "2. If the user restarts mid-sentence, output ONLY their final intent. Discard false starts.\n"
            "3. If input contains <original> and <correction> tags, use ONLY the <correction> content.\n"
            "4. When the user says ordinal words (first/second/third) or 'number one/two/three', output a numbered list. Each list item MUST be on its own line separated by a newline character. NEVER merge list items into a single paragraph. Correct format: '1. Item one\\n2. Item two\\n3. Item three'.\n"
            "5. Return ONLY the cleaned text. NEVER explain. NEVER add commentary.\n\n"
        )
        self.style_addon = ""
        self.mode_addon = ""
        self.examples = [
            "Raw: 'Schedule a meeting for two... wait no, make it three pm with Sarah.'\nOutput: Schedule a meeting for 3 PM with Sarah.\n\n",
            "Raw: 'That's five hundred... five thousand dollars.'\nOutput: That's $5,000.\n\n",
            "Raw: 'We need to buy first apples second bananas and third cherries.'\nOutput: 1. Apples\n2. Bananas\n3. Cherries\n\n",
            "Raw: 'Number one finish the report. Number two send the email. Number three call the client.'\nOutput: 1. Finish the report.\n2. Send the email.\n3. Call the client.\n\n",
            "Raw: 'This project is going well. Now for the action items: first update the docs, second run the tests, third deploy to staging.'\nOutput: This project is going well. Now for the action items:\n1. Update the docs.\n2. Run the tests.\n3. Deploy to staging.\n\n",
        ]

    def with_style(self, style_addon: str):
        if style_addon:
            self.style_addon = f"STYLE: {style_addon}\n\n"
        return self

    def with_code_mode(self):
        self.mode_addon = "CODE MODE: This is a code context. Preserve technical terms and syntax exactly.\n\n"
        return self

    def with_list_hint(self):
        self.mode_addon += (
            "LIST MODE: The user is dictating a numbered list. You MUST output each item on a separate line using the format '1. Item\\n2. Item'. "
            "Do NOT merge items into prose. "
            "You MUST start the output immediately with '1.' or '-'. "
            "DO NOT output conversational filler, introductions, or phrases like 'Here is the list:'. "
            "Only output the list items.\n\n"
        )
        return self

    def with_mixed_mode(self):
        self.mode_addon += (
            "MIXED MODE: The input contains a prose paragraph followed by a numbered list. "
            "CRITICAL RULES: "
            "(1) Preserve the paragraph text as normal cleaned prose — do NOT convert it into a list item. "
            "(2) After the prose, format the list items as a numbered list on separate lines starting with '1.'. "
            "(3) Separate the prose and the list with a single newline. "
            "(4) DO NOT add any preamble or introduction between the prose and the list.\n\n"
        )
        return self

    def build(self) -> str:
        prompt = (
            self.base_rules
            + self.style_addon
            + self.mode_addon
            + "EXAMPLES:\n"
            + "".join(self.examples)
        )
        # Reset state to prevent accumulation across calls
        self.style_addon = ""
        self.mode_addon = ""
        return prompt
