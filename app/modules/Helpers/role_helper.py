# helps handling and normalizing roles, for example... "Python Developer" vs "Python Dev"

_ROLE_NORMALIZATION: dict[str, str] = {
    "Python Developer": "Python Dev",
}


def normalize_role(role: str | None) -> str | None:
    if role is None:
        return None
    return _ROLE_NORMALIZATION.get(role, role)