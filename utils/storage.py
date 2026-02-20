"""
Supabase Storage integration for persistent file storage.

Render free tier has ephemeral disk — files vanish on restart.
Supabase free tier gives 1 GB storage, so we park all uploaded
PDFs there and pull them back when needed for processing.

Setup:
  1. Create a Supabase project at https://supabase.com/dashboard
  2. Create a PUBLIC bucket named "dabo-files"
  3. Set env vars: SUPABASE_URL, SUPABASE_KEY
"""
from __future__ import annotations

import os
from pathlib import Path

from utils.logger import get_logger

log = get_logger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
BUCKET = "dabo-files"

_client = None


def _get_client():
    """Lazy-init Supabase client."""
    global _client
    if _client is not None:
        return _client
    if not SUPABASE_URL or not SUPABASE_KEY:
        log.warning("Supabase not configured — files stay on local disk only")
        return None
    try:
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        log.info("Supabase storage connected: %s", SUPABASE_URL)
        return _client
    except Exception as e:
        log.error("Supabase init failed: %s", e)
        return None


def is_enabled() -> bool:
    """Check if Supabase storage is configured."""
    return bool(SUPABASE_URL and SUPABASE_KEY)


def upload_file(local_path: str | Path, project_id: int, filename: str) -> str | None:
    """
    Upload a file to Supabase Storage.

    Returns the remote path on success, None on failure.
    Files are stored as: projects/{project_id}/{filename}
    """
    client = _get_client()
    if not client:
        return None

    remote_path = f"projects/{project_id}/{filename}"

    try:
        with open(str(local_path), "rb") as f:
            client.storage.from_(BUCKET).upload(
                path=remote_path,
                file=f,
                file_options={"cache-control": "3600", "upsert": "true"},
            )
        log.info("Uploaded to Supabase: %s", remote_path)
        return remote_path
    except Exception as e:
        log.error("Supabase upload failed for %s: %s", filename, e)
        return None


def download_file(project_id: int, filename: str, local_dest: str | Path) -> bool:
    """
    Download a file from Supabase Storage to local disk.

    Returns True on success, False on failure.
    """
    client = _get_client()
    if not client:
        return False

    remote_path = f"projects/{project_id}/{filename}"

    try:
        data = client.storage.from_(BUCKET).download(remote_path)
        Path(local_dest).parent.mkdir(parents=True, exist_ok=True)
        with open(str(local_dest), "wb") as f:
            f.write(data)
        log.info("Downloaded from Supabase: %s -> %s", remote_path, local_dest)
        return True
    except Exception as e:
        log.error("Supabase download failed for %s: %s", remote_path, e)
        return False


def get_public_url(project_id: int, filename: str) -> str | None:
    """Get a public URL for a file (bucket must be public)."""
    client = _get_client()
    if not client:
        return None

    remote_path = f"projects/{project_id}/{filename}"
    try:
        url = client.storage.from_(BUCKET).get_public_url(remote_path)
        return url
    except Exception as e:
        log.error("Supabase public URL failed for %s: %s", remote_path, e)
        return None


def delete_file(project_id: int, filename: str) -> bool:
    """Delete a file from Supabase Storage."""
    client = _get_client()
    if not client:
        return False

    remote_path = f"projects/{project_id}/{filename}"
    try:
        client.storage.from_(BUCKET).remove([remote_path])
        log.info("Deleted from Supabase: %s", remote_path)
        return True
    except Exception as e:
        log.error("Supabase delete failed for %s: %s", remote_path, e)
        return False


def list_files(project_id: int) -> list[dict]:
    """List all files for a project in Supabase Storage."""
    client = _get_client()
    if not client:
        return []

    remote_prefix = f"projects/{project_id}"
    try:
        files = client.storage.from_(BUCKET).list(remote_prefix)
        return files or []
    except Exception as e:
        log.error("Supabase list failed for project %d: %s", project_id, e)
        return []


def ensure_local(project_id: int, filename: str, local_dir: str | Path) -> Path | None:
    """
    Make sure a file exists locally — download from Supabase if missing.

    This is the key function for Render ephemeral disk recovery:
    after a restart, files are gone locally but still in Supabase.
    """
    local_path = Path(local_dir) / filename
    if local_path.exists():
        return local_path

    if download_file(project_id, filename, local_path):
        return local_path

    return None
