from pydantic import BaseModel, ConfigDict

from domain.enums.identity import BindingRole, BindingStatus


class IdentityBindingCreateRequest(BaseModel):
    provider: str
    external_actor_id: str
    user_id: str
    member_id: str | None = None
    household_id: str
    role: BindingRole


class IdentityBindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider: str
    external_actor_id: str
    user_id: str
    member_id: str | None
    household_id: str
    role: BindingRole
    status: BindingStatus

