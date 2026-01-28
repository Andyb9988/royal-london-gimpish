from pydantic import BaseModel, Field


class ExtractMomentsOut(BaseModel):
    gimp_name: str | None = Field(
        default=None,
        description="Name of gimp of the day, if mentioned.",
    )
    champagne_moment: str | None = Field(
        default=None,
        description="Best moment excerpt, if mentioned.",
    )


__all__ = ["ExtractMomentsOut"]
