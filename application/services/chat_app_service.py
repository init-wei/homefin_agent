from application.dto.chat import ChatDispatchRequest, ChatDispatchResponse
from adapters.openclaw.gateway_client import OpenClawGatewayClient


class ChatAppService:
    def __init__(self, gateway_client: OpenClawGatewayClient) -> None:
        self.gateway_client = gateway_client

    def dispatch_to_openclaw(self, request: ChatDispatchRequest) -> ChatDispatchResponse:
        return self.gateway_client.dispatch_agent_turn(request)

