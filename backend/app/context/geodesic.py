import math
from typing import Optional, Tuple, Dict, Any

# Standard WGS-84 mean Earth radius in kilometers
EARTH_RADIUS_KM = 6371.0

# Curated reference gazetteer mapping common cities/locations to reference centroids (lat, lon).
# NOTE: These coordinates represent municipal or geographic reference centroids, NOT forensic event coordinates.
KNOWN_LOCATION_GAZETTEER: Dict[str, Tuple[float, float]] = {
    "mumbai": (18.9220, 72.8347),
    "delhi": (28.6139, 77.2090),
    "new delhi": (28.6139, 77.2090),
    "chennai": (13.0827, 80.2707),
    "hyderabad": (17.3850, 78.4867),
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "kolkata": (22.5726, 88.3639),
    "kerala": (10.8505, 76.2711),
    "tokyo": (35.6762, 139.6503),
    "japan": (36.2048, 138.2529),
    "turkey": (38.9637, 35.2433),
    "istanbul": (41.0082, 28.9784),
    "geneva": (46.2044, 6.1432),
    "switzerland": (46.8182, 8.2275),
    "paris": (48.8566, 2.3522),
    "france": (46.2276, 2.2137),
    "london": (51.5074, -0.1278),
    "united kingdom": (55.3781, -3.4360),
    "uk": (55.3781, -3.4360),
    "washington": (38.9072, -77.0369),
    "washington dc": (38.9072, -77.0369),
    "new york": (40.7128, -74.0060),
    "usa": (37.0902, -95.7129),
    "united states": (37.0902, -95.7129),
}

CAMERA_LOCATION_DISCLAIMER = (
    "Camera GPS indicates device position at capture time, which may differ significantly "
    "from event location in telephoto, aerial, drone, or high-altitude photography. "
    "City reference points are geographic centroids, not forensic coordinates. "
    "Distance differences are observational signals and do not constitute proof of "
    "geographic contradiction without independent corroborating context."
)

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes Great-Circle geodesic distance in kilometers between two points
    on the WGS-84 sphere using the Haversine formula.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    # Clamp to avoid numerical floating-point inaccuracies outside [-1.0, 1.0]
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(EARTH_RADIUS_KM * c, 2)

def get_known_location_coordinates(name: str) -> Optional[Tuple[float, float]]:
    """
    Retrieves reference coordinates for a named city, region, or country landmark.
    Case-insensitive lookup against the gazetteer.
    """
    if not name:
        return None
    normalized = name.strip().lower()
    return KNOWN_LOCATION_GAZETTEER.get(normalized)

def evaluate_spatial_relationship(
    claimed_location: Optional[str],
    observed_gps: Optional[Tuple[float, float]],
    has_corroborating_context: bool = False,
    corroborating_context_notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates geographical context between a claimed location and observed GPS coordinates.
    Epistemological Rules:
    - Distance is an observational quantitative metric, NEVER a universal truth criterion.
    - No fixed universal distance threshold is used as an absolute fraud arbiter.
    - Camera location is explicitly distinguished from event location.
    - Identifying a GEOGRAPHICAL_CONTRADICTION requires corroborating context
      (e.g., authoritative reports placing event in another country/region),
      not just an isolated distant camera GPS coordinate.
    """
    if not claimed_location or not observed_gps:
        return {
            "status": "INSUFFICIENT_GEOGRAPHICAL_DATA",
            "spatial_distance_km": None,
            "claimed_location": claimed_location,
            "observed_gps": observed_gps,
            "is_observational_divergence_signal": False,
            "is_geographical_contradiction": False,
            "camera_vs_event_caveat": CAMERA_LOCATION_DISCLAIMER,
            "rationale": "Incomplete geographic data (missing claimed location or camera GPS). Cannot evaluate spatial alignment."
        }

    ref_coords = get_known_location_coordinates(claimed_location)
    if not ref_coords:
        return {
            "status": "UNKNOWN_CLAIMED_LOCATION",
            "spatial_distance_km": None,
            "claimed_location": claimed_location,
            "observed_gps": observed_gps,
            "is_observational_divergence_signal": False,
            "is_geographical_contradiction": False,
            "camera_vs_event_caveat": CAMERA_LOCATION_DISCLAIMER,
            "rationale": f"Claimed location '{claimed_location}' not found in reference gazetteer. Coordinates unavailable."
        }

    distance_km = haversine_distance_km(
        ref_coords[0], ref_coords[1],
        observed_gps[0], observed_gps[1]
    )

    # Observational divergence: note substantial physical separation
    is_divergence = distance_km > 50.0

    # Contradiction: ONLY if substantial physical separation AND corroborating context is present
    is_contradiction = is_divergence and has_corroborating_context

    if is_contradiction:
        rationale = (
            f"Geographical contradiction identified: distance between reference centroid for '{claimed_location}' "
            f"and observed location is {distance_km} km, corroborated by context: {corroborating_context_notes or 'corroborating evidence confirms different origin'}."
        )
    elif is_divergence:
        rationale = (
            f"Observational spatial divergence noted: camera GPS is {distance_km} km from reference centroid "
            f"for '{claimed_location}'. In the absence of corroborating context, this remains an observational signal "
            f"(camera position at capture may differ from event location, or reference is an approximate centroid)."
        )
    else:
        rationale = (
            f"Observed camera GPS is within {distance_km} km of reference centroid for '{claimed_location}'. "
            f"Consistent with municipal / regional proximity."
        )

    return {
        "status": "GEOGRAPHICAL_EVALUATED",
        "spatial_distance_km": distance_km,
        "claimed_location": claimed_location,
        "reference_centroid": ref_coords,
        "observed_gps": observed_gps,
        "is_observational_divergence_signal": is_divergence,
        "is_geographical_contradiction": is_contradiction,
        "has_corroborating_context": has_corroborating_context,
        "corroborating_context_notes": corroborating_context_notes,
        "camera_vs_event_caveat": CAMERA_LOCATION_DISCLAIMER,
        "rationale": rationale
    }
