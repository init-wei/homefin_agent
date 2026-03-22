from application.dto.account import AccountCreateRequest
from infra.db.models import AccountModel
from infra.db.repositories import AccountRepository, HouseholdRepository, MemberRepository


class AccountAppService:
    def __init__(self, account_repo: AccountRepository, household_repo: HouseholdRepository, member_repo: MemberRepository) -> None:
        self.account_repo = account_repo
        self.household_repo = household_repo
        self.member_repo = member_repo

    def create_account(self, request: AccountCreateRequest) -> AccountModel:
        self.household_repo.get(request.household_id)
        if request.member_id:
            self.member_repo.get_for_household(member_id=request.member_id, household_id=request.household_id)
        return self.account_repo.create(**request.model_dump())

    def list_accounts(self, household_id: str, member_id: str | None = None) -> list[AccountModel]:
        self.household_repo.get(household_id)
        return self.account_repo.list_by_household(household_id, member_id)
