"""Minimal client for the Vercel Blob REST API.

There is no official Vercel Blob SDK for Python, so this calls the same
REST endpoint the @vercel/blob JS SDK uses under the hood
(https://vercel.com/api/blob). Only the operations Safety Sentinel needs
(upload, download) are implemented.
"""
from typing import Optional

import requests

from app.config import BLOB_READ_WRITE_TOKEN

BLOB_API_URL = "https://vercel.com/api/blob"
BLOB_API_VERSION = "12"


def _store_id_from_token(token: str) -> str:
    parts = token.split("_")
    return parts[3] if len(parts) > 3 else ""


def upload_blob(pathname: str, data: bytes, content_type: Optional[str] = None) -> str:
    """Upload bytes to Vercel Blob and return the public, fetchable URL."""
    headers = {
        "authorization": f"Bearer {BLOB_READ_WRITE_TOKEN}",
        "x-api-version": BLOB_API_VERSION,
        "x-vercel-blob-store-id": _store_id_from_token(BLOB_READ_WRITE_TOKEN),
        "x-vercel-blob-access": "public",
        "x-add-random-suffix": "0",
        "x-allow-overwrite": "1",
    }
    if content_type:
        headers["x-content-type"] = content_type

    response = requests.put(
        f"{BLOB_API_URL}/",
        params={"pathname": pathname},
        data=data,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["url"]


def download_blob(url: str) -> bytes:
    """Fetch blob bytes from its public URL (no auth required for public blobs)."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content
