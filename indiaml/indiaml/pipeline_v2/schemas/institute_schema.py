from enum import Enum
from typing import Annotated, List, Optional

from pydantic import BaseModel, HttpUrl, StringConstraints, constr


class InstituteType(str, Enum):
    """Allowed institution categories."""
    academic = "academic"
    corporate = "corporate"
    government = "government"


# Two-letter ISO-3166 code, uppercase
CountryCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")]


class Institute(BaseModel):
    institute_name: str
    department: Optional[str] = None
    lab: Optional[str] = None
    location: Optional[str] = None
    website: Optional[HttpUrl] = None  # Validates syntax & scheme
    type: Optional[InstituteType] = None
    country: Optional[CountryCode] = None

    class Config:
        extra = "allow"  # = additionalProperties: false


# --- Optional wrapper if you’d like to validate the whole list at once ----
class Institutes(BaseModel):
    """Root model representing an array of institutes."""
    __root__: List[Institute]
