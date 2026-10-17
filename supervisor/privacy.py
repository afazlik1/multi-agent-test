"""Keep machine-specific paths out of persisted diagnostics."""
import re

_HOME_PATH = re.compile(r'''(?:/Users|/home)/[^"'\r\n]+''')


def sanitize_diagnostic(text):
    """Preserve the fact of a local path without recording its owner or location."""
    return _HOME_PATH.sub('<local-path>', text)


def sanitize_record(value):
    if isinstance(value,str):
        return sanitize_diagnostic(value)
    if isinstance(value,list):
        return [sanitize_record(item) for item in value]
    if isinstance(value,dict):
        return {key:sanitize_record(item) for key,item in value.items()}
    return value
