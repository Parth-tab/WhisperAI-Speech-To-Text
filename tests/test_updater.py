from packaging.version import parse


def test_version_parsing_logic():
    latest = "v1.10.0"
    current = "v1.2.0"
    assert parse(latest) > parse(current)


def test_version_comparison_with_v_prefix():
    latest = "v2.0.0"
    current = "1.9.9"
    assert parse(latest) > parse(current)
