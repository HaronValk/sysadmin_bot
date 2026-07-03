import re
from config import MAX_PART

def strip_html(text):
    return re.sub(r'<[^>]+>', '', text)

def split_content(text):
    if not text: return [""]
    parts = []
    while len(text) > MAX_PART:
        split_pos = text.rfind('\n', 0, MAX_PART)
        if split_pos == -1: split_pos = MAX_PART
        parts.append(text[:split_pos])
        text = text[split_pos:].lstrip('\n')
    if text: parts.append(text)
    return parts or [""]