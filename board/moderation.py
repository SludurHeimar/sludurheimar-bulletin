"""
A rule-based first pass over new posts, run at submission time. This is
NOT an AI/LLM classifier - it's plain pattern matching that catches the
cheap, common cases (doxxing-shaped text, spammy links, shouting) and
surfaces them in the admin so you review those first. Everything still
goes through the moderation queue either way; this only prioritizes.

Swapping this for a real LLM-based check later (e.g. a Claude API call)
is a reasonable upgrade, but needs an API key and a cost decision -
that's on you when you want it, not something to block on now.
"""
import re

# Add specific banned words/phrases here yourself - left empty on purpose.
# You know exactly what you want flagged; a slur/hate-speech list is a
# judgment call better made by you than hardcoded by me.
BANNED_PHRASES = []

_URL_RE = re.compile(r"(https?://|www\.)", re.I)
_PHONE_RE = re.compile(r"(\+?\d[\d\-\s]{6,}\d)")
_KENNITALA_RE = re.compile(r"\b\d{6}-?\d{4}\b")
_REPEATED_CHARS_RE = re.compile(r"(.)\1{6,}")


def get_auto_flags(text):
    """Return a list of short human-readable flags for a post body."""
    flags = []

    if len(_URL_RE.findall(text)) >= 2:
        flags.append("multiple links")

    if _PHONE_RE.search(text):
        flags.append("possible phone number")

    if _KENNITALA_RE.search(text):
        flags.append("possible kennitala/ID number")

    if len(text) > 30:
        letters = [c for c in text if c.isalpha()]
        if letters and sum(1 for c in letters if c.isupper()) / len(letters) > 0.6:
            flags.append("mostly capitals")

    if _REPEATED_CHARS_RE.search(text):
        flags.append("repeated characters (possible spam)")

    lowered = text.lower()
    for phrase in BANNED_PHRASES:
        if phrase.lower() in lowered:
            flags.append("matches your banned-phrase list")
            break

    return flags
