"""Username normalization shared by registration and login.

Usernames are compared with Turkish letter rules:
- "İ" and "i" are the same letter
- "I" and "ı" are the same letter
- "i" and "ı" stay different letters

Text is also Unicode NFC-normalized, so the same visible name always produces
the same stored value, even when the input uses decomposed characters.
"""
import unicodedata


def canonical_username(value: str) -> str:
    """Return the form used for storage and comparison."""
    text = unicodedata.normalize("NFC", value.strip())
    # Map the Turkish capitals first: Python's lower() would turn "I" into "i"
    text = text.replace("\u0130", "i").replace("I", "\u0131")
    return text.lower()
