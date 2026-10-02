import re
import secrets

JOB_ID_PATTERN = re.compile(r"^[0-9a-f]{12}$")


def new_job_id() -> str:
    """Return a random, URL- and filesystem-safe job identifier."""
    return secrets.token_hex(6)


def is_valid_job_id(value: str) -> bool:
    return JOB_ID_PATTERN.fullmatch(value) is not None
