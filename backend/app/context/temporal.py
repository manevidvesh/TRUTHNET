import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

ARCHIVAL_KEYWORDS = [
    "file photo",
    "file picture",
    "file image",
    "archive photo",
    "archival photo",
    "archive",
    "archival",
    "retrospective",
    "flashback",
    "remembering",
    "on this day",
    "look back",
    "lookback",
    "historical photo",
    "vintage photo",
]

def parse_flexible_datetime(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parses common date and timestamp formats safely into UTC datetime objects.
    Supports ISO 8601, RFC 2822, YYYY-MM-DD, YYYY/MM/DD, and bare 4-digit years.
    """
    if not date_str:
        return None

    cleaned = str(date_str).strip()
    if not cleaned:
        return None

    # Check for bare year e.g. "2018", "2026", "2011"
    year_match = re.match(r"^(\d{4})$", cleaned)
    if year_match:
        year = int(year_match.group(1))
        return datetime(year, 1, 1, tzinfo=timezone.utc)

    # Common standard formats
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y:%m:%d %H:%M:%S",  # EXIF standard datetime format
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    # Attempt ISO fromisoformat fallback (Python 3.11+)
    try:
        iso_clean = cleaned.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso_clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass

    return None

class TemporalContextEngine:
    """
    Evaluates temporal relationships across the 7 distinct TRUTHNET timestamps,
    computes signed day deltas, enforces physical sequence causality invariants,
    and identifies archival framing as a contextual signal.
    """

    @staticmethod
    def detect_archival_signals(text: Optional[str]) -> Dict[str, Any]:
        """
        Analyzes text/caption for archival or retrospective indicator keywords.
        EPISTEMOLOGICAL RULE:
        Archival indicators are contextual signals only.
        They must NEVER independently establish that an underlying factual claim is SUPPORTED,
        nor do they automatically suppress misleading-context findings when older media is
        deceptively captioned as breaking news.
        """
        if not text:
            return {
                "archival_signal_detected": False,
                "matched_keywords": [],
                "note": "No text provided to evaluate archival signals."
            }

        text_lower = text.lower()
        matched = [kw for kw in ARCHIVAL_KEYWORDS if kw in text_lower]

        if matched:
            return {
                "archival_signal_detected": True,
                "matched_keywords": matched,
                "note": (
                    f"Archival indicator detected in text: {matched}. "
                    "This is an observational contextual signal indicating retrospective or archival presentation. "
                    "It does not automatically establish that the underlying claim is supported, "
                    "nor does it automatically suppress misleading-context findings."
                )
            }

        return {
            "archival_signal_detected": False,
            "matched_keywords": [],
            "note": "No archival indicator keywords identified in text."
        }

    @classmethod
    def evaluate_temporal_alignment(
        cls,
        claimed_date_str: Optional[str],
        observed_capture_date_str: Optional[str],
        publication_date_str: Optional[str] = None,
        archive_date_str: Optional[str] = None,
        retrieval_date_str: Optional[str] = None,
        caption_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates temporal consistency across available timestamps:
        - claimed_date (event date alleged by submitter/caption)
        - capture_date (camera sensor EXIF or recording timestamp)
        - publication_date (news/web public release)
        - archive_date (Wayback or fact-check snapshot)
        - retrieval_date (when TRUTHNET gathered external evidence)
        """
        claimed_dt = parse_flexible_datetime(claimed_date_str)
        capture_dt = parse_flexible_datetime(observed_capture_date_str)
        pub_dt = parse_flexible_datetime(publication_date_str)
        arch_dt = parse_flexible_datetime(archive_date_str)
        ret_dt = parse_flexible_datetime(retrieval_date_str)

        archival_info = cls.detect_archival_signals(caption_text)
        archival_signal = archival_info["archival_signal_detected"]

        temporal_delta_days: Optional[float] = None
        is_sequence_violation = False
        is_temporal_discrepancy = False
        findings: List[str] = []

        # Invariant 1: Capture must predate or coincide with publication
        if capture_dt and pub_dt and capture_dt > pub_dt:
            is_sequence_violation = True
            findings.append(
                f"Physical sequence violation: observed capture date ({capture_dt.date()}) "
                f"post-dates publication date ({pub_dt.date()})."
            )

        # Invariant 2: Claimed event date vs observed media capture date
        if claimed_dt and capture_dt:
            delta_seconds = (claimed_dt - capture_dt).total_seconds()
            temporal_delta_days = round(delta_seconds / 86400.0, 1)

            # Claiming event happened BEFORE the photo was taken
            if temporal_delta_days < -1.0:
                is_sequence_violation = True
                findings.append(
                    f"Physical sequence impossibility: claimed event date ({claimed_dt.date()}) "
                    f"is prior to media capture date ({capture_dt.date()}) by {abs(temporal_delta_days)} days."
                )
            # Photo taken significantly before the claimed event date
            elif temporal_delta_days > 30.0:
                is_temporal_discrepancy = True
                years_delta = round(temporal_delta_days / 365.25, 1)
                findings.append(
                    f"Temporal divergence noted: media capture date ({capture_dt.date()}) "
                    f"predates claimed event date ({claimed_dt.date()}) by {temporal_delta_days} days (~{years_delta} years)."
                )

        return {
            "claimed_date_str": claimed_date_str,
            "claimed_datetime": claimed_dt.isoformat() if claimed_dt else None,
            "observed_capture_date_str": observed_capture_date_str,
            "observed_capture_datetime": capture_dt.isoformat() if capture_dt else None,
            "publication_datetime": pub_dt.isoformat() if pub_dt else None,
            "archive_datetime": arch_dt.isoformat() if arch_dt else None,
            "retrieval_datetime": ret_dt.isoformat() if ret_dt else None,
            "temporal_delta_days": temporal_delta_days,
            "archival_signal_detected": archival_signal,
            "archival_details": archival_info,
            "is_physical_sequence_violation": is_sequence_violation,
            "is_temporal_discrepancy": is_temporal_discrepancy,
            "findings": findings
        }
