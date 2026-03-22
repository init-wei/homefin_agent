from pydantic import BaseModel


class HouseholdBootstrapRequest(BaseModel):
    household_name: str
    owner_email: str
    owner_display_name: str
    member_name: str | None = None


class HouseholdBootstrapRead(BaseModel):
    user_id: str
    household_id: str
    member_id: str

