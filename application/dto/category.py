from pydantic import BaseModel, ConfigDict


class CategoryCreateRequest(BaseModel):
    household_id: str
    name: str
    parent_id: str | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    household_id: str
    name: str
    parent_id: str | None

