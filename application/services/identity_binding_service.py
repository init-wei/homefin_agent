from application.dto.identity import IdentityBindingCreateRequest
from application.services.errors import PermissionDenied, ValidationError
from domain.entities.contracts import AgentExecutionContext, ExternalIdentityBinding
from domain.enums.identity import BindingRole
from infra.config.settings import Settings
from infra.db.models import ExternalIdentityBindingModel
from infra.db.repositories import BindingRepository, HouseholdRepository, MemberRepository, UserRepository


class IdentityBindingService:
    def __init__(
        self,
        binding_repo: BindingRepository,
        household_repo: HouseholdRepository,
        member_repo: MemberRepository,
        user_repo: UserRepository,
        settings: Settings,
    ) -> None:
        self.binding_repo = binding_repo
        self.household_repo = household_repo
        self.member_repo = member_repo
        self.user_repo = user_repo
        self.settings = settings

    def create_binding(self, request: IdentityBindingCreateRequest) -> ExternalIdentityBindingModel:
        household = self.household_repo.get(request.household_id)
        self.user_repo.get(request.user_id)
        if self.binding_repo.find_conflict(
            provider=request.provider,
            external_actor_id=request.external_actor_id,
            household_id=request.household_id,
        ):
            raise ValidationError(
                "binding_already_exists",
                f"An identity binding already exists for provider={request.provider}, actor={request.external_actor_id}, household={request.household_id}.",
            )
        if request.role == BindingRole.OWNER and request.user_id != household.owner_user_id:
            raise ValidationError(
                "binding_owner_user_mismatch",
                f"User {request.user_id} is not the owner of household {request.household_id}.",
            )
        member = None
        if request.member_id:
            member = self.member_repo.get_for_household(member_id=request.member_id, household_id=request.household_id)
            if member.user_id and member.user_id != request.user_id:
                raise ValidationError(
                    "binding_user_member_mismatch",
                    f"Member {member.id} belongs to user {member.user_id}, not {request.user_id}.",
                )
        if request.role == BindingRole.OWNER:
            if member and member.role != "owner":
                raise ValidationError(
                    "binding_owner_member_required",
                    f"Owner bindings must use a member with role 'owner'; got role {member.role}.",
                )
        else:
            if not request.member_id:
                raise ValidationError("binding_member_id_required", "Member bindings require a member_id.")
        binding = ExternalIdentityBinding(**request.model_dump())
        return self.binding_repo.create(binding)

    def resolve_context(
        self,
        *,
        provider: str,
        external_actor_id: str,
        household_id: str,
        channel: str | None = None,
        route: str | None = None,
    ) -> AgentExecutionContext:
        binding = self.binding_repo.find_active(
            provider=provider,
            external_actor_id=external_actor_id,
            household_id=household_id,
        )
        if not binding:
            raise PermissionDenied("identity_not_bound", "No active OpenClaw identity binding exists for this actor.")
        return AgentExecutionContext(
            session_key=f"agent:homefin:{household_id}:{provider}:{external_actor_id}",
            household_id=household_id,
            acting_user_id=binding.user_id,
            member_id=binding.member_id,
            role=binding.role,
            can_write=binding.role.value in self.settings.allowed_write_roles,
            channel=channel,
            route=route,
        )
