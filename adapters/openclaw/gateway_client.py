from __future__ import annotations

import json
import subprocess

from application.dto.chat import ChatDispatchRequest, ChatDispatchResponse
from application.services.errors import IntegrationError
from infra.config.settings import Settings


class OpenClawGatewayClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_system_event_command(self, *, text: str, mode: str = "now") -> list[str]:
        return [
            self.settings.openclaw_cli_command,
            "system",
            "event",
            "--text",
            text,
            "--mode",
            mode,
            "--json",
        ]

    def emit_system_event(self, *, event_name: str, payload: dict) -> list[str]:
        text = json.dumps({"event": event_name, "payload": payload}, ensure_ascii=False)
        command = self.build_system_event_command(text=text)
        self._run(command)
        return command

    def dispatch_agent_turn(self, request: ChatDispatchRequest) -> ChatDispatchResponse:
        command = [
            self.settings.openclaw_cli_command,
            "agent",
            "--message",
            request.message,
            "--to",
            request.session_key,
            "--json",
        ]
        self._run(command)
        return ChatDispatchResponse(dispatched=True, command=command)

    def send_message(self, *, message: str, channel: str | None = None, target: str | None = None) -> list[str]:
        resolved_channel = channel or self.settings.openclaw_default_channel
        resolved_target = target or self.settings.openclaw_default_target
        command = [self.settings.openclaw_cli_command, "message", "send", "--message", message, "--json"]
        if resolved_channel:
            command.extend(["--channel", resolved_channel])
        if resolved_target:
            command.extend(["--target", resolved_target])
        self._run(command)
        return command

    def _run(self, command: list[str]) -> None:
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except FileNotFoundError as exc:
            raise IntegrationError(
                "openclaw_cli_not_found",
                f"OpenClaw CLI command '{self.settings.openclaw_cli_command}' was not found in PATH.",
            ) from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip() if exc.stderr else "no stderr"
            raise IntegrationError(
                "openclaw_command_failed",
                f"OpenClaw command failed with exit code {exc.returncode}: {stderr}",
            ) from exc
