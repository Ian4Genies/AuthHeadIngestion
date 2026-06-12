import re

AUTH_SHAPE_KEY_PREFIX = "auth_"

GENDER_TOKENS = {
    "female": "f",
    "male": "m",
}

_FBX_ID_PATTERN = re.compile(r"_(\d{4})(?:_|$)")


def fbx_filename_to_shape_key(filename: str) -> str | None:
    """
    african_female_loPoly_body_0001_geo.fbx -> auth_african_f_0001
    """
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    parts = [part for part in stem.split("_") if part]
    if len(parts) < 2:
        return None

    ethnicity = parts[0].lower()
    gender = GENDER_TOKENS.get(parts[1].lower())
    if gender is None:
        return None

    id_match = _FBX_ID_PATTERN.search(stem)
    if id_match is None:
        return None

    return f"{AUTH_SHAPE_KEY_PREFIX}{ethnicity}_{gender}_{id_match.group(1)}"
