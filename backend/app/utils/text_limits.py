PUSH_LIMITS = {
    "title": 20,
    "body": 100,
    "cta": 30,
}


def _trim_to_limit(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    trimmed = text[:limit].rstrip()
    last_space = trimmed.rfind(" ")
    if last_space >= max(10, int(limit * 0.6)):
        trimmed = trimmed[:last_space].rstrip()
    return trimmed


def get_push_limit(component_type: str | None, content_type: str | None) -> int | None:
    if not component_type or content_type != "push_notification":
        return None
    return PUSH_LIMITS.get(component_type.lower())


def clamp_push_text(text: str | None, component_type: str | None, content_type: str | None) -> str | None:
    if not text or not component_type:
        return text
    limit = get_push_limit(component_type, content_type)
    if not limit:
        return text
    return _trim_to_limit(text, limit)


def push_limit_violations(values: dict, content_type: str | None) -> dict:
    if content_type != "push_notification":
        return {}
    violations = {}
    for key, limit in PUSH_LIMITS.items():
        val = values.get(key)
        if val and len(val) > limit:
            violations[key] = {"limit": limit, "length": len(val)}
    return violations
