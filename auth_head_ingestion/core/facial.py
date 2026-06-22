from ..core.naming import AUTH_SHAPE_KEY_PREFIX


def split_shape_key_name(auth_key_name: str, feature_name: str) -> str:
    return f"{auth_key_name}_{feature_name}"


def is_auth_shape_key(name: str) -> bool:
    return name.startswith(AUTH_SHAPE_KEY_PREFIX)


def is_base_auth_shape_key(name: str) -> bool:
    if not is_auth_shape_key(name):
        return False
    parts = name[len(AUTH_SHAPE_KEY_PREFIX):].split("_")
    return len(parts) == 3


def is_split_auth_shape_key(name: str) -> bool:
    return is_auth_shape_key(name) and not is_base_auth_shape_key(name)
