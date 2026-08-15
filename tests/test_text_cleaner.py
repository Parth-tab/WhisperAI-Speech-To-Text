from src.utils.text_cleaner import pre_filter_text


def test_pre_filter_text_dot_loops_and_ellipses():
    # Spaced dot chains
    t1 = "98% who suddenly . . . . . . . . . . . . . . ."
    res1 = pre_filter_text(t1)
    assert res1 == "98% who suddenly."

    # Massive continuous dot chains
    t2 = "98% who suddenly ...................................................."
    res2 = pre_filter_text(t2)
    assert res2 == "98% who suddenly."

    # Unicode ellipses
    t3 = "98% who suddenly……"
    res3 = pre_filter_text(t3)
    assert res3 == "98% who suddenly."

    # Fillers + dot loops
    t4 = "um 98% who suddenly . . . . . . uh"
    res4 = pre_filter_text(t4)
    assert res4 == "98% who suddenly."

    # User reported exact string: Forget ....................................................
    t5 = "Forget ....................................................................................."
    res5 = pre_filter_text(t5)
    assert res5 == "Forget."

    # User reported exact string: eeeeeeeeeeext and iiiing
    t7 = "Hello only due to start editing the eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeext ......"
    res7 = pre_filter_text(t7)
    assert res7 == "Hello only due to start editing the ext."

    t8 = "You to go on iiiing ........................................................................................"
    res8 = pre_filter_text(t8)
    assert res8 == "You to go on ing."

    # Normal English word with 2 repeating letters preserved
    t9 = "The bookkeeper arrived."
    res9 = pre_filter_text(t9)
    assert res9 == "The bookkeeper arrived."


def test_deduplicate_repeating_paragraphs():
    from src.utils.text_cleaner import sanitize_symbol_loops
    paragraph = (
        "Your GPUs and VRAM are used alongside system RAM for NVMe SSDs layered "
        "like a catch model dense components parts stay small about 17 billion parameters."
    )
    # 3x repeating paragraph block
    input_text = f"{paragraph}\n\n{paragraph}\n\n{paragraph}"
    result = sanitize_symbol_loops(input_text)

    # Should collapse to single paragraph instance
    assert result.count("17 billion parameters") == 1


def test_preserves_financial_numbers_and_decimals():
    from src.utils.text_cleaner import sanitize_symbol_loops
    assert sanitize_symbol_loops("$1,000,000 in revenue") == "$1,000,000 in revenue"
    assert sanitize_symbol_loops("Bond price was $999.00") == "Bond price was $999.00"
    assert sanitize_symbol_loops("Valuation $888M") == "Valuation $888M"


def test_preserves_single_letter_math_and_emojis():
    from src.utils.text_cleaner import sanitize_symbol_loops
    assert sanitize_symbol_loops("x = 1") == "x = 1"
    assert sanitize_symbol_loops("i += 1") == "i += 1"
    assert sanitize_symbol_loops("🚀 Launch ready 👍") == "🚀 Launch ready 👍"


def test_preserves_markdown_headers_and_code_blocks():
    from src.utils.text_cleaner import sanitize_symbol_loops
    assert sanitize_symbol_loops("### Section Title") == "### Section Title"
    assert sanitize_symbol_loops("```python\nprint('hello')\n```") == "```python\nprint('hello')\n```"


