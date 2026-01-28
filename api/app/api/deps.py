from fastapi import Header, HTTPException, status


async def get_author_id(x_author_id: str | None = Header(None, alias="X-Author-Id")) -> str:
    if not x_author_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Author-Id header is required",
        )
    return x_author_id


__all__ = ["get_author_id"]
