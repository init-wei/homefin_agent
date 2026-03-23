from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from application.dto.auth import AuthLoginRequest, AuthRegisterRequest, AuthTokenResponse, UserRead
from application.services.errors import AuthenticationError, ValidationError
from infra.config.settings import Settings
from infra.db.models import UserModel
from infra.db.repositories import UserRepository

PBKDF2_ITERATIONS = 390000


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        algorithm, iterations, salt, expected = password_hash.split("$", maxsplit=3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        _b64decode(salt),
        int(iterations),
    )
    return hmac.compare_digest(_b64encode(digest), expected)


def create_access_token(*, user: UserModel, settings: Settings) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=settings.auth_token_ttl_minutes)).timestamp()),
    }
    encoded_header = _b64encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    encoded_payload = _b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    signature = hmac.new(settings.auth_secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_payload}.{_b64encode(signature)}"


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".", maxsplit=2)
    except ValueError as exc:
        raise AuthenticationError("invalid_token", "Access token format is invalid.") from exc

    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    expected_signature = hmac.new(settings.auth_secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(_b64encode(expected_signature), encoded_signature):
        raise AuthenticationError("invalid_token", "Access token signature is invalid.")

    try:
        payload = json.loads(_b64decode(encoded_payload))
    except (ValueError, json.JSONDecodeError) as exc:
        raise AuthenticationError("invalid_token", "Access token payload is invalid.") from exc

    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(datetime.now(timezone.utc).timestamp()):
        raise AuthenticationError("token_expired", "Access token has expired.")
    return payload


class AuthService:
    def __init__(self, user_repo: UserRepository, settings: Settings) -> None:
        self.user_repo = user_repo
        self.settings = settings

    def register_user(self, request: AuthRegisterRequest) -> UserModel:
        if len(request.password) < 8:
            raise ValidationError("password_too_short", "Password must be at least 8 characters long.")
        return self.user_repo.create(
            email=request.email.strip().lower(),
            display_name=request.display_name.strip(),
            password_hash=hash_password(request.password),
        )

    def authenticate(self, request: AuthLoginRequest) -> UserModel:
        user = self.user_repo.get_by_email(request.email.strip().lower())
        if not user or not verify_password(request.password, user.password_hash):
            raise AuthenticationError("invalid_credentials", "Email or password is incorrect.")
        return user

    def issue_token_response(self, user: UserModel) -> AuthTokenResponse:
        return AuthTokenResponse(
            access_token=create_access_token(user=user, settings=self.settings),
            user=UserRead.model_validate(user),
        )
