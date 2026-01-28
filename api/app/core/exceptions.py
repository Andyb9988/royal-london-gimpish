class NotFoundError(Exception):
    pass


class ForbiddenError(Exception):
    pass


class ConflictError(Exception):
    pass


class BadRequestError(Exception):
    pass


__all__ = [
    "NotFoundError",
    "ForbiddenError",
    "ConflictError",
    "BadRequestError",
]
