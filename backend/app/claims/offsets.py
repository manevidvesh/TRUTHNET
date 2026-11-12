"""
Unicode Offset Convention Specification & Bridge Utilities for TRUTHNET AI.

CONVENTION SPECIFICATION:
=========================
TRUTHNET AI backend computes and stores character-level evidence spans as
0-indexed UNICODE CODE POINT OFFSETS (scalar values).
- In Python: text[start:end] operates directly on Unicode code points.
- In Basic Multilingual Plane (BMP) scripts (ASCII, Latin, Devanagari Hindi U+0900..U+097F,
  Telugu U+0C00..U+0C7F): 1 code point corresponds exactly to 1 UTF-16 code unit
  (JavaScript/TypeScript string.slice() index).
- In Supplementary Multilingual Planes (SMP) (e.g. emojis U+1F600..U+1F64F, mathematical symbols):
  1 Unicode code point is represented by 2 UTF-16 surrogate code units in JavaScript.

To guarantee zero misalignment when the frontend highlights source text, these helper functions
provide deterministic conversion between Python Unicode scalar offsets and JavaScript UTF-16 offsets.
"""

from typing import Tuple

def codepoint_to_utf16_offsets(text: str, cp_start: int, cp_end: int) -> Tuple[int, int]:
    """
    Translates Python Unicode code point offsets into JavaScript UTF-16 code unit offsets.
    For BMP text (English, Hindi, Telugu), output is identical to input.
    For text containing surrogate pairs (emojis), accounts for 2-unit surrogate representation.
    """
    utf16_start = 0
    utf16_end = 0

    for i, char in enumerate(text):
        if i == cp_start:
            utf16_start = utf16_end
        if i == cp_end:
            break
        # Characters above 0xFFFF require 2 UTF-16 code units (surrogate pair)
        utf16_end += 2 if ord(char) > 0xFFFF else 1

    if cp_end >= len(text):
        utf16_end = sum(2 if ord(c) > 0xFFFF else 1 for c in text)

    return utf16_start, utf16_end

def utf16_to_codepoint_offsets(text: str, utf16_start: int, utf16_end: int) -> Tuple[int, int]:
    """
    Translates JavaScript UTF-16 code unit offsets back into Python Unicode code point offsets.
    """
    current_utf16 = 0
    cp_start = 0
    cp_end = len(text)

    for cp_idx, char in enumerate(text):
        if current_utf16 == utf16_start:
            cp_start = cp_idx
        if current_utf16 == utf16_end:
            cp_end = cp_idx
            break
        current_utf16 += 2 if ord(char) > 0xFFFF else 1

    return cp_start, cp_end
