from src.utils.syntax_map import apply_syntax_map


def test_multi_word_operator_precedence():
    # Multi-word operators must match before single words (e.g. "plus equals" -> "+=", not "+=")
    assert apply_syntax_map("count plus equals one") == "count += one"
    assert apply_syntax_map("total minus equals ten") == "total -= ten"
    assert apply_syntax_map("if a greater than or equal to b") == "if a >= b"
    assert apply_syntax_map("if a less than or equal to b") == "if a <= b"
    assert apply_syntax_map("if x double equals y") == "if x == y"
    assert apply_syntax_map("if x not equals to y") == "if x != y"


def test_single_word_operators():
    assert apply_syntax_map("x equals five") == "x = five"
    assert apply_syntax_map("x plus y") == "x + y"
    assert apply_syntax_map("x minus y") == "x - y"
    assert apply_syntax_map("a greater than b") == "a > b"
    assert apply_syntax_map("a less than b") == "a < b"


def test_delimiters_and_brackets():
    assert apply_syntax_map("open paren x close paren") == "( x )"
    assert apply_syntax_map("open bracket zero close bracket") == "[ zero ]"
    assert apply_syntax_map("open brace return close brace") == "{ return }"
    assert apply_syntax_map("item semicolon") == "item ;"
    assert apply_syntax_map("key colon value comma") == "key : value ,"
    assert apply_syntax_map("object dot property") == "object . property"


def test_symbols_and_whitespace():
    assert apply_syntax_map("first line new line second line") == "first line \n second line"
    assert apply_syntax_map("indent block") == "\t block"
    assert apply_syntax_map("double quote hello double quote") == '" hello "'
    assert apply_syntax_map("single quote char single quote") == "' char '"
    assert apply_syntax_map("user underscore name") == "user _ name"
    assert apply_syntax_map("flag dash v") == "flag - v"
    assert apply_syntax_map("a ampersand b") == "a & b"
    assert apply_syntax_map("a pipe b") == "a | b"


def test_word_boundary_safety():
    # Words containing substrings should not trigger syntax mapping
    assert apply_syntax_map("equality for all") == "equality for all"
    assert apply_syntax_map("planet earth") == "planet earth"
    assert apply_syntax_map("surplus budget") == "surplus budget"
    assert apply_syntax_map("dashboards view") == "dashboards view"


def test_systems_and_cpp_rust_go_operators():
    assert apply_syntax_map("player arrow get location") == "player -> get location"
    assert apply_syntax_map("std double colon vector") == "std :: vector"
    assert apply_syntax_map("user short declare get user") == "user := get user"
    assert apply_syntax_map("channel receive data") == "<- data"
    assert apply_syntax_map("a logical and b") == "a && b"
    assert apply_syntax_map("a logical or b") == "a || b"
    assert apply_syntax_map("val nullish coalescing default") == "val ?? default"
    assert apply_syntax_map("obj optional chaining prop") == "obj ?. prop"


def test_markdown_and_emoji_macros():
    assert apply_syntax_map("heading one Introduction") == "# Introduction"
    assert apply_syntax_map("heading two Architecture") == "## Architecture"
    assert apply_syntax_map("heading three Details") == "### Details"
    assert apply_syntax_map("bullet item one") == "- item one"
    assert apply_syntax_map("todo checkbox buy milk") == "- [ ] buy milk"
    assert apply_syntax_map("rocket emoji launch") == "🚀 launch"
    assert apply_syntax_map("thumbs up good job") == "👍 good job"
    assert apply_syntax_map("fire emoji hot") == "🔥 hot"


def test_legal_and_academic_symbols():
    assert apply_syntax_map("section symbol 10") == "§ 10"
    assert apply_syntax_map("double section symbol 12") == "§§ 12"
    assert apply_syntax_map("paragraph symbol 5") == "¶ 5"
    assert apply_syntax_map("alpha plus beta") == "\\alpha + \\beta"
    assert apply_syntax_map("summation of x") == "\\sum of x"

