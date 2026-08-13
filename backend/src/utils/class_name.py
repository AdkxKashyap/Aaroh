import re


def normalize_class_name(name: str | None) -> str:
    if name is None:
        return ""

    value = str(name).strip().lower()
    value = re.sub(r"^(class|grade|section)\s*", "", value)
    return re.sub(r"[^a-z0-9]", "", value)
