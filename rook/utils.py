import re


def format_error_message(text):
    text = f"{text}"
    # TODO: error message is validated by pywps
    text = ' '.join(re.findall(r"['\w', '.', ':', '!', '?', '=', ',', '-']+", text.strip()))
    text = text[:144]
    return text
