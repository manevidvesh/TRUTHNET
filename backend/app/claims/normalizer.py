import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Gazetteer reference coordinates for prominent geopolitical locations
# NOTE: Centroids are reference points, NOT forensic crime/incident locations
KNOWN_LOCATION_CENTROIDS: Dict[str, Tuple[float, float]] = {
    "new delhi": (28.6139, 77.2090),
    "delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "hyderabad": (17.3850, 78.4867),
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "kerala": (10.8505, 76.2711),
    "london": (51.5074, -0.1278),
    "paris": (48.8566, 2.3522),
    "tokyo": (35.6762, 139.6503),
    "washington": (38.9072, -77.0369),
    "new york": (40.7128, -74.0060),
    "kyiv": (50.4501, 30.5234),
    "gaza": (31.5017, 34.4668),
    "tehran": (35.6892, 51.3890),
}

# Date patterns (ISO and natural English dates)
_ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
}
_NATURAL_DATE_RE = re.compile(
    r"\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\b",
    re.IGNORECASE
)
_YEAR_ONLY_RE = re.compile(r"\b(20\d{2}|19\d{2})\b")
_RELATIVE_DATE_RE = re.compile(
    r"\b(yesterday|today|tomorrow|last\s+(?:week|month|year|friday|monday|tuesday|wednesday|thursday|saturday|sunday)|earlier\s+today|recently|two\s+days\s+ago)\b",
    re.IGNORECASE
)

# Quantity and Currency regex (including Indian rupee symbol ₹ and crore/lakh)
_QUANTITY_RE = re.compile(
    r"(?:[\$₹€£]\s*)?\b\d+(?:[.,]\d+)?\s*(?:crore|lakh|million|billion|trillion|percent|%|people|dead|injured|killed|cases|rupees|dollars)?\b",
    re.IGNORECASE
)

# Organization patterns
_ORG_PATTERN = re.compile(
    r"\b(?:Ministry\s+of\s+[A-Z][a-zA-Z]+|Department\s+of\s+[A-Z][a-zA-Z]+|Supreme\s+Court|High\s+Court|Police\s+Department|Health\s+Ministry|WHO|UN|ISRO|NASA|FBI|CIA|BBC|CNN|PTI|ANI|Reuters|AP)\b",
    re.IGNORECASE
)

# Person titles pattern
_TITLE_PATTERN = re.compile(
    r"\b(?:Prime\s+Minister|President|Senator|Governor|Chief\s+Minister|Dr\.|Doctor|Spokesperson|Minister|Mayor|Judge)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\b"
)

class ClaimNormalizer:
    """
    Normalizes textual assertions for indexing and comparison, parses dates, quantities,
    and named entities, and looks up gazetteer reference centroids without mutating source text.
    """

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Collapses whitespace, normalizes smart quotes, and trims strings.
        Does NOT alter the underlying raw text stored in database.
        """
        if not text:
            return ""
        # Smart quotes to standard ASCII
        cleaned = text.replace("“", "\"").replace("”", "\"").replace("‘", "'").replace("’", "'")
        # Unicode normalization
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @staticmethod
    def parse_entities(text: str, reference_timestamp: Optional[datetime] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extracts entity candidates (persons, organizations, locations, dates, quantities)
        with exact character spans in the provided text.
        Relative dates are NEVER converted to absolute dates without a verified reference timestamp and timezone.
        """
        entities: Dict[str, List[Dict[str, Any]]] = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "dates": [],
            "quantities": []
        }

        if not text:
            return entities

        # 1. Dates
        # A. ISO dates
        for m in _ISO_DATE_RE.finditer(text):
            entities["dates"].append({
                "raw": m.group(0),
                "normalized": m.group(0),
                "type": "EXACT_DATE",
                "span": [m.start(), m.end()]
            })

        # B. Natural language dates (e.g. 15 March 2026)
        for m in _NATURAL_DATE_RE.finditer(text):
            day = int(m.group(1))
            month_str = m.group(2).lower()
            month = _MONTH_NAMES.get(month_str, 1)
            year = int(m.group(3))
            iso_str = f"{year:04d}-{month:02d}-{day:02d}"
            entities["dates"].append({
                "raw": m.group(0),
                "normalized": iso_str,
                "type": "EXACT_DATE",
                "span": [m.start(), m.end()]
            })

        # C. Relative dates (e.g. yesterday, last week)
        for m in _RELATIVE_DATE_RE.finditer(text):
            raw_match = m.group(0)
            raw_lower = raw_match.lower()
            normalized_date = None
            is_anchored = False

            # Only attempt relative date anchoring if reference_timestamp is valid and timezone-aware
            if reference_timestamp and reference_timestamp.tzinfo is not None:
                if "yesterday" in raw_lower:
                    dt = reference_timestamp - timedelta(days=1)
                    normalized_date = dt.strftime("%Y-%m-%d")
                    is_anchored = True
                elif "today" in raw_lower:
                    normalized_date = reference_timestamp.strftime("%Y-%m-%d")
                    is_anchored = True
                elif "two days ago" in raw_lower:
                    dt = reference_timestamp - timedelta(days=2)
                    normalized_date = dt.strftime("%Y-%m-%d")
                    is_anchored = True

            entities["dates"].append({
                "raw": raw_match,
                "normalized": normalized_date,
                "type": "RELATIVE_DATE" if is_anchored else "RELATIVE_DATE_UNRESOLVED",
                "is_anchored": is_anchored,
                "caveat": "Relative date anchored using submission intake timestamp" if is_anchored else "Relative date cannot be anchored without an explicit submission timestamp and timezone.",
                "span": [m.start(), m.end()]
            })

        # D. Year-only dates (when not part of a full date)
        covered_spans = [d["span"] for d in entities["dates"]]
        for m in _YEAR_ONLY_RE.finditer(text):
            span = [m.start(), m.end()]
            is_sub = any(span[0] >= c[0] and span[1] <= c[1] for c in covered_spans)
            if not is_sub:
                entities["dates"].append({
                    "raw": m.group(0),
                    "normalized": m.group(0),
                    "type": "YEAR_ONLY",
                    "span": span
                })

        # 2. Locations
        for loc_name, coords in KNOWN_LOCATION_CENTROIDS.items():
            pattern = re.compile(rf"\b{re.escape(loc_name)}\b", re.IGNORECASE)
            for m in pattern.finditer(text):
                entities["locations"].append({
                    "raw": text[m.start():m.end()],
                    "mentioned_location": loc_name.title(),
                    "canonical_name": loc_name.title(),
                    "reference_centroid_lat": coords[0],
                    "reference_centroid_lon": coords[1],
                    "is_reference_centroid": True,
                    "centroid_caveat": "Centroid coordinate represents general municipal center, NOT incident or crime scene location",
                    "span": [m.start(), m.end()]
                })

        # 3. Organizations
        for m in _ORG_PATTERN.finditer(text):
            entities["organizations"].append({
                "raw": m.group(0),
                "canonical_name": m.group(0).strip(),
                "span": [m.start(), m.end()]
            })

        # 4. Persons with Titles
        for m in _TITLE_PATTERN.finditer(text):
            entities["persons"].append({
                "raw": m.group(0),
                "name": m.group(1).strip(),
                "span": [m.start(), m.end()]
            })

        # 5. Quantities / Currencies / Statistics
        for m in _QUANTITY_RE.finditer(text):
            s = m.group(0).strip()
            # Ignore plain 4-digit years already caught as dates
            if re.match(r"^(?:19|20)\d{2}$", s):
                continue
            if len(s) > 1:
                entities["quantities"].append({
                    "raw": s,
                    "span": [m.start(), m.end()]
                })

        return entities

claim_normalizer = ClaimNormalizer()
