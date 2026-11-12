import re
import unicodedata
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

try:
    import importlib.metadata
    _LANGDETECT_VERSION = importlib.metadata.version("langdetect")
except Exception:
    _LANGDETECT_VERSION = "1.0.9"

try:
    import langdetect
    from langdetect import DetectorFactory
    DetectorFactory.seed = 0
    _HAS_LANGDETECT = True
except ImportError:
    _HAS_LANGDETECT = False
    _LANGDETECT_VERSION = None

# Unicode ranges for primary supported scripts
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
_TELUGU_RE = re.compile(r"[\u0C00-\u0C7F]")
_LATIN_RE = re.compile(r"[a-zA-Z]")

# Common Romanized Hindi (Hinglish) grammatical function markers
_HINGLISH_LEXICON = {
    "aaj", "kal", "yeh", "ye", "woh", "wo", "hai", "hain", "nahi", "nahin",
    "karo", "karna", "karega", "karenge", "bhi", "bahut", "bohot", "me", "mein",
    "par", "se", "ko", "aur", "ki", "ka", "ke", "kya", "kyu", "kyun", "kab",
    "kaha", "kahan", "kaise", "gaya", "gayi", "raha", "rahi", "hoga", "hogi"
}

@dataclass
class LanguageDetectionResult:
    language: str
    detection_method: str
    detector_version: Optional[str]
    detector_probability: Optional[float]
    is_reliable: bool
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class LanguageDetector:
    """
    Robust multilingual language detector providing genuine statistical n-gram detection,
    explicit short-text thresholds, mixed-language / transliteration recognition,
    and honest uncalibrated probability reporting.
    """

    def __init__(self):
        self.version = _LANGDETECT_VERSION
        self.has_langdetect = _HAS_LANGDETECT

    def detect(self, text: str) -> LanguageDetectionResult:
        if not text:
            return LanguageDetectionResult(
                language="UNKNOWN",
                detection_method="empty_input",
                detector_version=self.version,
                detector_probability=None,
                is_reliable=False,
                details={"reason": "Text is empty or whitespace"}
            )

        stripped = text.strip()
        alpha_chars = [c for c in stripped if unicodedata.category(c).startswith("L")]
        
        # 1. No alphabetic / syllabic characters
        if not alpha_chars:
            return LanguageDetectionResult(
                language="UNKNOWN",
                detection_method="no_alphabetic_features",
                detector_version=self.version,
                detector_probability=None,
                is_reliable=False,
                details={"reason": "Text contains no letters or syllables"}
            )

        devanagari_count = len(_DEVANAGARI_RE.findall(stripped))
        telugu_count = len(_TELUGU_RE.findall(stripped))
        latin_count = len(_LATIN_RE.findall(stripped))
        total_alpha = len(alpha_chars)

        # 2. Check for Mixed Scripts (e.g. Latin + Devanagari or Latin + Telugu)
        devanagari_ratio = devanagari_count / total_alpha if total_alpha else 0
        telugu_ratio = telugu_count / total_alpha if total_alpha else 0
        latin_ratio = latin_count / total_alpha if total_alpha else 0

        script_counts = {
            "devanagari": devanagari_count,
            "telugu": telugu_count,
            "latin": latin_count,
            "total_alpha": total_alpha
        }

        # If multiple scripts are present in significant numbers (> 15% each)
        active_scripts = sum([
            1 for ratio in (devanagari_ratio, telugu_ratio, latin_ratio) if ratio > 0.15
        ])
        if active_scripts >= 2:
            return LanguageDetectionResult(
                language="MIXED",
                detection_method="mixed_script_detection",
                detector_version=self.version,
                detector_probability=None,
                is_reliable=True,
                details={"script_counts": script_counts, "reason": "Multiple distinct writing systems detected"}
            )

        words = re.findall(r"\b\w+\b", stripped.lower())

        # 3. Check for Romanized Hindi / Transliterated Code-Switching in Latin text
        if latin_ratio > 0.70 and len(words) >= 3:
            hinglish_matches = [w for w in words if w in _HINGLISH_LEXICON]
            if len(hinglish_matches) >= 2:
                return LanguageDetectionResult(
                    language="MIXED",
                    detection_method="transliteration_heuristic",
                    detector_version=self.version,
                    detector_probability=None,
                    is_reliable=True,
                    details={
                        "hinglish_tokens": hinglish_matches,
                        "script": "Latin",
                        "primary_subtypes": ["en", "hi-Latn"]
                    }
                )

        # 4. Short-text threshold (< 12 alphabetic characters or < 3 words)
        # Statistical n-gram models are famously noisy on ultra-short text (e.g. "hi" -> Swahili)
        if len(alpha_chars) < 12 or len(words) < 3:
            if devanagari_ratio > 0.60:
                return LanguageDetectionResult(
                    language="hi",
                    detection_method="unicode_script_fallback",
                    detector_version=self.version,
                    detector_probability=None,
                    is_reliable=True,
                    details={"script": "Devanagari", "short_text": True}
                )
            elif telugu_ratio > 0.60:
                return LanguageDetectionResult(
                    language="te",
                    detection_method="unicode_script_fallback",
                    detector_version=self.version,
                    detector_probability=None,
                    is_reliable=True,
                    details={"script": "Telugu", "short_text": True}
                )
            else:
                return LanguageDetectionResult(
                    language="UNKNOWN",
                    detection_method="short_text_threshold",
                    detector_version=self.version,
                    detector_probability=None,
                    is_reliable=False,
                    details={"length": len(alpha_chars), "word_count": len(words), "reason": "Text too short for reliable statistical detection"}
                )

        # 5. Full Statistical N-gram Detection via langdetect
        if self.has_langdetect:
            try:
                candidate_langs = langdetect.detect_langs(stripped)
                if not candidate_langs:
                    raise ValueError("No language candidates returned")

                top = candidate_langs[0]
                detected_code = top.lang
                prob = float(top.prob)

                # Check if distribution is ambiguous (e.g. top < 0.70 or tight contest between top 2)
                if len(candidate_langs) > 1:
                    second = candidate_langs[1]
                    if top.prob < 0.70 or (top.prob - second.prob) < 0.25:
                        return LanguageDetectionResult(
                            language="MIXED",
                            detection_method="langdetect_ambiguous_distribution",
                            detector_version=self.version,
                            detector_probability=round(prob, 4),
                            is_reliable=False,
                            details={
                                "candidates": [{"lang": c.lang, "prob": round(c.prob, 4)} for c in candidate_langs],
                                "reason": "Language distribution split across multiple candidates"
                            }
                        )

                # Map to standard targets
                return LanguageDetectionResult(
                    language=detected_code,
                    detection_method="langdetect_ngram",
                    detector_version=self.version,
                    detector_probability=round(prob, 4),
                    is_reliable=True,
                    details={"candidates": [{"lang": c.lang, "prob": round(c.prob, 4)} for c in candidate_langs]}
                )

            except Exception as err:
                # Fallback to script detection on parser error
                pass

        # 6. Final Script-Based Fallback
        if devanagari_ratio > 0.50:
            return LanguageDetectionResult(
                language="hi",
                detection_method="unicode_script_fallback",
                detector_version=self.version,
                detector_probability=None,
                is_reliable=True,
                details={"script": "Devanagari"}
            )
        elif telugu_ratio > 0.50:
            return LanguageDetectionResult(
                language="te",
                detection_method="unicode_script_fallback",
                detector_version=self.version,
                detector_probability=None,
                is_reliable=True,
                details={"script": "Telugu"}
            )
        elif latin_ratio > 0.50:
            return LanguageDetectionResult(
                language="en",
                detection_method="unicode_script_fallback",
                detector_version=self.version,
                detector_probability=None,
                is_reliable=False,
                details={"script": "Latin", "reason": "Statistical detector unavailable, assumed Latin/en"}
            )

        return LanguageDetectionResult(
            language="UNKNOWN",
            detection_method="unresolved_fallback",
            detector_version=self.version,
            detector_probability=None,
            is_reliable=False,
            details={"script_counts": script_counts}
        )

language_detector = LanguageDetector()
