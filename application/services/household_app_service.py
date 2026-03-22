from application.dto.household import HouseholdBootstrapRead, HouseholdBootstrapRequest
from infra.db.repositories import HouseholdRepository, MemberRepository, UserRepository


class HouseholdAppService:
    def __init__(self, user_repo: UserRepository, household_repo: HouseholdRepository, member_repo: MemberRepository) -> None:
        self.user_repo = user_repo
        self.household_repo = household_repo
        self.member_repo = member_repo

    def bootstrap_household(self, request: HouseholdBootstrapRequest) -> HouseholdBootstrapRead:
        user = self.user_repo.get_or_create(email=request.owner_email, display_name=request.owner_display_name)
        household = self.household_repo.create(name=request.household_name, owner_user_id=user.id)
        member = self.member_repo.create(
            household_id=household.id,
            user_id=user.id,
            name=request.member_name or request.owner_display_name,
            role="owner",
        )
        return HouseholdBootstrapRead(user_id=user.id, household_id=household.id, member_id=member.id)

