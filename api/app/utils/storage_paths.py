import mimetypes

from app.core.enums import AssetKind

_MIME_OVERRIDES = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    "video/mp4": "mp4",
    "video/quicktime": "mov",
}


def mime_to_ext(mime_type: str) -> str:
    mime_type = mime_type.lower().strip()
    if mime_type in _MIME_OVERRIDES:
        return _MIME_OVERRIDES[mime_type]
    ext = mimetypes.guess_extension(mime_type)
    if ext:
        return ext.lstrip(".").lower()
    return "bin"


def gcs_object_key(report_id: str, kind: AssetKind | str, ext: str) -> str:
    ext = ext.lstrip(".").lower()
    kind_value = kind.value if isinstance(kind, AssetKind) else str(kind)
    return f"reports/{report_id}/{kind_value}.{ext}"


__all__ = ["mime_to_ext", "gcs_object_key"]
