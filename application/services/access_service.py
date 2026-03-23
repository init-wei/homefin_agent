from __future__ import annotations

from dataclasses import dataclass

from application.services.errors import PermissionDenied
from infra.db.models import HouseholdModel, MemberModel, UserModel
from infra.db.repositories import HouseholdRepository, MemberRepository


@dataclass(slots=True)
class HouseholdAccessContext:
    household: HouseholdModel
    user: UserModel
    member: MemberModel | None
    is_owner: bool


class AccessService:
    def __init__(self, household_repo: HouseholdRepository, member_repo: MemberRepository) -> None:
        self.household_repo = household_repo
        self.member_repo = member_repo

    def resolve_household_access(self, *, household_id: str, user: UserModel) -> HouseholdAccessContext:
        household = self.household_repo.get(household_id)
        owner_member = self.member_repo.find_by_user_and_household(user_id=user.id, household_id=household_id)
        if household.owner_user_id == user.id:
            return HouseholdAccessContext(household=household, user=user, member=owner_member, is_owner=True)
        if owner_member is None:
            raise PermissionDenied("household_access_denied", f"User {user.id} cannot access household {household_id}.")
        return HouseholdAccessContext(household=household, user=user, member=owner_member, is_owner=False)

    def require_owner(self, *, household_id: str, user: UserModel) -> HouseholdAccessContext:
        context = self.resolve_household_access(household_id=household_id, user=user)
        if not context.is_owner:
            raise PermissionDenied("owner_required", f"User {user.id} is not the owner of household {household_id}.")
        return context

    def resolve_member_scope(self, *, household_id: str, user: UserModel, requested_member_id: str | None) -> str | None:
        context = self.resolve_household_access(household_id=household_id, user=user)
        if context.is_owner:
            if requested_member_id:
                self.member_repo.get_for_household(member_id=requested_member_id, household_id=household_id)
            return requested_member_id
        if context.member is None:
            raise PermissionDenied("member_scope_missing", "This user is not bound to a member scope.")
        if requested_member_id and requested_member_id != context.member.id:
            raise PermissionDenied("member_scope_mismatch", "Members can only query their own records.")
        return context.member.id
