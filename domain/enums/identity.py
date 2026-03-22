from enum import StrEnum


class BindingRole(StrEnum):
    OWNER = "owner"
    MEMBER = "member"


class BindingStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"

