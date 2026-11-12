import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Tuple
import filetype
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

CHUNK_SIZE = 64 * 1024  # 64 KB
DISALLOWED_EXTENSIONS = {".exe", ".bat", ".cmd", ".sh", ".ps1", ".vbs", ".dll", ".so", ".dylib"}

class StorageManager:
    def __init__(self, upload_dir: Path | None = None, max_size_bytes: int | None = None):
        self.upload_dir = upload_dir or settings.UPLOAD_DIR
        self.max_size_bytes = max_size_bytes or settings.MAX_UPLOAD_SIZE_BYTES
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload_stream(self, upload_file: UploadFile) -> Tuple[str, str, int, str]:
        """
        Streams an uploaded file in chunks, computes SHA-256 in a single pass,
        detects MIME type safely from header magic bytes, and stores to content-addressed path.
        Returns: (sha256_hash, mime_type, file_size_bytes, relative_file_path)
        """
        hasher = hashlib.sha256()
        total_bytes = 0
        header_sample = bytearray()

        # Create temporary file to stream into
        temp_file = tempfile.NamedTemporaryFile(delete=False, dir=self.upload_dir)
        temp_path = Path(temp_file.name)
        try:
            while True:
                chunk = await upload_file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > self.max_size_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Uploaded file exceeds maximum allowed size of {self.max_size_bytes} bytes"
                    )
                hasher.update(chunk)
                if len(header_sample) < 2048:
                    header_sample.extend(chunk[:2048 - len(header_sample)])
                temp_file.write(chunk)
            
            # Explicitly close before any move or unlink (critical on Windows)
            temp_file.close()

            if total_bytes == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Submitted file is empty (0 bytes)"
                )

        except Exception:
            temp_file.close()
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise

        sha256_hash = hasher.hexdigest()

        # Determine genuine MIME type from magic bytes
        kind = filetype.guess(bytes(header_sample))
        if kind:
            detected_mime = kind.mime
            extension = f".{kind.extension}"
        else:
            detected_mime = upload_file.content_type or "application/octet-stream"
            # Extract extension from original filename if safe
            orig_ext = Path(upload_file.filename or "").suffix.lower()
            if orig_ext and orig_ext not in DISALLOWED_EXTENSIONS and len(orig_ext) <= 10:
                extension = orig_ext
            else:
                extension = ".bin"

        # Content-addressed path: data/uploads/ab/abcdef...ext
        shard_dir = self.upload_dir / sha256_hash[:2]
        shard_dir.mkdir(parents=True, exist_ok=True)
        final_path = shard_dir / f"{sha256_hash}{extension}"

        # If file already exists with same hash, remove temp file and reuse existing
        if final_path.exists():
            temp_path.unlink()
        else:
            shutil.move(str(temp_path), str(final_path))

        relative_path = str(final_path.relative_to(self.upload_dir.parent))
        return sha256_hash, detected_mime, total_bytes, relative_path

    def save_raw_text(self, text: str) -> Tuple[str, str, int, str]:
        """
        Saves raw text content directly into content-addressed storage.
        Returns: (sha256_hash, 'text/plain', byte_length, relative_file_path)
        """
        encoded = text.encode("utf-8")
        sha256_hash = hashlib.sha256(encoded).hexdigest()
        byte_length = len(encoded)

        shard_dir = self.upload_dir / sha256_hash[:2]
        shard_dir.mkdir(parents=True, exist_ok=True)
        final_path = shard_dir / f"{sha256_hash}.txt"

        if not final_path.exists():
            with open(final_path, "wb") as f:
                f.write(encoded)

        relative_path = str(final_path.relative_to(self.upload_dir.parent))
        return sha256_hash, "text/plain", byte_length, relative_path

    def resolve_safe_path(self, relative_path: str) -> Path:
        """
        Resolves a stored relative path and guarantees no directory traversal outside DATA_DIR.
        """
        base = self.upload_dir.parent.resolve()
        target = (base / relative_path).resolve()
        try:
            target.relative_to(base)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security violation: Directory traversal path detected"
            )
        return target

storage_manager = StorageManager()
