from enum import Enum


class ReportStatus(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    FAILED = "failed"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AssetKind(str, Enum):
    GIMP_ORIGINAL = "gimp_original"
    GIMPIFIED_IMAGE = "gimpified_image"
    VIDEO = "video"


class AssetStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"


class JobType(str, Enum):
    EXTRACT_MOMENTS = "extract_moments"
    GIMPIFY_IMAGE = "gimpify_image"
    GENERATE_VIDEO = "generate_video"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


__all__ = [
    "ReportStatus",
    "AssetKind",
    "AssetStatus",
    "JobType",
    "JobStatus",
]
