"""
Source Independence and Dependency Analysis Engine.

Analyzes multiple retrieved sources to evaluate true investigative independence:
- Wire service attribution (PTI, ANI, Reuters, AP, AFP, Bloomberg, etc.)
- Shared quotation analysis
- Non-quote text overlap & syndication detection
- Citation and backlink tracking
- Clustering into explainable dependency groupings
- Honest assessment: never confuses distinct domain names with independent confirmation.
"""

import re
import uuid
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
from app.schemas.source import (
    IndependenceAssessment,
    SourceDependencyCluster,
    SourceIndependenceResponse
)

# Known wire service identifiers and display names
WIRE_AGENCIES = {
    "PTI": "Press Trust of India (PTI)",
    "PRESS TRUST OF INDIA": "Press Trust of India (PTI)",
    "ANI": "Asian News International (ANI)",
    "ASIAN NEWS INTERNATIONAL": "Asian News International (ANI)",
    "REUTERS": "Reuters",
    "AP": "Associated Press (AP)",
    "ASSOCIATED PRESS": "Associated Press (AP)",
    "AFP": "Agence France-Presse (AFP)",
    "AGENCE FRANCE-PRESSE": "Agence France-Presse (AFP)",
    "AGENCE FRANCE PRESSE": "Agence France-Presse (AFP)",
    "BLOOMBERG": "Bloomberg",
    "UNI": "United News of India (UNI)",
    "UNITED NEWS OF INDIA": "United News of India (UNI)",
    "IANS": "Indo-Asian News Service (IANS)",
    "TASS": "TASS",
    "XINHUA": "Xinhua",
}

# Regex patterns for detecting wire agency attribution in text or bylines
WIRE_PATTERNS = [
    (re.compile(r'\((?:PTI|ANI|Reuters|AFP|Bloomberg|UNI|IANS)\)', re.IGNORECASE), "byline_parentheses"),
    (re.compile(r'\b(?:PTI|ANI|Reuters|AFP|Bloomberg|UNI|IANS)\s*[-—–]\s*', re.IGNORECASE), "dateline_prefix"),
    (re.compile(r'(?:Source|Via|From|Credit|By)\s*[:\-]\s*(PTI|ANI|Reuters|Associated\s+Press|AP|AFP|Bloomberg|UNI|IANS)\b', re.IGNORECASE), "source_field"),
    (re.compile(r'\b(?:reported\s+by|according\s+to|quoted\s+by)\s+(PTI|ANI|Reuters|Associated\s+Press|AFP|Bloomberg)\b', re.IGNORECASE), "attribution_clause"),
    (re.compile(r'\b(?:Press\s+Trust\s+of\s+India|Asian\s+News\s+International|Agence\s+France[- ]Presse|Associated\s+Press)\b', re.IGNORECASE), "full_name"),
    (re.compile(r'\bnews\s+agency\s+(PTI|ANI|Reuters|AP|AFP|UNI|IANS)\b', re.IGNORECASE), "news_agency_phrase"),
    (re.compile(r'\b(?:syndicated\s+feed|agency\s+feed|wire\s+service)\b', re.IGNORECASE), "syndicated_feed_flag"),
]

# Press release patterns
PRESS_RELEASE_PATTERNS = [
    re.compile(r'\b(?:press\s+release|press\s+statement|official\s+statement|official\s+communique|spokesperson\s+stated\s+in\s+a\s+release)\b', re.IGNORECASE),
    re.compile(r'\b(?:statement\s+issued\s+by|issued\s+a\s+statement|said\s+in\s+a\s+written\s+statement)\b', re.IGNORECASE),
    re.compile(r'\b(?:press\s+note|handout\s+issued|media\s+release)\b', re.IGNORECASE),
]

# Patterns citing a single original post/social media account or single witness without independent reporting
ORIGINAL_SOURCE_REPETITION_PATTERNS = [
    re.compile(r'\b(?:citing\s+a\s+(?:viral\s+)?(?:video|post|tweet|clip|photo)|according\s+to\s+a\s+viral\s+post)\b', re.IGNORECASE),
    re.compile(r'\b(?:circulating\s+on\s+(?:social\s+media|X|Twitter|Facebook|WhatsApp|Instagram)|went\s+viral\s+on)\b', re.IGNORECASE),
    re.compile(r'\b(?:as\s+seen\s+in\s+a\s+video\s+posted\s+by|user\s+posted\s+on)\b', re.IGNORECASE),
]

# Citation patterns between outlets
CITATION_PATTERNS = [
    re.compile(r'\b(?:as\s+(?:first\s+)?reported\s+by|according\s+to|citing)\s+([A-Z][a-zA-Z0-9\s]{2,25}(?:News|Times|Post|Express|Today|Live|Daily|Herald|Tribune|Chronicle|Wire|Standard))', re.IGNORECASE),
    re.compile(r'\b([A-Z][a-zA-Z0-9\s]{2,25})\s+first\s+reported\b', re.IGNORECASE),
]

def extract_quotes(text: str) -> List[str]:
    """Extract direct quotations enclosed in quotation marks."""
    # Look for quotes between standard double or single curly quotes
    matches = re.findall(r'["“]([^"”]{20,})["”]', text)
    matches += re.findall(r"'([^']{20,})'", text)
    cleaned = []
    for q in matches:
        q_clean = q.strip()
        if len(q_clean.split()) >= 4:  # At least 4 words
            cleaned.append(q_clean)
    return cleaned

def extract_prose_tokens(text: str) -> Set[str]:
    """Extract word tokens from text excluding short stopwords and quotes."""
    # Remove quotes first
    prose = re.sub(r'["“][^"”]*["”]', ' ', text)
    words = re.findall(r'\b[a-zA-Z0-9]{3,}\b', prose.lower())
    # Exclude common domain boilerplate tokens
    stopwords = {
        "the", "and", "that", "have", "for", "not", "with", "you", "this", "but", "his", "from",
        "they", "say", "her", "she", "will", "one", "all", "would", "there", "their", "what",
        "out", "about", "who", "get", "which", "when", "make", "can", "like", "time", "just",
        "him", "know", "take", "people", "into", "year", "your", "good", "some", "could",
        "them", "see", "other", "than", "then", "now", "look", "only", "come", "its", "over",
        "think", "also", "back", "after", "use", "two", "how", "our", "work", "first", "well",
        "way", "even", "new", "want", "because", "any", "these", "give", "day", "most", "us"
    }
    return {w for w in words if w not in stopwords}

def compute_jaccard_similarity(tokens_a: Set[str], tokens_b: Set[str]) -> float:
    """Compute Jaccard token similarity between two sets."""
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return float(intersection) / float(union) if union > 0 else 0.0

def detect_wire_agency(text: str, author: Optional[str] = None, publisher: Optional[str] = None) -> Optional[str]:
    """Detect if the source attributes its content to a wire service."""
    combined_header = f"{publisher or ''} {author or ''} {text[:400]}"
    
    # Check author/byline specifically
    if author:
        upper_author = author.strip().upper()
        for code, full_name in WIRE_AGENCIES.items():
            if code in upper_author or full_name.upper() in upper_author:
                return full_name
                
    # Check publisher
    if publisher:
        upper_pub = publisher.strip().upper()
        for code, full_name in WIRE_AGENCIES.items():
            if code in upper_pub or full_name.upper() in upper_pub:
                return full_name

    # Check pattern matches in text and headers
    for pattern, ptype in WIRE_PATTERNS:
        match = pattern.search(combined_header)
        if match:
            # Check if group captured
            matched_str = match.group(1) if match.groups() else match.group(0)
            cleaned = matched_str.strip("():- ").upper()
            for code, full_name in WIRE_AGENCIES.items():
                if code in cleaned or full_name.upper() in cleaned:
                    return full_name
            # Fallback for wire mentions
            if "PTI" in cleaned:
                return "Press Trust of India (PTI)"
            if "ANI" in cleaned:
                return "Asian News International (ANI)"
            if "REUTERS" in cleaned:
                return "Reuters"
            if "AFP" in cleaned:
                return "Agence France-Presse (AFP)"
            if "AP" in cleaned or "ASSOCIATED PRESS" in cleaned:
                return "Associated Press (AP)"
            if "BLOOMBERG" in cleaned:
                return "Bloomberg"
                
    # Also check full text body if short excerpt
    for pattern, ptype in WIRE_PATTERNS:
        match = pattern.search(text)
        if match:
            matched_str = match.group(1) if match.groups() else match.group(0)
            cleaned = matched_str.strip("():- ").upper()
            for code, full_name in WIRE_AGENCIES.items():
                if code in cleaned or full_name.upper() in cleaned:
                    return full_name
                    
    return None

def detect_press_release_markers(text: str) -> bool:
    """Detect if the source text cites an official press release or statement."""
    for pattern in PRESS_RELEASE_PATTERNS:
        if pattern.search(text):
            return True
    return False

def detect_original_source_repetition(text: str) -> bool:
    """Detect if the source merely repeats a viral social media post or witness without verification."""
    for pattern in ORIGINAL_SOURCE_REPETITION_PATTERNS:
        if pattern.search(text):
            return True
    return False

def detect_cited_outlet(text: str) -> Optional[str]:
    """Detect if the source explicitly cites another news outlet."""
    for pattern in CITATION_PATTERNS:
        m = pattern.search(text)
        if m:
            cited = m.group(1).strip()
            if len(cited) >= 3 and cited.lower() not in {"this", "that", "local"}:
                return cited
    return None


class SourceIndependenceAnalyzer:
    """
    Evaluates multi-signal source independence for a collection of retrieved sources.
    Produces structured clusters and an honest overall independence assessment.
    """

    def analyze(self, claim_id: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a list of source dicts or records for a specific claim.
        Returns a dict suitable for SourceIndependenceResponse.
        """
        total_count = len(sources)
        if total_count == 0:
            return {
                "id": str(uuid.uuid4()),
                "claim_id": claim_id,
                "total_sources_count": 0,
                "independent_sources_count": 0,
                "independence_assessment": IndependenceAssessment.UNKNOWN_DEPENDENCY,
                "clusters": [],
                "observable_signals": {"error": "No retrieved sources to evaluate"},
                "explanation": "Zero external sources were available for independence evaluation."
            }

        if total_count == 1:
            s = sources[0]
            sid = s.get("id") or "src-1"
            pub = s.get("publisher") or "Unknown Publisher"
            wire = detect_wire_agency(s.get("text_excerpt", "") or s.get("raw_content", ""), s.get("author"), pub)
            
            cluster = SourceDependencyCluster(
                cluster_id=f"cluster-{sid[:8]}",
                dependency_type=IndependenceAssessment.WIRE_SERVICE_DERIVED if wire else IndependenceAssessment.UNKNOWN_DEPENDENCY,
                primary_source_id=sid,
                source_ids=[sid],
                publishers=[pub],
                wire_agency=wire,
                rationale="Single source available. Multi-source independent confirmation cannot be verified." if not wire else f"Single source derived from wire agency: {wire}.",
                shared_phrases=[],
                text_overlap_ratio=1.0
            )
            return {
                "id": str(uuid.uuid4()),
                "claim_id": claim_id,
                "total_sources_count": 1,
                "independent_sources_count": 1 if not wire else 0,
                "independence_assessment": IndependenceAssessment.UNKNOWN_DEPENDENCY if not wire else IndependenceAssessment.WIRE_SERVICE_DERIVED,
                "clusters": [cluster.model_dump()],
                "observable_signals": {
                    "source_count": 1,
                    "wire_agency": wire,
                    "note": "Single source does not establish independent corroboration."
                },
                "explanation": "Only one external source is available. True multi-source independence requires distinct corroborating investigations."
            }

        # Multi-source analysis
        # 1. Feature extraction per source
        source_data = []
        for s in sources:
            sid = s.get("id") or str(uuid.uuid4())
            pub = s.get("publisher") or "Unknown Publisher"
            author = s.get("author")
            text = (s.get("text_excerpt") or "") + " " + (s.get("raw_content") or "")
            wire = detect_wire_agency(text, author, pub)
            quotes = extract_quotes(text)
            tokens = extract_prose_tokens(text)
            is_pr = detect_press_release_markers(text)
            is_repeats = detect_original_source_repetition(text)
            cited_outlet = detect_cited_outlet(text)
            
            source_data.append({
                "id": sid,
                "publisher": pub,
                "author": author,
                "text": text,
                "wire": wire,
                "quotes": set(q.lower() for q in quotes),
                "quotes_raw": quotes,
                "tokens": tokens,
                "is_pr": is_pr,
                "is_repeats": is_repeats,
                "cited_outlet": cited_outlet,
            })

        # 2. Pairwise comparison
        n = len(source_data)
        adjacency = defaultdict(set)  # sid -> set of connected sids
        pair_details = {}  # (i, j) -> dict of relationship details

        for i in range(n):
            for j in range(i + 1, n):
                s1 = source_data[i]
                s2 = source_data[j]
                
                shared_wire = s1["wire"] if s1["wire"] and (s1["wire"] == s2["wire"]) else None
                shared_quotes = s1["quotes"] & s2["quotes"]
                jaccard = compute_jaccard_similarity(s1["tokens"], s2["tokens"])
                
                # Check citations
                cites = False
                if s1["cited_outlet"] and (s1["cited_outlet"].lower() in s2["publisher"].lower()):
                    cites = True
                if s2["cited_outlet"] and (s2["cited_outlet"].lower() in s1["publisher"].lower()):
                    cites = True
                    
                dep_type = None
                reason = ""
                
                # Evaluation priority:
                # 1. Same wire service
                if shared_wire:
                    dep_type = IndependenceAssessment.WIRE_SERVICE_DERIVED
                    reason = f"Both sources carry dispatch from {shared_wire}."
                # 2. Both repeat official press release
                elif s1["is_pr"] and s2["is_pr"] and (jaccard > 0.35 or shared_quotes):
                    dep_type = IndependenceAssessment.SHARED_PRESS_RELEASE
                    reason = "Both sources publish details directly from an official press release or statement."
                # 3. High prose overlap without attribution
                elif jaccard >= 0.60:
                    dep_type = IndependenceAssessment.POSSIBLE_CONTENT_DEPENDENCY
                    reason = f"High verbatim text overlap ({jaccard:.2f}) indicates content syndication or copying."
                # 4. Outlets cite the same viral post / unverified witness or cite each other
                elif cites or (s1["is_repeats"] and s2["is_repeats"] and (shared_quotes or jaccard > 0.30)):
                    dep_type = IndependenceAssessment.REPEATS_ORIGINAL_SOURCE
                    reason = "Both outlets repeat a single primary post/witness without independent confirmation."
                elif jaccard >= 0.40 and shared_quotes:
                    dep_type = IndependenceAssessment.POSSIBLE_CONTENT_DEPENDENCY
                    reason = f"Significant shared quotations and non-trivial text overlap ({jaccard:.2f})."

                if dep_type:
                    adjacency[s1["id"]].add(s2["id"])
                    adjacency[s2["id"]].add(s1["id"])
                    pair_details[(s1["id"], s2["id"])] = {
                        "dep_type": dep_type,
                        "shared_wire": shared_wire,
                        "shared_quotes": list(shared_quotes)[:3],
                        "jaccard": round(jaccard, 3),
                        "reason": reason
                    }

        # 3. Form connected clusters (Transitive closure for connected components)
        visited = set()
        clusters_raw = []

        for s in source_data:
            sid = s["id"]
            if sid not in visited:
                component = []
                queue = [sid]
                visited.add(sid)
                
                while queue:
                    curr = queue.pop(0)
                    component.append(curr)
                    for neighbor in adjacency[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                            
                clusters_raw.append(component)

        # 4. Build SourceDependencyCluster models
        structured_clusters: List[SourceDependencyCluster] = []
        cluster_types = set()

        for idx, comp in enumerate(clusters_raw):
            cluster_id = f"cluster-{idx + 1}"
            comp_sources = [s for s in source_data if s["id"] in comp]
            publishers = list(set(s["publisher"] for s in comp_sources))
            
            if len(comp) == 1:
                # Single standalone source or isolated cluster
                s = comp_sources[0]
                if s["wire"]:
                    ctype = IndependenceAssessment.WIRE_SERVICE_DERIVED
                    rationale = f"Standalone report attributed to {s['wire']}."
                    wire = s["wire"]
                elif s["is_pr"]:
                    ctype = IndependenceAssessment.SHARED_PRESS_RELEASE
                    rationale = f"Official press release / government communique by {s['publisher']}."
                    wire = None
                elif s["is_repeats"]:
                    ctype = IndependenceAssessment.REPEATS_ORIGINAL_SOURCE
                    rationale = f"Uncorroborated repetition of a viral post/claim by {s['publisher']}."
                    wire = None
                else:
                    ctype = IndependenceAssessment.INDEPENDENT_REPORTING
                    rationale = f"Autonomous reporting by {s['publisher']} with separate byline and distinct prose."
                    wire = None
                overlap = 0.0
                shared_phrases = []
            else:
                # Multi-node dependent cluster
                # Determine dominant dependency type from pairs
                pair_types = []
                shared_wires = []
                all_quotes = []
                max_jaccard = 0.0
                
                for i in range(len(comp)):
                    for j in range(i + 1, len(comp)):
                        key = (comp[i], comp[j])
                        if key not in pair_details:
                            key = (comp[j], comp[i])
                        if key in pair_details:
                            d = pair_details[key]
                            pair_types.append(d["dep_type"])
                            if d["shared_wire"]:
                                shared_wires.append(d["shared_wire"])
                            all_quotes.extend(d["shared_quotes"])
                            if d["jaccard"] > max_jaccard:
                                max_jaccard = d["jaccard"]

                wire = shared_wires[0] if shared_wires else None
                if wire or IndependenceAssessment.WIRE_SERVICE_DERIVED in pair_types:
                    ctype = IndependenceAssessment.WIRE_SERVICE_DERIVED
                    rationale = f"{len(comp)} outlets ({', '.join(publishers)}) reprinted the same wire dispatch from {wire or 'a wire service'}."
                elif IndependenceAssessment.SHARED_PRESS_RELEASE in pair_types:
                    ctype = IndependenceAssessment.SHARED_PRESS_RELEASE
                    rationale = f"Multiple outlets republished an official press release/communique verbatim."
                elif IndependenceAssessment.REPEATS_ORIGINAL_SOURCE in pair_types:
                    ctype = IndependenceAssessment.REPEATS_ORIGINAL_SOURCE
                    rationale = f"Outlets repeat an unverified viral post/clip without independent newsroom investigation."
                elif IndependenceAssessment.POSSIBLE_CONTENT_DEPENDENCY in pair_types:
                    ctype = IndependenceAssessment.POSSIBLE_CONTENT_DEPENDENCY
                    rationale = f"High textual similarity ({max_jaccard:.2f}) indicates content sharing or syndication."
                else:
                    ctype = IndependenceAssessment.UNKNOWN_DEPENDENCY
                    rationale = "Inadequate metadata to definitively separate independent investigations."

                overlap = max_jaccard
                shared_phrases = list(set(all_quotes))[:3]

            cluster_types.add(ctype)
            structured_clusters.append(SourceDependencyCluster(
                cluster_id=cluster_id,
                dependency_type=ctype,
                primary_source_id=comp[0],
                source_ids=comp,
                publishers=publishers,
                wire_agency=wire,
                rationale=rationale,
                shared_phrases=shared_phrases,
                text_overlap_ratio=round(overlap, 3)
            ))

        # 5. Overall Independence Assessment
        # Count distinct independent entities:
        # A wire cluster counts as 1 entity; distinct INDEPENDENT_REPORTING clusters each count as 1.
        independent_entities_count = len(structured_clusters)
        
        # Assess overall verdict
        if len(structured_clusters) >= 2 and all(c.dependency_type == IndependenceAssessment.INDEPENDENT_REPORTING for c in structured_clusters):
            overall_assessment = IndependenceAssessment.INDEPENDENT_REPORTING
            explanation = (
                f"Multi-source independent verification established: {total_count} articles across "
                f"{len(structured_clusters)} distinct publishers with separate bylines, low text overlap, "
                f"and no common wire service origin."
            )
        elif all(c.dependency_type == IndependenceAssessment.WIRE_SERVICE_DERIVED for c in structured_clusters):
            overall_assessment = IndependenceAssessment.WIRE_SERVICE_DERIVED
            wires = list(set(c.wire_agency for c in structured_clusters if c.wire_agency))
            wire_str = wires[0] if wires else "wire agencies"
            explanation = (
                f"Apparent multi-source volume is non-independent: All {total_count} articles are reprints "
                f"or variations of a single wire service dispatch from {wire_str}."
            )
        elif all(c.dependency_type == IndependenceAssessment.SHARED_PRESS_RELEASE for c in structured_clusters):
            overall_assessment = IndependenceAssessment.SHARED_PRESS_RELEASE
            explanation = (
                f"All {total_count} sources republished the same official press release or government communique. "
                f"Represents a single primary statement rather than independent external corroboration."
            )
        elif all(c.dependency_type == IndependenceAssessment.REPEATS_ORIGINAL_SOURCE for c in structured_clusters):
            overall_assessment = IndependenceAssessment.REPEATS_ORIGINAL_SOURCE
            explanation = (
                f"All {total_count} outlets merely repeat or cite the same initial viral post or witness "
                f"without independent corroboration."
            )
        elif any(c.dependency_type == IndependenceAssessment.POSSIBLE_CONTENT_DEPENDENCY for c in structured_clusters) and independent_entities_count == 1:
            overall_assessment = IndependenceAssessment.POSSIBLE_CONTENT_DEPENDENCY
            explanation = (
                f"High non-quote prose overlap (> 0.60) detected across sources without explicit wire attribution, "
                f"indicating content syndication or verbatim copying."
            )
        elif independent_entities_count >= 2:
            # We have at least 2 distinct clusters (e.g. 1 independent investigative outlet + 1 wire cluster)
            overall_assessment = IndependenceAssessment.INDEPENDENT_REPORTING
            explanation = (
                f"Partially independent confirmation: {total_count} total sources grouped into "
                f"{len(structured_clusters)} distinct investigative clusters (including wire syndication and distinct outlets)."
            )
        else:
            overall_assessment = IndependenceAssessment.UNKNOWN_DEPENDENCY
            explanation = (
                f"Source metadata is insufficient to establish genuine investigative independence. "
                f"Recorded as UNKNOWN_DEPENDENCY to prevent deceptive corroboration."
            )

        return {
            "id": str(uuid.uuid4()),
            "claim_id": claim_id,
            "total_sources_count": total_count,
            "independent_sources_count": independent_entities_count,
            "independence_assessment": overall_assessment,
            "clusters": [c.model_dump() for c in structured_clusters],
            "observable_signals": {
                "total_retrieved": total_count,
                "independent_clusters_count": len(structured_clusters),
                "cluster_types": list(str(t.value) for t in cluster_types),
                "detected_wires": list(set(c.wire_agency for c in structured_clusters if c.wire_agency))
            },
            "explanation": explanation
        }
