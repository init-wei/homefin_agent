from pydantic import BaseModel


class ChatDispatchRequest(BaseModel):
    household_id: str
    session_key: str
    message: str
    route: str | None = None
    channel: str | None = None
    target: str | None = None


class ChatDispatchResponse(BaseModel):
    dispatched: bool
    command: list[str]
