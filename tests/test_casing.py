from src.utils.casing import (
    apply_casing_transforms,
    to_camel_case,
    to_kebab_case,
    to_pascal_case,
    to_path_case,
    to_screaming_snake_case,
    to_snake_case,
)


def test_camel_case():
    assert to_camel_case("parse auth token") == "parseAuthToken"
    assert to_camel_case("is modal open") == "isModalOpen"
    assert apply_casing_transforms("camel parse auth token") == "parseAuthToken"
    assert apply_casing_transforms("state is modal open") == "isModalOpen"


def test_snake_case():
    assert to_snake_case("get user by id") == "get_user_by_id"
    assert apply_casing_transforms("snake get user by id") == "get_user_by_id"


def test_pascal_case():
    assert to_pascal_case("user profile component") == "UserProfileComponent"
    assert apply_casing_transforms("pascal user profile component") == "UserProfileComponent"
    assert apply_casing_transforms("component user avatar") == "UserAvatar"


def test_screaming_snake_case():
    assert to_screaming_snake_case("max buffer size") == "MAX_BUFFER_SIZE"
    assert apply_casing_transforms("constant max buffer size") == "MAX_BUFFER_SIZE"
    assert apply_casing_transforms("screaming snake api base url") == "API_BASE_URL"


def test_kebab_case():
    assert to_kebab_case("auth service deployment") == "auth-service-deployment"
    assert apply_casing_transforms("kebab auth service deployment") == "auth-service-deployment"


def test_path_case():
    assert to_path_case("internal slash auth slash handler") == "internal/auth/handler"
    assert apply_casing_transforms("path internal slash auth slash handler") == "internal/auth/handler"
