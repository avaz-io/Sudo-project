from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    """Base for response schemas: can be built directly from ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class InputModel(BaseModel):
    """Base for request bodies: trims strings and rejects unknown fields."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
