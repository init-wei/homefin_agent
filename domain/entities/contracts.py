import json
from dataclasses import asdict, dataclass
from typing import Any

from domain.enums.identity import BindingRole, BindingStatus


@dataclass(slots=True)
class ExternalIdentityBinding:
    provider: str
    external_actor_id: str
    user_id: str
    member_id: str | None
    household_id: str
    role: BindingRole
    status: BindingStatus = BindingStatus.ACTIVE


@dataclass(slots=True)
class AgentExecutionContext:
    session_key: str
    household_id: str
    acting_user_id: str
    member_id: str | None
    role: BindingRole
    can_write: bool
    channel: str | None = None
    route: str | None = None


@dataclass(slots=True)
class AgentToolResult:
    ok: bool
    data: dict[str, Any] | None
    display_text: str
    audit_id: str
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self), default=str))
