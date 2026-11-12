import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from PIL import Image, ExifTags
import av
import mutagen

logger = logging.getLogger("truthnet.extractors.metadata")

def _convert_gps_coordinate(coord_tuple: Any, ref: Optional[str]) -> Optional[float]:
    """Convert EXIF GPS coordinate tuple (degrees, minutes, seconds) to decimal degrees."""
    if not coord_tuple or len(coord_tuple) < 3:
        return None
    try:
        def _to_float(val: Any) -> float:
            if hasattr(val, "numerator") and hasattr(val, "denominator"):
                return float(val.numerator) / float(val.denominator) if val.denominator != 0 else 0.0
            if isinstance(val, tuple) and len(val) == 2:
                return float(val[0]) / float(val[1]) if val[1] != 0 else 0.0
            return float(val)

        degrees = _to_float(coord_tuple[0])
        minutes = _to_float(coord_tuple[1])
        seconds = _to_float(coord_tuple[2])

        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        if ref and str(ref).upper() in ("S", "W"):
            decimal = -decimal
        return round(decimal, 6)
    except Exception as e:
        logger.warning(f"Error parsing GPS coordinate {coord_tuple} with ref {ref}: {e}")
        return None

def _sanitize_for_json(val: Any) -> Any:
    """Recursively convert bytes, IFDRational, and complex types to JSON-serializable types."""
    if isinstance(val, bytes):
        try:
            return val.decode("utf-8", errors="replace")
        except Exception:
            return val.hex()
    if hasattr(val, "numerator") and hasattr(val, "denominator"):
        return float(val.numerator) / float(val.denominator) if val.denominator != 0 else 0.0
    if isinstance(val, dict):
        return {str(k): _sanitize_for_json(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_sanitize_for_json(x) for x in val]
    return val

class ImageMetadataExtractor:
    """
    Extracts observed technical metadata and EXIF properties from image files.
    Preserves raw EXIF verbatim alongside normalized values.
    Enforces timezone discipline: naive timestamps are never assumed to be UTC.
    """

    @staticmethod
    def extract(file_path: Path) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "category": "OBSERVED_DATA",
            "media_type": "IMAGE",
            "file_size_bytes": file_path.stat().st_size if file_path.exists() else 0,
            "dimensions": None,
            "format": None,
            "color_mode": None,
            "is_animated": False,
            "raw_exif": {},
            "normalized_exif": {},
            "gps": None,
            "timezone_info": {
                "timezone_detected": False,
                "timezone_offset": None,
                "confidence": "UNSPECIFIED_LOCAL",
                "disclaimer": "Observed timestamp lacks explicit timezone offset. Do not assume UTC or local timezone as verified fact."
            },
            "missing_fields": [],
            "malformed_fields": [],
            "metadata_status": "COMPLETED",
            "disclaimer": "All metadata represents unverified observed header properties and does not constitute cryptographic proof of capture authenticity."
        }

        try:
            with Image.open(file_path) as img:
                result["dimensions"] = {"width": img.width, "height": img.height}
                result["format"] = img.format
                result["color_mode"] = img.mode
                result["is_animated"] = getattr(img, "is_animated", False)

                raw_exif_data = img._getexif()
                if not raw_exif_data:
                    result["missing_fields"].append("EXIF")
                    return result

                raw_exif_dict: Dict[str, Any] = {}
                gps_info_raw: Dict[str, Any] = {}

                for tag_id, value in raw_exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag_id, f"Tag_{tag_id}")
                    sanitized_val = _sanitize_for_json(value)
                    raw_exif_dict[tag_name] = sanitized_val

                    if tag_name == "GPSInfo" and isinstance(value, dict):
                        for gps_id, gps_val in value.items():
                            gps_tag_name = ExifTags.GPSTAGS.get(gps_id, f"GPS_{gps_id}")
                            gps_info_raw[gps_tag_name] = _sanitize_for_json(gps_val)

                result["raw_exif"] = raw_exif_dict

                # Normalized fields extraction
                normalized: Dict[str, Any] = {}
                if "Make" in raw_exif_dict:
                    normalized["camera_make"] = raw_exif_dict["Make"]
                if "Model" in raw_exif_dict:
                    normalized["camera_model"] = raw_exif_dict["Model"]
                if "Software" in raw_exif_dict:
                    normalized["software"] = raw_exif_dict["Software"]
                if "LensModel" in raw_exif_dict:
                    normalized["lens_model"] = raw_exif_dict["LensModel"]
                if "Orientation" in raw_exif_dict:
                    normalized["orientation"] = raw_exif_dict["Orientation"]

                # Timestamp normalization and timezone discipline
                dt_original = raw_exif_dict.get("DateTimeOriginal") or raw_exif_dict.get("DateTime")
                if dt_original:
                    normalized["datetime_original_raw"] = str(dt_original)
                    
                    # Check for explicit EXIF offset tag (0x9288 OffsetTimeOriginal or OffsetTime)
                    offset = raw_exif_dict.get("OffsetTimeOriginal") or raw_exif_dict.get("OffsetTime")
                    if offset:
                        result["timezone_info"]["timezone_detected"] = True
                        result["timezone_info"]["timezone_offset"] = str(offset)
                        result["timezone_info"]["confidence"] = "EXPLICIT_HEADER_OFFSET"
                        result["timezone_info"]["disclaimer"] = "Timezone offset was explicitly recorded in EXIF header."
                    else:
                        result["timezone_info"]["timezone_detected"] = False
                        result["timezone_info"]["timezone_offset"] = None
                        result["timezone_info"]["confidence"] = "UNSPECIFIED_LOCAL"
                else:
                    result["missing_fields"].append("DateTimeOriginal")

                # GPS extraction
                if gps_info_raw:
                    lat = _convert_gps_coordinate(gps_info_raw.get("GPSLatitude"), gps_info_raw.get("GPSLatitudeRef"))
                    lon = _convert_gps_coordinate(gps_info_raw.get("GPSLongitude"), gps_info_raw.get("GPSLongitudeRef"))
                    alt = gps_info_raw.get("GPSAltitude")
                    
                    if lat is not None and lon is not None:
                        result["gps"] = {
                            "latitude": lat,
                            "longitude": lon,
                            "altitude": alt,
                            "status": "OBSERVED",
                            "disclaimer": "GPS coordinates are observed EXIF values and do not constitute verified proof of capture location."
                        }
                    else:
                        result["malformed_fields"].append("GPSInfo")

                result["normalized_exif"] = normalized

        except Exception as e:
            logger.error(f"Image metadata extraction failed for {file_path}: {e}")
            result["metadata_status"] = "FAILED"
            result["error"] = str(e)

        return result

class VideoMetadataExtractor:
    """
    Extracts container, video stream, and audio stream metadata from video files using PyAV.
    Validates unreliable/missing FPS, durations, and frame counts.
    """

    @staticmethod
    def extract(file_path: Path) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "category": "OBSERVED_DATA",
            "media_type": "VIDEO",
            "file_size_bytes": file_path.stat().st_size if file_path.exists() else 0,
            "container_format": None,
            "duration_seconds": None,
            "bit_rate": None,
            "video_streams": [],
            "audio_streams": [],
            "has_audio": False,
            "audio_stream_count": 0,
            "unreliable_metrics": [],
            "metadata_status": "COMPLETED",
            "disclaimer": "Container stream metrics are observed file headers and do not certify playback integrity across all decoders."
        }

        try:
            with av.open(str(file_path)) as container:
                result["container_format"] = container.format.name if container.format else None
                if container.duration:
                    result["duration_seconds"] = round(float(container.duration) / float(av.time_base), 3)
                result["bit_rate"] = container.bit_rate

                for v_stream in container.streams.video:
                    fps = None
                    if v_stream.average_rate:
                        fps = round(float(v_stream.average_rate), 2)
                    elif v_stream.base_rate:
                        fps = round(float(v_stream.base_rate), 2)

                    if fps is None or fps <= 0 or fps > 240:
                        result["unreliable_metrics"].append("fps_unreliable_or_variable")

                    v_info = {
                        "index": v_stream.index,
                        "codec_name": v_stream.codec_context.name if v_stream.codec_context else None,
                        "width": v_stream.codec_context.width if v_stream.codec_context else None,
                        "height": v_stream.codec_context.height if v_stream.codec_context else None,
                        "fps": fps,
                        "frames": v_stream.frames if v_stream.frames > 0 else None,
                        "pixel_format": v_stream.codec_context.pix_fmt if v_stream.codec_context else None,
                        "bit_rate": v_stream.codec_context.bit_rate if v_stream.codec_context else None,
                    }
                    result["video_streams"].append(v_info)

                for a_stream in container.streams.audio:
                    a_info = {
                        "index": a_stream.index,
                        "codec_name": a_stream.codec_context.name if a_stream.codec_context else None,
                        "channels": a_stream.codec_context.channels if a_stream.codec_context else None,
                        "sample_rate": a_stream.codec_context.sample_rate if a_stream.codec_context else None,
                        "bit_rate": a_stream.codec_context.bit_rate if a_stream.codec_context else None,
                        "format": a_stream.codec_context.format.name if (a_stream.codec_context and a_stream.codec_context.format) else None
                    }
                    result["audio_streams"].append(a_info)

                result["has_audio"] = len(result["audio_streams"]) > 0
                result["audio_stream_count"] = len(result["audio_streams"])

        except Exception as e:
            logger.error(f"Video metadata extraction failed for {file_path}: {e}")
            result["metadata_status"] = "FAILED"
            result["error"] = str(e)

        return result

class AudioMetadataExtractor:
    """
    Extracts observed technical properties from standalone audio files.
    """

    @staticmethod
    def extract(file_path: Path) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "category": "OBSERVED_DATA",
            "media_type": "AUDIO",
            "file_size_bytes": file_path.stat().st_size if file_path.exists() else 0,
            "duration_seconds": None,
            "channels": None,
            "sample_rate": None,
            "bit_rate": None,
            "codec": None,
            "tags": {},
            "metadata_status": "COMPLETED",
            "disclaimer": "Audio properties represent stream metadata and do not authenticate acoustic origin."
        }

        try:
            # Try PyAV first for unified decoding
            with av.open(str(file_path)) as container:
                if container.duration:
                    result["duration_seconds"] = round(float(container.duration) / float(av.time_base), 3)
                result["bit_rate"] = container.bit_rate
                if container.streams.audio:
                    astream = container.streams.audio[0]
                    if astream.codec_context:
                        result["codec"] = astream.codec_context.name
                        result["channels"] = astream.codec_context.channels
                        result["sample_rate"] = astream.codec_context.sample_rate

            # Try mutagen for ID3/Vorbis/FLAC tags
            try:
                m_file = mutagen.File(str(file_path))
                if m_file and m_file.tags:
                    for k, v in m_file.tags.items():
                        result["tags"][str(k)] = str(v)
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Audio metadata extraction failed for {file_path}: {e}")
            result["metadata_status"] = "FAILED"
            result["error"] = str(e)

        return result
